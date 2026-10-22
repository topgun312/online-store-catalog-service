from html import escape
from http import HTTPStatus

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from keyboards.inline.inline_markup import admin_actions_keyboard, category_list_keyboard
from loader import backend, bot
from middleware.admin_middleware import AdminMiddleware
from states.product_states import ProductCreate
from utils.backend_api import BackendError

router = Router(name='create_product')
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


@router.callback_query(F.data == 'admin:panel')
async def admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.answer('Админ-панель:', reply_markup=admin_actions_keyboard())
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == 'admin:create')
async def create_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await _show_category_choice(callback.message, state)
        await callback.message.delete()
    await callback.answer()


async def _show_category_choice(message: Message, state: FSMContext) -> None:
    try:
        categories = await backend.get_categories()
    except BackendError as exc:
        logger.error('get categories failed: {e}', e=exc)
        await message.answer(f'Не удалось получить список категорий: {exc}')
        await state.clear()
        return

    await state.set_state(ProductCreate.waiting_category)
    await state.update_data(
        category_id=None,
        category_name=None,
        category_names={str(category['id']): str(category['name']) for category in categories},
    )
    text = 'Выберите категорию товара:' if categories else 'Категорий пока нет. Добавьте новую:'
    await message.answer(text, reply_markup=category_list_keyboard(categories))


@router.callback_query(ProductCreate.waiting_category, F.data.startswith('category:'))
async def create_category_selected(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    value = callback.data.removeprefix('category:')

    if value == 'new':
        await state.set_state(ProductCreate.waiting_new_category)
        if callback.message:
            await callback.message.answer('Введите название новой категории:')
            await callback.message.delete()
        await callback.answer()
        return

    data = await state.get_data()
    category_name = data.get('category_names', {}).get(value)
    if category_name is None:
        await callback.answer('Категория не найдена, выберите заново.', show_alert=True)
        return

    if callback.message:
        await _ask_for_product(callback.message, state, category_id=value, category_name=category_name)
        await callback.message.delete()
    await callback.answer()


@router.message(ProductCreate.waiting_category, F.text)
async def create_category_from_text(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    name = message.text.strip()
    if not name:
        await message.answer('Название категории не может быть пустым.')
        return
    await _create_category_and_ask_for_product(message, state, name)


@router.message(ProductCreate.waiting_new_category, F.text)
async def create_new_category(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    name = message.text.strip()
    if not name:
        await message.answer('Название категории не может быть пустым.')
        return
    await _create_category_and_ask_for_product(message, state, name)


async def _create_category_and_ask_for_product(message: Message, state: FSMContext, name: str) -> None:
    try:
        category = await backend.create_category(name=name)
    except BackendError as exc:
        if exc.status_code == HTTPStatus.CONFLICT:
            try:
                existing = await backend.find_category_by_name(name)
            except BackendError:
                existing = None
            if existing is not None:
                await _ask_for_product(
                    message,
                    state,
                    category_id=str(existing['id']),
                    category_name=str(existing['name']),
                )
                return
            await message.answer('Такая категория уже существует. Выберите её из списка.')
            await _show_category_choice(message, state)
        else:
            logger.error('create category failed: {e}', e=exc)
            await message.answer(f'Не удалось создать категорию: {exc}. Попробуйте ещё раз.')
        return
    await _ask_for_product(
        message,
        state,
        category_id=str(category['id']),
        category_name=str(category['name']),
    )


async def _ask_for_product(
    message: Message,
    state: FSMContext,
    *,
    category_id: str,
    category_name: str,
) -> None:
    await state.update_data(category_id=category_id, category_name=category_name)
    await state.set_state(ProductCreate.waiting_title_photo)
    await message.answer(
        f'Категория «{escape(category_name)}» выбрана.\n'
        'Отправьте название и фото одним сообщением (подпись к фото).',
    )


@router.message(ProductCreate.waiting_title_photo, F.photo, F.caption)
async def create_product_process(message: Message, state: FSMContext) -> None:
    assert message.photo is not None
    assert message.caption is not None
    title = message.caption.strip()
    if not title:
        await message.answer('Подпись пустая — отправьте непустое название.')
        return

    data = await state.get_data()
    category_id = data.get('category_id')

    file = await bot.download(message.photo[-1])
    file_bytes = file.read() if hasattr(file, 'read') else bytes(file)
    content_type = 'image/jpeg'

    try:
        product = await backend.create_product(
            title=title,
            file_bytes=file_bytes,
            content_type=content_type,
            category_id=category_id,
        )
    except BackendError as exc:
        logger.error('create product failed: {e}', e=exc)
        await message.answer(f'Не удалось создать товар: {exc}')
    else:
        await message.answer(f'Товар «{escape(str(product["title"]))}» создан ✅')
    finally:
        await state.clear()


@router.message(ProductCreate.waiting_title_photo)
async def create_product_trap(message: Message) -> None:
    await message.answer('Нужно именно фото с подписью-названием 📸✍️')


@router.message(ProductCreate.waiting_category)
async def create_category_trap(message: Message) -> None:
    await message.answer('Выберите категорию кнопкой или отправьте название новой категории текстом.')


@router.message(ProductCreate.waiting_new_category)
async def create_new_category_trap(message: Message) -> None:
    await message.answer('Введите название категории текстом.')
