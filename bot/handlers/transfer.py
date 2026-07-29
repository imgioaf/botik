from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    get_wallet, get_user_by_username, transfer_internal
)
from bot.keyboards.main_kb import back_keyboard, confirm_keyboard, currency_keyboard

router = Router()


class TransferStates(StatesGroup):
    waiting_username = State()
    waiting_currency = State()
    waiting_amount = State()
    confirm = State()


@router.callback_query(F.data == "transfer")
async def start_transfer(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📤 <b>Перевод</b>\n\nВведи @username получателя:",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TransferStates.waiting_username)
    await callback.answer()


@router.message(TransferStates.waiting_username)
async def get_recipient(message: Message, state: FSMContext, session: AsyncSession):
    username = message.text.strip().lstrip("@")
    recipient = await get_user_by_username(session, username)

    if not recipient:
        await message.answer(
            "❌ Пользователь не найден. Убедись что он уже запускал бота.\n\n"
            "Попробуй ещё раз или введи /cancel для отмены."
        )
        return

    if recipient.id == message.from_user.id:
        await message.answer("❌ Нельзя переводить самому себе.")
        return

    await state.update_data(
        recipient_id=recipient.id,
        recipient_username=username,
        recipient_name=recipient.first_name
    )
    await message.answer(
        f"✅ Получатель: <b>{recipient.first_name}</b> (@{username})\n\nВыбери валюту:",
        reply_markup=currency_keyboard(prefix="transfer_cur"),
        parse_mode="HTML"
    )
    await state.set_state(TransferStates.waiting_currency)


@router.callback_query(
    TransferStates.waiting_currency,
    F.data.startswith("transfer_cur_")
)
async def get_currency(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    currency = callback.data.split("_")[2]
    wallet = await get_wallet(session, callback.from_user.id, currency)

    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"💰 Баланс: <b>{wallet.balance:.6f} {currency}</b>\n\nВведи сумму:",
        parse_mode="HTML"
    )
    await state.set_state(TransferStates.waiting_amount)
    await callback.answer()


@router.message(TransferStates.waiting_amount)
async def get_amount(message: Message, state: FSMContext, session: AsyncSession):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= Decimal("0"):
            raise ValueError("negative")
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму (например: 1.5)")
        return

    data = await state.get_data()
    currency = data["currency"]
    fee = (amount * Decimal("0.005")).quantize(Decimal("0.000001"))
    total = amount + fee

    wallet = await get_wallet(session, message.from_user.id, currency)
    if wallet.balance < total:
        await message.answer(
            f"❌ Недостаточно средств.\n"
            f"Нужно: <b>{total:.6f} {currency}</b> (включая комиссию)\n"
            f"Доступно: <b>{wallet.balance:.6f} {currency}</b>",
            parse_mode="HTML"
        )
        return

    await state.update_data(amount=str(amount), fee=str(fee))
    await message.answer(
        f"📋 <b>Подтверди перевод</b>\n\n"
        f"Получатель: @{data['recipient_username']}\n"
        f"Сумма: <b>{amount} {currency}</b>\n"
        f"Комиссия: <b>{fee} {currency}</b>\n"
        f"Итого спишется: <b>{total} {currency}</b>",
        reply_markup=confirm_keyboard(yes_data="transfer_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(TransferStates.confirm)


@router.callback_query(TransferStates.confirm, F.
data == "transfer_confirm")
async def confirm_transfer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    success, err = await transfer_internal(
        session,
        from_id=callback.from_user.id,
        to_id=data["recipient_id"],
        currency=data["currency"],
        amount=Decimal(data["amount"])
    )

    if success:
        from bot.keyboards.main_kb import main_keyboard
        await callback.message.edit_text(
            f"✅ <b>Перевод выполнен!</b>\n\n"
            f"@{data['recipient_username']} получил <b>{data['amount']} {data['currency']}</b>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка перевода: {err}",
            reply_markup=back_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()