from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    BOT_TOKEN: str = "placeholder_token"
    ADMIN_IDS: str = "123456789"
    DATABASE_URL: str = "sqlite+aiosqlite:///./wardeum.db"
    WEBAPP_URL: str = ""
    SECRET_KEY: str = "super_secret_key_change_me"
    GEMINI_API_KEY: str = ""
    CORS_ORIGINS: str = "*"

    @property
    def admin_ids_list(self) -> list[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
