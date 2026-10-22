from html import escape
from http import HTTPStatus

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from keyboards.inline.inline_markup import (
    category_list_keyboard,
    delete_confirm_keyboard,
    edit_product_actions_keyboard,
    product_list_keyboard,
)
from loader import backend, bot
from middleware.admin_middleware import AdminMiddleware
from states.product_states import ProductEdit, ProductSelect
from utils.backend_api import BackendError

router = Router(name='manage_products')
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

PRODUCTS_PER_PAGE = 20


def _edit_prompt_text() -> str:
    return (
        'Отправьте изменение:\n'
        '— новое фото с подписью (название + фото),\n'
        '— фото без подписи (оставить старое название),\n'
        '— текст без фото (оставить старое фото).\n'
        'Или нажмите «Изменить категорию».'
    )


async def _ask_for_edit(message: Message, state: FSMContext, *, prefix: str | None = None) -> None:
    await state.set_state(ProductEdit.waiting_title_photo)
    text = f'{prefix}\n\n{_edit_prompt_text()}' if prefix else _edit_prompt_text()
    await message.answer(text, reply_markup=edit_product_actions_keyboard())


async def _show_edit_category_choice(message: Message, state: FSMContext) -> None:
    try:
        categories = await backend.get_categories()
    except BackendError as exc:
        logger.error('get categories failed: {e}', e=exc)
        await message.answer(f'Не удалось получить список категорий: {exc}')
        return

    await state.set_state(ProductEdit.choosing_category)
    await state.update_data(
        category_names={str(category['id']): str(category['name']) for category in categories},
    )
    text = 'Выберите новую категорию:' if categories else 'Категорий пока нет. Добавьте новую:'
    await message.answer(
        text,
        reply_markup=category_list_keyboard(
            categories,
            prefix='edit_category',
            back_callback='edit_category:back',
        ),
    )


async def _show_product_list(message: Message, state: FSMContext, action: str) -> None:
    try:
        products = await backend.get_products(per_page=PRODUCTS_PER_PAGE)
    except BackendError as exc:
        logger.error('get products failed: {e}', e=exc)
        await message.answer(f'Не удалось получить список товаров: {exc}')
        return
    if not products:
        await message.answer('Товаров пока нет')
        return
    await state.set_state(ProductSelect.choosing)
    labels = [{'id': str(product['id']), 'title': product['title']} for product in products]
    await state.update_data(action=action, titles={item['id']: item['title'] for item in labels})
    await message.answer('Выберите товар:', reply_markup=product_list_keyboard(labels))


@router.callback_query(F.data == 'admin:edit')
async def edit_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await _show_product_list(callback.message, state, action='edit')
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == 'admin:delete')
async def delete_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await _show_product_list(callback.message, state, action='delete')
        await callback.message.delete()
    await callback.answer()


