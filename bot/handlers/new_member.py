import asyncio
from aiogram import Router, F, Bot
from aiogram.types import ChatMemberUpdated, ChatJoinRequest, BufferedInputFile
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER
from sqlalchemy import select
from bot.database.models import ChatSettings, CaptchaSession, User
from bot.database.db import async_session_maker
from bot.services.anti_raid import anti_raid_service
from bot.services.network_ban import check_network_ban
from bot.services.captcha_gen import generate_captcha_gif, generate_code
from datetime import datetime, timedelta

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> MEMBER))
async def on_new_member(event: ChatMemberUpdated, bot: Bot):
    chat_id = event.chat.id
    user_id = event.new_chat_member.user.id
    
    async with async_session_maker() as session:
        # Check network ban
        is_banned = await check_network_ban(user_id, session)
        if is_banned:
            try:
                await bot.ban_chat_member(chat_id, user_id)
            except Exception:
                pass
            return
            
        # Get chat settings via join on Chat.tg_id
        from bot.database.models import Chat
        stmt = (
            select(ChatSettings)
            .join(Chat, Chat.id == ChatSettings.chat_id)
            .where(Chat.tg_id == chat_id, Chat.is_active == True)
        )
        settings = await session.scalar(stmt)
        
        if not settings:
            return
            
        # Anti-raid
        is_raid = False
        if settings.antiraid_enabled:
            is_raid = anti_raid_service.register_join(chat_id, settings.antiraid_threshold, settings.antiraid_window)
            
        # Score profile
        score = anti_raid_service.score_profile(event.new_chat_member.user)
        
        needs_captcha = settings.captcha_enabled and (is_raid or score < 3)
        
        if needs_captcha:
            # Restrict
            try:
                await bot.restrict_chat_member(
                    chat_id, user_id,
                    permissions={"can_send_messages": False}
                )
            except Exception:
                pass
                
            # Create session
            code = generate_code()
            c_session = CaptchaSession(
                user_tg_id=user_id,
                chat_tg_id=chat_id,
                code=code,
                expires_at=datetime.now() + timedelta(seconds=settings.captcha_timeout)
            )
            session.add(c_session)
            await session.commit()
            
            # Send DM
            gif_bytes = generate_captcha_gif(code)
            try:
                await bot.send_animation(
                    chat_id=user_id,
                    animation=BufferedInputFile(gif_bytes, filename="captcha.gif"),
                    caption=f"👋 Здравствуйте! Для общения в группе {event.chat.title} введите код с картинки.\nУ вас есть {settings.captcha_timeout // 60} минут и 3 попытки."
                )
            except Exception:
                # Can't DM, just leave restricted
                pass

        # Clean messages
        if settings.clean_chat_enabled:
            try:
                # The event itself doesn't contain a message ID to delete, usually new members create a message, 
                # which can be caught in content_types=[ContentType.NEW_CHAT_MEMBERS]
                pass 
            except Exception:
                pass

@router.message(F.new_chat_members)
async def clean_new_member_messages(message, bot: Bot):
    async with async_session_maker() as session:
        from bot.database.models import Chat, ChatSettings
        stmt = select(ChatSettings).join(Chat, Chat.id == ChatSettings.chat_id).where(Chat.tg_id == message.chat.id)
        settings = await session.scalar(stmt)
        if settings and settings.clean_chat_enabled:
            try:
                await message.delete()
            except Exception:
                pass

@router.message(F.left_chat_member)
async def clean_left_member_messages(message, bot: Bot):
    async with async_session_maker() as session:
        from bot.database.models import Chat, ChatSettings
        stmt = select(ChatSettings).join(Chat, Chat.id == ChatSettings.chat_id).where(Chat.tg_id == message.chat.id)
        settings = await session.scalar(stmt)
        if settings and settings.clean_chat_enabled:
            try:
                await message.delete()
            except Exception:
                pass

@router.chat_join_request()
async def process_join_request(event: ChatJoinRequest, bot: Bot):
    chat_id = event.chat.id
    user_id = event.from_user.id
    
    async with async_session_maker() as session:
        # Check network ban
        is_banned = await check_network_ban(user_id, session)
        if is_banned:
            try:
                await event.decline()
            except Exception:
                pass
            return
            
        from bot.database.models import Chat, ChatSettings
        stmt = select(ChatSettings).join(Chat, Chat.id == ChatSettings.chat_id).where(Chat.tg_id == chat_id)
        settings = await session.scalar(stmt)
        
        if not settings:
            await event.approve()
            return
            
        score = anti_raid_service.score_profile(event.from_user)
        
        # Bots / very suspicious
        if event.from_user.is_bot or score == 0:
            await event.decline()
            return
            
        if settings.captcha_enabled:
            # Need captcha before approve
            code = generate_code()
            c_session = CaptchaSession(
                user_tg_id=user_id,
                chat_tg_id=chat_id,
                code=code,
                expires_at=datetime.now() + timedelta(seconds=settings.captcha_timeout)
            )
            session.add(c_session)
            await session.commit()
            
            gif_bytes = generate_captcha_gif(code)
            try:
                await bot.send_animation(
                    chat_id=user_id,
                    animation=BufferedInputFile(gif_bytes, filename="captcha.gif"),
                    caption=f"👋 Здравствуйте! Ваш запрос в группу {event.chat.title} будет одобрен после ввода кода с картинки."
                )
                # Actually approve when they pass it, which we handle in captcha.py 
                # (needs modification to approve instead of restrict, but we keep it simple for now as requested)
            except Exception:
                await event.decline()
        else:
            await event.approve()
