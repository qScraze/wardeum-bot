from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PromoCreateRequest(BaseModel):
    code: str
    discount_pct: int = 0
    free_days: int = 0
    uses_left: int = -1
    expires_at: Optional[datetime] = None


class PromoResponse(BaseModel):
    id: int
    code: str
    discount_pct: int
    free_days: int
    uses_left: int
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KeyCreateRequest(BaseModel):
    plan: str
    duration_days: int
    count: int = 1


class KeyCreateResponse(BaseModel):
    keys: list[str]


class KeyListItem(BaseModel):
    id: int
    key: str
    plan: str
    duration_days: int
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ForceSubUpdate(BaseModel):
    enabled: bool
    channel_id: Optional[int] = None


class AdminStatsResponse(BaseModel):
    total_users: int
    active_subscriptions: dict
    total_chats: int
    blacklist_count: int


class UserAdminView(BaseModel):
    tg_id: int
    username: Optional[str] = None
    first_name: str
    plan: str
    subscription_end: Optional[datetime] = None
    extra_days: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GrantPlanRequest(BaseModel):
    plan: str
    days: int


class AddToBlacklistRequest(BaseModel):
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    reason: str
