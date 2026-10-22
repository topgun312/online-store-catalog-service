import asyncio
import signal
import sys

from aiohttp import web
from loguru import logger

from config_data.config_reader import config
from handlers.command_handlers import start_help_command
from handlers.menu_handlers import create_product_command, manage_products_command
from loader import backend, bot, dp, storage
from utils.set_bot_commands import set_bot_commands

dp.include_router(start_help_command.router)
dp.include_router(create_product_command.router)
dp.include_router(manage_products_command.router)


async def on_startup() -> None:
    await set_bot_commands(bot)
    webhook_url = f'{config.WEBHOOK_URL.rstrip("/")}{config.WEBHOOK_PATH}'
    if not config.WEBHOOK_URL:
        logger.warning('WEBHOOK_URL is empty, set_webhook is skipped (local mode)')
    elif config.SET_WEBHOOK_ON_STARTUP:
        await bot.set_webhook(url=webhook_url, secret_token=config.WEBHOOK_SECRET or None)
        logger.info('webhook registered: {url}', url=webhook_url)
    else:
        logger.info('set_webhook is disabled, using existing webhook')
    logger.info('bot started (backend={url})', url=backend.base_url)


async def on_shutdown() -> None:
    if config.DELETE_WEBHOOK_ON_SHUTDOWN and config.WEBHOOK_URL:
        await bot.delete_webhook()
        logger.info('webhook deleted')
    await storage.close()
    await backend.aclose()
    await bot.session.close()
    logger.info('bot stopped')


async def handle_webhook(request: web.Request) -> web.Response:
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if config.WEBHOOK_SECRET and secret != config.WEBHOOK_SECRET:
        return web.Response(status=403)
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response()


async def handle_healthz(request: web.Request) -> web.Response:
    try:
        await storage.redis.ping()
    except Exception:
        logger.exception('healthcheck failed: redis is unavailable')
        return web.json_response({'status': 'error', 'redis': 'unavailable'}, status=503)
    return web.json_response({'status': 'ok'})


async def main() -> None:
    logger.remove()
    logger.add(sys.stdout, level='INFO')
    if config.LOG_TO_FILE:
        logger.add(config.LOG_FILE, rotation='10 MB', serialize=True)

    app = web.Application()
    app.router.add_post(config.WEBHOOK_PATH, handle_webhook)
    app.router.add_get('/healthz', handle_healthz)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.WEBHOOK_PORT)  # noqa: S104

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await on_startup()
        await site.start()
        logger.info(
            'webhook server listening on 0.0.0.0:{port}{path}',
            port=config.WEBHOOK_PORT,
            path=config.WEBHOOK_PATH,
        )
        await stop_event.wait()
    finally:
        await on_shutdown()
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
