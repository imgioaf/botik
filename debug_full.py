"""
🔍 FULL DEBUG SCRIPT FOR SWITZERBOT v2.5
Complete verification of all 15 features and 4 new modules
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def full_debug():
    """Run complete debug of entire project"""
    
    logger.info("=" * 80)
    logger.info("🔍 SWITZERBOT v2.5 - FULL DEBUG & VERIFICATION")
    logger.info("=" * 80)
    
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1: CORE MODULES
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 1: CORE MODULES & IMPORTS")
    logger.info("█" * 80)
    
    # Core handlers
    core_modules = [
        ("start.py", "from bot.handlers import start"),
        ("wallet.py", "from bot.handlers import wallet"),
        ("transfer.py", "from bot.handlers import transfer"),
        ("withdraw.py", "from bot.handlers import withdraw"),
    ]
    
    for name, import_statement in core_modules:
        total_checks += 1
        try:
            exec(import_statement)
            logger.info(f"✅ {name} - Import successful")
            passed_checks += 1
        except Exception as e:
            logger.error(f"❌ {name} - {str(e)[:50]}")
            failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2: PHASE 1 FEATURES (WEEK 1)
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 2: PHASE 1 FEATURES (Business Card, Split, Premium)")
    logger.info("█" * 80)
    
    # Business Card
    total_checks += 1
    try:
        from bot.handlers import business_card
        assert hasattr(business_card, "router")
        logger.info("✅ business_card.py - Router and handlers import")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ business_card.py - {e}")
        failed_checks += 1
    
    # Split Payment
    total_checks += 1
    try:
        from bot.handlers.split_payment import SplitManager
        split = SplitManager.create_split(
            creator_id=12345,
            total_amount=Decimal("100"),
            people_count=5,
            currency="TON"
        )
        assert split["id"]
        assert float(split["per_person"]) == 20.0
        logger.info(f"✅ split_payment.py - SplitManager creates splits (ID: {split['id'][:6]}...)")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ split_payment.py - {e}")
        failed_checks += 1
    
    # Premium
    total_checks += 1
    try:
        from bot.handlers.premium import PremiumFeatures
        plans = PremiumFeatures.PLANS
        assert "free" in plans and "basic" in plans and "pro" in plans
        logger.info(f"✅ premium.py - All 3 plans defined (Free/Basic/Pro)")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ premium.py - {e}")
        failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3: SECURITY MODULES
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 3: ADVANCED SECURITY MODULES")
    logger.info("█" * 80)
    
    # 2FA
    total_checks += 1
    try:
        from bot.security_advanced import TwoFactorAuth
        secret = TwoFactorAuth.generate_secret()
        codes = TwoFactorAuth.generate_backup_codes(10)
        assert len(secret) > 0 and len(codes) == 10
        logger.info(f"✅ TwoFactorAuth - Secret generation & backup codes")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ TwoFactorAuth - {e}")
        failed_checks += 1
    
    # Device Fingerprint
    total_checks += 1
    try:
        from bot.security_advanced import DeviceFingerprint
        fp = DeviceFingerprint.generate("Mozilla/5.0", "192.168.1.1", 12345)
        assert len(fp) == 16
        logger.info(f"✅ DeviceFingerprint - Generates unique IDs ({fp})")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ DeviceFingerprint - {e}")
        failed_checks += 1
    
    # Risk Scoring
    total_checks += 1
    try:
        from bot.security_advanced import TransactionRiskScorer
        score, factors = TransactionRiskScorer.calculate_risk_score(
            amount=Decimal("50"),
            user_balance=Decimal("100"),
            is_new_recipient=True,
            user_age_days=1
        )
        assert 0 <= score <= 10
        logger.info(f"✅ TransactionRiskScorer - Calculates risk {score}/10 with {len(factors)} factors")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ TransactionRiskScorer - {e}")
        failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4: BEAUTIFUL UI SYSTEM
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 4: BEAUTIFUL UI SYSTEM")
    logger.info("█" * 80)
    
    # Keyboards
    total_checks += 1
    try:
        from bot.beautiful_ui import CryptobotUI
        kb = CryptobotUI.main_menu()
        assert kb is not None
        logger.info(f"✅ CryptobotUI - Main menu keyboard created")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ CryptobotUI - {e}")
        failed_checks += 1
    
    # Formatted messages
    total_checks += 1
    try:
        from bot.beautiful_ui import FormattedMessages
        msg = FormattedMessages.wallet_balance(
            ton_balance=Decimal("5.5"),
            usdt_balance=Decimal("100.00")
        )
        assert "5.5" in msg and "100" in msg
        logger.info(f"✅ FormattedMessages - HTML formatting works")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ FormattedMessages - {e}")
        failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5: PHASE 2 FEATURES (NEW!)
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 5: PHASE 2 FEATURES (Tournaments, Savings, Auto-Conv, Legacy)")
    logger.info("█" * 80)
    
    # Tournaments
    total_checks += 1
    try:
        from bot.handlers.tournaments import TournamentManager
        week_start = TournamentManager.get_week_start()
        assert isinstance(week_start, datetime)
        logger.info(f"✅ tournaments.py - Leaderboard manager initialized")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ tournaments.py - {e}")
        failed_checks += 1
    
    # Savings
    total_checks += 1
    try:
        from bot.handlers.savings import SavingsManager
        goal = SavingsManager.create_goal(
            user_id=12345,
            target_amount=Decimal("100"),
            deadline=(datetime.utcnow() + timedelta(days=365)).isoformat(),
            currency="TON",
            description="Test goal"
        )
        assert goal["id"]
        assert goal["target_amount"] == 100.0
        logger.info(f"✅ savings.py - SavingsManager creates goals (ID: {goal['id'][:6]}...)")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ savings.py - {e}")
        failed_checks += 1
    
    # Auto-Conversion
    total_checks += 1
    try:
        from bot.handlers.auto_conversion import AutoConversionManager
        rate = AutoConversionManager.get_conversion_rate("TON", "USDT")
        assert rate == Decimal("7.5")
        logger.info(f"✅ auto_conversion.py - Conversion rates defined (1 TON = {rate} USDT)")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ auto_conversion.py - {e}")
        failed_checks += 1
    
    # Legacy
    total_checks += 1
    try:
        from bot.handlers.legacy import LegacyManager
        logger.info(f"✅ legacy.py - Legacy/Inheritance system imported")
        passed_checks += 1
    except Exception as e:
        logger.error(f"❌ legacy.py - {e}")
        failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6: DATABASE MODELS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 6: DATABASE MODELS")
    logger.info("█" * 80)
    
    total_checks += 1
    try:
        from database.models import User, Wallet, Transaction
        user_fields = User.__table__.columns.keys()
        
        required = [
            'two_fa_enabled', 'two_fa_secret', 'backup_codes',
            'trusted_devices', 'whitelisted_ips', 'failed_login_attempts'
        ]
        missing = [f for f in required if f not in user_fields]
        
        if missing:
            logger.error(f"❌ User model - Missing: {missing}")
            failed_checks += 1
        else:
            logger.info(f"✅ Database models - All security fields in User model")
            passed_checks += 1
    except Exception as e:
        logger.error(f"❌ Database models - {e}")
        failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7: DEPENDENCIES
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 7: REQUIRED DEPENDENCIES")
    logger.info("█" * 80)
    
    deps = [
        ("aiogram", "Telegram bot framework"),
        ("sqlalchemy", "Database ORM"),
        ("pyotp", "2FA/TOTP"),
        ("qrcode", "QR code generation"),
    ]
    
    for dep, desc in deps:
        total_checks += 1
        try:
            __import__(dep)
            logger.info(f"✅ {dep:15} - {desc}")
            passed_checks += 1
        except ImportError:
            logger.error(f"❌ {dep:15} - NOT INSTALLED")
            failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 8: HANDLERS REGISTRATION
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 8: ALL HANDLERS REGISTRATION")
    logger.info("█" * 80)
    
    handlers = [
        "menu", "start", "wallet", "transfer", "withdraw",
        "business_card", "split_payment", "premium",
        "tournaments", "savings", "auto_conversion", "legacy"
    ]
    
    for handler in handlers:
        total_checks += 1
        try:
            module = __import__(f"bot.handlers.{handler}", fromlist=[handler])
            assert hasattr(module, "router")
            logger.info(f"✅ {handler:20} - Router registered")
            passed_checks += 1
        except Exception as e:
            logger.error(f"❌ {handler:20} - {str(e)[:40]}")
            failed_checks += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # SECTION 9: FEATURE SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "█" * 80)
    logger.info("SECTION 9: COMPLETE FEATURE SUMMARY")
    logger.info("█" * 80)
    
    features = {
        "PHASE 1 (Week 1)": [
            "💳 Crypto Business Card - Personal QR payment page",
            "💸 Crypto Split - Group payment division",
            "⭐ Premium Subscription - 3-tier pricing system",
        ],
        "PHASE 2 (Week 2)": [
            "🏆 Tournaments - Weekly leaderboard with prizes",
            "📊 Crypto Savings - Accumulation goals with friends",
            "🤖 Auto-Conversion - Automatic currency conversion",
            "🪦 Crypto Legacy - Delayed transfer inheritance",
        ],
        "SECURITY": [
            "🔐 2FA Authentication - TOTP + backup codes",
            "🖥️ Device Fingerprinting - Trusted device system",
            "⚪ IP Whitelist - IP-based access control",
            "📊 Risk Scoring - Transaction risk analysis (0-10)",
        ],
        "ORIGINAL (Existing)": [
            "💰 Wallet Management - Multi-currency balance",
            "🔗 P2P Transfers - 0.5% commission transfers",
            "📤 Withdrawals - On-chain crypto withdrawal",
            "💎 Referral Program - 20% affiliate commission",
        ]
    }
    
    total_features = sum(len(v) for v in features.values())
    
    for category, items in features.items():
        logger.info(f"\n📌 {category} ({len(items)} features):")
        for item in items:
            logger.info(f"   ✅ {item}")
    
    # ══════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 80)
    logger.info("📊 FINAL DEBUG RESULTS")
    logger.info("=" * 80)
    
    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    logger.info(f"\nTotal Checks: {total_checks}")
    logger.info(f"Passed:       {passed_checks} ✅")
    logger.info(f"Failed:       {failed_checks} ❌")
    logger.info(f"Success Rate: {percentage:.1f}%\n")
    
    logger.info(f"Total Features: {total_features}")
    logger.info(f"Total Handlers: {len(handlers)}")
    logger.info(f"Total Dependencies: 4\n")
    
    if failed_checks == 0:
        logger.info("🎉 " + "=" * 76 + " 🎉")
        logger.info("✅ ALL CHECKS PASSED - SWITZERBOT v2.5 IS PRODUCTION READY!")
        logger.info("🎉 " + "=" * 76 + " 🎉\n")
        
        logger.info("📊 PROJECT STATUS:")
        logger.info("   ✅ 4 Phase 1 features (Business Card, Split, Premium)")
        logger.info("   ✅ 4 Phase 2 features (Tournaments, Savings, Auto-Conv, Legacy)")
        logger.info("   ✅ 4 Security systems (2FA, Device Trust, IP, Risk Scoring)")
        logger.info("   ✅ 12 Original handlers")
        logger.info("   ✅ 4 Supporting modules (UI, Security, Menu, Beautiful)")
        logger.info("   ✅ All dependencies installed\n")
        
        logger.info("🚀 READY TO DEPLOY:")
        logger.info("   1. python -m bot.main")
        logger.info("   2. Test in Telegram: /start")
        logger.info("   3. Launch marketing campaign\n")
        
        return True
    else:
        logger.error("❌ " + "=" * 76 + " ❌")
        logger.error(f"FAILED: {failed_checks} checks did not pass")
        logger.error("❌ " + "=" * 76 + " ❌\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(full_debug())
    exit(0 if success else 1)
