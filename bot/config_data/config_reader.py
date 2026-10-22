from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Bot settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    BOT_TOKEN: str
    ADMIN_IDS: Annotated[list[int], NoDecode] = Field(default_factory=list)
    BACKEND_URL: str = 'http://localhost:8000'
    REDIS_URL: str = 'redis://localhost:6379/0'
    WEBAPP_URL: str = ''
    WEBHOOK_URL: str = ''
    WEBHOOK_PATH: str = '/webhook'
    WEBHOOK_PORT: int = 8081
    WEBHOOK_SECRET: str = ''
    SET_WEBHOOK_ON_STARTUP: bool = True
    DELETE_WEBHOOK_ON_SHUTDOWN: bool = False
    LOG_TO_FILE: bool = False
    LOG_FILE: str = 'logs.json'

    @field_validator('ADMIN_IDS', mode='before')
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return [int(part) for part in value.split(',') if part.strip()]
        return value

    @property
    def admin_ids(self) -> frozenset[int]:
        return frozenset(self.ADMIN_IDS)


config = Settings()
