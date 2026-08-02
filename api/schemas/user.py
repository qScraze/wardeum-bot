from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    tg_id: int
    username: Optional[str] = None
    first_name: str
    plan: str
    subscription_end: Optional[datetime] = None
    extra_days: int
    referral_code: str
    is_admin: bool = False

    model_config = {"from_attributes": True}
