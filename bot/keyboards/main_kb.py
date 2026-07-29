from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💼 Кошелёк",   callback_data="wallet"),
            InlineKeyboardButton(text="📊 История",   callback_data="history"),
        ],
        [
            InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit_menu"),
            InlineKeyboardButton(text="📤 Вывести",   callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton(text="➡️ Перевод",   callback_data="transfer"),
            InlineKeyboardButton(text="🔄 P2P",        callback_data="p2p_menu"),
        ],
        [
            InlineKeyboardButton(text="🧾 Чеки",      callback_data="check_menu"),
            InlineKeyboardButton(text="📋 Счета",     callback_data="invoice_menu"),
        ],
        [
            InlineKeyboardButton(text="🎁 Розыгрыш",  callback_data="giveaway_menu"),
            InlineKeyboardButton(text="💳 Подписки",  callback_data="sub_menu"),
        ],
        [
            InlineKeyboardButton(text="👥 Рефералы",  callback_data="referral"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
    ])


def wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit_menu"),
            InlineKeyboardButton(text="📤 Вывести",   callback_data="withdraw"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def deposit_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 TON",  callback_data="deposit_TON"),
            InlineKeyboardButton(text="💵 USDT", callback_data="deposit_USDT"),
        ],
        [
            InlineKeyboardButton(text="⟠ ETH",  callback_data="deposit_ETH"),
            InlineKeyboardButton(text="₿ BTC",  callback_data="deposit_BTC"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def currency_keyboard(prefix: str = "select") -> InlineKeyboardMarkup:
    currencies = [
        ("💎 TON", "TON"), ("💵 USDT", "USDT"),
        ("⟠ ETH",  "ETH"), ("₿ BTC",   "BTC"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"{prefix}_{cur}")]
        for label, cur in currencies
    ] + [[InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]])


def confirm_keyboard(
    yes_data: str, no_data: str = "back_main"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=yes_data),
        InlineKeyboardButton(text="❌ Отмена",      callback_data=no_data),
    ]])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])