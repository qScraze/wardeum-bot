import json
import re
from aiogram import Router, F, Bot
from aiogram.types import Message
from sqlalchemy import select
from bot.database.models import ChatSettings, Chat, User, PlanEnum
from bot.database.db import async_session_maker
from bot.services.ai_censor import ai_censor

router = Router()

URL_REGEX = re.compile(r'(https?://\S+|www\.\S+|\w+\.\w+/\S*)')

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def message_filter(message: Message, bot: Bot):
    if not message.text and not message.caption:
        return
        
    text = message.text or message.caption
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if admin
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return
    except Exception:
        pass
        
    async with async_session_maker() as session:
        # Get settings & chat owner plan
        stmt = select(ChatSettings, User.plan).join(Chat, Chat.id == ChatSettings.chat_id).join(User, User.id == Chat.owner_id).where(Chat.tg_id == chat_id)
        result = await session.execute(stmt)
        row = result.first()
        
        if not row:
            return
            
        settings: ChatSettings = row[0]
        owner_plan: PlanEnum = row[1]
        
        # Link filter
        if settings.link_filter_enabled:
            if URL_REGEX.search(text):
                try:
                    await message.delete()
                    await message.answer(f"🚫 {message.from_user.first_name}, ссылки в этом чате запрещены!")
                except Exception:
                    pass
                return
                
        # Stop words
        if settings.stop_words_filter_enabled:
            try:
                stop_words = json.loads(settings.stop_words)
                text_lower = text.lower()
                if any(word.lower() in text_lower for word in stop_words):
                    try:
                        await message.delete()
                        await message.answer(f"🚫 {message.from_user.first_name}, ваше сообщение содержит запрещенные слова!")
                    except Exception:
                        pass
                    return
            except json.JSONDecodeError:
                pass
                
        # AI Censor
        if settings.ai_censor_enabled and owner_plan in [PlanEnum.PRO, PlanEnum.CORPORATE]:
            # Simple context fetching (last 3 messages could be passed, but we pass empty for performance/simplicity here)
            context = [] 
            censor_result = await ai_censor.analyze_message(text, context)
            
            if censor_result.is_harmful:
                try:
                    await message.delete()
                    reason_ru = {
                        "spam": "спам",
                        "scam": "мошенничество",
                        "adult": "18+ контент",
                        "ads": "реклама"
                    }.get(censor_result.category, "запрещенный контент")
                    
                    await message.answer(f"🤖 Сообщение от {message.from_user.first_name} удалено AI-фильтром (причина: {reason_ru}).")
                except Exception:
                    pass
