from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from bot.database.models import User, Referral, PromoCode, ActivationKey, PlanEnum
from bot.database.db import async_session_maker
from bot.services.referral import generate_referral_code, process_referral
from bot.services.captcha_gen import generate_code, generate_captcha_gif
from bot.config import config
from datetime import datetime, timedelta

router = Router()

class RedeemCodeState(StatesGroup):
    waiting_for_code = State()

def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals")
        ],
        [
            InlineKeyboardButton(text="💳 Подписка", callback_data="subscription"),
            InlineKeyboardButton(text="🎟 Активировать код", callback_data="activate_code")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids_list

async def send_captcha(message: Message, session):
    # Генерируем новый код
    code = generate_code()
    
    # Ищем или создаем пользователя в БД
    stmt = select(User).where(User.tg_id == message.from_user.id)
    user = await session.scalar(stmt)
    
    if not user:
        new_ref_code = await generate_referral_code()
        user = User(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referral_code=new_ref_code,
            captcha_passed=False,
            captcha_code=code
        )
        session.add(user)
    else:
        user.captcha_code = code
        user.captcha_passed = False
        
    await session.commit()
    
    # Генерируем GIF
    gif_bytes = generate_captcha_gif(code)
    
    await message.answer_animation(
        animation=BufferedInputFile(gif_bytes, filename="captcha.gif"),
        caption="🤖 <b>Проверка на робота</b>\n\nЧтобы начать пользоваться ботом, пожалуйста, введите код с картинки выше:",
        parse_mode="HTML"
    )

@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    # Сбрасываем любые состояния FSM при старте
    await state.clear()
    
    args = message.text.split(maxsplit=1)
    ref_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]

    async with async_session_maker() as session:
        # Проверяем, является ли пользователь админом
        user_is_admin = is_admin(message.from_user.id)
        
        stmt = select(User).where(User.tg_id == message.from_user.id)
        user = await session.scalar(stmt)

        if not user:
            new_ref_code = await generate_referral_code()
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                referral_code=new_ref_code,
                captcha_passed=True if user_is_admin else False
            )
            session.add(user)
            await session.flush()
            
            if ref_code and not user_is_admin:
                await process_referral(ref_code, message.from_user.id, session)
                
            await session.commit()
        elif user_is_admin and not user.captcha_passed:
            user.captcha_passed = True
            await session.commit()

        # Если админ — сразу пускаем
        if user_is_admin:
            welcome_text = (
                "🛡 <b>Добро пожаловать в Wardeum (Панель Администратора)!</b>\n\n"
                "Вы авторизованы как администратор. Капча пропущена.\n"
                "Выберите нужное действие в меню ниже:"
            )
            await message.answer(welcome_text, reply_markup=get_start_keyboard(), parse_mode="HTML")
            return
            
        # Для обычных пользователей проверяем прохождение капчи
        if not user.captcha_passed:
            await send_captcha(message, session)
            return

    # Если капча уже пройдена обычным пользователем
    welcome_text = (
        "🛡 <b>Добро пожаловать в Wardeum!</b>\n\n"
        "Я — ваш персональный Telegram бот с поддержкой реферальной системы и управления подписками.\n\n"
        "Выберите нужное действие в меню ниже:"
    )
    await message.answer(welcome_text, reply_markup=get_start_keyboard(), parse_mode="HTML")

# Обработчик проверки капчи
@router.message(F.text, ~F.text.startswith("/"))
async def check_captcha_msg(message: Message, state: FSMContext):
    # Если пользователь находится в FSM состояниях (например, вводит промокод), то капча не проверяется тут
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Если пользователь админ, то капча его не касается
    if is_admin(message.from_user.id):
        return

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        user = await session.scalar(stmt)
        
        # Если пользователя нет в БД или капча уже пройдена — ничего не делаем
        if not user or user.captcha_passed:
            return
            
        user_code = message.text.strip()
        
        if user.captcha_code and user_code.lower() == user.captcha_code.lower():
            # Капча пройдена!
            user.captcha_passed = True
            user.captcha_code = None
            await session.commit()
            
            await message.answer("✅ <b>Проверка успешно пройдена!</b>", parse_mode="HTML")
            
            welcome_text = (
                "🛡 <b>Добро пожаловать в Wardeum!</b>\n\n"
                "Вы успешно подтвердили, что не являетесь роботом.\n"
                "Выберите нужное действие в меню ниже:"
            )
            await message.answer(welcome_text, reply_markup=get_start_keyboard(), parse_mode="HTML")
        else:
            # Капча не пройдена, генерируем новую
            await message.answer("❌ <b>Неверный код!</b> Попробуйте еще раз.", parse_mode="HTML")
            await send_captcha(message, session)

