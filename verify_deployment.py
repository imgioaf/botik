"""
🔍 FINAL VERIFICATION SCRIPT
Run this before deploying to production
"""

import asyncio
import logging
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def verify_all():
    """Run all verification checks"""
    
    logger.info("=" * 80)
    logger.info("🔍 SWITZERBOT v2.0 - FINAL VERIFICATION")
    logger.info("=" * 80)
    
    checks_passed = 0
    checks_failed = 0
    
    # ══════════════════════════════════════════════════════════════════════
    # 1. IMPORTS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n📦 Checking imports...")
    
    try:
        from bot.security_advanced import (
            TwoFactorAuth, DeviceFingerprint, IPWhitelist, 
            TransactionRiskScorer, WithdrawalVerification, LoginAttemptTracker
        )
        logger.info("✅ bot/security_advanced.py - All classes import")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ bot/security_advanced.py - {e}")
        checks_failed += 1
    
    try:
        from bot.beautiful_ui import (
            CryptobotUI, FormattedMessages, QRCodeGenerator
        )
        logger.info("✅ bot/beautiful_ui.py - All classes import")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ bot/beautiful_ui.py - {e}")
        checks_failed += 1
    
    try:
        from bot.handlers import business_card, split_payment, premium, menu
        logger.info("✅ All new handlers import")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ New handlers - {e}")
        checks_failed += 1
    
    try:
        from database.models import User, Wallet, Transaction
        logger.info("✅ database/models.py - All models import")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ database/models.py - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 2. SECURITY MODULE CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n🔐 Checking security module...")
    
    try:
        # Test 2FA secret generation
        secret = TwoFactorAuth.generate_secret()
        assert len(secret) > 0
        logger.info(f"✅ TwoFactorAuth.generate_secret() - Generated: {secret[:8]}...")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ TwoFactorAuth.generate_secret() - {e}")
        checks_failed += 1
    
    try:
        # Test backup codes
        codes = TwoFactorAuth.generate_backup_codes(10)
        assert len(codes) == 10
        logger.info(f"✅ TwoFactorAuth.generate_backup_codes() - {len(codes)} codes")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ TwoFactorAuth.generate_backup_codes() - {e}")
        checks_failed += 1
    
    try:
        # Test device fingerprint
        fp = DeviceFingerprint.generate("Mozilla/5.0", "192.168.1.1", 12345)
        assert len(fp) == 16
        logger.info(f"✅ DeviceFingerprint.generate() - {fp}")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ DeviceFingerprint.generate() - {e}")
        checks_failed += 1
    
    try:
        # Test risk scoring
        score, factors = TransactionRiskScorer.calculate_risk_score(
            amount=Decimal("50"),
            user_balance=Decimal("100"),
            is_new_recipient=True,
            is_new_device=True,
            user_age_days=1
        )
        assert 0 <= score <= 10
        assert len(factors) > 0
        logger.info(f"✅ TransactionRiskScorer.calculate_risk_score() - Score: {score}/10")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ TransactionRiskScorer.calculate_risk_score() - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 3. BEAUTIFUL UI CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n🎨 Checking beautiful UI module...")
    
    try:
        kb = CryptobotUI.main_menu()
        assert kb is not None
        logger.info("✅ CryptobotUI.main_menu() - Keyboard created")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ CryptobotUI.main_menu() - {e}")
        checks_failed += 1
    
    try:
        msg = FormattedMessages.wallet_balance(
            ton_balance=Decimal("5.5"),
            usdt_balance=Decimal("100.00")
        )
        assert "5.5" in msg
        logger.info("✅ FormattedMessages.wallet_balance() - Message formatted")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ FormattedMessages.wallet_balance() - {e}")
        checks_failed += 1
    
    try:
        msg = FormattedMessages.referral_program(
            referral_link="https://t.me/Switzerwalletbot?start=ref_123",
            ref_count=5,
            earned=Decimal("0.5")
        )
        assert "t.me" in msg
        logger.info("✅ FormattedMessages.referral_program() - Message formatted")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ FormattedMessages.referral_program() - {e}")
        checks_failed += 1
    
    try:
        msg = FormattedMessages.security_status(
            two_fa_enabled=True,
            trusted_devices=2,
            whitelisted_ips=1
        )
        assert "✅" in msg
        logger.info("✅ FormattedMessages.security_status() - Message formatted")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ FormattedMessages.security_status() - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 4. PREMIUM FEATURES CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n⭐ Checking premium module...")
    
    try:
        from bot.handlers.premium import PremiumFeatures
        
        plans = PremiumFeatures.PLANS
        assert "free" in plans
        assert "basic" in plans
        assert "pro" in plans
        
        logger.info("✅ PremiumFeatures.PLANS - All plans defined")
        logger.info(f"   Free: {plans['free']['features']}")
        logger.info(f"   Basic: {plans['basic']['price']} TON/{plans['basic']['duration_days']}d")
        logger.info(f"   Pro: {plans['pro']['price']} TON/{plans['pro']['duration_days']}d")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ PremiumFeatures.PLANS - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 5. SPLIT PAYMENT CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n💸 Checking split payment module...")
    
    try:
        from bot.handlers.split_payment import SplitManager
        
        split = SplitManager.create_split(
            creator_id=12345,
            total_amount=Decimal("100"),
            people_count=4,
            currency="TON",
            description="Test split"
        )
        
        assert split["id"]
        assert float(split["per_person"]) == 25.0
        assert split["status"] == "active"
        
        logger.info(f"✅ SplitManager.create_split() - Created: {split['id']}")
        logger.info(f"   Amount: {split['total_amount']} {split['currency']}")
        logger.info(f"   Per person: {split['per_person']}")
        checks_passed += 1
    except Exception as e:
        logger.error(f"❌ SplitManager.create_split() - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 6. DATABASE MODEL CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n💾 Checking database models...")
    
    try:
        from database.models import User
        from sqlalchemy.orm import mapped_column
        
        # Check new security fields exist
        user_fields = User.__table__.columns.keys()
        
        required_fields = [
            'two_fa_enabled', 'two_fa_secret', 'backup_codes',
            'trusted_devices', 'whitelisted_ips', 'failed_login_attempts',
            'locked_until'
        ]
        
        missing = [f for f in required_fields if f not in user_fields]
        
        if missing:
            logger.error(f"❌ User model - Missing fields: {missing}")
            checks_failed += 1
        else:
            logger.info("✅ User model - All security fields added")
            checks_passed += 1
    except Exception as e:
        logger.error(f"❌ User model check - {e}")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # 7. DEPENDENCY CHECKS
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n📦 Checking dependencies...")
    
    try:
        import pyotp
        logger.info("✅ pyotp - Installed for 2FA")
        checks_passed += 1
    except ImportError:
        logger.error("❌ pyotp - NOT installed. Run: pip install pyotp")
        checks_failed += 1
    
    try:
        import qrcode
        logger.info("✅ qrcode - Installed for QR generation")
        checks_passed += 1
    except ImportError:
        logger.error("❌ qrcode - NOT installed. Run: pip install qrcode[pil]")
        checks_failed += 1
    
    try:
        import aiogram
        logger.info("✅ aiogram - Installed")
        checks_passed += 1
    except ImportError:
        logger.error("❌ aiogram - NOT installed")
        checks_failed += 1
    
    try:
        import sqlalchemy
        logger.info("✅ sqlalchemy - Installed")
        checks_passed += 1
    except ImportError:
        logger.error("❌ sqlalchemy - NOT installed")
        checks_failed += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 80)
    logger.info("📊 VERIFICATION RESULTS")
    logger.info("=" * 80)
    
    total = checks_passed + checks_failed
    percentage = (checks_passed / total * 100) if total > 0 else 0
    
    logger.info(f"Checks Passed: {checks_passed}/{total}")
    logger.info(f"Success Rate: {percentage:.1f}%")
    
    if checks_failed == 0:
        logger.info("\n✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        logger.info("\nNext steps:")
        logger.info("1. python -m bot.main")
        logger.info("2. Test in Telegram: /start")
        logger.info("3. Monitor logs for errors")
        logger.info("4. Launch marketing campaign")
        return True
    else:
        logger.error(f"\n❌ {checks_failed} CHECKS FAILED - FIX BEFORE DEPLOYMENT")
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_all())
    exit(0 if success else 1)
