from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config_data.config_reader import config
from keyboards.inline.inline_markup import catalog_and_admin_keyboard, catalog_webapp_keyboard

router = Router(name='start_help')


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = 'У меня есть товар 📦\nКаталог открыт по кнопке ниже 👇'
    if message.from_user and message.from_user.id in config.admin_ids:
        markup = catalog_and_admin_keyboard(config.WEBAPP_URL)
    else:
        markup = catalog_webapp_keyboard(config.WEBAPP_URL)
    await message.answer(text, reply_markup=markup)


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    await message.answer(
        'Это бот каталога товаров.\n'
        'Кнопка «Открыть каталог» — страница товаров (Telegram Mini App).\n'
        'Админам доступна панель управления товарами.',
    )
