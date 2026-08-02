from typing import Any
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    BOT_TOKEN: str = "placeholder_token"
    ADMIN_IDS: Any = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./wardeum.db"
    WEBAPP_URL: str = ""
    SECRET_KEY: str = "super_secret_key_change_me"
    GEMINI_API_KEY: str = ""
    CORS_ORIGINS: str = "*"

    @property
    def admin_ids_list(self) -> list[int]:
        if isinstance(self.ADMIN_IDS, int):
            return [self.ADMIN_IDS]
        if isinstance(self.ADMIN_IDS, list):
            res = []
            for x in self.ADMIN_IDS:
                try:
                    res.append(int(x))
                except (ValueError, TypeError):
                    pass
            return res
        if not self.ADMIN_IDS:
            return []
        res = []
        for x in str(self.ADMIN_IDS).split(","):
            x_clean = x.strip()
            if x_clean.lstrip("-").isdigit():
                res.append(int(x_clean))
        return res

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