@router.message(Command("help"))
async def help_cmd(message: Message):
    # Не пускаем к справке, если капча не пройдена
    if not is_admin(message.from_user.id):
        async with async_session_maker() as session:
            user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
            if not user or not user.captcha_passed:
                return

    text = (
        "<b>Справка по боту Wardeum:</b>\n\n"
        "Используйте кнопки под сообщением для быстрой навигации:\n"
        "👤 <b>Профиль</b> — информация о вашей подписке и реферальной ссылке.\n"
        "👥 <b>Рефералы</b> — статистика ваших приглашений.\n"
        "💳 <b>Подписка</b> — информация о тарифах.\n"
        "🎟 <b>Активировать код</b> — активация промокодов и ключей.\n\n"
        "Команды:\n"
        "/start - Перезапустить бота\n"
        "/help - Показать эту справку"
    )
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    text = (
        "<b>Справка по боту Wardeum:</b>\n\n"
        "Используйте кнопки под сообщением для быстрой навигации:\n"
        "👤 <b>Профиль</b> — информация о вашей подписке и реферальной ссылке.\n"
        "👥 <b>Рефералы</b> — статистика ваших приглашений.\n"
        "💳 <b>Подписка</b> — информация о тарифах.\n"
        "🎟 <b>Активировать код</b> — активация промокодов и ключей.\n\n"
        "Команды:\n"
        "/start - Перезапустить бота\n"
        "/help - Показать эту справку"
    )
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, bot: Bot):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == callback.from_user.id)
        user = await session.scalar(stmt)
        
        if not user:
            await callback.answer("Ошибка: пользователь не найден в базе данных.", show_alert=True)
            return

        bot_info = await bot.get_me()
        bot_username = bot_info.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.tg_id}"
        
        plan_name = {
            PlanEnum.NONE: "Отсутствует",
            PlanEnum.LITE: "Lite 💳",
            PlanEnum.PRO: "Pro ⭐",
            PlanEnum.CORPORATE: "Corporate 💎"
        }.get(user.plan, str(user.plan))
        
        now = datetime.now()
        sub_end_str = "Истекла"
        if user.subscription_end:
            if user.subscription_end > now:
                sub_end_str = user.subscription_end.strftime("%d.%m.%Y %H:%M")
            else:
                sub_end_str = f"Истекла ({user.subscription_end.strftime('%d.%m.%Y %H:%M')})"
        elif user.plan != PlanEnum.NONE:
            sub_end_str = "Бессрочно"

        text = (
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"🆔 <b>Telegram ID:</b> <code>{user.tg_id}</code>\n"
            f"💎 <b>Тариф подписки:</b> {plan_name}\n"
            f"📅 <b>Срок действия:</b> <code>{sub_end_str}</code>\n"
            f"🎁 <b>Бонусные дни:</b> <code>{user.extra_days}</code>\n\n"
            f"🔗 <b>Ваша реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>"
        )
        
        await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "referrals")
async def referrals_callback(callback: CallbackQuery, bot: Bot):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == callback.from_user.id)
        user = await session.scalar(stmt)
        
        if not user:
            await callback.answer("Пользователь не найден.", show_alert=True)
            return

        # Получаем количество приглашенных
        count_stmt = select(func.count(Referral.id)).where(Referral.inviter_id == user.id)
        referrals_count = await session.scalar(count_stmt)

        bot_info = await bot.get_me()
        bot_username = bot_info.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.tg_id}"

        text = (
            f"👥 <b>Ваши рефералы:</b>\n\n"
            f"📊 <b>Всего приглашено:</b> <code>{referrals_count}</code>\n"
            f"🎁 <b>Заработано бонусных дней:</b> <code>{user.extra_days}</code>\n\n"
            f"📢 Приглашайте друзей по вашей ссылке и получайте по <b>5 дней подписки</b> за каждого приглашенного пользователя!\n\n"
            f"🔗 <b>Ваша реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>"
        )
        
        await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "subscription")
