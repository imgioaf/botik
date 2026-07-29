"""
Main Menu Handler (Главное Меню)
Central command router for all main menu items
"""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from database.models import User, Wallet

# Supported cryptocurrencies with exchange rates to USD
CRYPTO_RATES = {
    "TON": Decimal("7.5"),      # TON to USD
    "USDT": Decimal("1.0"),     # USDT to USD (stablecoin)
    "ETH": Decimal("3000"),     # ETH to USD
    "BTC": Decimal("65000"),    # BTC to USD
    "BNB": Decimal("600"),      # BNB to USD
    "SOL": Decimal("150"),      # SOL to USD
    "ADA": Decimal("0.50"),     # ADA to USD
    "XRP": Decimal("2.50"),     # XRP to USD
    "DOGE": Decimal("0.12"),    # DOGE to USD
    "MATIC": Decimal("0.70"),   # MATIC to USD
}

router = Router()


def get_main_menu() -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    kb = ReplyKeyboardBuilder()
    
    kb.button(text="💰 Кошелек")
    kb.button(text="📤 Вывести")
    kb.adjust(2)
    
    kb.button(text="🔗 Перевод")
    kb.button(text="💸 Сплит")
    kb.adjust(2)
    
    kb.button(text="💳 Визитка")
    kb.button(text="📊 История")
    kb.adjust(2)
    
    kb.button(text="💎 Рефер")
    kb.button(text="⭐ Премиум")
    kb.adjust(2)
    
    kb.button(text="🏆 Турнир")
    kb.button(text="📊 Копилка")
    kb.adjust(2)
    
    kb.button(text="🤖 Конвертация")
    kb.button(text="🪦 Завещание")
    kb.adjust(2)
    
    kb.button(text="⚙️ Настройки")
    kb.button(text="📚 Справка")
    kb.adjust(2)
    
    return kb.as_markup(resize_keyboard=True)


