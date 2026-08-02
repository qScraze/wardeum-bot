import os
from pydantic import field_validator
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
    FORCE_SUB_CHANNEL: int | str | None = None
    FORCE_SUB_ENABLED: bool = False
    SECRET_KEY: str = os.urandom(32).hex()

    @field_validator("FORCE_SUB_CHANNEL", mode="before")
    @classmethod
    def parse_force_sub_channel(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

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
