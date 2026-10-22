from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config_data.config_reader import config
from utils.backend_api import BackendClient

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
storage = RedisStorage.from_url(config.REDIS_URL)
dp = Dispatcher(storage=storage)
backend = BackendClient(base_url=config.BACKEND_URL)
