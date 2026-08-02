import secrets
import string
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.database.db import get_session
from api.middleware.tg_auth import get_current_admin
from api.config import settings
from bot.database.models import (
    User, Chat, Blacklist, PromoCode, ActivationKey, ForceSub, PlanEnum
)
from api.schemas.schemas import (
    PromoCreateRequest, KeyCreateRequest, ForceSubUpdate,
    GrantPlanRequest, AddToBlacklistRequest, BlacklistEntryResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])

KEY_ALPHABET = string.ascii_uppercase + string.digits


def _generate_key() -> str:
    """Generate activation key in format XXXX-XXXX-XXXXX-XXXXX."""
    def seg(n: int) -> str:
        return "".join(secrets.choice(KEY_ALPHABET) for _ in range(n))
    return f"{seg(4)}-{seg(4)}-{seg(5)}-{seg(5)}"


def _plan_str(plan) -> str:
    return plan.value if hasattr(plan, "value") else str(plan)


@router.get("/stats")
async def get_stats(
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    total_users = await session.scalar(select(func.count()).select_from(User)) or 0
    total_chats = await session.scalar(
        select(func.count()).select_from(Chat).where(Chat.is_active == True)
    ) or 0
    blacklist_count = await session.scalar(select(func.count()).select_from(Blacklist)) or 0

    # Subscription breakdown
    subs: dict[str, int] = {}
    now = datetime.utcnow()
    for plan in PlanEnum:
        count = await session.scalar(
            select(func.count()).select_from(User).where(
                User.plan == plan,
                User.subscription_end > now,
            )
        ) or 0
        if count:
            subs[plan.value] = count

    return {
        "total_users": total_users,
        "active_subscriptions": subs,
        "total_chats": total_chats,
        "blacklist_count": blacklist_count,
    }


@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * limit
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            User.username.ilike(pattern) | User.first_name.ilike(pattern)
        )
    users = (await session.execute(stmt)).scalars().all()
    total = await session.scalar(select(func.count()).select_from(User)) or 0
    return {
        "items": [
            {
                "tg_id": u.tg_id,
                "username": u.username,
                "first_name": u.first_name,
                "plan": _plan_str(u.plan),
                "subscription_end": u.subscription_end,
                "extra_days": u.extra_days,
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/users/{tg_id}/grant")
async def grant_plan(
    tg_id: int,
    body: GrantPlanRequest,
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        user.plan = PlanEnum(body.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный тариф: {body.plan}")

    now = datetime.utcnow()
    base = user.subscription_end if user.subscription_end and user.subscription_end > now else now
    user.subscription_end = base + timedelta(days=body.days)
    await session.commit()
    return {"success": True, "message": f"Тариф {body.plan} выдан на {body.days} дней"}


@router.post("/promo")
async def create_promo(
    body: PromoCreateRequest,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.scalar(
        select(PromoCode).where(func.upper(PromoCode.code) == body.code.upper())
    )
    if existing:
        raise HTTPException(status_code=400, detail="Промокод уже существует")

    promo = PromoCode(
        code=body.code.upper(),
        discount_pct=body.discount_pct,
        free_days=body.free_days,
        uses_left=body.uses_left,
        expires_at=body.expires_at,
        created_by=current_user.tg_id,
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    return {
        "success": True,
        "promo": {
            "id": promo.id,
            "code": promo.code,
            "discount_pct": promo.discount_pct,
            "free_days": promo.free_days,
            "uses_left": promo.uses_left,
            "expires_at": promo.expires_at,
            "created_at": promo.created_at,
        },
    }


@router.get("/promos")
async def list_promos(
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    promos = (await session.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))).scalars().all()
    return [
        {
            "id": p.id, "code": p.code, "discount_pct": p.discount_pct,
            "free_days": p.free_days, "uses_left": p.uses_left,
            "expires_at": p.expires_at, "created_at": p.created_at,
        }
        for p in promos
    ]


@router.post("/keys")
async def create_keys(
    body: KeyCreateRequest,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        plan = PlanEnum(body.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный тариф: {body.plan}")

    count = min(body.count, 100)  # safety cap
    generated: list[str] = []

    for _ in range(count):
        key_str = _generate_key()
        # Ensure uniqueness
        while await session.scalar(select(ActivationKey).where(ActivationKey.key == key_str)):
            key_str = _generate_key()

        key = ActivationKey(
            key=key_str,
            plan=plan,
            duration_days=body.duration_days,
            created_by=current_user.tg_id,
        )
        session.add(key)
        generated.append(key_str)

    await session.commit()
    return {"keys": generated}


@router.get("/keys")
async def list_keys(
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    keys = (
        await session.execute(select(ActivationKey).order_by(ActivationKey.created_at.desc()))
    ).scalars().all()
    return [
        {
            "id": k.id, "key": k.key,
            "plan": _plan_str(k.plan), "duration_days": k.duration_days,
            "used": k.used_by is not None, "used_at": k.used_at,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(
    key_id: int,
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    key = await session.scalar(select(ActivationKey).where(ActivationKey.id == key_id))
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    await session.delete(key)
    await session.commit()


@router.put("/force-sub")
async def update_force_sub(
    body: ForceSubUpdate,
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    from bot.middlewares.subscription import format_telegram_channel_id

    parsed_channel_id = None
    if body.channel_id is not None and str(body.channel_id).strip():
        formatted = format_telegram_channel_id(body.channel_id)
        if isinstance(formatted, int):
            parsed_channel_id = formatted
        elif str(formatted).lstrip("-").isdigit():
            parsed_channel_id = int(formatted)

    force_sub = await session.scalar(select(ForceSub).where(ForceSub.id == 1))
    if not force_sub:
        force_sub = ForceSub(id=1, enabled=body.enabled, channel_id=parsed_channel_id)
        session.add(force_sub)
    else:
        force_sub.enabled = body.enabled
        force_sub.channel_id = parsed_channel_id
    await session.commit()
    return {"success": True, "enabled": force_sub.enabled, "channel_id": force_sub.channel_id}



@router.get("/force-sub")
async def get_force_sub(
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    force_sub = await session.scalar(select(ForceSub).where(ForceSub.id == 1))
    return {
        "enabled": force_sub.enabled if force_sub else False,
        "channel_id": force_sub.channel_id if force_sub else None,
    }


@router.get("/blacklist")
async def admin_list_blacklist(
    page: int = 1,
    limit: int = 50,
    global_only: bool = False,
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * limit
    stmt = select(Blacklist).order_by(Blacklist.created_at.desc()).offset(offset).limit(limit)
    if global_only:
        stmt = stmt.where(Blacklist.is_global == True)

    rows = (await session.execute(stmt)).scalars().all()
    total = await session.scalar(select(func.count()).select_from(Blacklist)) or 0
    return {
        "items": [BlacklistEntryResponse.model_validate(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/blacklist", status_code=201)
async def admin_add_blacklist(
    body: AddToBlacklistRequest,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    entry = Blacklist(
        tg_id=body.tg_id,
        username=body.username,
        first_name=body.first_name,
        reason=body.reason,
        banned_by=current_user.tg_id,
        is_global=True,
        chat_tg_id=None,
    )
    session.add(entry)
    await session.commit()
    return {"success": True}


@router.delete("/blacklist/{tg_id}", status_code=204)
async def admin_remove_blacklist(
    tg_id: int,
    _: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    entry = await session.scalar(
        select(Blacklist).where(Blacklist.tg_id == tg_id, Blacklist.is_global == True)
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    await session.delete(entry)
    await session.commit()
