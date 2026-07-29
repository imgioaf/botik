#!/usr/bin/env python3
"""Full system debug script"""
import sys
import sqlite3
import json
from pathlib import Path

print('╔════════════════════════════════════════════════════════════════╗')
print('║         🔍 ПОЛНЫЙ СИСТЕМНЫЙ ДЕБАГ                            ║')
print('╚════════════════════════════════════════════════════════════════╝\n')

# 1. Python версия
print(f'[1] Python версия: {sys.version.split()[0]}')

# 2. Проверка файлов
print('\n[2] Проверка файлов проекта:')
files_to_check = [
    'bot/main.py',
    'bot/handlers/miniapp.py',
    'web_app_mini.html',
    'config.py/config.py',
    'database/models.py',
    'database/crud.py',
    'requirements.txt',
    'switzerbot.db'
]

for f in files_to_check:
    path = Path(f)
    if path.exists():
        size = path.stat().st_size
        print(f'  ✅ {f:30} {size:>10} bytes')
    else:
        print(f'  ❌ {f:30} NOT FOUND')

# 3. Проверка БД
print('\n[3] Проверка базы данных:')
try:
    conn = sqlite3.connect('switzerbot.db')
    cursor = conn.cursor()
    
    # Таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'  ✅ Таблиц: {len(tables)}')
    print(f'     Таблицы: {", ".join(tables[:5])}...')
    
    # Users
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    print(f'  ✅ Колонок в users: {len(columns)}')
    
    # Данные
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'  ✅ Пользователей: {user_count}')
    
    cursor.execute('SELECT COUNT(*) FROM transactions')
    tx_count = cursor.fetchone()[0]
    print(f'  ✅ Транзакций: {tx_count}')
    
    # Проверить нужные колонки в users
    security_cols = ['two_fa_enabled', 'two_fa_secret', 'backup_codes', 'trusted_devices', 'whitelisted_ips', 'failed_login_attempts', 'locked_until']
    cursor.execute('PRAGMA table_info(users)')
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    print(f'\n  [Security columns check]:')
    for col in security_cols:
        status = '✅' if col in existing_cols else '❌'
        print(f'    {status} {col}')
    
    conn.close()
except Exception as e:
    print(f'  ❌ Ошибка БД: {e}')

# 4. Импорты
print('\n[4] Проверка Python модулей:')
modules = [
    ('aiogram', 'aiogram'),
    ('sqlalchemy', 'sqlalchemy'),
    ('aiosqlite', 'aiosqlite'),
    ('tonsdk', 'tonsdk'),
    ('cryptography', 'cryptography'),
]

for name, import_name in modules:
    try:
        mod = __import__(import_name)
        version = getattr(mod, '__version__', 'OK')
        print(f'  ✅ {name:20} {version}')
    except ImportError:
        print(f'  ❌ {name:20} NOT FOUND')

# 5. Проверка handlers
print('\n[5] Проверка handlers:')
handlers_dir = Path('bot/handlers')
if handlers_dir.exists():
    handlers = [f.stem for f in handlers_dir.glob('*.py') if f.name != '__init__.py']
    print(f'  ✅ Handlers: {len(handlers)}')
    for h in sorted(handlers):
        print(f'     • {h}')
else:
    print('  ❌ Папка handlers не найдена')

# 6. Проверка config
print('\n[6] Проверка конфигурации:')
try:
    sys.path.insert(0, '/root' if Path('/root').exists() else 'c:\\switzerbot')
    from config import settings
    
    print(f'  ✅ BOT_TOKEN: {settings.BOT_TOKEN[:10]}...')
    print(f'  ✅ DATABASE_URL: {settings.DATABASE_URL[:30]}...')
    print(f'  ✅ TONCENTER_API_KEY: {settings.TONCENTER_API_KEY[:15]}...')
except Exception as e:
    print(f'  ⚠️  Ошибка чтения config: {e}')

print('\n╔════════════════════════════════════════════════════════════════╗')
print('║                ✅ ДЕБАГ ЗАВЕРШЕН                              ║')
print('╚════════════════════════════════════════════════════════════════╝')
