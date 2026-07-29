from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import get_or_create_user
from bot.keyboards.main_kb import main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):    
    """Основной обработчик /start"""
    # Проверяем, есть ли параметры после /start (например ref_12345)
    args = message.text.split()[1] if len(message.text.split()) > 1 else None

    if args and args.startswith("ref_"):
        # Если пришёл по реферальной ссылке — обрабатываем в referral
        from bot.handlers.referral import deeplink_ref
        return await deeplink_ref(message, session)
    
    # Обычный запуск бота
    await get_or_create_user(
        session,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name
    )
    
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"💎 Добро пожаловать в <b>Switzer Wallet</b>\n\n"
        f"Храни, отправляй и получай криптовалюту прямо в Telegram.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )