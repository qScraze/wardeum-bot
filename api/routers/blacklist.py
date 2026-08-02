from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from api.database.db import get_session
from api.middleware.tg_auth import get_current_user
from bot.database.models import User, Chat, Blacklist
from api.schemas.schemas import BlacklistEntryResponse

router = APIRouter(tags=["blacklist"])


@router.get("/blacklist", response_model=dict)
async def get_blacklist(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Возвращает ЧС для чатов текущего пользователя + глобальные записи."""
    # Get user's chat tg_ids
    chats_result = await session.execute(
        select(Chat.tg_id).where(Chat.owner_id == current_user.id, Chat.is_active == True)
    )
    chat_ids = [r for r in chats_result.scalars().all()]

    offset = (page - 1) * limit
    stmt = (
        select(Blacklist)
        .where(or_(Blacklist.is_global == True, Blacklist.chat_tg_id.in_(chat_ids)))
        .order_by(Blacklist.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()

    from sqlalchemy import func
    total = await session.scalar(
        select(func.count()).select_from(Blacklist).where(
            or_(Blacklist.is_global == True, Blacklist.chat_tg_id.in_(chat_ids))
        )
    ) or 0

    return {
        "items": [BlacklistEntryResponse.model_validate(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.delete("/blacklist/{tg_id}", status_code=204)
async def remove_from_blacklist(
    tg_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаляет из ЧС (только записи из своих чатов; глобальные — только через /admin)."""
    chats_result = await session.execute(
        select(Chat.tg_id).where(Chat.owner_id == current_user.id)
    )
    chat_ids = [r for r in chats_result.scalars().all()]

    entry = await session.scalar(
        select(Blacklist).where(
            Blacklist.tg_id == tg_id,
            Blacklist.chat_tg_id.in_(chat_ids),
            Blacklist.is_global == False,
        )
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена или недостаточно прав")

    await session.delete(entry)
    await session.commit()
