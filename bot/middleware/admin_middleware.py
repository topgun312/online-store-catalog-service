from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru import logger

from config_data.config_reader import config


class AdminMiddleware(BaseMiddleware):
    """Restrict handlers to admin users."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get('event_from_user')
        if user is None or user.id not in config.admin_ids:
            logger.warning('non-admin user tried to access admin route: {user}', user=user)
            return None
        return await handler(event, data)
