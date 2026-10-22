from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

MAX_TITLE_LABEL_LEN = 32


def catalog_webapp_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Открыть каталог', web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1)
    return builder.as_markup()


def catalog_and_admin_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Открыть каталог', web_app=WebAppInfo(url=webapp_url))
    builder.button(text='🛠 Админ-панель', callback_data='admin:panel')
    builder.adjust(1)
    return builder.as_markup()


def admin_actions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ Создать товар', callback_data='admin:create')
    builder.button(text='✏️ Изменить товар', callback_data='admin:edit')
    builder.button(text='🗑 Удалить товар', callback_data='admin:delete')
    builder.adjust(1)
    return builder.as_markup()


def category_list_keyboard(
    categories: list[dict],
    *,
    prefix: str = 'category',
    back_callback: str = 'admin:panel',
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        name = str(category.get('name', ''))
        label = name if len(name) <= MAX_TITLE_LABEL_LEN else f'{name[: MAX_TITLE_LABEL_LEN - 1]}…'
        builder.button(text=label, callback_data=f"{prefix}:{category['id']}")
    builder.button(text='➕ Добавить категорию', callback_data=f'{prefix}:new')
    builder.button(text='« Назад', callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()


def edit_product_actions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='🏷 Изменить категорию', callback_data='edit_category:start')
    builder.adjust(1)
    return builder.as_markup()


def product_list_keyboard(products: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        title = str(product.get('title', ''))
        label = title if len(title) <= MAX_TITLE_LABEL_LEN else f'{title[: MAX_TITLE_LABEL_LEN - 1]}…'
        builder.button(text=label, callback_data=f"product:{product['id']}")
    builder.button(text='« Назад', callback_data='admin:panel')
    builder.adjust(1)
    return builder.as_markup()


def delete_confirm_keyboard(product_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Точно удалить', callback_data=f'delete_confirm:{product_id}')
    builder.button(text='❌ Отмена', callback_data='delete_cancel')
    builder.adjust(1)
    return builder.as_markup()
