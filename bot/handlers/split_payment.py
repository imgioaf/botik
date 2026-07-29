"""
Crypto Split (Крипто-сплит)
Split payments between multiple people
Create, share, and collect payments from group
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
from datetime import datetime, timedelta
import json
import secrets
import logging

from database.models import User, Transaction, Wallet
from database.crud import transfer_internal, get_wallet

logger = logging.getLogger(__name__)
router = Router()


class SplitFSM(StatesGroup):
    create_amount = State()
    create_people_count = State()
    create_description = State()
    join_split = State()


class SplitManager:
    """Manage split payments"""
    
    # In-memory storage (в production - в БД)
    splits = {}
    
    @staticmethod
    def create_split(
        creator_id: int,
        total_amount: Decimal,
        people_count: int,
        currency: str = "TON",
        description: str = ""
    ) -> dict:
        """Create new split"""
        split_id = secrets.token_hex(6).upper()
        per_person = total_amount / people_count
        
        split = {
            "id": split_id,
            "creator_id": creator_id,
            "total_amount": float(total_amount),
            "per_person": float(per_person),
            "people_count": people_count,
            "currency": currency,
            "description": description,
            "participants": {str(creator_id): True},  # creator pays
            "paid": {str(creator_id): float(per_person)},
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active"
        }
        
        SplitManager.splits[split_id] = split
        return split
    
    @staticmethod
    def join_split(split_id: str, user_id: int) -> tuple[bool, str]:
        """Join existing split"""
        split = SplitManager.splits.get(split_id)
        
        if not split:
            return False, "❌ Сплит не найден"
        
        if split["status"] != "active":
            return False, f"❌ Сплит завершен ({split['status']})"
        
        if str(user_id) in split["participants"]:
            return False, "❌ Вы уже участник"
        
        if len(split["participants"]) >= split["people_count"]:
            return False, "❌ Все места заняты"
        
        split["participants"][str(user_id)] = False
        return True, "✅ Вы присоединились!"
    
    @staticmethod
    def pay_split(split_id: str, user_id: int) -> tuple[bool, str, Decimal]:
        """Mark user as paid for split"""
        split = SplitManager.splits.get(split_id)
        
        if not split:
            return False, "❌ Сплит не найден", Decimal("0")
        
        if str(user_id) not in split["participants"]:
            return False, "❌ Вы не участник", Decimal("0")
        
        if split["paid"].get(str(user_id)):
            return False, "✅ Вы уже оплатили", Decimal("0")
        
        amount = Decimal(str(split["per_person"]))
        split["paid"][str(user_id)] = float(amount)
        
        # Check if all paid
        all_paid = len(split["paid"]) == len(split["participants"])
        if all_paid:
            split["status"] = "completed"
        
        return True, "✅ Оплачено!", amount


def format_split_message(split: dict, show_details: bool = False) -> str:
    """Format split payment message"""
    people_count = split["people_count"]
    paid_count = len(split["paid"])
    remaining = people_count - paid_count
    
    msg = "💸 <b>КРИПТО-СПЛИТ</b> 💸\n\n"
    msg += f"📌 <b>{split['description']}</b>\n"
    msg += f"💰 Сумма: {split['total_amount']} {split['currency']}\n"
    msg += f"👥 Участники: {people_count} чел.\n"
    msg += f"💵 На каждого: {split['per_person']:.4f} {split['currency']}\n\n"
    
    # Progress bar
    progress = int((paid_count / people_count) * 10)
    bar = "█" * progress + "░" * (10 - progress)
    msg += f"Оплачено: {bar} {paid_count}/{people_count}\n\n"
    
    if show_details:
        msg += "<b>Участники:</b>\n"
        for user_id_str, paid in split["paid"].items():
            status = "✅" if paid else "⏳"
            msg += f"{status} User {user_id_str}\n"
        msg += "\n"
    
    if split["status"] == "active":
        msg += f"⏱️ <i>Осталось {remaining} участников</i>\n"
    elif split["status"] == "completed":
        msg += "✅ <i>Все оплачено!</i>"
    
    return msg


@router.message(F.text == "💸 Сплит")
async def show_splits_menu(message: types.Message):
    """Show splits menu"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Создать", callback_data="split_create"),
            InlineKeyboardButton(text="🔍 Найти", callback_data="split_find")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(
        "💸 <b>КРИПТО-СПЛИТ</b> — Разделяй платежи с друзьями!\n\n"
        "🍕 Поели в ресторане?\n"
        "🎂 Собираем на подарок?\n"
        "🚗 Делим такси?\n\n"
        "Создай сплит → поделись со всеми → каждый платит свою долю! 💰",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "split_create")
