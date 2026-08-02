from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from bot.database.models import ForceSub
from bot.database.db import async_session_maker
from bot.config import config

def format_telegram_channel_id(channel_id: int | str) -> int | str:
    if not channel_id:
        return ""
    s = str(channel_id).strip()
    if s.startswith("@"):
        return s
    if s.startswith("-100"):
        return int(s)
    if s.lstrip("-").isdigit():
        val = abs(int(s))
        return int(f"-100{val}")
    return s

def format_channel_url(channel_id: int | str) -> str:
    if not channel_id:
        return ""
    s = str(channel_id).strip()
    if s.startswith("@"):
        return f"https://t.me/{s[1:]}"
    clean = s.replace("-100", "").lstrip("-")
    return f"https://t.me/c/{clean}"

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat.type != "private":
            return await handler(event, data)
            
        bot: Bot = data.get("bot")
        user_id = event.from_user.id
        
        # Bypass check for bot admins
        if user_id in config.admin_ids_list:
            return await handler(event, data)
        
        async with async_session_maker() as session:
            stmt = select(ForceSub).where(ForceSub.id == 1)
            result = await session.execute(stmt)
            force_sub = result.scalar_one_or_none()
            
            if force_sub and force_sub.enabled and force_sub.channel_id:
                try:
                    target_chat_id = format_telegram_channel_id(force_sub.channel_id)
                    member = await bot.get_chat_member(chat_id=target_chat_id, user_id=user_id)
                    if member.status in ["left", "kicked"]:
                        # User is not subscribed
                        url = format_channel_url(force_sub.channel_id)
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Присоединиться", url=url)]
                        ])
                        await event.answer("Для использования бота необходимо подписаться на наш канал!", reply_markup=keyboard)
                        return
                except Exception:
                    # If bot can't check, just let it pass or handle gracefully
                    pass
                    
        return await handler(event, data)

