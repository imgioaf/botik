#!/usr/bin/env python3
"""Extended debug - check all handlers and functionality"""
import sys
import importlib
from pathlib import Path

print('╔════════════════════════════════════════════════════════════════╗')
print('║         🔍 РАСШИРЕННЫЙ ДЕБАГ - ПРОВЕРКА HANDLERS             ║')
print('╚════════════════════════════════════════════════════════════════╝\n')

sys.path.insert(0, 'c:\\switzerbot')

# 1. Проверка импортов главного модуля
print('[1] Проверка основных импортов:')
try:
    from bot.main import main
    print('  ✅ bot.main импортирован')
except Exception as e:
    print(f'  ❌ bot.main: {e}')

# 2. Проверка каждого handler
print('\n[2] Проверка handlers (импорты):')
handlers_to_check = [
    'start', 'wallet', 'transfer', 'checks',
    'invoices', 'withdraw', 'giveaway',
    'subscriptions', 'referral', 'settings', 'p2p',
    'business_card', 'split_payment', 'premium', 'menu',
    'tournaments', 'savings', 'auto_conversion', 'legacy',
    'help_explain', 'miniapp'
]

successful_handlers = []
failed_handlers = []

for handler_name in handlers_to_check:
    try:
        mod = importlib.import_module(f'bot.handlers.{handler_name}')
        if hasattr(mod, 'router'):
            print(f'  ✅ {handler_name:20} router found')
            successful_handlers.append(handler_name)
        else:
            print(f'  ⚠️  {handler_name:20} router NOT FOUND')
            failed_handlers.append(handler_name)
    except Exception as e:
        print(f'  ❌ {handler_name:20} {str(e)[:50]}')
        failed_handlers.append(handler_name)

print(f'\n  Успешно: {len(successful_handlers)}/{len(handlers_to_check)}')

# 3. Проверка Mini App специально
print('\n[3] Проверка Mini App интеграции:')
try:
    from bot.handlers import miniapp
    print(f'  ✅ miniapp импортирован')
    
    if hasattr(miniapp, 'router'):
        print(f'  ✅ miniapp.router существует')
    
    if hasattr(miniapp, 'cmd_miniapp'):
        print(f'  ✅ cmd_miniapp функция существует')
    
    if hasattr(miniapp, 'handle_miniapp_data'):
        print(f'  ✅ handle_miniapp_data функция существует')
        
    # Проверить action handlers
    handlers_list = ['deposit', 'withdraw', 'transfer', 'history', '2fa', 'devices']
    for handler in handlers_list:
        func_name = f'handle_{handler}_action'
        if hasattr(miniapp, func_name):
            print(f'  ✅ {func_name} существует')
        else:
            print(f'  ❌ {func_name} НЕ НАЙДЕНА')
    
except Exception as e:
    print(f'  ❌ Ошибка с miniapp: {e}')

# 4. Проверка HTML файла
print('\n[4] Проверка web_app_mini.html:')
html_path = Path('web_app_mini.html')
if html_path.exists():
    content = html_path.read_text()
    size = len(content)
    print(f'  ✅ Файл существует ({size} bytes)')
    
    checks = {
        'DOCTYPE': '<!DOCTYPE' in content,
        'Telegram API': 'telegram-web-app.js' in content,
        'sendAction function': 'function sendAction' in content,
        'Button handlers': 'onclick="sendAction' in content,
        'Theme support': 'colorScheme' in content,
        'Haptic feedback': 'HapticFeedback' in content,
    }
    
    for check_name, result in checks.items():
        status = '✅' if result else '❌'
        print(f'    {status} {check_name}')
else:
    print('  ❌ web_app_mini.html не найден')

# 5. Проверка config.py
print('\n[5] Проверка конфигурации:')
try:
    from config import settings
    
    required_settings = ['BOT_TOKEN', 'DATABASE_URL', 'TONCENTER_API_KEY']
    for setting in required_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            print(f'  ✅ {setting}: {"***" if len(str(value)) > 20 else value}')
        else:
            print(f'  ❌ {setting}: НЕ НАЙДЕН')
            
except Exception as e:
    print(f'  ❌ Ошибка с config: {e}')

# 6. Проверка database models
print('\n[6] Проверка database моделей:')
try:
    from database.models import User, Wallet, Transaction, Base
    print('  ✅ User импортирован')
    print('  ✅ Wallet импортирован')
    print('  ✅ Transaction импортирован')
    
    # Проверить что User имеет нужные атрибуты
    user_attrs = [
        'id', 'username', 'first_name', 'is_verified', 'is_banned',
        'referrer_id', 'two_fa_enabled', 'two_fa_secret', 'backup_codes'
    ]
    
    print(f'\n  Атрибуты User модели:')
    for attr in user_attrs[:5]:
        if hasattr(User, attr):
            print(f'    ✅ {attr}')
        else:
            print(f'    ❌ {attr}')
            
except Exception as e:
    print(f'  ❌ Ошибка с models: {e}')

# 7. Проверка keyboard imports
print('\n[7] Проверка клавиатур (keyboards):')
try:
    from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
    print('  ✅ ReplyKeyboardBuilder импортирован')
    print('  ✅ InlineKeyboardBuilder импортирован')
except Exception as e:
    print(f'  ❌ Ошибка с keyboards: {e}')

# 8. Проверка исправленных файлов
print('\n[8] Проверка исправленных файлов:')

# help_explain.py
try:
    from bot.handlers import help_explain
    content = Path('bot/handlers/help_explain.py').read_text()
    if '&lt;100ms' in content:
        print('  ✅ help_explain.py: HTML escape исправлено')
    else:
        print('  ❌ help_explain.py: HTML escape НЕ найден')
except Exception as e:
    print(f'  ❌ help_explain.py: {e}')

# business_card.py
try:
    from bot.handlers import business_card
    content = Path('bot/handlers/business_card.py').read_text()
    if 'try:' in content and 'user_id = int' in content:
        print('  ✅ business_card.py: Safe parsing добавлено')
    else:
        print('  ⚠️  business_card.py: Нужно проверить')
except Exception as e:
    print(f'  ❌ business_card.py: {e}')

# menu.py
try:
    from bot.handlers import menu
    content = Path('bot/handlers/menu.py').read_text()
    if 'query.message.text' in content:
        print('  ✅ menu.py: Text check добавлено')
    else:
        print('  ⚠️  menu.py: Нужно проверить')
except Exception as e:
    print(f'  ❌ menu.py: {e}')

# tournaments.py
try:
    from bot.handlers import tournaments
    content = Path('bot/handlers/tournaments.py').read_text()
    if 'subquery' in content or 'subq' in content:
        print('  ✅ tournaments.py: Subquery добавлена')
    else:
        print('  ⚠️  tournaments.py: Нужно проверить')
except Exception as e:
    print(f'  ❌ tournaments.py: {e}')

print('\n╔════════════════════════════════════════════════════════════════╗')
print('║                ✅ РАСШИРЕННЫЙ ДЕБАГ ЗАВЕРШЕН                  ║')
print('╚════════════════════════════════════════════════════════════════╝')

# Итоговая статистика
print(f'\n📊 ИТОГИ:')
print(f'  Handlers: {len(successful_handlers)}/{len(handlers_to_check)} успешно загружены')
if failed_handlers:
    print(f'  ⚠️  Проблемные handlers: {", ".join(failed_handlers)}')
