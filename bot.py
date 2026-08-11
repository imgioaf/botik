"""
🤖 SWITZER WALLET BOT v3.0
Telegram Bot с Mini App, реферальной системой и админ-командами
Логика по плану Блок B (B1-B6)
"""

import asyncio
import logging
import os
import hmac
import hashlib
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
    Message, CallbackQuery, User
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import aiohttp

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфиг
load_dotenv("/opt/botik/.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
API_URL = os.getenv("API_URL", "https://switzerwallet.duckdns.org")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://imgioaf.github.io/botik/web_app.html?v=11")

# Bot setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# FSM States (для будущих операций)
class WithdrawState(StatesGroup):
    waiting_address = State()
    waiting_amount = State()

# ═══════════════════════════════════════════════════════════════
# 🔐 HMAC ВАЛИДАЦИЯ TELEGRAM DATA
# ═══════════════════════════════════════════════════════════════
def validate_telegram_data(init_data: str) -> bool:
    """Проверяет подпись Telegram данных (B1 безопасность)"""
    try:
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(
                dict(item.split("=") for item in init_data.split("&") 
                     if item != "hash").items()
            )
        )
        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        provided_hash = dict(
            item.split("=") for item in init_data.split("&")
        ).get("hash", "")
        return computed_hash == provided_hash
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# 📡 API ЗАПРОСЫ
# ═══════════════════════════════════════════════════════════════
async def api_get(endpoint: str, init_data: str = ""):
    """GET запрос к API с HMAC валидацией"""
    try:
        headers = {"X-Telegram-Init-Data": init_data} if init_data else {}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/{endpoint}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"API GET error: {e}")
        return None

async def api_post(endpoint: str, data: dict, init_data: str = ""):
    """POST запрос к API"""
    try:
        headers = {
            "X-Telegram-Init-Data": init_data,
            "Content-Type": "application/json"
        } if init_data else {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/{endpoint}",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"API POST error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# 🎯 ГЛАВНЫЕ КО��АНДЫ
# ═══════════════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    B6: Команда /start с богатым текстом, Mini App кнопкой, рефераллом
    """
    args = message.text.split()
    referrer_id = None
    
    # B1: Парсим рефералку из deep link
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
            # Отправляем на API для синхронизации
            await api_post("api/user/sync", {
                "user_id": message.from_user.id,
                "referrer_id": referrer_id
            })
        except (ValueError, IndexError):
            pass
    
    # Клавиатура с Mini App и кнопками
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Открыть кошелёк",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [
            InlineKeyboardButton(text="🔳 QR-визитка", web_app=WebAppInfo(url=WEBAPP_URL + "#qr")),
            InlineKeyboardButton(text="🔗 Рефералка", callback_data="ref")
        ],
        [
            InlineKeyboardButton(text="📖 Справка", callback_data="help"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ]
    ])
    
    welcome_text = (
        "🇨 **SWITZER WALLET** — крипто-кошелёк в Telegram\n\n"
        "Добро пожаловать! Весь интерфейс встроен в Mini App:\n\n"
        "💰 **Кошелёк** — баланс и живые курсы\n"
        "💵 **Пополнить** — депозит с адресом и QR\n"
        "📤 **Вывести** — на свой адрес с валидацией\n"
        "🔁 **Перевод** — друзьям за 0.5% комиссии\n"
        "📷 **QR-сканер** — быстрая отправка\n"
        "💎 **Мой QR** — визитка для приёма платежей\n"
        "📊 **История** — все транзакции\n"
        "🔗 **Рефералка** — 20% от комиссий друзей\n\n"
        "⚡ Быстро · 🔐 Безопасно · 💯 Прозрачно\n\n"
        f"{'✨ Ты по реферралу!' if referrer_id else 'Приглашай друзей!'}"
    )
    
    await message.answer(welcome_text, reply_markup=kb, parse_mode="Markdown")
    logger.info(f"User {message.from_user.id} started bot")

@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    """B2: Справка по всем функциям"""
    text = (
        "📖 **Справочник SwiWallet**\n\n"
        "**Основное:**\n"
        "• Жми 🚀 и открывается Mini App с полным интерфейсом\n"
        "• Там же баланс, пополнение, вывод, перевод, QR, история\n\n"
        "**QR-функции:**\n"
        "• 📷 Сканер — отсканируй чужой QR (bitcoin:/ethereum:/ton://)\n"
        "• 🔳 Мой QR — поделись своей визиткой для приёма денег\n\n"
        "**Реферралка:**\n"
        "• Твоя ссылка: /ref\n"
        "• Каждый друг = 20% от его комиссий тебе\n"
        "• Выплата ежедневно в USDT\n\n"
        "**Вывод:**\n"
        "• На адрес любого блокчейна (TON, BTC, ETH, TRX и т.д.)\n"
        "• Комиссия сети + 0.5% SwiWallet\n"
        "• Мин. вывод зависит от монеты\n\n"
        "**Поддержка:** @switzer_support"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "ref")
async def cb_ref(callback: CallbackQuery):
    """B4: Рефералка — показываем личную ссылку"""
    user_id = callback.from_user.id
    ref_link = f"https://t.me/Switzerwalletbot?start=ref_{user_id}"
    text = (
        f"🔗 **Твоя рефералка:**\n\n"
        f"`{ref_link}`\n\n"
        "📊 **Как это работает:**\n"
        "• Каждый друг, перешедший по твоей ссылке, даёт тебе 20% от его комиссий\n"
        "• Сумма = 20% × 0.5% комиссии друга\n"
        "• Выплачивается ежедневно в USDT\n\n"
        "👥 **Активные рефереры:** /stats"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    """Настройки (заготовка на будущее)"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌙 Тема", callback_data="theme")],
        [InlineKeyboardButton(text="🌍 Язык", callback_data="lang")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notif")],
        [InlineKeyboardButton(text="← Назад", callback_data="back")]
    ])
    await callback.message.edit_text("⚙️ Настройки (разработка в процессе)", reply_markup=kb)
    await callback.answer()

