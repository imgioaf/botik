"""
Реферальная программа.

Механика:
  Пользователь получает свою реф-ссылку → делится → кто перешёл
  становится его рефералом → с каждой комиссии реферала
  реферер получает 20% (уже реализовано в crud.transfer_internal).

Ссылка: t.me/Switzerwalletbot?start=ref_<user_id>
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    get_or_create_user, get_referral_count, get_user_by_id
)
from bot.keyboards.main_kb import back_keyboard, main_keyboard

router = Router()
BOT_USERNAME = "Switzerwalletbot"
REF_PERCENT = 20  # % для отображения


@router.callback_query(F.data == "referral")
async def referral_menu(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await get_user_by_id(session, user_id)
    ref_count = await get_referral_count(session, user_id)

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"

    await callback.message.edit_text(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей и получай <b>{REF_PERCENT}%</b> от их комиссий навсегда.\n\n"
        f"📊 Твоя статистика:\n"
        f"• Рефералов: <b>{ref_count}</b>\n"
        f"• Заработано: <b>{user.ref_earnings:.4f}</b> (в разных валютах)\n\n"
        f"🔗 Твоя ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"Просто поделись ссылкой — остальное автоматически.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# Обработка deep link /start ref_<user_id>
# Регистрируем реферала при первом запуске
@router.message(F.text.regexp(r"^/start ref_(\d+)$"))
async def deeplink_ref(message: Message, session: AsyncSession):
    import re
    match = re.match(r"^/start ref_(\d+)$", message.text)
    referrer_id = int(match.group(1))

    # Создаём пользователя с реферером
    await get_or_create_user(
        session,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name,
        referrer_id=referrer_id
    )

    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"💎 Добро пожаловать в <b>Switzerwalletbot</b>\n\n"
        f"Ты пришёл по реферальной ссылке.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

async def send_referral_menu(message, session):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from database.crud import get_user_by_id, get_referral_count
    uid = message.from_user.id
    user = await get_user_by_id(session, uid)
    ref_count = await get_referral_count(session, uid)
    ref_link = f"https://t.me/Switzerwalletbot?start=ref_{uid}"
    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Рефералов: <b>{ref_count}</b>\n"
        f"Заработано: <b>{user.ref_earnings:.4f}</b>\n\n"
        f"🔗 <code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="referral")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)
