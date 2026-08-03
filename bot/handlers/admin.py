import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from bot.database.models import User, Blacklist, PlanEnum
from bot.database.db import async_session_maker
from bot.config import config
from datetime import datetime, timedelta

router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_gift_tg_id = State()
    waiting_for_gift_plan = State()
    waiting_for_gift_days = State()

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids_list

def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🎟 Выдать план", callback_data="admin_gift_start"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")
        ]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
    ])

# --- Интерактивная Панель Админа ---

@router.message(Command("admin"))
async def admin_menu_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    await message.answer(
        "🛠 <b>Панель администратора Wardeum</b>\n\n"
        "Выберите нужное действие на клавиатуре ниже:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
        
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Панель администратора Wardeum</b>\n\n"
        "Выберите нужное действие на клавиатуре ниже:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
        
    async with async_session_maker() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        
        # Subscriptions breakdown
        subs = await session.execute(
            select(User.plan, func.count(User.id))
            .where(User.plan != PlanEnum.NONE)
            .group_by(User.plan)
        )
        subs_breakdown = "\n".join([f"• {row[0].value if hasattr(row[0], 'value') else str(row[0])}: <code>{row[1]}</code>" for row in subs])
        
    text = (
        f"📊 <b>Статистика бота Wardeum:</b>\n\n"
        f"👥 Всего пользователей в БД: <code>{users_count}</code>\n\n"
        f"💎 <b>Активные подписки:</b>\n"
        f"{subs_breakdown if subs_breakdown else 'Нет активных подписок'}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()

# --- Рассылка (FSM) ---

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
        
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение (текст, поддерживается HTML-разметка), которое вы хотите разослать всем пользователям бота.",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
        
    broadcast_text = message.text
    await state.clear()
    
    async with async_session_maker() as session:
        stmt = select(User.tg_id)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
    if not users:
        await message.answer("Пользователей в базе данных нет.", reply_markup=get_admin_keyboard())
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
            
    await status_msg.answer(
        f"📊 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно доставлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# --- Выдача подписки (FSM) ---

@router.callback_query(F.data == "admin_gift_start")
async def admin_gift_start_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
        
    await state.set_state(AdminStates.waiting_for_gift_tg_id)
    await callback.message.edit_text(
        "🎟 <b>Выдача подписки</b>\n\n"
        "Отправьте Telegram ID пользователя, которому хотите выдать тариф:",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_gift_tg_id)
async def process_gift_tg_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    tg_id_str = message.text.strip()
    if not tg_id_str.isdigit():
        await message.answer("❌ ID должен состоять только из цифр. Попробуйте еще раз:", reply_markup=get_back_keyboard())
        return
        
    target_tg_id = int(tg_id_str)
    
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.tg_id == target_tg_id))
        if not user:
            await message.answer("❌ Пользователь с таким Telegram ID не найден в базе данных. Попробуйте еще раз:", reply_markup=get_back_keyboard())
            return
            
    await state.update_data(gift_tg_id=target_tg_id)
    await state.set_state(AdminStates.waiting_for_gift_plan)
    
    plan_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Lite 💳", callback_data="gift_plan_lite"),
            InlineKeyboardButton(text="Pro ⭐", callback_data="gift_plan_pro"),
            InlineKeyboardButton(text="Corporate 💎", callback_data="gift_plan_corporate")
        ],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="admin_menu")]
    ])
    
    await message.answer(
        f"🎟 <b>Выдача подписки</b>\n\n"
        f"Выбран пользователь: <code>{target_tg_id}</code>\n\n"
        f"Выберите тариф подписки:",
        reply_markup=plan_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("gift_plan_"), AdminStates.waiting_for_gift_plan)
async def process_gift_plan(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
        
    selected_plan_str = callback.data.split("_")[2] # "lite", "pro", "corporate"
    selected_plan = PlanEnum(selected_plan_str)
    
    await state.update_data(gift_plan=selected_plan)
    await state.set_state(AdminStates.waiting_for_gift_days)
    
    data = await state.get_data()
    target_tg_id = data.get("gift_tg_id")
    
    await callback.message.edit_text(
        f"🎟 <b>Выдача подписки</b>\n\n"
        f"Пользователь: <code>{target_tg_id}</code>\n"
        f"Тариф: <b>{selected_plan_str.capitalize()}</b>\n\n"
        f"Отправьте количество дней подписки (целое число):",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_gift_days)
async def process_gift_days(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    days_str = message.text.strip()
    if not days_str.isdigit():
        await message.answer("❌ Количество дней должно быть целым числом. Попробуйте еще раз:", reply_markup=get_back_keyboard())
        return
        
    days = int(days_str)
    data = await state.get_data()
    target_tg_id = data.get("gift_tg_id")
    selected_plan = data.get("gift_plan")
    
    await state.clear()
    
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.tg_id == target_tg_id))
        if not user:
            await message.answer("❌ Пользователь потерялся. Попробуйте сначала.", reply_markup=get_admin_keyboard())
            return
            
        user.plan = selected_plan
        now = datetime.now()
        current_end = user.subscription_end if user.subscription_end and user.subscription_end > now else now
        user.subscription_end = current_end + timedelta(days=days)
        await session.commit()
        
    plan_name = {
        PlanEnum.LITE: "Lite",
        PlanEnum.PRO: "Pro",
        PlanEnum.CORPORATE: "Corporate"
    }.get(selected_plan, str(selected_plan))
    
    await message.answer(
        f"✅ <b>Подписка успешно выдана!</b>\n\n"
        f"👤 Пользователь: <code>{target_tg_id}</code>\n"
        f"💎 Тариф: <b>{plan_name}</b>\n"
        f"📅 Добавлено: <b>{days} дней</b>.",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# --- Классические Команды (для обратной совместимости) ---

@router.message(Command("admin_stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    await admin_stats_callback(message) # Поведение аналогичное

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
            await asyncio.sleep(0.05)
        except Exception:
            failed_count += 1
            
    await status_msg.answer(
        f"📊 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно доставлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