# ═══════════════════════════════════════════════════════════════
# 👨‍💼 АДМИН-КОМАНДЫ (B3)
# ═══════════════════════════════════════════════════════════════

def check_owner(user_id: int) -> bool:
    """Проверка прав владельца"""
    return user_id == OWNER_ID

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика бота (только для владельца)"""
    if not check_owner(message.from_user.id):
        await message.answer("❌ Доступно только владельцу")
        return
    
    try:
        stats = await api_get("api/stats")
        if stats:
            text = (
                f"📊 **Статистика SwiWallet**\n\n"
                f"👥 Пользователи: {stats.get('total_users', '?')}\n"
                f"💰 Объём 24ч: ${stats.get('volume_24h', '?')}\n"
                f"💸 Комиссии 24ч: ${stats.get('fees_24h', '?')}\n"
                f"📈 Активные: {stats.get('active_users', '?')}\n"
                f"🔗 Рефареры: {stats.get('referrers', '?')}"
            )
        else:
            text = "⚠️ Не удалось получить статистику"
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("users"))
async def cmd_users(message: Message):
    """Список пользователей с фильтром (только владелец)"""
    if not check_owner(message.from_user.id):
        await message.answer("❌ Доступно только владельцу")
        return
    
    try:
        users = await api_get("api/users")
        if users:
            user_list = "\n".join([
                f"• {u.get('name', '?')} ({u.get('user_id', '?')}) — ${u.get('balance', '?')}"
                for u in users[:10]
            ])
            text = f"👥 **Топ-10 пользователей:**\n\n{user_list}"
        else:
            text = "⚠️ Нет данных"
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Рассылка сообщения всем пользователям (только владелец)"""
    if not check_owner(message.from_user.id):
        await message.answer("❌ Доступно только владельцу")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /broadcast <сообщение>")
        return
    
    broadcast_text = args[1]
    try:
        result = await api_post("api/broadcast", {"text": broadcast_text})
        if result:
            await message.answer(f"✅ Рассылка отправлена: {result.get('sent', '?')} пользователям")
        else:
            await message.answer("⚠️ Ошибка при рассылке")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ═══════════════════════════════════════════════════════════════
# 💬 ОБРАБОТЧИКИ PUSH-УВЕДОМЛЕНИЙ (B2)
# ═══════════════════════════════════════════════════════════════

async def send_push_notification(
    user_id: int,
    title: str,
    message: str,
    emoji: str = "ℹ️"
):
    """B2: Отправка push-уведомления пользователю"""
    try:
        text = f"{emoji} **{title}**\n{message}"
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown"
        )
        logger.info(f"Push sent to {user_id}: {title}")
    except Exception as e:
        logger.error(f"Push notification error for {user_id}: {e}")

# Webhook для входящих депозитов (заглушка, будет вызвана из backend)
@router.post("/webhook/deposit")
async def webhook_deposit(request):
    """B2: Webhook для уведомления о входящем депозите"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        amount = data.get("amount")
        coin = data.get("coin")
        
        await send_push_notification(
            user_id,
            "Депозит поступил!",
            f"Получено: **{amount} {coin}**",
            emoji="💰"
        )
    except Exception as e:
        logger.error(f"Webhook deposit error: {e}")

# ═══════════════════════════════════════════════════════════════
# 🚀 ЗАПУСК БОТА
# ═══════════════════════════════════════════════════════════════

async def main():
    """Основной entry point"""
    dp.include_router(router)
    
    logger.info("🤖 SwiWallet Bot v3.0 starting...")
    logger.info(f"Owner ID: {OWNER_ID}")
    logger.info(f"WebApp URL: {WEBAPP_URL}")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
