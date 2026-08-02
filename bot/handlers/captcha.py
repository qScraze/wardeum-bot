from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from bot.database.models import CaptchaSession
from bot.database.db import async_session_maker
from bot.services.captcha_gen import generate_captcha_gif, generate_code
from datetime import datetime, timedelta

router = Router()

@router.message(Command("captcha"), F.chat.type == "private")
async def resend_captcha(message: Message):
    async with async_session_maker() as session:
        stmt = select(CaptchaSession).where(
            CaptchaSession.user_tg_id == message.from_user.id,
            CaptchaSession.passed == False,
            CaptchaSession.expires_at > datetime.now()
        ).order_by(CaptchaSession.created_at.desc())
        
        c_session = await session.scalar(stmt)
        if not c_session:
            await message.answer("У вас нет активной сессии капчи.")
            return
            
        # Generate new code
        new_code = generate_code()
        c_session.code = new_code
        await session.commit()
        
        gif_bytes = generate_captcha_gif(new_code)
        
    await message.answer_animation(
        animation=BufferedInputFile(gif_bytes, filename="captcha.gif"),
        caption="Пожалуйста, введите код с картинки для прохождения проверки."
    )

@router.message(F.chat.type == "private", F.text)
async def process_captcha_answer(message: Message):
    # Ignore commands
    if message.text.startswith("/"):
        return
        
    async with async_session_maker() as session:
        stmt = select(CaptchaSession).where(
            CaptchaSession.user_tg_id == message.from_user.id,
            CaptchaSession.passed == False,
            CaptchaSession.expires_at > datetime.now()
        ).order_by(CaptchaSession.created_at.desc())
        
        c_session = await session.scalar(stmt)
        if not c_session:
            return
            
        answer = message.text.strip()
        if answer.lower() == c_session.code.lower():
            c_session.passed = True
            await session.commit()
            
            # Unrestrict user in chat
            try:
                await message.bot.restrict_chat_member(
                    chat_id=c_session.chat_tg_id,
                    user_id=message.from_user.id,
                    permissions={
                        "can_send_messages": True,
                        "can_send_audios": True,
                        "can_send_documents": True,
                        "can_send_photos": True,
                        "can_send_videos": True,
                        "can_send_video_notes": True,
                        "can_send_voice_notes": True,
                        "can_send_polls": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True
                    }
                )
            except Exception:
                pass
                
            await message.answer("✅ Капча пройдена! Теперь вы можете писать в группе.")
            await session.delete(c_session)
            await session.commit()
        else:
            c_session.attempts += 1
            if c_session.attempts >= 3:
                # Ban user
                try:
                    await message.bot.ban_chat_member(
                        chat_id=c_session.chat_tg_id,
                        user_id=message.from_user.id
                    )
                except Exception:
                    pass
                await message.answer("❌ Вы исчерпали количество попыток и были заблокированы в группе.")
                await session.delete(c_session)
                await session.commit()
            else:
                new_code = generate_code()
                c_session.code = new_code
                await session.commit()
                
                gif_bytes = generate_captcha_gif(new_code)
                await message.answer_animation(
                    animation=BufferedInputFile(gif_bytes, filename="captcha.gif"),
                    caption=f"❌ Неверно. Осталось попыток: {3 - c_session.attempts}. Введите новый код."
                )
