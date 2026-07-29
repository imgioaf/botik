import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.models import Base
from bot.middlewares.db import DbSessionMiddleware
from bot.security import ThrottlingMiddleware
from bot.handlers import (
    start, wallet, transfer, checks,
    invoices, withdraw, giveaway,
    subscriptions, referral, settings, p2p,
    business_card, split_payment, premium, menu,
    tournaments, savings, auto_conversion, legacy,
    help_explain, miniapp, menu_fixes, fallback
)
# from blockchain.ton_monitor import TONDepositMonitor
from config import settings as cfg


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

    # ── БД ─────────────────────────────────────────────────────────────────
    # На Windows для теста используем SQLite (не нужен отдельный сервер)
    # На VPS меняем на PostgreSQL через .env
    engine = create_async_engine(cfg.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # ── BOT ────────────────────────────────────────────────────────────────
    bot = Bot(
        token=cfg.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp  = Dispatcher()

    # Security: Rate limiting middleware
    dp.update.middleware(ThrottlingMiddleware())
    dp.update.middleware(DbSessionMiddleware(session_factory))

    # Регистрация всех роутеров
    dp.include_router(menu.router)
    dp.include_router(menu_fixes.router)         # главное меню первым
    dp.include_router(referral.router)   # раньше start — перехватывает /start ref_
    dp.include_router(wallet.router)
    dp.include_router(transfer.router)
    dp.include_router(checks.router)
    dp.include_router(invoices.router)
    dp.include_router(withdraw.router)
    dp.include_router(giveaway.router)
    dp.include_router(subscriptions.router)
    dp.include_router(settings.router)
    dp.include_router(p2p.router)
    dp.include_router(business_card.router)  # новое
    dp.include_router(split_payment.router)  # новое
    dp.include_router(premium.router)        # новое
    dp.include_router(tournaments.router)    # новое (неделя 2)
    dp.include_router(savings.router)        # новое (неделя 2)
    dp.include_router(auto_conversion.router) # новое (неделя 2)
    dp.include_router(legacy.router)         # новое (неделя 2)
    dp.include_router(miniapp.router)        # мини-приложение
    dp.include_router(help_explain.router)
    dp.include_router(fallback.router)   # справка и объяснения

    # ── МОНИТОР ДЕПОЗИТОВ ──────────────────────────────────────────────────
    # TODO: Требует tonsdk с bitarray (нужен MSVC Build Tools)
    # monitor = TONDepositMonitor(
    #     session_factory=session_factory,
    #     api_key=cfg.TONCENTER_API_KEY
    # )
    # asyncio.create_task(monitor.run())

    logger.info(f"✅ Bot @Switzerwalletbot started")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
    