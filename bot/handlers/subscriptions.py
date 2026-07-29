"""
Платные подписки на Telegram-каналы.

Флоу владельца канала:
  меню → создать подписку → channel_id → валюта → цена/мес → готово
  → получает ссылку для пользователей

Флоу подписчика:
  переходит по ссылке → видит условия → оплачивает
  → бот добавляет его в канал через invite link

Автопродление: отдельная фоновая задача проверяет истёкшие подписки.
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ChatInviteLink
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    create_subscription, pay_subscription,
    get_active_subscriptions, get_wallet
)
from bot.keyboards.main_kb import back_keyboard, currency_keyboard, confirm_keyboard

router = Router()
BOT_USERNAME = "Switzerwalletbot"


class SubStates(StatesGroup):
    waiting_channel_id = State()
    waiting_currency   = State()
    waiting_price      = State()
    confirm            = State()


# ─── МЕНЮ ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sub_menu")
async def sub_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать подписку", callback_data="sub_create")],
        [InlineKeyboardButton(text="📋 Мои подписки", callback_data="sub_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(
        "💳 <b>Платные подписки</b>\n\n"
        "Подключи платный доступ к своему Telegram-каналу.\n"
        "Пользователи платят криптой — ты получаешь автоматически.",
        reply_markup=kb, parse_mode="HTML"
    )
    await callback.answer()


# ─── СОЗДАНИЕ ПОДПИСКИ ────────────────────────────────────────────────────────

@router.callback_query(F.data == "sub_create")
async def sub_create_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "➕ <b>Создание подписки</b>\n\n"
        "Шаги:\n"
        "1. Добавь бота @Switzerwalletbot в свой канал как администратора\n"
        "2. Введи числовой ID канала\n\n"
        "Как узнать ID канала:\n"
        "• Перешли любое сообщение из канала боту @userinfobot\n"
        "• Или используй @username_to_id_bot\n\n"
        "Введи ID канала (например: <code>-1001234567890</code>):",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(SubStates.waiting_channel_id)
    await callback.answer()


@router.message(SubStates.waiting_channel_id)
async def sub_channel_id(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    try:
        channel_id = int(text)
    except ValueError:
        await message.answer("❌ ID канала должен быть числом. Например: -1001234567890")
        return

    # Проверяем что бот является администратором канала
    try:
        chat = await bot.get_chat(channel_id)
        member = await bot.get_chat_member(channel_id, (await bot.get_me()).id)
        if member.status not in ("administrator", "creator"):
            await message.answer(
                "❌ Бот не является администратором этого канала.\n"
                "Добавь @Switzerwalletbot как администратора и попробуй снова."
            )
            return
        channel_title = chat.title or str(channel_id)
    except (TelegramForbiddenError, TelegramBadRequest):
        await message.answer(
            "❌ Не удалось получить информацию о канале.\n"
            "Убедись что бот добавлен в канал как администратор."
        )
        return

    await state.update_data(channel_id=channel_id, channel_title=channel_title)
    await message.answer(
        f"✅ Канал найден: <b>{channel_title}</b>\n\nВыбери валюту подписки:",
        reply_markup=currency_keyboard(prefix="sub_cur"),
        parse_mode="HTML"
    )
    await state.set_state(SubStates.waiting_currency)


@router.callback_query(SubStates.waiting_currency, F.data.startswith("sub_cur_"))
async def sub_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[2]
    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"Валюта: <b>{currency}</b>\n\nВведи цену подписки <b>в месяц</b>:",
        parse_mode="HTML"
    )
    await state.set_state(SubStates.waiting_price)
    await callback.answer()


@router.message(SubStates.waiting_price)
async def sub_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму")
        return

    await state.update_data(price=str(price))
    data = await state.get_data()

    await message.answer(
        f"📋 <b>Подтверди подписку</b>\n\n"
        f"Канал: <b>{data['channel_title']}</b>\n"
        f"Цена: <b>{price} {data['currency']}/мес</b>\n\n"
        f"После создания ты получишь ссылку для пользователей.",
        reply_markup=confirm_keyboard(yes_data="sub_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(SubStates.confirm)


@router.callback_query(SubStates.confirm, F.data == "sub_confirm")
async def sub_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    sub = await create_subscription(
        session,
        owner_id=callback.from_user.id,
        channel_id=data["channel_id"],
        channel_title=data["channel_title"],
        currency=data["currency"],
        price_month=Decimal(data["price"])
    )

    pay_link = f"https://t.me/{BOT_USERNAME}?start=sub_{sub.id}"
    await callback.message.edit_text(
        f"✅ <b>Подписка создана!</b>\n\n"
        f"Канал: <b>{sub.channel_title}</b>\n"
        f"Цена: <b>{sub.price_month} {sub.currency}/мес</b>\n\n"
        f"🔗 Ссылка для подписчиков:\n<code>{pay_link}</code>\n\n"
        f"Размести её в описании канала или закреплённом посте.",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ─── МОИ ПОДПИСКИ ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sub_list")
async def sub_list(callback: CallbackQuery, session: AsyncSession):
    subs = await get_active_subscriptions(session, callback.from_user.id)

    if not subs:
        await callback.message.edit_text(
            "📋 У тебя нет активных подписок.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    lines = ["📋 <b>Твои подписки</b>\n"]
    for s in subs:
        lines.append(
            f"• <b>{s.channel_title}</b>\n"
            f"  {s.price_month} {s.currency}/мес"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ─── ОПЛАТА ПОДПИСКИ (deep link: /start sub_<id>) ─────────────────────────────

@router.message(F.text.regexp(r"^/start sub_(\d+)$"))
async def deeplink_sub(message: Message, session: AsyncSession, bot: Bot):
    import re
    match = re.match(r"^/start sub_(\d+)$", message.text)
    sub_id = int(match.group(1))

    from sqlalchemy import select
    from database.models import Subscription
    result = await session.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.is_active == True  # noqa
        )
    )
    sub = result.scalar_one_or_none()

    if not sub:
        await message.answer("❌ Подписка не найдена.")
        return

    wallet = await get_wallet(session, message.from_user.id, sub.currency)
    has_funds = wallet and wallet.balance >= sub.price_month
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 Подписаться за {sub.price_month} {sub.currency}/мес",
            callback_data=f"sub_pay_{sub_id}_1"
        )],
        [InlineKeyboardButton(
            text=f"💰 3 месяца ({sub.price_month * 3} {sub.currency})",
            callback_data=f"sub_pay_{sub_id}_3"
        )],
    ])

    balance_note = (
        f"💰 Твой баланс {sub.currency}: <b>{wallet.balance:.4f}</b>"
        if wallet else ""
    )

    await message.answer(
        f"📺 <b>{sub.channel_title}</b>\n\n"
        f"Цена подписки: <b>{sub.price_month} {sub.currency}/мес</b>\n"
        f"{balance_note}\n\n"
        f"Выбери период:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub_pay_"))
async def sub_pay(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split("_")
    sub_id = int(parts[2])
    months = int(parts[3])

    ok, err = await pay_subscription(session, sub_id, callback.from_user.id, months)

    if not ok:
        await callback.answer(f"❌ {err}", show_alert=True)
        return

    # Получаем подписку для генерации invite link
    from sqlalchemy import select
    from database.models import Subscription
    result = await session.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()

    # Генерируем одноразовую invite ссылку
    invite_link = None
    if sub:
        try:
            link_obj: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=sub.channel_id,
                member_limit=1,   # одноразовая
                name=f"sub_{callback.from_user.id}"
            )
            invite_link = link_obj.invite_link
        except Exception:
            pass

    if invite_link:
        await callback.message.edit_text(
            f"✅ <b>Подписка оплачена!</b>\n\n"
            f"Период: <b>{months} мес.</b>\n\n"
            f"🔗 Ссылка для вступления (одноразовая):\n{invite_link}\n\n"
            f"⚠️ Ссылка одноразовая — используй сразу.",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"✅ <b>Подписка оплачена на {months} мес!</b>\n\n"
            f"Свяжись с владельцем канала для получения доступа.",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    await callback.answer()