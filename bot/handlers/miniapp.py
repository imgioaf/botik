"""
Mini App Handler (Мини-приложение)
Interactive web interface embedded in Telegram
Handles button actions and data from the Mini App interface
"""

from aiogram import Router, types, F
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

logger = logging.getLogger(__name__)
router = Router()

# ⚙️ Configuration
# Replace with your actual domain
MINIAPP_URL = "https://your-domain.com/web_app.html"
# For testing, you can use a local file path (Telegram will handle it)
# MINIAPP_URL = "file:///C:/switzerbot/web_app.html"  # Windows local
# MINIAPP_URL = "file:///home/user/switzerbot/web_app.html"  # Linux local


@router.message(Command("miniapp"))
async def cmd_miniapp(message: types.Message):
    """Open Mini App interface"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🚀 Открыть Mini App",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]])
    
    await message.answer(
        "🎮 <b>Мини-приложение Switzerbot</b>\n\n"
        "Быстрые действия:\n"
        "• 💵 Пополнение кошелька\n"
        "• 📤 Вывод средств\n"
        "• ↔️ Переводы\n"
        "• 📊 История транзакций\n"
        "• 🔐 Параметры безопасности\n\n"
        "<i>Нажми кнопку ниже, чтобы открыть приложение</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(F.web_app_data)
async def handle_miniapp_data(message: types.Message, session: AsyncSession):
    """Handle data sent from Mini App"""
    try:
        # Parse data from Mini App
        app_data = json.loads(message.web_app_data.data)
        action = app_data.get("action", "unknown").lower()
        timestamp = app_data.get("timestamp")
        user_id = app_data.get("user_id", message.from_user.id)
        
        logger.info(f"🎮 Mini App action: {action} from user {user_id} at {timestamp}")
        
        # Verify user
        if user_id != message.from_user.id:
            await message.answer("❌ Несовпадение ID пользователя")
            return
        
        # Route to appropriate handler
        if action == "deposit":
            await handle_deposit_action(message, session)
            
        elif action == "withdraw":
            await handle_withdraw_action(message, session)
            
        elif action == "transfer":
            await handle_transfer_action(message, session)
            
        elif action == "history":
            await handle_history_action(message, session)
            
        elif action == "2fa":
            await handle_2fa_action(message, session)
            
        elif action == "devices":
            await handle_devices_action(message, session)
        
        else:
            await message.answer(f"❓ Неизвестное действие: {action}")
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Mini App: {e}")
        await message.answer("❌ Ошибка обработки данных")
    
    except Exception as e:
        logger.error(f"Error handling mini app data: {e}")
        await message.answer("❌ Неожиданная ошибка")


async def handle_deposit_action(message: types.Message, session: AsyncSession):
    """Handle deposit action from Mini App"""
    from database.crud import get_user_by_id
    
    user = await get_user_by_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 TON", callback_data="deposit_TON")],
        [InlineKeyboardButton(text="💵 USDT", callback_data="deposit_USDT")],
        [InlineKeyboardButton(text="💵 ETH", callback_data="deposit_ETH")],
        [InlineKeyboardButton(text="💵 BTC", callback_data="deposit_BTC")],
    ])
    
    await message.answer(
        "💳 <b>Выбери валюту для пополнения:</b>\n\n"
        "<i>Минимум: 0.001 (размер комиссии не взимается)</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_withdraw_action(message: types.Message, session: AsyncSession):
    """Handle withdraw action from Mini App"""
    await message.answer(
        "📤 <b>Функция вывода в разработке</b>\n\n"
        "Используй основное меню для вывода средств",
        parse_mode="HTML"
    )


async def handle_transfer_action(message: types.Message, session: AsyncSession):
    """Handle transfer action from Mini App"""
    await message.answer(
        "↔️ <b>Отправить перевод</b>\n\n"
        "Укажи получателя (username или адрес кошелька)",
        parse_mode="HTML"
    )


async def handle_history_action(message: types.Message, session: AsyncSession):
    """Handle history action from Mini App"""
    from database.models import Transaction
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    # Get last 10 transactions
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == message.from_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
    )
    
    result = await session.execute(stmt)
    transactions = result.scalars().all()
    
    if not transactions:
        await message.answer("📊 <b>История транзакций пуста</b>", parse_mode="HTML")
        return
    
    history_text = "📊 <b>Последние 10 транзакций:</b>\n\n"
    
    for i, tx in enumerate(transactions, 1):
        icon = "➕" if tx.type == "deposit" else "➖"
        history_text += (
            f"{i}. {icon} <b>{tx.type.upper()}</b>\n"
            f"   Сумма: {tx.amount} {tx.currency}\n"
            f"   Дата: {tx.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"   Статус: {tx.status}\n\n"
        )
    
    await message.answer(history_text, parse_mode="HTML")


async def handle_2fa_action(message: types.Message, session: AsyncSession):
    """Handle 2FA settings action from Mini App"""
    from database.crud import get_user_by_id
    
    user = await get_user_by_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    status = "✅ Включена" if user.two_fa_enabled else "❌ Отключена"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Управлять 2FA", callback_data="2fa_manage")],
        [InlineKeyboardButton(text="🔑 Backup коды", callback_data="2fa_backup")],
    ])
    
    await message.answer(
        f"🔐 <b>Двухфакторная аутентификация</b>\n\n"
        f"Статус: {status}\n\n"
        f"<i>Двухфакторная аутентификация защищает ваш аккаунт от несанкционированного доступа</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_devices_action(message: types.Message, session: AsyncSession):
    """Handle trusted devices action from Mini App"""
    from database.crud import get_user_by_id
    
    user = await get_user_by_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    devices_info = user.trusted_devices or "Нет доверенных устройств"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить устройство", callback_data="device_add")],
        [InlineKeyboardButton(text="🗑️ Удалить все", callback_data="device_clear")],
    ])
    
    await message.answer(
        f"📱 <b>Доверенные устройства</b>\n\n"
        f"{devices_info}\n\n"
        f"<i>Добавляй устройства для быстрого входа</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ═══════════════════════════════════════════════════════════════════════════
# Mini App Button Callbacks (Processing mini app actions)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("deposit_"))
async def process_deposit(query: types.CallbackQuery, session: AsyncSession):
    """Process deposit currency selection from Mini App"""
    currency = query.data.split("_")[1]
    
    # Import here to avoid circular imports
    from bot.handlers.wallet import show_deposit_address
    
    await show_deposit_address(query.message, currency, session)
    await query.answer()


@router.callback_query(F.data == "2fa_manage")
async def manage_2fa(query: types.CallbackQuery, session: AsyncSession):
    """Manage 2FA from Mini App"""
    # Route to main 2FA handler
    from bot.handlers.settings import cmd_2fa_setup
    
    await cmd_2fa_setup(query.message, session)
    await query.answer()


@router.callback_query(F.data == "device_add")
async def add_device(query: types.CallbackQuery):
    """Add trusted device from Mini App"""
    await query.message.answer(
        "📱 <b>Добавить как доверенное устройство?</b>\n\n"
        "<i>Это устройство будет добавлено в список доверенных</i>",
        parse_mode="HTML"
    )
    await query.answer()
