import asyncio

from loguru import logger

from config_data.config_reader import config
from loader import backend, bot, storage


async def main() -> None:
    if not config.WEBHOOK_URL:
        msg = 'WEBHOOK_URL is empty, webhook registration is skipped'
        raise RuntimeError(msg)
    webhook_url = f'{config.WEBHOOK_URL.rstrip("/")}{config.WEBHOOK_PATH}'
    try:
        await bot.set_webhook(url=webhook_url, secret_token=config.WEBHOOK_SECRET or None)
        logger.info('webhook registered: {url}', url=webhook_url)
    finally:
        await storage.close()
        await backend.aclose()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
