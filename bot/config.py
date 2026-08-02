import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: list[int]
    DATABASE_URL: str = 'sqlite+aiosqlite:///./wardeum.db'
    GEMINI_API_KEY: str = ''
    WEBAPP_URL: str
    WEBHOOK_URL: str = ''
    WEBHOOK_PATH: str = '/webhook'
    HOST: str = '0.0.0.0'
    PORT: int = 8080
    FORCE_SUB_CHANNEL: int | None = None
    FORCE_SUB_ENABLED: bool = False
    SECRET_KEY: str = os.urandom(32).hex()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()