async def subscription_callback(callback: CallbackQuery):
    text = (
        "💳 <b>Тарифные планы Wardeum:</b>\n\n"
        "1️⃣ <b>Lite Plan</b>\n"
        "• Базовый доступ к возможностям бота.\n"
        "• Стоимость: 290 руб / мес.\n\n"
        "2️⃣ <b>Pro Plan</b>\n"
        "• Полный доступ к расширенным функциям.\n"
        "• Стоимость: 590 руб / мес.\n\n"
        "3️⃣ <b>Corporate Plan</b>\n"
        "• Максимальные лимиты и приоритетная поддержка.\n"
        "• Стоимость: 1190 руб / мес.\n\n"
        "📎 Для активации подписки вы можете использовать <b>активационный ключ</b> или <b>промокод</b> кнопкой ниже."
    )
    
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "activate_code")
async def activate_code_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RedeemCodeState.waiting_for_code)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_redeem")]
    ])
    
    await callback.message.edit_text(
        "🎟 <b>Активация кода</b>\n\n"
        "Пожалуйста, отправьте ваш промокод или активационный ключ ответным сообщением.",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_redeem")
async def cancel_redeem_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛡 <b>Добро пожаловать в Wardeum!</b>\n\n"
        "Выберите нужное действие в меню ниже:",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RedeemCodeState.waiting_for_code)
async def process_redeem_code(message: Message, state: FSMContext):
    code_text = message.text.strip()
    await state.clear()

    now = datetime.now()

    async with async_session_maker() as session:
        # Ищем пользователя
        user_stmt = select(User).where(User.tg_id == message.from_user.id)
        user = await session.scalar(user_stmt)
        if not user:
            await message.answer("❌ <b>Ошибка:</b> пользователь не найден в базе данных.", parse_mode="HTML")
            return

        # 1. Проверяем активационный ключ
        key_stmt = select(ActivationKey).where(ActivationKey.key == code_text)
        act_key = await session.scalar(key_stmt)

        if act_key:
            if act_key.used_by is not None:
                await message.answer("❌ <b>Этот активационный ключ уже был использован.</b>", reply_markup=get_start_keyboard(), parse_mode="HTML")
                return
            
            # Активируем ключ
            act_key.used_by = user.id
            act_key.used_at = now
            
            # Начисляем подписку
            user.plan = act_key.plan
            
            current_end = user.subscription_end if user.subscription_end and user.subscription_end > now else now
            user.subscription_end = current_end + timedelta(days=act_key.duration_days)
            
            await session.commit()
            
            plan_name = {
                PlanEnum.LITE: "Lite",
                PlanEnum.PRO: "Pro",
                PlanEnum.CORPORATE: "Corporate"
            }.get(act_key.plan, str(act_key.plan))
            
            await message.answer(
                f"✅ <b>Успешная активация!</b>\n\n"
                f"Активирован ключ тарифа: <b>{plan_name}</b>\n"
                f"Срок действия продлен на <b>{act_key.duration_days} дней</b>.",
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
            return

        # 2. Проверяем промокод
        promo_stmt = select(PromoCode).where(PromoCode.code == code_text)
        promo = await session.scalar(promo_stmt)

        if promo:
            if promo.expires_at and promo.expires_at < now:
                await message.answer("❌ <b>Срок действия этого промокода истек.</b>", reply_markup=get_start_keyboard(), parse_mode="HTML")
                return
            
            if promo.uses_left == 0:
                await message.answer("❌ <b>Этот промокод исчерпал лимит использований.</b>", reply_markup=get_start_keyboard(), parse_mode="HTML")
                return

            # Если промокод дает дни подписки
            if promo.free_days > 0:
                if user.plan == PlanEnum.NONE:
                    user.plan = PlanEnum.LITE # Даем базовый план
                
                current_end = user.subscription_end if user.subscription_end and user.subscription_end > now else now
                user.subscription_end = current_end + timedelta(days=promo.free_days)

            # Уменьшаем количество использований
            if promo.uses_left > 0:
                promo.uses_left -= 1
                
            await session.commit()
            
            await message.answer(
                f"✅ <b>Промокод активирован!</b>\n\n"
                f"Вам начислено <b>{promo.free_days} дней</b> бесплатного доступа.",
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
            return

        # Если код не подошел
        await message.answer(
            "❌ <b>Код не найден или недействителен.</b>\n\n"
            "Пожалуйста, проверьте правильность ввода кода.",
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )
