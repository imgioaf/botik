"""
🔧 FULL DEBUG & FIX SCRIPT
Диагностика и исправление всех проблем
"""

import sys
import os
from pathlib import Path

def print_header(title):
    print("\n" + "="*80)
    print(f"🔍 {title}")
    print("="*80 + "\n")

def check_imports():
    """Check all critical imports"""
    print_header("ПРОВЕРКА ИМПОРТОВ")
    
    imports_to_check = [
        ("aiogram", "Telegram Bot Framework"),
        ("sqlalchemy", "Database ORM"),
        ("pyotp", "2FA/TOTP"),
        ("qrcode", "QR codes"),
        ("aiohttp", "Async HTTP"),
        ("cryptography", "Encryption"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in imports_to_check:
        try:
            __import__(module_name)
            print(f"✅ {module_name:20} - {description}")
            passed += 1
        except ImportError as e:
            print(f"❌ {module_name:20} - {description}")
            print(f"   Error: {str(e)[:60]}")
            failed += 1
    
    print(f"\nРезультат: {passed} OK, {failed} FAILED")
    return failed == 0

def check_files():
    """Check critical files exist"""
    print_header("ПРОВЕРКА ФАЙЛОВ")
    
    critical_files = [
        "bot/main.py",
        "bot/handlers/menu.py",
        "bot/handlers/help_explain.py",
        "database/models.py",
        "database/crud.py",
        "config.py",
        "switzerbot.db",
    ]
    
    passed = 0
    failed = 0
    base_path = Path(__file__).parent
    
    for file_path in critical_files:
        full_path = base_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path:40} ({size:,} bytes)")
            passed += 1
        else:
            print(f"❌ {file_path:40} - ОТСУТСТВУЕТ")
            failed += 1
    
    print(f"\nРезультат: {passed} OK, {failed} FAILED")
    return failed == 0

def check_database():
    """Check database configuration"""
    print_header("ПРОВЕРКА БАЗЫ ДАННЫХ")
    
    try:
        import sqlite3
        db_path = Path(__file__).parent / "switzerbot.db"
        
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"✅ Users таблица: {users_count} записей")
            
            # Check columns
            cursor.execute("PRAGMA table_info(users)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {
                'id', 'username', 'first_name', 'is_verified',
                'two_fa_enabled', 'two_fa_secret', 'backup_codes',
                'trusted_devices', 'whitelisted_ips'
            }
            
            missing = required_columns - columns
            if missing:
                print(f"❌ Отсутствуют столбцы: {missing}")
                return False
            else:
                print(f"✅ Все необходимые столбцы присутствуют")
            
            conn.close()
            return True
        else:
            print(f"❌ Database файл не найден: {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def check_handlers():
    """Check all handlers import"""
    print_header("ПРОВЕРКА HANDLERS")
    
    handlers = [
        "menu", "start", "wallet", "transfer", "withdraw",
        "business_card", "split_payment", "premium",
        "tournaments", "savings", "auto_conversion", "legacy",
        "help_explain"
    ]
    
    passed = 0
    failed = 0
    
    for handler_name in handlers:
        try:
            module = __import__(f"bot.handlers.{handler_name}", fromlist=[handler_name])
            assert hasattr(module, "router"), f"No router in {handler_name}"
            print(f"✅ {handler_name:20} - Router OK")
            passed += 1
        except Exception as e:
            print(f"❌ {handler_name:20} - {str(e)[:40]}")
            failed += 1
    
    print(f"\nРезультат: {passed} OK, {failed} FAILED")
    return failed == 0

def check_config():
    """Check configuration"""
    print_header("ПРОВЕРКА КОНФИГУРАЦИИ")
    
    try:
        from config import settings
        
        checks = [
            ("BOT_TOKEN", bool(settings.BOT_TOKEN), "Токен Telegram API"),
            ("TONCENTER_API_KEY", bool(settings.TONCENTER_API_KEY), "TON Center API key"),
            ("DATABASE_URL", bool(settings.DATABASE_URL), "Database URL"),
        ]
        
        passed = 0
        for name, value, desc in checks:
            if value:
                print(f"✅ {name:20} - {desc}")
                passed += 1
            else:
                print(f"⚠️  {name:20} - {desc} (может быть пустым для тестирования)")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def check_security():
    """Check security modules"""
    print_header("ПРОВЕРКА БЕЗОПАСНОСТИ")
    
    try:
        from bot.security import ThrottlingMiddleware
        print(f"✅ ThrottlingMiddleware - Rate limiting")
        
        from bot.security_advanced import (
            TwoFactorAuth, DeviceFingerprint,
            TransactionRiskScorer, IPWhitelist
        )
        print(f"✅ TwoFactorAuth - 2FA система")
        print(f"✅ DeviceFingerprint - Device trust")
        print(f"✅ TransactionRiskScorer - Risk analysis")
        print(f"✅ IPWhitelist - IP control")
        
        # Test 2FA
        secret = TwoFactorAuth.generate_secret()
        print(f"✅ 2FA secret generation: {secret[:8]}...")
        
        # Test Device fingerprint
        fp = DeviceFingerprint.generate("test", "127.0.0.1", 12345)
        print(f"✅ Device fingerprint: {fp}")
        
        # Test Risk scoring
        from decimal import Decimal
        score, factors = TransactionRiskScorer.calculate_risk_score(
            Decimal("100"), Decimal("1000"), False
        )
        print(f"✅ Risk score: {score}/10 with {len(factors)} factors")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка безопасности: {e}")
        return False

def check_features():
    """Check Phase 1 & 2 features"""
    print_header("ПРОВЕРКА ФУНКЦИЙ")
    
    features = [
        ("business_card", "Business Card", "💳 Personal QR page"),
        ("split_payment", "Split Payment", "💸 Payment division"),
        ("premium", "Premium Plan", "⭐ 3-tier pricing"),
        ("tournaments", "Tournaments", "🏆 Weekly leaderboard"),
        ("savings", "Savings Goals", "📊 Goal accumulation"),
        ("auto_conversion", "Auto Conversion", "🤖 Auto currency swap"),
        ("legacy", "Legacy System", "🪦 Inheritance"),
    ]
    
    passed = 0
    for module_name, feature_name, desc in features:
        try:
            module = __import__(f"bot.handlers.{module_name}", fromlist=[module_name])
            assert hasattr(module, "router")
            print(f"✅ {feature_name:20} - {desc}")
            passed += 1
        except Exception as e:
            print(f"❌ {feature_name:20} - {str(e)[:40]}")
    
    return passed == len(features)

def print_summary(all_checks):
    """Print summary"""
    print_header("ФИНАЛЬНЫЙ ОТЧЕТ")
    
    all_passed = all(all_checks.values())
    
    status_emoji = "✅" if all_passed else "⚠️"
    
    print(f"{status_emoji} <b>РЕЗУЛЬТАТЫ ПРОВЕРКИ:</b>\n")
    for check_name, result in all_checks.items():
        emoji = "✅" if result else "❌"
        print(f"{emoji} {check_name}")
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! БОТ ГОТОВ К РАБОТЕ!")
        print("\nЗапусти бота:")
        print("  cd c:\\switzerbot")
        print("  venv\\Scripts\\activate")
        print("  python -m bot.main")
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("Исправь ошибки и запусти скрипт снова")
    
    print("="*80)

if __name__ == "__main__":
    print("\n🔧 SWITZERBOT v2.5 - ПОЛНАЯ ДИАГНОСТИКА\n")
    
    results = {
        "Импорты": check_imports(),
        "Файлы": check_files(),
        "База данных": check_database(),
        "Handlers": check_handlers(),
        "Конфигурация": check_config(),
        "Безопасность": check_security(),
        "Функции": check_features(),
    }
    
    print_summary(results)
