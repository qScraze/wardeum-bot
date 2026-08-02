from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import select
from bot.database.models import User
from bot.database.db import async_session_maker
from bot.services.referral import generate_referral_code, process_referral
from bot.config import config

router = Router()

@router.message(CommandStart())
async def start_cmd(message: Message):
    args = message.text.split(maxsplit=1)
    ref_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            new_ref_code = await generate_referral_code()
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                referral_code=new_ref_code
            )
            session.add(user)
            await session.flush()
            
            if ref_code:
                await process_referral(ref_code, message.from_user.id, session)
                
            await session.commit()
            
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Открыть Mini App", web_app=WebAppInfo(url=config.WEBAPP_URL))]
    ])
    
    welcome_text = (
        "🛡 <b>Добро пожаловать в Wardeum!</b>\n\n"
        "Я — ваш надежный защитник чатов в Telegram. Я спасу вашу группу от спама, "
        "рейдов и нежелательного контента с помощью искусственного интеллекта.\n\n"
        "Нажмите кнопку ниже, чтобы настроить защиту через удобное Mini App!"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

@router.message(Command("help"))
async def help_cmd(message: Message):
    text = (
        "<b>Помощь по Wardeum:</b>\n"
        "Для настройки бота, добавьте его в свою группу с правами администратора, "
        "затем откройте Mini App по кнопке в меню /start.\n\n"
        "Команды:\n"
        "/start - Перезапустить бота\n"
        "/help - Справка\n"
        "/captcha - Запросить новую капчу (в случае необходимости)"
    )
    await message.answer(text, parse_mode="HTML")
