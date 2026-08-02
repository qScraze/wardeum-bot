from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from bot.database.models import Blacklist, Chat

async def add_to_network(tg_id: int, reason: str, banned_by: int, session: AsyncSession) -> None:
    stmt = select(Blacklist).where(Blacklist.tg_id == tg_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    
    if not entry:
        entry = Blacklist(tg_id=tg_id, reason=reason, banned_by=banned_by, is_global=True)
        session.add(entry)
    else:
        entry.is_global = True
        entry.reason = reason
        entry.banned_by = banned_by
    await session.commit()

async def check_network_ban(tg_id: int, session: AsyncSession) -> Blacklist | None:
    stmt = select(Blacklist).where(Blacklist.tg_id == tg_id, Blacklist.is_global == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def remove_from_network(tg_id: int, session: AsyncSession) -> bool:
    stmt = select(Blacklist).where(Blacklist.tg_id == tg_id, Blacklist.is_global == True)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    
    if entry:
        await session.delete(entry)
        await session.commit()
        return True
    return False

async def propagate_ban(bot: Bot, tg_id: int, chat_ids: list[int]) -> None:
    for chat_id in chat_ids:
        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=tg_id)
        except Exception:
            pass
