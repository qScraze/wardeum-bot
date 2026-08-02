from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# ChatSettings
# ---------------------------------------------------------------------------

class ChatSettingsResponse(BaseModel):
    ai_censor_enabled: bool
    captcha_enabled: bool
    antiraid_enabled: bool
    clean_chat_enabled: bool
    link_filter_enabled: bool
    stop_words_filter_enabled: bool
    stop_words: list[str]
    antiraid_threshold: int
    antiraid_window: int
    captcha_timeout: int

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_stop_words(cls, data: Any) -> Any:
        """
        ORM objects expose stop_words as a JSON string.
        Convert it to a list before Pydantic validates.
        """
        if hasattr(data, "stop_words"):
            # SQLAlchemy model instance
            raw = data.stop_words
            if isinstance(raw, str):
                try:
                    words = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    words = []
                # Return a plain dict for the remaining validators
                return {
                    "ai_censor_enabled": data.ai_censor_enabled,
                    "captcha_enabled": data.captcha_enabled,
                    "antiraid_enabled": data.antiraid_enabled,
                    "clean_chat_enabled": data.clean_chat_enabled,
                    "link_filter_enabled": data.link_filter_enabled,
                    "stop_words_filter_enabled": data.stop_words_filter_enabled,
                    "stop_words": words,
                    "antiraid_threshold": data.antiraid_threshold,
                    "antiraid_window": data.antiraid_window,
                    "captcha_timeout": data.captcha_timeout,
                }
        return data


class ChatSettingsUpdate(BaseModel):
    """PATCH body — every field is optional."""
    ai_censor_enabled: Optional[bool] = None
    captcha_enabled: Optional[bool] = None
    antiraid_enabled: Optional[bool] = None
    clean_chat_enabled: Optional[bool] = None
    link_filter_enabled: Optional[bool] = None
    stop_words_filter_enabled: Optional[bool] = None
    stop_words: Optional[list[str]] = None
    antiraid_threshold: Optional[int] = None
    antiraid_window: Optional[int] = None
    captcha_timeout: Optional[int] = None


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    id: int
    tg_id: int
    title: str
    username: Optional[str] = None
    is_active: bool
    settings: Optional[ChatSettingsResponse] = None

    model_config = {"from_attributes": True}


class AddChatRequest(BaseModel):
    tg_id: int
    title: str
    username: Optional[str] = None