@router.callback_query(ProductSelect.choosing, F.data.startswith('product:'))
async def product_selected(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    product_id = callback.data.removeprefix('product:')
    data = await state.get_data()
    action = data.get('action')
    title = data.get('titles', {}).get(product_id, product_id)

    if action == 'delete':
        await callback.message.answer(
            f'Точно удалить «{title}»?',
            reply_markup=delete_confirm_keyboard(product_id),
        )
    elif action == 'edit':
        await state.update_data(product_id=product_id)
        await _ask_for_edit(callback.message, state)
    if callback.message:
        await callback.message.delete()
    await callback.answer()


@router.callback_query(ProductEdit.waiting_title_photo, F.data == 'edit_category:start')
async def edit_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await _show_edit_category_choice(callback.message, state)
        await callback.message.delete()
    await callback.answer()


@router.callback_query(ProductEdit.choosing_category, F.data.startswith('edit_category:'))
async def edit_category_selected(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    value = callback.data.removeprefix('edit_category:')

    if value == 'new':
        await state.set_state(ProductEdit.waiting_new_category)
        if callback.message:
            await callback.message.answer('Введите название новой категории:')
            await callback.message.delete()
        await callback.answer()
        return

    if value == 'back':
        if callback.message:
            await _ask_for_edit(callback.message, state)
            await callback.message.delete()
        await callback.answer()
        return

    data = await state.get_data()
    category_name = data.get('category_names', {}).get(value)
    if category_name is None:
        await callback.answer('Категория не найдена, выберите заново.', show_alert=True)
        return

    if callback.message:
        await _apply_category_edit(
            callback.message,
            state,
            category_id=value,
            category_name=category_name,
        )
        await callback.message.delete()
    await callback.answer()


@router.message(ProductEdit.waiting_new_category, F.text)
async def edit_new_category(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    name = message.text.strip()
    if not name:
        await message.answer('Название категории не может быть пустым.')
        return

    try:
        category = await backend.create_category(name=name)
    except BackendError as exc:
        if exc.status_code == HTTPStatus.CONFLICT:
            try:
                existing = await backend.find_category_by_name(name)
            except BackendError:
                existing = None
            if existing is not None:
                await _apply_category_edit(
                    message,
                    state,
                    category_id=str(existing['id']),
                    category_name=str(existing['name']),
                )
                return
            await message.answer('Такая категория уже существует. Выберите её из списка.')
            await _show_edit_category_choice(message, state)
        else:
            logger.error('create category failed: {e}', e=exc)
            await message.answer(f'Не удалось создать категорию: {exc}. Попробуйте ещё раз.')
        return

    await _apply_category_edit(
        message,
        state,
        category_id=str(category['id']),
        category_name=str(category['name']),
    )


async def _apply_category_edit(
    message: Message,
    state: FSMContext,
    *,
    category_id: str,
    category_name: str,
) -> None:
    data = await state.get_data()
    product_id = data.get('product_id')
    if not product_id:
        await message.answer('Товар не выбран, начните заново: «Изменить товар».')
        await state.clear()
        return

    try:
        product = await backend.update_product(product_id=product_id, category_id=category_id)
    except BackendError as exc:
        logger.error('update product category failed: {e}', e=exc)
        await message.answer(f'Не удалось изменить категорию: {exc}')
        return

    await _ask_for_edit(
        message,
        state,
        prefix=(
            f'Категория «{escape(category_name)}» установлена ✅\nТовар «{escape(str(product["title"]))}» обновлён.'
        ),
    )


@router.callback_query(F.data.startswith('delete_confirm:'))
async def delete_product_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    product_id = callback.data.removeprefix('delete_confirm:')
    try:
        await backend.delete_product(product_id)
    except BackendError as exc:
        logger.error('delete product failed: {e}', e=exc)
        await callback.answer(f'Не удалось удалить: {exc}', show_alert=True)
        if callback.message:
            await callback.message.delete()
        return
    await state.clear()
    await callback.message.answer('Удалено ✅')
    if callback.message:
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == 'delete_cancel')
async def delete_product_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Удаление отменено.')
    if callback.message:
        await callback.message.delete()
    await callback.answer()


async def _apply_edit(
    message: Message,
    state: FSMContext,
    *,
    title: str | None,
    file_bytes: bytes | None,
) -> None:
    data = await state.get_data()
    product_id = data.get('product_id')
    if not product_id:
        await message.answer('Товар не выбран, начните заново: «Изменить товар».')
        await state.clear()
        return
    try:
        product = await backend.update_product(product_id=product_id, title=title, file_bytes=file_bytes)
    except BackendError as exc:
        logger.error('update product failed: {e}', e=exc)
        await message.answer(f'Не удалось обновить товар: {exc}')
    else:
        await message.answer(f'Товар «{product["title"]}» обновлён ✅')
    finally:
        await state.clear()


@router.message(ProductEdit.waiting_title_photo, F.photo, F.caption)
async def edit_title_and_photo(message: Message, state: FSMContext) -> None:
    assert message.photo is not None
    assert message.caption is not None
    title = message.caption.strip()
    if not title:
        await message.answer('Подпись пустая — отправьте непустое название или фото без подписи.')
        return
    file = await bot.download(message.photo[-1])
    file_bytes = file.read() if hasattr(file, 'read') else bytes(file)
    await _apply_edit(message, state, title=title, file_bytes=file_bytes)


@router.message(ProductEdit.waiting_title_photo, F.photo)
async def edit_photo_only(message: Message, state: FSMContext) -> None:
    assert message.photo is not None
    file = await bot.download(message.photo[-1])
    file_bytes = file.read() if hasattr(file, 'read') else bytes(file)
    await _apply_edit(message, state, title=None, file_bytes=file_bytes)


@router.message(ProductEdit.waiting_title_photo, F.text)
async def edit_title_only(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    title = message.text.strip()
    if not title:
        await message.answer('Название пустое — отправьте непустой текст или фото.')
        return
    await _apply_edit(message, state, title=title, file_bytes=None)


@router.message(ProductEdit.waiting_title_photo)
async def edit_trap(message: Message) -> None:
    await message.answer('Отправьте фото и/или текст (см. подсказку выше).')


@router.message(ProductEdit.choosing_category)
async def edit_category_choice_trap(message: Message) -> None:
    await message.answer('Выберите категорию кнопкой ниже или нажмите «Назад».')


@router.message(ProductEdit.waiting_new_category)
async def edit_new_category_trap(message: Message) -> None:
    await message.answer('Введите название категории текстом.')
