import os
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: Any = ""
    DATABASE_URL: str = 'sqlite+aiosqlite:///./wardeum.db'
    FORCE_SUB_CHANNEL: int | str | None = None
    FORCE_SUB_ENABLED: bool = False

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()

