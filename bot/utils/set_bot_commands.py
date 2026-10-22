from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command='start', description='Открыть каталог / главное меню'),
            BotCommand(command='help', description='Помощь'),
        ],
    )
