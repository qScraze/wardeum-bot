from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromoApplyRequest(BaseModel):
    code: str


class PromoApplyResponse(BaseModel):
    success: bool
    message: str
    free_days: int = 0
    discount_pct: int = 0


class KeyActivateRequest(BaseModel):
    key: str


class KeyActivateResponse(BaseModel):
    success: bool
    message: str
    plan: str = ""
    duration_days: int = 0


class PlanFeature(BaseModel):
    name: str


class PlanInfo(BaseModel):
    id: str
    name: str
    price: int  # RUB/month
    max_chats: int
    features: list[str]


class ReferralInfo(BaseModel):
    code: str
    url: str
    total_referrals: int
    total_bonus_days: int
