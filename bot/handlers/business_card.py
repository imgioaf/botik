"""
Crypto Business Card (Криптовизитка)
Unique personal page for receiving crypto payments
t.me/Switzerwalletbot?start=card_username
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
import logging

from database.models import User, Wallet
from bot.beautiful_ui import CryptobotUI, FormattedMessages, QRCodeGenerator

logger = logging.getLogger(__name__)
router = Router()


async def get_user_card(session: AsyncSession, user_id: int) -> dict:
    """Get user's business card data"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Get wallet balances
    wallets_result = await session.execute(
        select(Wallet).where(Wallet.user_id == user_id)
    )
    wallets = wallets_result.scalars().all()
    
    wallet_data = {w.currency: w.balance for w in wallets}
    
    return {
        "user_id": user_id,
        "username": user.username or f"user{user_id}",
        "first_name": user.first_name,
        "ton_balance": wallet_data.get("TON", Decimal("0")),
        "usdt_balance": wallet_data.get("USDT", Decimal("0")),
        "ref_earnings": user.ref_earnings,
        "created_at": user.created_at.strftime("%d.%m.%Y"),
        "verified": user.is_verified
    }


async def format_business_card(card_data: dict) -> str:
    """Format beautiful business card"""
    verified_badge = "✅" if card_data["verified"] else ""
    
    msg = "╔═══════════════════════════╗\n"
    msg += "║    💳 КРИПТО-ВИЗИТКА 💳   ║\n"
    msg += "╚═══════════════════════════╝\n\n"
    
    msg += f"👤 <b>{card_data['first_name']}</b> {verified_badge}\n"
    msg += f"🔗 @{card_data['username']}\n\n"
    
    msg += "┌─ СЧЁТ ─────────────────────┐\n"
    msg += f"│ 🪙 TON: {card_data['ton_balance']:.4f}\n"
    msg += f"│ 🔹 USDT: {card_data['usdt_balance']:.2f}\n"
    msg += f"│ 💰 Заработок: {card_data['ref_earnings']:.4f} TON\n"
    msg += "└────────────────────────────┘\n\n"
    
    msg += f"📅 Пользователь с {card_data['created_at']}\n"
    msg += "✨ Надежный партнер на блокчейне\n\n"
    
    msg += "💡 Отправьте ему крипту через QR ниже 👇"
    
    return msg


async def get_business_card_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get business card action buttons"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="💸 Отправить TON", callback_data=f"card_send_ton_{user_id}")
    kb.button(text="💳 Отправить USDT", callback_data=f"card_send_usdt_{user_id}")
    kb.adjust(2)
    
    kb.button(text="📱 Показать Код", callback_data=f"card_show_qr_{user_id}")
    kb.button(text="🔗 Скопировать", callback_data=f"card_copy_link_{user_id}")
    kb.adjust(2)
    
    kb.button(text="↩️ Назад", callback_data="back_main")
    
    return kb.as_markup()


@router.message(F.text == "💳 Визитка")
async def show_my_card(message: types.Message, session: AsyncSession):
    """Show user's business card"""
    card_data = await get_user_card(session, message.from_user.id)
    
    if not card_data:
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    # Get TON deposit address for QR
    result = await session.execute(
        select(Wallet).where(
            Wallet.user_id == message.from_user.id,
            Wallet.currency == "TON"
        )
    )
    wallet = result.scalar_one_or_none()
    
    if not wallet or not wallet.deposit_address:
        await message.answer("❌ Адрес кошелька не найден")
        return
    
    # Generate QR code
    qr_bytes = await QRCodeGenerator.generate_deposit_qr(wallet.deposit_address)
    
    # Format message
    card_msg = await format_business_card(card_data)
    
    # Send message with QR
    await message.answer_photo(
        photo=types.BufferedInputFile(qr_bytes, filename="card_qr.png"),
        caption=card_msg,
        parse_mode="HTML",
        reply_markup=await get_business_card_keyboard(message.from_user.id)
    )


@router.callback_query(F.data.startswith("card_"))
async def handle_card_action(query: types.CallbackQuery, session: AsyncSession):
    """Handle business card actions"""
    parts = query.data.split("_")
    action = parts[1] if len(parts) > 1 else None
    
    if action == "show":
        # Show personal card
        try:
            user_id = int(parts[2]) if len(parts) > 2 else None
            if not user_id:
                await query.answer("❌ Некорректные данные", show_alert=True)
                return
            card_data = await get_user_card(session, user_id)
        except (ValueError, IndexError):
            await query.answer("❌ Ошибка обработки", show_alert=True)
            return
        
        if not card_data:
            await query.answer("❌ Карточка не найдена", show_alert=True)
            return
        
        # Get wallet
        result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == "TON"
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            await query.answer("❌ Кошелек не найден", show_alert=True)
            return
        
        qr_bytes = await QRCodeGenerator.generate_deposit_qr(wallet.deposit_address)
        card_msg = await format_business_card(card_data)
        
        await query.message.edit_media(
            media=types.InputMediaPhoto(
                media=types.BufferedInputFile(qr_bytes, filename="card_qr.png"),
                caption=card_msg,
                parse_mode="HTML"
            ),
            reply_markup=await get_business_card_keyboard(user_id)
        )
    
    elif action == "copy":
        user_id = int(query.data.split("_")[2])
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        link = f"https://t.me/Switzerwalletbot?start=card_{user.username or user_id}"
        await query.answer(
            f"Ссылка скопирована:\n{link}",
            show_alert=True
        )
    
    elif action == "send":
        currency = query.data.split("_")[2]
        recipient_id = int(query.data.split("_")[3])
        
        # Start transfer FSM
        await query.message.answer(
            f"💸 Введите сумму для отправки {currency}:"
        )
        await query.answer()
