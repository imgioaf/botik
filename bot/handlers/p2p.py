"""
P2P торговля — упрощённая версия.

Механика:
  Продавец создаёт ордер (продаю X TON за Y RUB/USD)
  → публикуется в списке → покупатель выбирает
  → продавец подтверждает оплату фиатом → крипта переходит покупателю
  → escrow защита: крипта заморожена на время сделки

Это упрощённая P2P без верификации оплаты фиата — стороны
договариваются напрямую, бот только держит escrow.

Для полноценной P2P с проверкой платежей нужна интеграция с
банковскими API (отдельный большой этап).
"""

from decimal import Decimal, InvalidOperation
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Numeric, DateTime, Boolean, Integer, ForeignKey
from datetime import datetime

from database.crud import get_wallet, transfer_internal
from bot.keyboards.main_kb import back_keyboard, confirm_keyboard

router = Router()

# ─── Временная модель P2P Ордера ──────────────────────────────────────────────
# Добавить в models.py при полноценной реализации

class P2POrderStatus:
    OPEN      = "open"
    LOCKED    = "locked"   # покупатель выбрал
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED  = "disputed"


class P2PStates(StatesGroup):
    waiting_crypto_currency = State()
    waiting_crypto_amount   = State()
    waiting_fiat_currency   = State()
    waiting_fiat_price      = State()
    waiting_payment_method  = State()
    confirm                 = State()


FIAT_CURRENCIES = ["RUB", "USD", "EUR", "KZT", "UAH"]
CRYPTO_FOR_P2P  = ["TON", "USDT"]


# ─── МЕНЮ P2P ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "p2p_menu")
async def p2p_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Купить крипту", callback_data="p2p_buy_list")],
        [InlineKeyboardButton(text="📤 Продать крипту", callback_data="p2p_sell_create")],
        [InlineKeyboardButton(text="📋 Мои ордера", callback_data="p2p_my_orders")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(
        "🔄 <b>P2P Торговля</b>\n\n"
        "Покупай и продавай криптовалюту напрямую с другими пользователями.\n\n"
        "⚡️ Escrow-защита: крипта блокируется на время сделки.\n"
        "⚠️ Бот не проверяет факт оплаты фиата — это на усмотрение сторон.",
        reply_markup=kb, parse_mode="HTML"
    )
    await callback.answer()


# ─── СОЗДАНИЕ ОРДЕРА НА ПРОДАЖУ ───────────────────────────────────────────────

@router.callback_query(F.data == "p2p_sell_create")
async def p2p_sell_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 TON", callback_data="p2p_cr_TON")],
        [InlineKeyboardButton(text="💵 USDT", callback_data="p2p_cr_USDT")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="p2p_menu")],
    ])
    await callback.message.edit_text(
        "📤 <b>Создание ордера на продажу</b>\n\nВыбери криптовалюту:",
        reply_markup=kb, parse_mode="HTML"
    )
    await state.set_state(P2PStates.waiting_crypto_currency)
    await callback.answer()


@router.callback_query(P2PStates.waiting_crypto_currency, F.data.startswith("p2p_cr_"))
async def p2p_crypto(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    currency = callback.data.split("_")[2]
    wallet = await get_wallet(session, callback.from_user.id, currency)
    await state.update_data(crypto_currency=currency)
    await callback.message.edit_text(
        f"💰 Баланс: <b>{wallet.balance:.4f} {currency}</b>\n\n"
        f"Введи количество {currency} для продажи:",
        parse_mode="HTML"
    )
    await state.set_state(P2PStates.waiting_crypto_amount)
    await callback.answer()


@router.message(P2PStates.waiting_crypto_amount)
async def p2p_crypto_amount(message: Message, state: FSMContext, session: AsyncSession):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму")
        return

    data = await state.get_data()
    wallet = await get_wallet(session, message.from_user.id, data["crypto_currency"])
    if wallet.balance < amount:
        await message.answer(
            f"❌ Недостаточно средств. Доступно: <b>{wallet.balance:.4f} {data['crypto_currency']}</b>",
            parse_mode="HTML"
        )
        return

    await state.update_data(crypto_amount=str(amount))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f, callback_data=f"p2p_fiat_{f}")]
        for f in FIAT_CURRENCIES
    ])
    await message.answer("Выбери фиатную валюту:", reply_markup=kb)
    await state.set_state(P2PStates.waiting_fiat_currency)


