#!/usr/bin/env python3
"""Full bot functionality test"""
import asyncio
import sys
from pathlib import Path

print('╔════════════════════════════════════════════════════════════════╗')
print('║      🤖 ПОЛНЫЙ ТЕСТ ФУНКЦИОНАЛЬНОСТИ БОТА                    ║')
print('╚════════════════════════════════════════════════════════════════╝\n')

sys.path.insert(0, 'c:\\switzerbot')

async def test_bot():
    """Test bot components"""
    
    print('[1] Инициализация компонентов:')
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from database.models import Base
        from config import settings
        
        print('  ✅ Импорты успешны')
        
        # Создать engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        print('  ✅ Engine создан')
        
        # Создать session factory
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        print('  ✅ Session factory создана')
        
        # Проверить базу
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print('  ✅ База готова')
        
    except Exception as e:
        print(f'  ❌ Ошибка инициализации: {e}')
        return

    print('\n[2] Тест CRUD операций:')
    try:
        from database.crud import get_or_create_user
        
        async with session_factory() as session:
            # Создать/получить пользователя
            user = await get_or_create_user(
                session,
                user_id=123456789,
                username='testuser',
                first_name='Test'
            )
            print(f'  ✅ Пользователь получен/создан: {user.username}')
            
            # Проверить кошельки
            from sqlalchemy import select
            from database.models import Wallet
            
            wallets = await session.execute(
                select(Wallet).where(Wallet.user_id == user.id)
            )
            wallet_list = wallets.scalars().all()
            print(f'  ✅ Кошельков: {len(wallet_list)}')
            
    except Exception as e:
        print(f'  ❌ Ошибка CRUD: {e}')

    print('\n[3] Тест Telegram Bot API:')
    try:
        from aiogram import Bot
        from config import settings
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        # Проверить что бот может подключиться
        me = await bot.get_me()
        print(f'  ✅ Bot ID: {me.id}')
        print(f'  ✅ Bot username: @{me.username}')
        print(f'  ✅ Bot first_name: {me.first_name}')
        
        await bot.session.close()
        
    except Exception as e:
        print(f'  ❌ Ошибка Telegram API: {e}')

    print('\n[4] Тест Dispatcher:')
    try:
        from bot.main import main
        from aiogram import Dispatcher
        
        print('  ✅ Dispatcher импортирован')
        
        # Проверить что можно создать dispatcher
        dp = Dispatcher()
        print('  ✅ Dispatcher создан')
        
    except Exception as e:
        print(f'  ❌ Ошибка Dispatcher: {e}')

    print('\n[5] Проверка middleware:')
    try:
        from bot.security import ThrottlingMiddleware
        from bot.middlewares.db import DbSessionMiddleware
        
        print('  ✅ ThrottlingMiddleware найден')
        print('  ✅ DbSessionMiddleware найден')
        
    except Exception as e:
        print(f'  ❌ Ошибка middleware: {e}')

    print('\n[6] Проверка TON интеграции:')
    try:
        from blockchain.ton_monitor import TONDepositMonitor
        from config import settings
        
        print('  ✅ TONDepositMonitor импортирован')
        print(f'  ✅ TONCENTER_API_KEY: {"***" if settings.TONCENTER_API_KEY else "NOT SET"}')
        
    except Exception as e:
        print(f'  ❌ Ошибка TON: {e}')

    print('\n[7] Проверка Mini App:')
    try:
        from bot.handlers import miniapp
        
        # Проверить что все нужные функции существуют
        functions = [
            'cmd_miniapp',
            'handle_miniapp_data',
            'handle_deposit_action',
            'handle_withdraw_action',
            'handle_transfer_action',
            'handle_history_action',
            'handle_2fa_action',
            'handle_devices_action',
            'process_deposit',
            'manage_2fa',
            'add_device'
        ]
        
        for func in functions:
            if hasattr(miniapp, func):
                print(f'  ✅ {func}')
            else:
                print(f'  ❌ {func} NOT FOUND')
                
    except Exception as e:
        print(f'  ❌ Ошибка Mini App: {e}')

# Run tests
try:
    asyncio.run(test_bot())
except Exception as e:
    print(f'\n❌ FATAL ERROR: {e}')
    import traceback
    traceback.print_exc()

print('\n╔════════════════════════════════════════════════════════════════╗')
print('║             ✅ ТЕСТ ФУНКЦИОНАЛЬНОСТИ ЗАВЕРШЕН                 ║')
print('╚════════════════════════════════════════════════════════════════╝')
