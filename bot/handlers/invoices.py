from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    create_invoice, pay_invoice, get_user_by_username
)
from bot.keyboards.main_kb import (
    back_keyboard, currency_keyboard, confirm_keyboard
)

router = Router()
BOT_USERNAME = "Switzerwalletbot"  # замени на реальный username бота


class InvoiceStates(StatesGroup):
    waiting_username = State()
    waiting_currency = State()
    waiting_amount = State()
    waiting_description = State()
    confirm = State()
    waiting_invoice_id = State()


# ─── МЕНЮ СЧЕТОВ ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "invoice_menu")
async def invoice_menu(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выставить счёт", callback_data="invoice_create")],
        [InlineKeyboardButton(text="💳 Оплатить счёт", callback_data="invoice_pay")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(
        "📋 <b>Счета</b>\n\nВыставь счёт пользователю — он оплатит в один клик.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


# ─── СОЗДАНИЕ СЧЁТА ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "invoice_create")
async def invoice_create_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>Новый счёт</b>\n\nВведи @username плательщика:",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(InvoiceStates.waiting_username)
    await callback.answer()


@router.message(InvoiceStates.waiting_username)
async def invoice_username(message: Message, state: FSMContext, session: AsyncSession):
    username = message.text.strip().lstrip("@")
    user = await get_user_by_username(session, username)

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    if user.id == message.from_user.id:
        await message.answer("❌ Нельзя выставить счёт самому себе.")
        return

    await state.update_data(payer_id=user.id, payer_username=username)
    await message.answer(
        f"✅ Плательщик: @{username}\n\nВыбери валюту:",
        reply_markup=currency_keyboard(prefix="inv_cur"),
        parse_mode="HTML"
    )
    await state.set_state(InvoiceStates.waiting_currency)


@router.callback_query(InvoiceStates.waiting_currency, F.data.startswith("inv_cur_"))
async def invoice_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[2]
    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"Валюта: <b>{currency}</b>\n\nВведи сумму:",
        parse_mode="HTML"
    )
    await state.set_state(InvoiceStates.waiting_amount)
    await callback.answer()


@router.message(InvoiceStates.waiting_amount)
async def invoice_amount(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= Decimal("0"):
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму")
        return

    await state.update_data(amount=str(amount))
    await message.answer(
        "Введи описание (или напиши <b>-</b> чтобы пропустить):",
        parse_mode="HTML"
    )
    await state.set_state(InvoiceStates.waiting_description)


@router.message(InvoiceStates.waiting_description)
async def invoice_description(message: Message, state: FSMContext):
    desc = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    data = await state.get_data()

    await message.answer(
        f"📋 <b>Подтверди счёт</b>\n\n"
        f"Плательщик: @{data['payer_username']}\n"
        f"Сумма: <b>{data['amount']} {data['currency']}</b>\n"
        f"Описание: {desc or '—'}\n"
        f"Срок: <b>24 часа</b>",
        reply_markup=confirm_keyboard(yes_data="invoice_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(InvoiceStates.confirm)


@router.callback_query(InvoiceStates.confirm, F.data == "invoice_confirm")
async def invoice_confirmed(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    await state.clear()

    invoice = await create_invoice(
        session,
        creator_id=callback.from_user.id,
        currency=data["currency"],
        amount=Decimal(data["amount"]),
        description=data.get("description")
    )

    pay_link = f"https://t.me/{BOT_USERNAME}?start=pay_{invoice.id}"
    await callback.message.edit_text(
        f"✅ <b>Счёт выставлен!</b>\n\n"
        f"Ссылка для оплаты:\n{pay_link}\n\n"
        f"Отправь её @{data['payer_username']}",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ─── ОПЛАТА СЧЁТА ─────────────────────────────────────────────────────────────

# Deep link: /start pay_<id>
@router.message(F.text.regexp(r"^/start pay_(\d+)$"))
async def deeplink_pay(message: Message, session: AsyncSession):
    import re
    match = re.match(r"^/start pay_(\d+)$", message.text)
    invoice_id = int(match.group(1))

    from sqlalchemy import select
    from database.models import Invoice
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        await message.answer("❌ Счёт не найден.")
        return
    if invoice.is_paid:
        await message.answer("❌ Этот счёт уже оплачен.")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"💳 Оплатить {invoice.amount} {invoice.currency}",
            callback_data=f"pay_invoice_{invoice.id}"
        )
    ]])

    await message.answer(
        f"📋 <b>Счёт #{invoice.id}</b>\n\n"
        f"Сумма: <b>{invoice.amount} {invoice.currency}</b>\n"
        f"Описание: {invoice.description or '—'}",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_invoice_"))
async def pay_invoice_cb(callback: CallbackQuery, session: AsyncSession):
    invoice_id = int(callback.data.split("_")[2])
    ok, err = await pay_invoice(session, invoice_id, callback.from_user.id)

    if ok:
        await callback.message.edit_text(
            "✅ <b>Счёт оплачен!</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка оплаты: {err}",
            reply_markup=back_keyboard()
        )
    await callback.answer()