"""Обработчики кнопок меню."""
from decimal import Decimal
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_all_wallets, get_transaction_history
from bot.keyboards.main_kb import currency_keyboard, back_keyboard, deposit_menu_keyboard
from bot.handlers.withdraw import WithdrawStates
from bot.handlers.transfer import TransferStates

router = Router()

def _wallet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Пополнить", callback_data="deposit_menu"),
         InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="wallet_refresh"),
         InlineKeyboardButton(text="📋 История", callback_data="history")],
    ])

async def _wallet_text(session, uid):
    wallets = await get_all_wallets(session, uid)
    d = {w.currency: w.balance for w in wallets}
    ton, usdt = d.get("TON", Decimal(0)), d.get("USDT", Decimal(0))
    total = float(ton * Decimal("7.5") + usdt)
    return (
        f"💰 <b>Кошелек</b>\n\n"
        f"TON: <code>{ton:.4f}</code>\n"
        f"USDT: <code>{usdt:.2f}</code>\n"
        f"Итого ≈ <b>${total:.2f}</b>"
    )

async def _hist(session, uid):
    txs = await get_transaction_history(session, uid, limit=10)
    if not txs:
        return "📊 <b>История</b>\n\nПока пусто."
    lines = ["📊 <b>История</b>\n"]
    for tx in txs:
        sign = "+" if tx.type in ("deposit", "transfer_in", "check_received") else "-"
        lines.append(f"{sign}{tx.amount:.4f} {tx.currency} ({tx.created_at.strftime('%d.%m %H:%M')})")
    return "\n".join(lines)

@router.callback_query(F.data == "wallet_refresh")
async def wallet_refresh(cb: types.CallbackQuery, session: AsyncSession):
    msg = await _wallet_text(session, cb.from_user.id)
    try:
        await cb.message.edit_text(msg, parse_mode="HTML", reply_markup=_wallet_kb())
    except TelegramBadRequest:
        await cb.message.answer(msg, parse_mode="HTML", reply_markup=_wallet_kb())
    await cb.answer("Обновлено")

@router.callback_query(F.data.in_({"wallet_deposit", "deposit_menu"}))
async def cb_dep(cb: types.CallbackQuery):
    text = "📥 <b>Пополнение</b>\n\nВыбери валюту:"
    kb = deposit_menu_keyboard()
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.in_({"wallet_withdraw", "withdraw"}))
async def cb_wd(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "📤 <b>Вывод</b>\n\nВыбери валюту:"
    kb = currency_keyboard(prefix="wd_cur")
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(WithdrawStates.waiting_currency)
    await cb.answer()

@router.callback_query(F.data.in_({"wallet_history", "history"}))
async def cb_hist(cb: types.CallbackQuery, session: AsyncSession):
    text = await _hist(session, cb.from_user.id)
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=back_keyboard())
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=back_keyboard())
    await cb.answer()

@router.message(F.text == "📤 Вывести")
async def m_wd(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("📤 <b>Вывод</b>\n\nВыбери валюту:",
        reply_markup=currency_keyboard(prefix="wd_cur"), parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_currency)

@router.message(F.text == "🔗 Перевод")
async def m_tr(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("📤 <b>Перевод</b>\n\nВведи @username:",
        reply_markup=back_keyboard(), parse_mode="HTML")
    await state.set_state(TransferStates.waiting_username)

@router.message(F.text == "📊 История")
async def m_hi(msg: types.Message, session: AsyncSession):
    await msg.answer(await _hist(session, msg.from_user.id),
        parse_mode="HTML", reply_markup=back_keyboard())

@router.message(F.text == "💎 Рефер")
async def m_ref(msg: types.Message, session: AsyncSession):
    from bot.handlers.referral import send_referral_menu
    await send_referral_menu(msg, session)

@router.message(F.text == "📚 Справка")
async def m_help(msg: types.Message):
    from bot.handlers.help_explain import cmd_help
    await cmd_help(msg)

@router.callback_query(F.data.in_({"withdraw_ton", "withdraw_usdt"}))
async def legacy_wd(cb: types.CallbackQuery, state: FSMContext):
    await cb_wd(cb, state)

@router.callback_query(F.data.startswith("settings_"))
async def settings_stub(cb: types.CallbackQuery, session: AsyncSession):
    action = cb.data.split("_", 1)[1]
    if action == "security":
        from bot.handlers.settings import settings_security
        return await settings_security(cb)
    if action in ("2fa", "devices", "ip", "language"):
        await cb.message.answer("⚙️ В разработке.", reply_markup=back_keyboard())
        await cb.answer()
