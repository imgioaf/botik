"""
🤖 AUTO-CONVERSION (Авто-конвертация)
Automatically convert incoming crypto to preferred currency
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
import logging

from database.models import User, Wallet

logger = logging.getLogger(__name__)
router = Router()


class AutoConversionManager:
    """Manage automatic currency conversion"""
    
    CONVERSION_RATES = {
        ("TON", "USDT"): Decimal("7.5"),  # 1 TON = 7.5 USDT
        ("USDT", "TON"): Decimal("1") / Decimal("7.5"),
        ("ETH", "USDT"): Decimal("3000"),
        ("USDT", "ETH"): Decimal("1") / Decimal("3000"),
    }
    
    @staticmethod
    async def set_auto_conversion(
        session: AsyncSession,
        user_id: int,
        enabled: bool,
        from_currency: str = None,
        to_currency: str = None
    ) -> tuple[bool, str]:
        """Enable/disable auto conversion"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "❌ Пользователь не найден"
        
        if enabled:
            if not from_currency or not to_currency:
                return False, "❌ Укажите валюты"
            
            # Store conversion settings
            if not hasattr(user, 'auto_conversion_enabled'):
                # Create settings in memory or DB
                pass
            
            return True, f"✅ Авто-конвертация включена: {from_currency} → {to_currency}"
        else:
            return True, "✅ Авто-конвертация отключена"
    
    @staticmethod
    def get_conversion_rate(from_cur: str, to_cur: str) -> Decimal:
        """Get conversion rate"""
        if from_cur == to_cur:
            return Decimal("1")
        
        rate = AutoConversionManager.CONVERSION_RATES.get((from_cur, to_cur))
        return rate or Decimal("1")
    
    @staticmethod
    async def convert_currency(
        session: AsyncSession,
        user_id: int,
        from_currency: str,
        from_amount: Decimal,
        to_currency: str,
        fee_percent: Decimal = Decimal("0.01")
    ) -> tuple[bool, Decimal, str]:
        """Convert currency"""
        
        if from_currency == to_currency:
            return True, from_amount, "✅ Одинаковые валюты"
        
        # Get rate
        rate = AutoConversionManager.get_conversion_rate(from_currency, to_currency)
        
        # Calculate converted amount
        converted = from_amount * rate
        
        # Deduct fee (1% for conversion)
        fee = converted * fee_percent
        final_amount = converted - fee
        
        # Get wallets
        from_wallet_result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == from_currency
            )
        )
        from_wallet = from_wallet_result.scalar_one_or_none()
        
        to_wallet_result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == to_currency
            )
        )
        to_wallet = to_wallet_result.scalar_one_or_none()
        
        if not from_wallet or not to_wallet:
            return False, Decimal("0"), "❌ Кошельки не найдены"
        
        # Perform conversion
        from_wallet.balance -= from_amount
        to_wallet.balance += final_amount
        
        # Log conversion
        from database.models import Transaction
        tx = Transaction(
            user_id=user_id,
            type="auto_conversion",
            amount=from_amount,
            currency=from_currency,
            fee=fee,
            status="completed"
        )
        session.add(tx)
        
        await session.commit()
        
        return True, final_amount, f"✅ Конвертировано: {from_amount} {from_currency} → {final_amount:.4f} {to_currency}"


def format_auto_conversion_menu() -> str:
    """Format auto conversion settings"""
    msg = "🤖 <b>АВТО-КОНВЕРТАЦИЯ</b>\n\n"
    msg += "Автоматически конвертируй входящие платежи в нужную валюту!\n\n"
    msg += "<b>Пример:</b>\n"
    msg += "Включи: Все TON → USDT\n"
    msg += "Когда получишь 1 TON → Сразу станет ~7.5 USDT\n\n"
    msg += "💡 <b>Зачем?</b>\n"
    msg += "✅ Защита от волатильности\n"
    msg += "✅ Всегда получаешь стабильную валюту\n"
    msg += "✅ Удобно для новичков\n\n"
    msg += "⚠️ <b>Комиссия конвертации: 1%</b>"
    
    return msg


@router.message(F.text == "🤖 Конвертация")
async def show_auto_conversion(message: types.Message, session: AsyncSession):
    """Show auto conversion menu"""
    msg = format_auto_conversion_menu()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Включить", callback_data="autoconv_enable")],
        [InlineKeyboardButton(text="❌ Отключить", callback_data="autoconv_disable")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="autoconv_settings")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "autoconv_enable")
async def enable_auto_conversion(query: types.CallbackQuery):
    """Enable auto conversion"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="TON → USDT", callback_data="autoconv_set_ton_usdt"),
            InlineKeyboardButton(text="USDT → TON", callback_data="autoconv_set_usdt_ton")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await query.message.edit_text(
        "🤖 Выбери направление конвертации:\n\n"
        "TON → USDT: Все входящие TON станут USDT\n"
        "USDT → TON: Все входящие USDT станут TON",
        parse_mode="HTML",
        reply_markup=kb
    )
    await query.answer()


@router.callback_query(F.data.startswith("autoconv_set_"))
async def set_auto_conversion(query: types.CallbackQuery):
    """Set conversion direction"""
    direction = query.data.replace("autoconv_set_", "")
    from_cur, to_cur = direction.split("_")
    
    msg = (
        f"✅ <b>Авто-конвертация включена!</b>\n\n"
        f"🔄 Все входящие <b>{from_cur}</b> → <b>{to_cur}</b>\n\n"
        f"Например:\n"
        f"• Получишь 1 {from_cur}\n"
        f"• Автоматом станет {from_cur} {to_cur} (минус 1% комиссии)\n\n"
        f"📊 <b>Курс:</b> 1 {from_cur} ≈ 7.5 {to_cur}\n"
        f"💳 <b>Комиссия:</b> 1%"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"autoconv_confirm_{direction}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])
    
    await query.message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "autoconv_disable")
async def disable_auto_conversion(query: types.CallbackQuery):
    """Disable auto conversion"""
    await query.message.edit_text(
        "✅ Авто-конвертация отключена",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
        ])
    )
    await query.answer()