def get_main_inline_menu() -> InlineKeyboardMarkup:
    """Alternative inline menu"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Кошелек", callback_data="menu_wallet"),
            InlineKeyboardButton(text="📤 Вывести", callback_data="menu_withdraw"),
        ],
        [
            InlineKeyboardButton(text="🔗 Перевод", callback_data="menu_transfer"),
            InlineKeyboardButton(text="💸 Сплит", callback_data="menu_split"),
        ],
        [
            InlineKeyboardButton(text="💳 Визитка", callback_data="menu_card"),
            InlineKeyboardButton(text="⭐ Премиум", callback_data="menu_premium"),
        ]
    ])
    return kb


@router.message(Command("start"))
async def cmd_start(message: types.Message, session: AsyncSession):
    """Handle /start command"""
    
    # Check if user exists
    result = await session.execute(
        select(User).where(User.id == message.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name or "User"
        )
        session.add(user)
        
        # Create wallets
        for currency in ["TON", "USDT"]:
            wallet = Wallet(
                user_id=message.from_user.id,
                currency=currency,
                balance=Decimal("0")
            )
            session.add(wallet)
        
        await session.commit()
    
    msg = (
        "🪙 <b>SWITZERBOT — Крипто-кошелек в Telegram</b> 🪙\n\n"
        "Добро пожаловать! Вот что ты можешь делать:\n\n"
        "💰 <b>Кошелек</b> — Пополнение и баланс\n"
        "📤 <b>Вывести</b> — Вывод на адрес\n"
        "🔗 <b>Перевод</b> — Переводи друзьям за 0.5% комиссии\n"
        "💸 <b>Сплит</b> — Разделяй платежи (обед, такси, подарок)\n"
        "💳 <b>Визитка</b> — Твоя QR-карточка для платежей\n"
        "⭐ <b>Премиум</b> — Увеличенные лимиты и функции\n"
        "💎 <b>Рефер</b> — Приглашай друзей, получай 20% комиссии\n\n"
        "🔐 <b>Безопасно:</b> Все транзакции подписаны и на блокчейне\n"
        "⚡ <b>Быстро:</b> Транзакции за 1-2 секунды\n"
        "💯 <b>Прозрачно:</b> Видишь все свои деньги в реальном времени"
    )
    
    await message.answer(msg, parse_mode="HTML", reply_markup=get_main_menu())


@router.message(F.text == "💰 Кошелек")
async def show_wallet(message: types.Message, session: AsyncSession):
    """Show wallet balance"""
    result = await session.execute(
        select(Wallet).where(Wallet.user_id == message.from_user.id)
    )
    wallets = result.scalars().all()
    
    wallet_dict = {w.currency: w.balance for w in wallets}
    ton = wallet_dict.get("TON", Decimal("0"))
    usdt = wallet_dict.get("USDT", Decimal("0"))
    
    # Estimate USD value (1 TON ~ 7.5 USD)
    total_usd = (ton * Decimal("7.5")) + usdt
    
    msg = (
        "💰 <b>Ваш Кошелек</b>\n\n"
        "┌─────────────────────┐\n"
        f"│ 🪙 TON\n"
        f"│ <code>{ton:.4f}</code>\n"
        f"│ ≈ ${ton * Decimal('7.5'):.2f}\n"
        "├─────────────────────┤\n"
        f"│ 🔹 USDT\n"
        f"│ <code>{usdt:.2f}</code>\n"
        f"│ ≈ ${usdt:.2f}\n"
        "├─────────────────────┤\n"
        f"│ 💵 Итого\n"
        f"│ ≈ <b>${total_usd:.2f}</b>\n"
        "└─────────────────────┘\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 Пополнить", callback_data="deposit_menu"),
            InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="wallet_refresh"),
            InlineKeyboardButton(text="📋 История", callback_data="history"),
        ],
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: types.Message):
    """Show settings menu"""
    msg = (
        "⚙️ <b>Настройки</b>\n\n"
        "Выбери, что хочешь настроить:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Безопасность", callback_data="settings_security")],
        [InlineKeyboardButton(text="📱 Двухфакторная", callback_data="settings_2fa")],
        [InlineKeyboardButton(text="🖥️ Устройства", callback_data="settings_devices")],
        [InlineKeyboardButton(text="⚪ IP Whitelist", callback_data="settings_ip")],
        [InlineKeyboardButton(text="🌍 Язык", callback_data="settings_language")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")],
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "back_main")
async def back_to_main(query: types.CallbackQuery):
    """Go back to main menu"""
    msg = (
        "🪙 <b>SWITZERBOT — Главное Меню</b> 🪙\n\n"
        "Выбери действие:"
    )
    
    try:
        if query.message.text:
            await query.message.edit_text(msg, parse_mode="HTML", reply_markup=get_main_inline_menu())
        else:
            await query.message.edit_caption(msg, parse_mode="HTML", reply_markup=get_main_inline_menu())
    except Exception:
        await query.message.answer(msg, parse_mode="HTML", reply_markup=get_main_inline_menu())
    await query.answer()


@router.callback_query(F.data.startswith("menu_"))
async def handle_menu_action(query: types.CallbackQuery, session: AsyncSession):
    """Handle menu item clicks"""
    action = query.data.split("_")[1]
    
    if action == "wallet":
        await show_wallet(query.message, session)
    elif action == "withdraw":
        await query.message.answer("Выбери валюту для вывода:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🪙 TON", callback_data="withdraw_ton"),
                InlineKeyboardButton(text="🔹 USDT", callback_data="withdraw_usdt"),
            ]
        ]))
    elif action == "transfer":
        await query.message.answer("Введи ник пользователя для перевода (@username):")
    elif action == "split":
        await query.message.answer("💸 <b>КРИПТО-СПЛИТ</b>\n\nДелись платежами с друзьями!", parse_mode="HTML")
    elif action == "card":
        await query.message.answer("💳 <b>Твоя Визитка</b>\n\nПокажи эту карточку, и люди смогут легко отправить тебе крипту!", parse_mode="HTML")
    elif action == "premium":
        await query.message.answer("⭐ <b>ПРЕМИУМ</b>\n\nУлучши свой аккаунт!", parse_mode="HTML")
    
    await query.answer()

# Import for select
from sqlalchemy import select
from aiogram.utils.keyboard import InlineKeyboardBuilder