async def start_create_split(query: types.CallbackQuery, state: FSMContext):
    """Start creating split"""
    await query.message.answer(
        "Сколько всего нужно собрать? (в TON или USDT)\n"
        "Пример: 100 TON или 50 USDT"
    )
    await state.set_state(SplitFSM.create_amount)
    await query.answer()


@router.message(SplitFSM.create_amount)
async def split_amount_entered(message: types.Message, state: FSMContext):
    """Process split amount"""
    try:
        parts = message.text.split()
        amount = Decimal(parts[0])
        currency = parts[1].upper() if len(parts) > 1 else "TON"
        
        if currency not in ["TON", "USDT"]:
            await message.answer("❌ Неизвестная валюта. Используйте TON или USDT")
            return
        
        await state.update_data(amount=amount, currency=currency)
        await message.answer("Сколько человек участвует?")
        await state.set_state(SplitFSM.create_people_count)
    except:
        await message.answer("❌ Неправильный формат. Пример: 100 TON")


@router.message(SplitFSM.create_people_count)
async def split_people_count(message: types.Message, state: FSMContext):
    """Process people count"""
    try:
        count = int(message.text)
        if count < 2 or count > 20:
            await message.answer("❌ От 2 до 20 человек")
            return
        
        await state.update_data(people_count=count)
        await message.answer(
            "Описание сплита (опционально):\n"
            "Пример: Обед в ресторане\n"
            "Нажми /skip чтобы пропустить"
        )
        await state.set_state(SplitFSM.create_description)
    except:
        await message.answer("❌ Введите число")


@router.message(SplitFSM.create_description)
async def split_description(message: types.Message, state: FSMContext):
    """Create split and show code"""
    data = await state.get_data()
    
    description = message.text if message.text != "/skip" else "Сплит"
    
    # Create split
    split = SplitManager.create_split(
        creator_id=message.from_user.id,
        total_amount=data["amount"],
        people_count=data["people_count"],
        currency=data["currency"],
        description=description
    )
    
    split_msg = format_split_message(split)
    split_code = split["id"]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔗 Поделиться",
            url=f"https://t.me/Switzerwalletbot?start=split_{split_code}"
        )],
        [InlineKeyboardButton(text="👥 Участники", callback_data=f"split_details_{split_code}")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(split_msg, parse_mode="HTML", reply_markup=kb)
    await state.clear()


@router.callback_query(F.data.startswith("split_"))
async def handle_split_callback(query: types.CallbackQuery, state: FSMContext):
    """Handle split callbacks"""
    action = query.data.split("_")[1]
    split_id = query.data.split("_")[2] if len(query.data.split("_")) > 2 else None
    
    if action == "find":
        await query.message.answer("Введите код сплита (6 символов):")
        await state.set_state(SplitFSM.join_split)
    
    elif action == "details":
        split = SplitManager.splits.get(split_id)
        if split:
            msg = format_split_message(split, show_details=True)
            await query.message.edit_text(msg, parse_mode="HTML")
    
    await query.answer()


@router.message(SplitFSM.join_split)
async def join_split_code(message: types.Message, state: FSMContext):
    """Join split by code"""
    code = message.text.upper()
    
    success, msg = SplitManager.join_split(code, message.from_user.id)
    
    if success:
        split = SplitManager.splits[code]
        split_msg = format_split_message(split)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💳 Оплатить",
                callback_data=f"split_pay_{code}"
            )],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
        ])
        
        await message.answer(split_msg, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(msg)
    
    await state.clear()
