"""
Настройки пользователя.
- Язык (RU/EN)
- 2FA (заглушка — будет в следующей версии)
- Информация об аккаунте
- Безопасность
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from database.crud import get_referral_count
from bot.keyboards.main_kb import back_keyboard

router = Router()


@router.callback_query(F.data == "settings")
async def settings_menu(callback: CallbackQuery, session: AsyncSession):
    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()

    ref_count = await get_referral_count(session, callback.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="settings_profile")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="referral")],
        [InlineKeyboardButton(text="🔒 Безопасность", callback_data="settings_security")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])

    verified_str = "✅ Верифицирован" if user and user.is_verified else "❌ Не верифицирован"

    await callback.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"👤 ID: <code>{callback.from_user.id}</code>\n"
        f"📛 Username: @{callback.from_user.username or '—'}\n"
        f"🔐 KYC: {verified_str}\n"
        f"👥 Рефералов: {ref_count}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_profile")
async def settings_profile(callback: CallbackQuery, session: AsyncSession):
    from database.crud import get_all_wallets, get_transaction_history
    wallets = await get_all_wallets(session, callback.from_user.id)
    txs = await get_transaction_history(session, callback.from_user.id, limit=100)

    total_tx = len(txs)
    deposits = sum(1 for t in txs if t.type == "deposit")
    withdraws = sum(1 for t in txs if t.type == "withdraw")

    lines = [
        f"👤 <b>Профиль</b>\n",
        f"🆔 ID: <code>{callback.from_user.id}</code>",
        f"📛 Имя: {callback.from_user.first_name}",
        f"🔗 Username: @{callback.from_user.username or '—'}\n",
        f"📊 Статистика:",
        f"• Всего транзакций: {total_tx}",
        f"• Пополнений: {deposits}",
        f"• Выводов: {withdraws}\n",
        f"💼 Балансы:",
    ]
    emoji_map = {"TON": "💎", "USDT": "💵", "ETH": "⟠", "BTC": "₿"}
    for w in wallets:
        lines.append(f"• {emoji_map.get(w.currency,'🪙')} {w.currency}: {w.balance:.6f}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_security")
async def settings_security(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔑 2FA (скоро)",
            callback_data="security_2fa"
        )],
        [InlineKeyboardButton(
            text="📋 Активные сессии (скоро)",
            callback_data="security_sessions"
        )],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")],
    ])
    await callback.message.edit_text(
        "🔒 <b>Безопасность</b>\n\n"
        "• Двухфакторная аутентификация — <i>в разработке</i>\n"
        "• Управление сессиями — <i>в разработке</i>\n\n"
        "💡 Основная защита:\n"
        "— Бот привязан к твоему Telegram-аккаунту\n"
        "— Включи 2FA в настройках Telegram",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.in_({"security_2fa", "security_sessions"}))
async def security_stub(callback: CallbackQuery):
    await callback.answer("🚧 Функция в разработке", show_alert=True)