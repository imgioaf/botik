import logging
from aiogram import Router
from aiogram.types import CallbackQuery
logger = logging.getLogger(__name__)
router = Router()

@router.callback_query()
async def unknown(cb: CallbackQuery):
    logger.warning("Unhandled callback: %s", cb.data)
    await cb.answer("Устаревшая кнопка. Отправь /start", show_alert=True)
