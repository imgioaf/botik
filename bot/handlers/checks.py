from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import create_check, activate_check, get_user_checks
from bot.keyboards.main_kb import back_keyboard, currency_keyboard, confirm_keyboard

router = Router()
BOT_USERNAME = "Switzerwalletbot"  # замени на реальный username бота


class CheckStates(StatesGroup):
    waiting_currency = State()
    waiting_amount = State()
    confirm = State()
    waiting_code = State()


# ─── МЕНЮ ЧЕКОВ ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "check_menu")
async def check_menu(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать чек", callback_data="check_create")],
        [InlineKeyboardButton(text="✅ Активировать чек", callback_data="check_activate")],
        [InlineKeyboardButton(text="📋 Мои чеки", callback_data="check_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(
        "🧾 <b>Чеки</b>\n\nМоментальный перевод по ссылке без комиссии.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


# ─── СОЗДАНИЕ ЧЕКА ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "check_create")
async def create_check_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🧾 <b>Создание чека</b>\n\nВыбери валюту:",
        reply_markup=currency_keyboard(prefix="check_cur"),
        parse_mode="HTML"
    )
    await state.set_state(CheckStates.waiting_currency)
    await callback.answer()


@router.callback_query(CheckStates.waiting_currency, F.data.startswith("check_cur_"))
async def check_currency_selected(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    currency = callback.data.split("_")[2]
    from database.crud import get_wallet
    wallet = await get_wallet(session, callback.from_user.id, currency)

    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"💰 Баланс: <b>{wallet.balance:.6f} {currency}</b>\n\nВведи сумму чека:",
        parse_mode="HTML"
    )
    await state.set_state(CheckStates.waiting_amount)
    await callback.answer()


@router.message(CheckStates.waiting_amount)
async def check_amount_entered(
    message: Message, state: FSMContext, session: AsyncSession
):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= Decimal("0"):
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму")
        return

    data = await state.get_data()
    from database.crud import get_wallet
    wallet = await get_wallet(session, message.from_user.id, data["currency"])

    if wallet.balance < amount:
        await message.answer(
            f"❌ Недостаточно средств.\n"
            f"Доступно: <b>{wallet.balance:.6f} {data['currency']}</b>",
            parse_mode="HTML"
        )
        return

    await state.update_data(amount=str(amount))
    await message.answer(
        f"📋 <b>Подтверди создание чека</b>\n\n"
        f"Сумма: <b>{amount} {data['currency']}</b>\n"
        f"Комиссия: <b>0 (бесплатно)</b>\n\n"
        f"Средства будут заморожены до активации.",
        reply_markup=confirm_keyboard(yes_data="check_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(CheckStates.confirm)


@router.callback_query(CheckStates.confirm, F.data == "check_confirm")
async def check_confirmed(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    await state.clear()

    check = await create_check(
        session,
        creator_id=callback.from_user.id,
        currency=data["currency"],
        amount=Decimal(data["amount"])
    )

    if not check:
        await callback.message.edit_text(
            "❌ Не удалось создать чек. Проверь баланс.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    link = f"https://t.me/{BOT_USERNAME}?start=check_{check.code}"
    await callback.message.edit_text(
        f"✅ <b>Чек создан!</b>\n\n"
        f"Сумма: <b>{check.amount} {check.currency}</b>\n\n"
        f"🔗 Ссылка для активации:\n{link}\n\n"
        f"Отправь эту ссылку получателю. Чек одноразовый.",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ─── АКТИВАЦИЯ ЧЕКА ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "check_activate")
async def activate_check_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ <b>Активация чека</b>\n\nВведи код чека или нажми на ссылку из чека:",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CheckStates.waiting_code)
    await callback.answer()


@router.message(CheckStates.waiting_code)
async def activate_check_code(
    message: Message, state: FSMContext, session: AsyncSession
):
    code = message.text.strip()
    await state.clear()

    check, err = await activate_check(session, code=code, user_id=message.from_user.id)

    if not check:
        await message.answer(f"❌ {err}", reply_markup=back_keyboard())
        return

    await message.answer(
        f"✅ <b>Чек активирован!</b>\n\n"
        f"Зачислено: <b>+{check.amount} {check.currency}</b>",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


# Обработка deep link: /start check_<code>
@router.message(F.text.regexp(r"^/start check_(.+)$"))
async def deeplink_check(message: Message, session: AsyncSession):
    import re
    match = re.match(r"^/start check_(.+)$", message.text)
    code = match.group(1)

    check, err = await activate_check(session, code=code, user_id=message.from_user.id)

    if not check:
        await message.answer(f"❌ {err}")
        return

    await message.answer(
        f"✅ <b>Чек активирован!</b>\n\nЗачислено: <b>+{check.amount} {check.currency}</b>",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


# ─── МОИ ЧЕКИ ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "check_list")
async def list_checks(callback: CallbackQuery, session: AsyncSession):
    checks = await get_user_checks(session, callback.from_user.id)

    if not checks:
        await callback.message.edit_text(
            "📋 У тебя пока нет чеков.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    lines = ["📋 <b>Твои чеки</b>\n"]
    for c in checks:
        status = "✅ активирован" if c.is_activated else "⏳ ожидает"
        lines.append(f"{c.amount} {c.currency} — {status}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()