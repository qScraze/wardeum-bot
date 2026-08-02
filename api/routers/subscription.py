import re
import secrets
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.database.db import get_session
from api.middleware.tg_auth import get_current_user
from bot.database.models import User, PromoCode, ActivationKey, Referral, PlanEnum
from api.schemas.schemas import (
    PromoApplyRequest, KeyActivateRequest, PlanInfo,
)

router = APIRouter(tags=["subscription"])

PLANS: list[PlanInfo] = [
    PlanInfo(
        id="lite",
        name="Лайт",
        price=150,
        max_chats=2,
        features=[
            "Фирменная GIF-капча в шуме",
            "Фильтр ссылок и стоп-слов",
            "Удаление уведомлений о входе/выходе",
            "Базовая панель настроек",
        ],
    ),
    PlanInfo(
        id="pro",
        name="Про",
        price=400,
        max_chats=5,
        features=[
            "Всё из тарифа Лайт",
            "ИИ-модерация Google Gemini 2.0 Flash",
            "Умный Anti-Raid со скорингом профилей",
            "Расширенное меню управления",
        ],
    ),
    PlanInfo(
        id="corporate",
        name="Корпоративный",
        price=800,
        max_chats=10,
        features=[
            "Всё из тарифа Про",
            "Wardeum Network — глобальный чёрный список",
            "Максимальная скорость серверов",
            "White-label бот под вашим брендом",
        ],
    ),
]

KEY_PATTERN = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{5}-[A-Z0-9]{5}$")


def _plan_str(user: User) -> str:
    return user.plan.value if hasattr(user.plan, "value") else str(user.plan)


def _extend_subscription(user: User, days: int) -> None:
    """Extend user subscription by N days from today or from current end."""
    now = datetime.utcnow()
    base = user.subscription_end if user.subscription_end and user.subscription_end > now else now
    user.subscription_end = base + timedelta(days=days)


@router.get("/subscription/plans", response_model=list[PlanInfo])
async def get_plans() -> list[PlanInfo]:
    return PLANS


@router.post("/subscription/promo")
async def apply_promo(
    body: PromoApplyRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    code = body.code.strip().upper()
    promo: PromoCode | None = await session.scalar(
        select(PromoCode).where(func.upper(PromoCode.code) == code)
    )

    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден")
    if promo.uses_left == 0:
        raise HTTPException(status_code=400, detail="Промокод уже исчерпан")
    if promo.expires_at and promo.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Срок действия промокода истёк")

    if promo.free_days > 0:
        _extend_subscription(current_user, promo.free_days)

    if promo.uses_left > 0:
        promo.uses_left -= 1

    await session.commit()
    return {
        "success": True,
        "message": f"Промокод применён! +{promo.free_days} дней к подписке.",
        "free_days": promo.free_days,
        "discount_pct": promo.discount_pct,
    }


@router.post("/subscription/key")
async def activate_key(
    body: KeyActivateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    key_str = body.key.strip().upper()
    if not KEY_PATTERN.match(key_str):
        raise HTTPException(status_code=400, detail="Неверный формат ключа. Ожидается: XXXX-XXXX-XXXXX-XXXXX")

    key: ActivationKey | None = await session.scalar(
        select(ActivationKey).where(ActivationKey.key == key_str)
    )

    if not key:
        raise HTTPException(status_code=404, detail="Ключ активации не найден")
    if key.used_by is not None:
        raise HTTPException(status_code=400, detail="Ключ уже использован")

    # Apply plan
    plan_val = key.plan.value if hasattr(key.plan, "value") else str(key.plan)
    current_user.plan = PlanEnum(plan_val)
    _extend_subscription(current_user, key.duration_days)

    key.used_by = current_user.id
    key.used_at = datetime.utcnow()

    await session.commit()
    return {
        "success": True,
        "message": f"Ключ активирован! Тариф «{plan_val.capitalize()}» на {key.duration_days} дней.",
        "plan": plan_val,
        "duration_days": key.duration_days,
    }


@router.get("/subscription/referral")
async def get_referral(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    total_referrals = await session.scalar(
        select(func.count()).where(Referral.inviter_id == current_user.id)
    ) or 0
    total_bonus = await session.scalar(
        select(func.coalesce(func.sum(Referral.bonus_days), 0)).where(
            Referral.inviter_id == current_user.id
        )
    ) or 0

    bot_username = "wardeum_bot"  # change to actual bot username in production
    referral_url = f"https://t.me/{bot_username}?start=ref_{current_user.referral_code}"

    return {
        "code": current_user.referral_code,
        "url": referral_url,
        "total_referrals": total_referrals,
        "total_bonus_days": total_bonus,
    }
