"""
📊 CRYPTO SAVINGS POT (Крипто-копилка)
Save towards a goal with friends
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import json
import logging

from database.models import User, Wallet, Transaction

logger = logging.getLogger(__name__)
router = Router()


class SavingsFSM(StatesGroup):
    create_goal = State()
    create_target_amount = State()
    create_deadline = State()
    create_description = State()


class SavingsManager:
    """Manage savings goals"""
    
    # In-memory storage (in production - in DB)
    savings = {}
    
    @staticmethod
    def create_goal(
        user_id: int,
        target_amount: Decimal,
        deadline: str,
        currency: str = "TON",
        description: str = ""
    ) -> dict:
        """Create new savings goal"""
        goal_id = secrets.token_hex(6).upper()
        
        goal = {
            "id": goal_id,
            "user_id": user_id,
            "target_amount": float(target_amount),
            "current_amount": 0.0,
            "currency": currency,
            "deadline": deadline,
            "description": description,
            "contributors": {str(user_id): 0.0},  # user: amount_contributed
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        SavingsManager.savings[goal_id] = goal
        return goal
    
    @staticmethod
    def contribute_to_goal(goal_id: str, user_id: int, amount: Decimal) -> tuple[bool, str]:
        """Add contribution to goal"""
        goal = SavingsManager.savings.get(goal_id)
        
        if not goal:
            return False, "❌ Копилка не найдена"
        
        if goal["status"] != "active":
            return False, "❌ Копилка закрыта"
        
        # Check deadline
        deadline = datetime.fromisoformat(goal["deadline"])
        if datetime.utcnow() > deadline:
            goal["status"] = "completed"
            return False, "❌ Срок истёк"
        
        # Add contribution
        current = goal["current_amount"]
        new_amount = current + float(amount)
        
        # Check if complete
        if new_amount >= goal["target_amount"]:
            goal["status"] = "completed"
            goal["current_amount"] = new_amount
            return True, f"✅ Цель достигнута! Собрано {new_amount:.4f}"
        
        goal["current_amount"] = new_amount
        
        # Track contributor
        user_key = str(user_id)
        if user_key not in goal["contributors"]:
            goal["contributors"][user_key] = 0.0
        goal["contributors"][user_key] += float(amount)
        
        return True, f"✅ Добавлено {amount:.4f}. Прогресс: {new_amount:.4f}/{goal['target_amount']:.4f}"
    
    @staticmethod
    def get_progress_percent(goal_id: str) -> float:
        """Get goal progress percentage"""
        goal = SavingsManager.savings.get(goal_id)
        if not goal:
            return 0.0
        return (goal["current_amount"] / goal["target_amount"]) * 100


def format_savings_goal(goal: dict) -> str:
    """Format savings goal message"""
    progress = (goal["current_amount"] / goal["target_amount"]) * 100
    progress = min(progress, 100)
    
    # Progress bar
    filled = int(progress / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    deadline = datetime.fromisoformat(goal["deadline"])
    days_left = (deadline - datetime.utcnow()).days
    
    msg = "📊 <b>КРИПТО-КОПИЛКА</b> 📊\n\n"
    msg += f"🎯 <b>{goal['description']}</b>\n"
    msg += f"💰 Цель: {goal['target_amount']:.4f} {goal['currency']}\n"
    msg += f"💵 Собрано: {goal['current_amount']:.4f} {goal['currency']}\n\n"
    
    msg += f"Прогресс:\n{bar} {progress:.0f}%\n\n"
    
    msg += f"📅 До сроку: {days_left} дней\n"
    msg += f"👥 Помощников: {len(goal['contributors'])}\n"
    
    if goal['status'] == 'completed':
        msg += "\n✅ <b>ЦЕЛЬ ДОСТИГНУТА!</b>"
    
    return msg


@router.message(F.text == "📊 Копилка")
async def show_savings_menu(message: types.Message):
    """Show savings menu"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Создать", callback_data="savings_create"),
            InlineKeyboardButton(text="🔍 Найти", callback_data="savings_find")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(
        "📊 <b>КРИПТО-КОПИЛКА</b>\n\n"
        "💡 Накопи на мечту вместе с друзьями!\n\n"
        "🎂 Копила на подарок?\n"
        "🎮 Хочешь консоль?\n"
        "✈️ Копишь на путешествие?\n\n"
        "Создай цель → поделись со всеми → друзья помогут!",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "savings_create")
async def start_create_savings(query: types.CallbackQuery, state: FSMContext):
    """Start creating savings goal"""
    await query.message.answer(
        "Какая у тебя цель? (краткое описание)\n"
        "Пример: iPhone 15 Pro"
    )
    await state.set_state(SavingsFSM.create_goal)
    await query.answer()


@router.message(SavingsFSM.create_goal)
async def savings_goal_entered(message: types.Message, state: FSMContext):
    """Process goal name"""
    await state.update_data(description=message.text)
    await message.answer(
        "Сколько нужно собрать?\n"
        "Пример: 1000 USDT или 100 TON"
    )
    await state.set_state(SavingsFSM.create_target_amount)


@router.message(SavingsFSM.create_target_amount)
async def savings_amount_entered(message: types.Message, state: FSMContext):
    """Process target amount"""
    try:
        parts = message.text.split()
        amount = Decimal(parts[0])
        currency = parts[1].upper() if len(parts) > 1 else "TON"
        
        await state.update_data(target_amount=amount, currency=currency)
        await message.answer(
            "На какую дату накопить?\n"
            "Пример: 31.12.2026 или 2026-12-31"
        )
        await state.set_state(SavingsFSM.create_deadline)
    except:
        await message.answer("❌ Неправильный формат")


@router.message(SavingsFSM.create_deadline)
async def savings_deadline_entered(message: types.Message, state: FSMContext):
    """Create savings goal"""
    try:
        # Parse date
        try:
            deadline = datetime.strptime(message.text, "%d.%m.%Y")
        except:
            deadline = datetime.strptime(message.text, "%Y-%m-%d")
        
        data = await state.get_data()
        
        goal = SavingsManager.create_goal(
            user_id=message.from_user.id,
            target_amount=data["target_amount"],
            deadline=deadline.isoformat(),
            currency=data["currency"],
            description=data["description"]
        )
        
        goal_msg = format_savings_goal(goal)
        goal_code = goal["id"]
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔗 Поделиться",
                url=f"https://t.me/Switzerwalletbot?start=savings_{goal_code}"
            )],
            [InlineKeyboardButton(text="💰 Добавить", callback_data=f"savings_add_{goal_code}")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
        ])
        
        await message.answer(goal_msg, parse_mode="HTML", reply_markup=kb)
        await state.clear()
    except:
        await message.answer("❌ Неправильный формат даты")


@router.callback_query(F.data.startswith("savings_"))
async def handle_savings_callback(query: types.CallbackQuery):
    """Handle savings callbacks"""
    parts = query.data.split("_")
    action = parts[1]
    goal_id = parts[2] if len(parts) > 2 else None
    
    if action == "find":
        await query.message.answer("Введите ID копилки (6 символов):")
    
    elif action == "add" and goal_id:
        goal = SavingsManager.savings.get(goal_id)
        if goal:
            goal_msg = format_savings_goal(goal)
            await query.message.edit_text(goal_msg, parse_mode="HTML")
    
    await query.answer()
