from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int
    tg_id: int
    username: Optional[str] = None
    first_name: str
    plan: str
    subscription_end: Optional[datetime] = None
    extra_days: int
    referral_code: str
    is_admin: bool = False

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class ChatSettingsUpdate(BaseModel):
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

class ChatResponse(BaseModel):
    id: int
    tg_id: int
    title: str
    username: Optional[str] = None
    is_active: bool
    settings: Optional[ChatSettingsResponse] = None

    class Config:
        from_attributes = True

class AddChatRequest(BaseModel):
    tg_id: int
    title: str
    username: Optional[str] = None

class PromoApplyRequest(BaseModel):
    code: str

class KeyActivateRequest(BaseModel):
    key: str

class PlanInfo(BaseModel):
    id: str
    name: str
    price: int
    max_chats: int
    features: list[str]

class BlacklistEntryResponse(BaseModel):
    id: int
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    reason: str
    banned_by: int
    is_global: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PromoCreateRequest(BaseModel):
    code: str
    discount_pct: int = 0
    free_days: int = 0
    uses_left: int = -1
    expires_at: Optional[datetime] = None

class KeyCreateRequest(BaseModel):
    plan: str
    duration_days: int
    count: int = 1

class ForceSubUpdate(BaseModel):
    enabled: bool
    channel_id: Optional[int] = None

class GrantPlanRequest(BaseModel):
    plan: str
    days: int

class AddToBlacklistRequest(BaseModel):
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    reason: str
