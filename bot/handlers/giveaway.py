"""
Розыгрыши (Giveaway / Airdrop).

Флоу создателя:
  кнопка → валюта → сумма на победителя → кол-во победителей
  → описание → подтверждение → создан → кнопка "Участвовать"

Участник:
  нажимает кнопку "🎉 Участвовать" прямо в сообщении

Завершение:
  создатель нажимает "🏁 Завершить" → победители выбираются рандомно
  → всем победителям зачисляется приз → уведомления
"""

from decimal import Decimal, InvalidOperation
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    create_giveaway, join_giveaway,
    finish_giveaway, get_giveaway, get_wallet
)
from bot.keyboards.main_kb import back_keyboard, currency_keyboard, confirm_keyboard

router = Router()


class GiveawayStates(StatesGroup):
    waiting_currency = State()
    waiting_amount   = State()
    waiting_winners  = State()
    waiting_caption  = State()
    confirm          = State()


def giveaway_keyboard(giveaway_id: int, finished: bool = False) -> InlineKeyboardMarkup:
    if finished:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Розыгрыш завершён", callback_data="noop")]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎉 Участвовать",
            callback_data=f"ga_join_{giveaway_id}"
        )],
        [InlineKeyboardButton(
            text="🏁 Завершить розыгрыш",
            callback_data=f"ga_finish_{giveaway_id}"
        )],
    ])


# ─── МЕНЮ ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "giveaway_menu")
async def giveaway_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Создать розыгрыш", callback_data="ga_create")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(
        "🎁 <b>Розыгрыши</b>\n\n"
        "Создай аирдроп — победители получат крипту прямо на баланс бота.",
        reply_markup=kb, parse_mode="HTML"
    )
    await callback.answer()


# ─── СОЗДАНИЕ ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "ga_create")
async def ga_create_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎁 <b>Создание розыгрыша</b>\n\nВыбери валюту приза:",
        reply_markup=currency_keyboard(prefix="ga_cur"),
        parse_mode="HTML"
    )
    await state.set_state(GiveawayStates.waiting_currency)
    await callback.answer()


@router.callback_query(GiveawayStates.waiting_currency, F.data.startswith("ga_cur_"))
async def ga_currency(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    currency = callback.data.split("_")[2]
    wallet = await get_wallet(session, callback.from_user.id, currency)
    await state.update_data(currency=currency)
    await callback.message.edit_text(
        f"💰 Баланс: <b>{wallet.balance:.4f} {currency}</b>\n\n"
        "Введи сумму приза <b>на одного победителя</b>:",
        parse_mode="HTML"
    )
    await state.set_state(GiveawayStates.waiting_amount)
    await callback.answer()


@router.message(GiveawayStates.waiting_amount)
async def ga_amount(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Введи корректную сумму")
        return
    await state.update_data(amount=str(amount))
    await message.answer(
        "Сколько победителей? (от 1 до 100)\nВведи число:"
    )
    await state.set_state(GiveawayStates.waiting_winners)


@router.message(GiveawayStates.waiting_winners)
async def ga_winners(message: Message, state: FSMContext):
    try:
        n = int(message.text.strip())
        if not (1 <= n <= 100):
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи число от 1 до 100")
        return
    await state.update_data(winners=n)
    await message.answer(
        "Добавь описание розыгрыша (или напиши <b>-</b> чтобы пропустить):",
        parse_mode="HTML"
    )
    await state.set_state(GiveawayStates.waiting_caption)


@router.message(GiveawayStates.waiting_caption)
async def ga_caption(message: Message, state: FSMContext, session: AsyncSession):
    caption = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(caption=caption)
    data = await state.get_data()

    amount = Decimal(data["amount"])
    winners = data["winners"]
    total = amount * winners
    currency = data["currency"]

    wallet = await get_wallet(session, message.from_user.id, currency)
    if wallet.balance < total:
        await message.answer(
            f"❌ Недостаточно средств.\n"
            f"Нужно: <b>{total} {currency}</b>\n"
            f"Доступно: <b>{wallet.balance:.4f} {currency}</b>",
            parse_mode="HTML"
        )
        await state.clear()
        return

    await message.answer(
        f"📋 <b>Подтверди розыгрыш</b>\n\n"
        f"Приз: <b>{amount} {currency}</b> × {winners} победителей\n"
        f"Итого заморозить: <b>{total} {currency}</b>\n"
        f"Описание: {caption or '—'}",
        reply_markup=confirm_keyboard(yes_data="ga_confirm"),
        parse_mode="HTML"
    )
    await state.set_state(GiveawayStates.confirm)


@router.callback_query(GiveawayStates.confirm, F.data == "ga_confirm")
async def ga_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    giveaway = await create_giveaway(
        session,
        creator_id=callback.from_user.id,
        currency=data["currency"],
        amount_per_winner=Decimal(data["amount"]),
        winners_count=data["winners"],
        caption=data.get("caption")
    )

    if not giveaway:
        await callback.message.edit_text(
            "❌ Не удалось создать розыгрыш. Проверь баланс.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    text = (
        f"🎁 <b>Розыгрыш!</b>\n\n"
        f"Приз: <b>{giveaway.amount_per_winner} {giveaway.currency}</b>\n"
        f"Победителей: <b>{giveaway.winners_count}</b>\n"
    )
    if giveaway.caption:
        text += f"\n{giveaway.caption}\n"
    text += "\nНажми кнопку чтобы участвовать 👇"

    await callback.message.edit_text(
        text,
        reply_markup=giveaway_keyboard(giveaway.id),
        parse_mode="HTML"
    )
    await callback.answer("✅ Розыгрыш создан!")


# ─── УЧАСТИЕ ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ga_join_"))
async def ga_join(callback: CallbackQuery, session: AsyncSession):
    giveaway_id = int(callback.data.split("_")[2])
    ok, err = await join_giveaway(session, giveaway_id, callback.from_user.id)

    if ok:
        await callback.answer("🎉 Ты в розыгрыше! Ждём завершения.", show_alert=True)
    else:
        await callback.answer(f"❌ {err}", show_alert=True)


# ─── ЗАВЕРШЕНИЕ ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ga_finish_"))
async def ga_finish(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    giveaway_id = int(callback.data.split("_")[2])
    giveaway = await get_giveaway(session, giveaway_id)

    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    if giveaway.creator_id != callback.from_user.id:
        await callback.answer("❌ Только создатель может завершить розыгрыш", show_alert=True)
        return

    winner_ids = await finish_giveaway(session, giveaway_id)

    if not winner_ids:
        await callback.message.edit_text(
            "😔 Никто не принял участие. Средства возвращены.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    # Уведомляем победителей
    for uid in winner_ids:
        try:
            await bot.send_message(
                uid,
                f"🏆 <b>Ты победил в розыгрыше!</b>\n\n"
                f"Зачислено: <b>{giveaway.amount_per_winner} {giveaway.currency}</b>\n\n"
                f"Средства уже на твоём балансе.",
                parse_mode="HTML"
            )
        except Exception:
            pass  # пользователь заблокировал бота

    names = ", ".join([f"user {uid}" for uid in winner_ids])
    await callback.message.edit_text(
        f"🏆 <b>Розыгрыш завершён!</b>\n\n"
        f"Победители ({len(winner_ids)}): {names}\n"
        f"Каждый получил: <b>{giveaway.amount_per_winner} {giveaway.currency}</b>",
        reply_markup=giveaway_keyboard(giveaway_id, finished=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()