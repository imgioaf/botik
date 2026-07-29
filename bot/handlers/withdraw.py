"""
Handler вывода средств on-chain.

Флоу:
  /withdraw или кнопка → выбор валюты → ввод адреса → ввод суммы
  → показ комиссии + подтверждение → on-chain транзакция → результат

Важные моменты:
  - Адрес валидируется перед подтверждением
  - Средства резервируются ДО отправки в сеть
  - При ошибке сети — средства возвращаются автоматически
  - Для USDT проверяется наличие TON на газ
"""

import asyncio
import re
from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.withdraw_crud import (
    check_and_reserve_withdraw,
    finalize_withdraw,
    WITHDRAW_FEE,
    JETTON_GAS_TON
)
from database.crud import get_wallet
from blockchain.ton_withdraw import TONWithdrawService, MIN_WITHDRAW_TON, MIN_WITHDRAW_USDT
from bot.keyboards.main_kb import back_keyboard, currency_keyboard, confirm_keyboard
from config import settings

router = Router()

# Инициализируем сервис вывода один раз
_withdraw_service = TONWithdrawService(
    master_mnemonic=settings.ton_mnemonic_list,
    api_key=settings.TONCENTER_API_KEY
)

# Поддерживаемые валюты вывода (ETH/BTC — когда будет интеграция)
WITHDRAW_CURRENCIES = {"TON", "USDT"}


# ─── Валидация адресов ────────────────────────────────────────────────────────

def is_valid_ton_address(address: str) -> bool:
    """
    Базовая валидация TON адреса.
    TON адрес: начинается с EQ/UQ + 46 base64url символов (48 всего).
    """
    address = address.strip()
    pattern = r'^[EUe][Qq][A-Za-z0-9_\-]{46}$'
    return bool(re.match(pattern, address))


# ─── FSM Состояния ────────────────────────────────────────────────────────────

class WithdrawStates(StatesGroup):
    waiting_currency = State()
    waiting_address = State()
    waiting_amount = State()
    confirm = State()


# ─── Handlers ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "withdraw")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📤 <b>Вывод средств</b>\n\nВыбери валюту для вывода:",
        reply_markup=currency_keyboard(prefix="wd_cur"),
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_currency)
    await callback.answer()


@router.callback_query(WithdrawStates.waiting_currency, F.data.startswith("wd_cur_"))
async def withdraw_currency(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    currency = callback.data.split("_")[2]

    if currency not in WITHDRAW_CURRENCIES:
        await callback.answer(
            f"Вывод {currency} пока не поддерживается", show_alert=True
        )
        return

    wallet = await get_wallet(session, callback.from_user.id, currency)
    fee = WITHDRAW_FEE.get(currency, Decimal("0"))

    # Формируем подсказку по минимуму и комиссии
    min_amount = MIN_WITHDRAW_TON if currency == "TON" else MIN_WITHDRAW_USDT
    gas_note = (
        f"\n⛽ Газ: ~{JETTON_GAS_TON} TON (спишется с TON-баланса)"
        if currency == "USDT" else ""
    )

    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"📤 <b>Вывод {currency}</b>\n\n"
        f"💰 Баланс: <b>{wallet.balance:.6f} {currency}</b>\n"
        f"💸 Комиссия сервиса: <b>{fee} {currency}</b>\n"
        f"📉 Минимум: <b>{min_amount} {currency}</b>"
        f"{gas_note}\n\n"
        f"Введи адрес получателя:",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_address)
    await callback.answer()


@router.message(WithdrawStates.waiting_address)
async def withdraw_address(message: Message, state: FSMContext):
    address = message.text.strip()
    data = await state.get_data()
    currency = data["currency"]

    # Валидация адреса
    # TON и USDT используют один формат адреса (TON-адрес)
    if not is_valid_ton_address(address):
        await message.answer(
            "❌ <b>Неверный формат адреса.</b>\n\n"
            "TON адрес должен начинаться с <code>EQ</code> или <code>UQ</code> "
            "и содержать 48 символов.\n\n"
            "Пример: <code>EQDrjaLahLkMB-hMCmkzOyBuHJ139ZUYmPHu6RRBKnbdLIYI</code>\n\n"
            "Попробуй ещё раз:",
            parse_mode="HTML"
        )
        return

    await state.update_data(to_address=address)

    data = await state.get_data()
    fee = WITHDRAW_FEE.get(currency, Decimal("0"))

    await message.answer(
        f"✅ Адрес принят\n\n"
        f"Комиссия: <b>{fee} {currency}</b>\n\n"
        f"Введи сумму для вывода:",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_amount)


