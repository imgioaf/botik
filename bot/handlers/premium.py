"""
Premium Subscription System
Monetization through premium features
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from database.models import User, Wallet, Transaction

logger = logging.getLogger(__name__)
router = Router()


class PremiumFeatures:
    """Premium subscription plans"""
    
    PLANS = {
        "free": {
            "name": "Free",
            "price": Decimal("0"),
            "duration_days": 0,
            "features": {
                "daily_transfers": 10,
                "max_transfer": Decimal("1000"),
                "checks": 5,
                "splits": 3,
                "qr_codes": True,
                "priority_support": False,
                "custom_nickname": False,
                "fast_withdrawal": False,
                "badge": None
            }
        },
        "basic": {
            "name": "Basic",
            "price": Decimal("1"),  # 1 TON per month
            "duration_days": 30,
            "features": {
                "daily_transfers": 100,
                "max_transfer": Decimal("10000"),
                "checks": 50,
                "splits": 50,
                "qr_codes": True,
                "priority_support": False,
                "custom_nickname": False,
                "fast_withdrawal": False,
                "badge": "👤"
            }
        },
        "pro": {
            "name": "Pro",
            "price": Decimal("5"),  # 5 TON per month
            "duration_days": 30,
            "features": {
                "daily_transfers": 1000,
                "max_transfer": Decimal("100000"),
                "checks": 500,
                "splits": 500,
                "qr_codes": True,
                "priority_support": True,
                "custom_nickname": True,
                "fast_withdrawal": True,
                "badge": "💎"
            }
        }
    }
    
    @staticmethod
    async def get_user_plan(session: AsyncSession, user_id: int) -> str:
        """Get user's current plan"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return "free"
        
        # Check if premium is expired
        if hasattr(user, 'premium_until') and user.premium_until:
            if datetime.utcnow() < user.premium_until:
                return user.premium_plan or "free"
            else:
                # Downgrade to free
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(premium_plan="free", premium_until=None)
                )
                await session.commit()
        
        return "free"
    
    @staticmethod
    async def upgrade_plan(
        session: AsyncSession,
        user_id: int,
        plan: str
    ) -> tuple[bool, str]:
        """Upgrade user to premium plan"""
        
        if plan not in PremiumFeatures.PLANS:
            return False, "❌ План не найден"
        
        plan_info = PremiumFeatures.PLANS[plan]
        
        # Get user's TON wallet
        result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == "TON"
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            return False, "❌ TON кошелек не найден"
        
        price = plan_info["price"]
        
        # Check balance
        if wallet.balance < price:
            return False, f"❌ Недостаточно средств. Нужно {price} TON"
        
        # Deduct payment
        wallet.balance -= price
        
        # Create transaction
        tx = Transaction(
            user_id=user_id,
            type="premium_subscription",
            amount=price,
            currency="TON",
            fee=Decimal("0"),
            status="completed"
        )
        session.add(tx)
        
        # Update user premium status
        premium_until = datetime.utcnow() + timedelta(days=plan_info["duration_days"])
        
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                premium_plan=plan,
                premium_until=premium_until
            )
        )
        
        await session.commit()
        
        return True, f"✅ Подписка на {plan_info['name']} активирована на {plan_info['duration_days']} дней!"


def format_premium_message() -> str:
    """Format premium pricing message"""
    msg = "⭐ <b>PREMIUM ПОДПИСКА</b> ⭐\n\n"
    
    for plan_key, plan in PremiumFeatures.PLANS.items():
        msg += f"<b>🔹 {plan['name']}</b>\n"
        
        if plan["price"] == 0:
            msg += "💰 Бесплатно\n"
        else:
            msg += f"💰 {plan['price']} TON / месяц\n"
        
        features = plan["features"]
        msg += f"📊 До {features['daily_transfers']} переводов/день\n"
        msg += f"💵 Макс {features['max_transfer']} за раз\n"
        
        if features["custom_nickname"]:
            msg += "✨ Красивый никнейм\n"
        
        if features["fast_withdrawal"]:
            msg += "⚡ Быстрый вывод (1 мин)\n"
        
        if features["priority_support"]:
            msg += "📞 Приоритетная поддержка\n"
        
        msg += "\n"
    
    return msg


def get_premium_keyboard() -> InlineKeyboardMarkup:
    """Get premium plan selection keyboard"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Basic (1 TON)", callback_data="premium_basic"),
            InlineKeyboardButton(text="💎 Pro (5 TON)", callback_data="premium_pro")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    return kb


@router.message(F.text == "⭐ Премиум")
async def show_premium(message: types.Message, session: AsyncSession):
    """Show premium plans"""
    current_plan = await PremiumFeatures.get_user_plan(session, message.from_user.id)
    
    msg = format_premium_message()
    
    if current_plan != "free":
        msg += f"\n✅ Ваш текущий план: <b>{PremiumFeatures.PLANS[current_plan]['name']}</b>"
    
    await message.answer(msg, parse_mode="HTML", reply_markup=get_premium_keyboard())


@router.callback_query(F.data.startswith("premium_"))
async def handle_premium(query: types.CallbackQuery, session: AsyncSession):
    """Handle premium subscription"""
    plan = query.data.split("_")[1]
    
    plan_info = PremiumFeatures.PLANS.get(plan)
    if not plan_info:
        await query.answer("❌ План не найден", show_alert=True)
        return
    
    success, msg = await PremiumFeatures.upgrade_plan(session, query.from_user.id, plan)
    
    await query.answer(msg, show_alert=True)
    
    if success:
        # Update message
        current_plan = await PremiumFeatures.get_user_plan(session, query.from_user.id)
        message_text = format_premium_message()
        message_text += f"\n\n✅ Ваш текущий план: <b>{PremiumFeatures.PLANS[current_plan]['name']}</b>"
        
        await query.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=get_premium_keyboard()
        )
