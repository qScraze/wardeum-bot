import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str | list[int] = ""
    DATABASE_URL: str = 'sqlite+aiosqlite:///./wardeum.db'
    GEMINI_API_KEY: str = ''
    WEBAPP_URL: str = ''
    WEBHOOK_URL: str = ''
    WEBHOOK_PATH: str = '/webhook'
    HOST: str = '0.0.0.0'
    PORT: int = 8080
    FORCE_SUB_CHANNEL: int | None = None
    FORCE_SUB_ENABLED: bool = False
    SECRET_KEY: str = os.urandom(32).hex()

    @property
    def admin_ids_list(self) -> list[int]:
        if isinstance(self.ADMIN_IDS, list):
            return self.ADMIN_IDS
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in str(self.ADMIN_IDS).split(",") if x.strip().isdigit()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()
