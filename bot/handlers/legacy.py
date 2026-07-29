"""
🪦 CRYPTO LEGACY (Крипто-завещание)
Delayed transfer if user doesn't login for N days
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio

from database.models import User, Wallet, Transaction

logger = logging.getLogger(__name__)
router = Router()


class LegacyFSM(StatesGroup):
    set_days = State()
    set_amount = State()
    set_address = State()
    confirm = State()


class LegacyManager:
    """Manage crypto legacy (delayed transfer)"""
    
    @staticmethod
    async def create_legacy(
        session: AsyncSession,
        user_id: int,
        inactive_days: int,
        amount: Decimal,
        recipient_address: str,
        currency: str = "TON"
    ) -> tuple[bool, str]:
        """Create legacy instruction"""
        
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "❌ Пользователь не найден"
        
        # Store legacy settings (in memory or DB)
        if not hasattr(user, 'legacy_settings'):
            user.legacy_settings = {}
        
        legacy_info = {
            "inactive_days": inactive_days,
            "amount": float(amount),
            "recipient_address": recipient_address,
            "currency": currency,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        user.legacy_settings = str(legacy_info)
        await session.commit()
        
        return True, f"✅ Завещание создано! При неактивности {inactive_days} дней отправим {amount} {currency} на адрес"
    
    @staticmethod
    async def check_legacy_transfers(session: AsyncSession):
        """Check and execute legacy transfers (run daily)"""
        
        result = await session.execute(
            select(User).where(User.legacy_settings != None)
        )
        users = result.scalars().all()
        
        for user in users:
            if not user.legacy_settings:
                continue
            
            try:
                import json
                legacy = json.loads(user.legacy_settings)
            except:
                continue
            
            if legacy.get("status") != "active":
                continue
            
            # Check if inactive
            last_login = datetime.fromisoformat(legacy.get("last_login", datetime.utcnow().isoformat()))
            inactive_days = legacy.get("inactive_days", 30)
            
            if (datetime.utcnow() - last_login).days >= inactive_days:
                # Execute transfer
                await LegacyManager.execute_legacy_transfer(
                    session,
                    user.id,
                    legacy
                )
    
    @staticmethod
    async def execute_legacy_transfer(
        session: AsyncSession,
        user_id: int,
        legacy_info: dict
    ):
        """Execute the legacy transfer"""
        
        currency = legacy_info.get("currency", "TON")
        amount = Decimal(str(legacy_info.get("amount", 0)))
        
        # Get wallet
        result = await session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.currency == currency
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet or wallet.balance < amount:
            logger.error(f"Legacy transfer failed for user {user_id}: insufficient balance")
            return
        
        # Execute transfer
        wallet.balance -= amount
        
        # Log transfer
        tx = Transaction(
            user_id=user_id,
            type="legacy_transfer",
            amount=amount,
            currency=currency,
            fee=Decimal("0"),
            status="completed"
        )
        session.add(tx)
        
        # Mark legacy as completed
        legacy_info["status"] = "completed"
        
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(legacy_settings=str(legacy_info))
        )
        
        await session.commit()
        
        logger.info(f"Executed legacy transfer: {amount} {currency} from user {user_id}")


def format_legacy_message() -> str:
    """Format legacy information message"""
    msg = "🪦 <b>КРИПТО-ЗАВЕЩАНИЕ</b> 🪦\n\n"
    msg += "Что это?\n"
    msg += "Если ты не заходил в бот N дней → крипта автоматом отправляется на адрес\n\n"
    msg += "<b>Примеры использования:</b>\n"
    msg += "💼 Наследство для семьи\n"
    msg += "👨‍👩‍👧‍👦 Подарок для близких если что-то случится\n"
    msg += "🔐 Страховка средств\n"
    msg += "🤝 Долг другу (если забуду отправить)\n\n"
    msg += "⚠️ <b>Как это работает:</b>\n"
    msg += "1. Создаешь завещание\n"
    msg += "2. Указываешь: дни неактивности, сумму, адрес\n"
    msg += "3. Если не залогинишься N дней → крипта отправляется\n"
    msg += "4. Если заходишь → счетчик сбрасывается\n\n"
    msg += "🔓 Всегда можно отменить"
    
    return msg


@router.message(F.text == "🪦 Завещание")
async def show_legacy(message: types.Message):
    """Show legacy menu"""
    msg = format_legacy_message()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Создать", callback_data="legacy_create")],
        [InlineKeyboardButton(text="📋 Просмотр", callback_data="legacy_view")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="legacy_cancel")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "legacy_create")
async def start_create_legacy(query: types.CallbackQuery, state: FSMContext):
    """Start creating legacy"""
    await query.message.answer(
        "Через сколько дней неактивности отправить крипту?\n"
        "Рекомендуемое: 30 дней\n"
        "Пример: 30"
    )
    await state.set_state(LegacyFSM.set_days)
    await query.answer()


@router.message(LegacyFSM.set_days)
async def legacy_days_set(message: types.Message, state: FSMContext):
    """Set inactive days"""
    try:
        days = int(message.text)
        if days < 7:
            await message.answer("❌ Минимум 7 дней")
            return
        
        await state.update_data(days=days)
        await message.answer("Сколько крипты отправить?\nПример: 1 TON или 50 USDT")
        await state.set_state(LegacyFSM.set_amount)
    except:
        await message.answer("❌ Введите число")


@router.message(LegacyFSM.set_amount)
async def legacy_amount_set(message: types.Message, state: FSMContext):
    """Set amount"""
    try:
        parts = message.text.split()
        amount = Decimal(parts[0])
        currency = parts[1].upper() if len(parts) > 1 else "TON"
        
        await state.update_data(amount=amount, currency=currency)
        await message.answer(
            "На какой адрес отправить?\n"
            f"(Адрес {currency} кошелька)"
        )
        await state.set_state(LegacyFSM.set_address)
    except:
        await message.answer("❌ Неправильный формат")


@router.message(LegacyFSM.set_address)
async def legacy_address_set(message: types.Message, state: FSMContext):
    """Confirm legacy"""
    address = message.text.strip()
    
    data = await state.get_data()
    
    msg = (
        f"🪦 <b>Проверь завещание:</b>\n\n"
        f"⏰ Дней неактивности: {data['days']}\n"
        f"💰 Отправить: {data['amount']} {data['currency']}\n"
        f"📍 На адрес: <code>{address[:20]}...</code>\n\n"
        f"✅ Подтвердить?"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"legacy_confirm_{data['days']}_{data['amount']}_{data['currency']}")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="back_main")]
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)
    await state.update_data(address=address)
    await state.set_state(LegacyFSM.confirm)


@router.callback_query(F.data.startswith("legacy_"))
async def handle_legacy_callback(query: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle legacy callbacks"""
    action = query.data.split("_")[1]
    
    if action == "view":
        await query.message.edit_text(
            "📋 <b>Твое завещание:</b>\n\n"
            "Нет активного завещания",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Создать", callback_data="legacy_create")],
                [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
            ])
        )
    
    elif action == "cancel":
        await query.message.edit_text(
            "✅ Завещание отменено",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
            ])
        )
    
    elif action == "confirm":
        data = await state.get_data()
        success, msg = await LegacyManager.create_legacy(
            session,
            query.from_user.id,
            data["days"],
            data["amount"],
            data["address"],
            data["currency"]
        )
        
        await query.message.edit_text(msg, parse_mode="HTML")
        await state.clear()
    
    await query.answer()
