import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from bot.database.models import User, Blacklist, PlanEnum
from bot.database.db import async_session_maker
from bot.config import config
from datetime import datetime, timedelta

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids_list

@router.message(Command("admin_stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    async with async_session_maker() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        
        # Subscriptions breakdown
        subs = await session.execute(
            select(User.plan, func.count(User.id))
            .where(User.plan != PlanEnum.NONE)
            .group_by(User.plan)
        )
        subs_breakdown = "\n".join([f"{row[0].value if hasattr(row[0], 'value') else str(row[0])}: {row[1]}" for row in subs])
        
    text = (
        f"📊 <b>Статистика бота Wardeum:</b>\n\n"
        f"👥 Всего пользователей в БД: {users_count}\n\n"
        f"💎 <b>Активные подписки:</b>\n"
        f"{subs_breakdown if subs_breakdown else 'Нет активных подписок'}"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("ban"))
async def ban_user(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /ban <tg_id> <причина>")
        return
        
    try:
        tg_id = int(args[1])
        reason = args[2]
    except ValueError:
        await message.answer("Неверный ID.")
        return
        
    async with async_session_maker() as session:
        entry = Blacklist(tg_id=tg_id, reason=reason, banned_by=message.from_user.id, is_global=True)
        session.add(entry)
        await session.commit()
        
    await message.answer(f"Пользователь {tg_id} заблокирован в боте.")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /unban <tg_id>")
        return
        
    try:
        tg_id = int(args[1])
    except ValueError:
        await message.answer("Неверный ID.")
        return
        
    async with async_session_maker() as session:
        entry = await session.scalar(select(Blacklist).where(Blacklist.tg_id == tg_id, Blacklist.is_global == True))
        if entry:
            await session.delete(entry)
            await session.commit()
            await message.answer(f"Пользователь {tg_id} разблокирован в боте.")
        else:
            await message.answer("Пользователь не найден в глобальном бане.")

@router.message(Command("give_plan"))
async def give_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.answer("Использование: /give_plan <tg_id> <plan(lite/pro/corporate)> <days>")
        return
        
    try:
        tg_id = int(args[1])
        plan = PlanEnum(args[2].lower())
        days = int(args[3])
    except ValueError:
        await message.answer("Неверные параметры.")
        return
        
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            await message.answer("Пользователь не найден.")
            return
            
        user.plan = plan
        user.subscription_end = datetime.now() + timedelta(days=days)
        await session.commit()
        
    await message.answer(f"Подписка {plan.value} на {days} дней выдана пользователю {tg_id}.")

@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /broadcast <текст рассылки>")
        return
        
    broadcast_text = args[1]
    
    async with async_session_maker() as session:
        stmt = select(User.tg_id)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
    if not users:
        await message.answer("Пользователей в базе данных нет.")
        return
        
    sent_count = 0
    failed_count = 0
    
    status_msg = await message.answer(f"Начинаю рассылку для {len(users)} пользователей...")
    
    for user_tg_id in users:
        try:
            await bot.send_message(chat_id=user_tg_id, text=broadcast_text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)  # Telegram limits protection
        except Exception:
            failed_count += 1
            
    await status_msg.edit_text(
        f"📊 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно доставлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}",
        parse_mode="HTML"
    )
