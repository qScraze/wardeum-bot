from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BlacklistEntryResponse(BaseModel):
    id: int
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    reason: str
    banned_by: int
    is_global: bool
    chat_tg_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlacklistListResponse(BaseModel):
    items: list[BlacklistEntryResponse]
    total: int
    page: int
    limit: int
