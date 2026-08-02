from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from bot.database.models import ForceSub
from bot.database.db import async_session_maker

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
        
        async with async_session_maker() as session:
            stmt = select(ForceSub).where(ForceSub.id == 1)
            result = await session.execute(stmt)
            force_sub = result.scalar_one_or_none()
            
            if force_sub and force_sub.enabled and force_sub.channel_id:
                try:
                    member = await bot.get_chat_member(chat_id=force_sub.channel_id, user_id=event.from_user.id)
                    if member.status in ["left", "kicked"]:
                        # User is not subscribed
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Присоединиться", url=f"https://t.me/c/{str(force_sub.channel_id).replace('-100', '')}")]
                        ])
                        await event.answer("Для использования бота необходимо подписаться на наш канал!", reply_markup=keyboard)
                        return
                except Exception:
                    # If bot can't check, just let it pass or handle gracefully
                    pass
                    
        return await handler(event, data)