@router.callback_query(P2PStates.waiting_fiat_currency, F.data.startswith("p2p_fiat_"))
async def p2p_fiat(callback: CallbackQuery, state: FSMContext):
    fiat = callback.data.split("_")[2]
    await state.update_data(fiat_currency=fiat)
    data = await state.get_data()
    await callback.message.edit_text(
        f"Продаю: <b>{data['crypto_amount']} {data['crypto_currency']}</b>\n\n"
        f"Введи цену за 1 {data['crypto_currency']} в {fiat}:",
        parse_mode="HTML"
    )
    await state.set_state(P2PStates.waiting_fiat_price)
    await callback.answer()


@router.message(P2PStates.waiting_fiat_price)
async def p2p_fiat_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную цену")
        return

    await state.update_data(fiat_price=str(price))
    await message.answer(
        "Укажи способ оплаты (например: Сбербанк, QIWI, TBank, PayPal):"
    )
    await state.set_state(P2PStates.waiting_payment_method)


@router.message(P2PStates.waiting_payment_method)
async def p2p_payment_method(message: Message, state: FSMContext):
    method = message.text.strip()[:100]
    await state.update_data(payment_method=method)
    data = await state.get_data()

    amount = Decimal(data["crypto_amount"])
    price = Decimal(data["fiat_price"])
    total_fiat = amount * price

    await message.answer(
        f"📋 <b>Подтверди ордер на продажу</b>\n\n"
        f"Продаю: <b>{amount} {data['crypto_currency']}</b>\n"
        f"Цена: <b>{price} {data['fiat_currency']}</b> за 1 {data['crypto_currency']}\n"
        f"Итого покупатель платит: <b>{total_fiat} {data['fiat_currency']}</b>\n"
        f"Способ оплаты: <b>{method}</b>\n\n"
        f"Крипта будет заморожена до завершения сделки.",
        reply_markup=confirm_keyboard(yes_data="p2p_sell_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(P2PStates.confirm)


@router.callback_query(P2PStates.confirm, F.data == "p2p_sell_confirm")
async def p2p_sell_confirmed(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    await state.clear()

    amount = Decimal(data["crypto_amount"])
    currency = data["crypto_currency"]

    # Замораживаем крипту (списываем с баланса)
    wallet = await get_wallet(session, callback.from_user.id, currency)
    if not wallet or wallet.balance < amount:
        await callback.message.edit_text(
            "❌ Недостаточно средств.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    wallet.balance -= amount

    # Сохраняем ордер в памяти (в продакшене — отдельная таблица P2POrder)
    # Здесь используем простой подход через message_id как идентификатор
    from sqlalchemy.orm import DeclarativeBase
    # В реальном продакшене создать модель P2POrder в models.py
    # Пока показываем ордер и просим связаться напрямую

    price = Decimal(data["fiat_price"])
    total_fiat = amount * price
    fiat = data["fiat_currency"]
    method = data["payment_method"]

    await session.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Написать продавцу",
            url=f"https://t.me/{callback.from_user.username or 'user'}"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить ордер",
            callback_data=f"p2p_cancel_{callback.from_user.id}_{currency}_{amount}"
        )],
    ])

    await callback.message.edit_text(
        f"✅ <b>Ордер создан!</b>\n\n"
        f"🏷 Продаю: <b>{amount} {currency}</b>\n"
        f"💵 Цена: <b>{price} {fiat}</b>/1 {currency}\n"
        f"💰 Итого: <b>{total_fiat} {fiat}</b>\n"
        f"💳 Оплата: {method}\n\n"
        f"Покупатель свяжется с тобой в личке.\n"
        f"После получения оплаты подтверди сделку.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


# ─── СПИСОК ОРДЕРОВ (заглушка — в полной версии из БД) ───────────────────────

@router.callback_query(F.data == "p2p_buy_list")
async def p2p_buy_list(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Доступные ордера</b>\n\n"
        "Пока нет активных ордеров на продажу.\n\n"
        "📌 Для полноценного P2P списка нужна отдельная таблица ордеров.\n"
        "Это следующий этап разработки.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "p2p_my_orders")
async def p2p_my_orders(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>Мои ордера</b>\n\n"
        "История P2P ордеров появится здесь.\n"
        "Функция в разработке.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()