@router.message(WithdrawStates.waiting_amount)
async def withdraw_amount(
    message: Message, state: FSMContext, session: AsyncSession
):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= Decimal("0"):
            raise ValueError("negative")
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму (например: 5.5)")
        return

    data = await state.get_data()
    currency = data["currency"]
    fee = WITHDRAW_FEE.get(currency, Decimal("0"))
    total = amount + fee

    wallet = await get_wallet(session, message.from_user.id, currency)
    if wallet.balance < total:
        await message.answer(
            f"❌ Недостаточно средств.\n"
            f"Нужно: <b>{total} {currency}</b> (с комиссией)\n"
            f"Доступно: <b>{wallet.balance:.6f} {currency}</b>",
            parse_mode="HTML"
        )
        return

    min_amount = MIN_WITHDRAW_TON if currency == "TON" else MIN_WITHDRAW_USDT
    if amount < min_amount:
        await message.answer(
            f"❌ Минимальная сумма вывода: <b>{min_amount} {currency}</b>",
            parse_mode="HTML"
        )
        return

    await state.update_data(amount=str(amount))

    # Подготавливаем строку с газом для USDT
    gas_line = (
        f"\n⛽ Газ (TON): <b>~{JETTON_GAS_TON} TON</b>"
        if currency == "USDT" else ""
    )
    short_addr = data['to_address'][:12] + "..." + data['to_address'][-6:]

    await message.answer(
        f"📋 <b>Подтверди вывод</b>\n\n"
        f"Валюта: <b>{currency}</b>\n"
        f"Адрес: <code>{short_addr}</code>\n"
        f"Сумма: <b>{amount} {currency}</b>\n"
        f"Комиссия сервиса: <b>{fee} {currency}</b>\n"
        f"Итого спишется: <b>{total} {currency}</b>"
        f"{gas_line}\n\n"
        f"⚠️ Транзакция необратима. Проверь адрес!",
        reply_markup=confirm_keyboard(yes_data="withdraw_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.confirm)


@router.callback_query(WithdrawStates.confirm, F.data == "withdraw_confirm")
async def withdraw_confirmed(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    await state.clear()

    currency = data["currency"]
    amount = Decimal(data["amount"])
    to_address = data["to_address"]

    # Показываем что обрабатываем
    await callback.message.edit_text(
        "⏳ <b>Отправляем транзакцию...</b>\n\nЭто займёт несколько секунд.",
        parse_mode="HTML"
    )
    await callback.answer()

    # 1. Резервируем средства в БД
    ok, err, total = await check_and_reserve_withdraw(
        session, callback.from_user.id, currency, amount
    )
    if not ok:
        await callback.message.edit_text(
            f"❌ {err}",
            reply_markup=back_keyboard()
        )
        return

    # 2. Отправляем on-chain (в фоне чтобы не блокировать хендлер)
    success, result = await _send_withdraw(currency, callback.from_user.id, to_address, amount)

    # 3. Финализируем в БД
    await finalize_withdraw(
        session=session,
        user_id=callback.from_user.id,
        currency=currency,
        amount=amount,
        tx_hash=result if success else "",
        success=success,
        error_msg=result if not success else ""
    )

    # 4. Отвечаем пользователю
    if success:
        short_addr = to_address[:12] + "..." + to_address[-6:]
        await callback.message.edit_text(
            f"✅ <b>Транзакция отправлена!</b>\n\n"
            f"Сумма: <b>{amount} {currency}</b>\n"
            f"Адрес: <code>{short_addr}</code>\n\n"
            f"Средства поступят в течение 1–2 минут после подтверждения сети.",
            reply_markup=back_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка транзакции</b>\n\n"
            f"{result}\n\n"
            f"Средства возвращены на твой баланс.",
            reply_markup=back_keyboard(),
            parse_mode="HTML"
        )


async def _send_withdraw(
    currency: str, user_id: int, to_address: str, amount: Decimal
) -> tuple[bool, str]:
    """Диспатчим на нужный метод вывода."""
    if currency == "TON":
        return await _withdraw_service.withdraw_ton(
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            comment="Withdrawal"
        )
    elif currency == "USDT":
        return await _withdraw_service.withdraw_usdt(
            user_id=user_id,
            to_address=to_address,
            amount=amount
        )
    else:
        return False, f"Вывод {currency} пока не поддерживается"