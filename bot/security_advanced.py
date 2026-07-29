"""
Advanced Security Module for Switzerbot
- 2FA (Two-Factor Authentication)
- IP Whitelist & Device Fingerprinting
- Withdrawal Verification Delays
- Transaction Risk Scoring
"""

import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import logging

logger = logging.getLogger(__name__)

# Security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
WITHDRAWAL_VERIFICATION_DELAY_HOURS = 24
MAX_DAILY_WITHDRAWAL = Decimal("100000")  # USDT
RISK_SCORE_THRESHOLD = 7.0


class DeviceFingerprint:
    """Generate device fingerprint from user metadata"""
    
    @staticmethod
    def generate(user_agent: str, ip: str, user_id: int) -> str:
        """Generate unique device fingerprint"""
        data = f"{user_agent}|{ip}|{user_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @staticmethod
    async def is_trusted_device(
        session: AsyncSession,
        user_id: int,
        fingerprint: str
    ) -> bool:
        """Check if device is in user's trusted list"""
        from database.models import User
        
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.trusted_devices:
            return False
        
        devices = json.loads(user.trusted_devices)
        return fingerprint in devices


class TwoFactorAuth:
    """2FA implementation using TOTP"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate random 2FA secret (base32 encoded)"""
        return secrets.token_hex(20)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    async def generate_otp_qr(user_id: int, email: str) -> str:
        """Generate QR code for authenticator app"""
        import pyotp
        import qrcode
        import io
        
        secret = TwoFactorAuth.generate_secret()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate QR code
        qr = qrcode.QR(
            totp.provisioning_uri(
                name=email,
                issuer_name='Switzerbot'
            )
        )
        
        return secret
    
    @staticmethod
    def verify_otp(secret: str, otp_code: str) -> bool:
        """Verify OTP code"""
        import pyotp
        
        totp = pyotp.TOTP(secret)
        return totp.verify(otp_code)


class IPWhitelist:
    """IP-based access control"""
    
    @staticmethod
    async def is_ip_whitelisted(
        session: AsyncSession,
        user_id: int,
        ip_address: str
    ) -> bool:
        """Check if IP is whitelisted for user"""
        from database.models import User
        
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.whitelisted_ips:
            return False
        
        ips = json.loads(user.whitelisted_ips)
        return ip_address in ips
    
    @staticmethod
    async def add_ip_to_whitelist(
        session: AsyncSession,
        user_id: int,
        ip_address: str
    ):
        """Add IP to user's whitelist"""
        from database.models import User
        
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            ips = json.loads(user.whitelisted_ips or "[]")
            if ip_address not in ips:
                ips.append(ip_address)
                await session.execute(
                    update(User)
                    .where(User.user_id == user_id)
                    .values(whitelisted_ips=json.dumps(ips))
                )
                await session.commit()


class TransactionRiskScorer:
    """Analyze transaction risk and require additional verification if needed"""
    
    @staticmethod
    def calculate_risk_score(
        amount: Decimal,
        user_balance: Decimal,
        is_new_recipient: bool = False,
        is_new_device: bool = False,
        is_unusual_time: bool = False,
        is_new_user: bool = False,
        user_age_days: int = 30
    ) -> tuple[float, list[str]]:
        """
        Calculate risk score (0-10)
        Returns: (score, risk_factors)
        """
        score = 0.0
        factors = []
        
        # Factor 1: Large transaction
        if amount > user_balance * Decimal("0.5"):
            score += 2.0
            factors.append("Большой перевод (>50% баланса)")
        
        if amount > user_balance * Decimal("0.8"):
            score += 1.5
            factors.append("Очень большой перевод (>80% баланса)")
        
        # Factor 2: New recipient
        if is_new_recipient:
            score += 1.5
            factors.append("Новый адрес получателя")
        
        # Factor 3: New device
        if is_new_device:
            score += 2.0
            factors.append("Новое устройство")
        
        # Factor 4: Unusual time (3am-6am UTC)
        if is_unusual_time:
            score += 1.0
            factors.append("Необычное время операции")
        
        # Factor 5: New user
        if is_new_user or user_age_days < 7:
            score += 2.0
            factors.append("Новый аккаунт")
        
        return min(score, 10.0), factors


class WithdrawalVerification:
    """Verify high-risk withdrawals with delay"""
    
    @staticmethod
    async def create_verification_request(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        address: str,
        currency: str,
        risk_score: float
    ) -> dict:
        """Create withdrawal verification request"""
        from database.models import Transaction
        
        verification_code = secrets.token_hex(3).upper()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Store in transaction record
        tx = Transaction(
            user_id=user_id,
            type="withdrawal_pending",
            amount=amount,
            currency=currency,
            fee=Decimal("0"),
            status="verification_pending",
            metadata=json.dumps({
                "address": address,
                "risk_score": risk_score,
                "verification_code": verification_code,
                "expires_at": expires_at.isoformat()
            })
        )
        
        session.add(tx)
        await session.commit()
        
        return {
            "verification_code": verification_code,
            "expires_at": expires_at,
            "transaction_id": tx.id
        }
    
    @staticmethod
    async def verify_withdrawal(
        session: AsyncSession,
        transaction_id: int,
        verification_code: str
    ) -> bool:
        """Verify withdrawal with code"""
        from database.models import Transaction
        
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        tx = result.scalar_one_or_none()
        
        if not tx or tx.status != "verification_pending":
            return False
        
        metadata = json.loads(tx.metadata or "{}")
        if metadata.get("verification_code") != verification_code:
            return False
        
        # Check if not expired
        expires_at = datetime.fromisoformat(metadata.get("expires_at", ""))
        if datetime.utcnow() > expires_at:
            return False
        
        # Mark as approved
        await session.execute(
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(status="verified")
        )
        await session.commit()
        
        return True


class LoginAttemptTracker:
    """Track failed login attempts and lock account if needed"""
    
    @staticmethod
    async def track_failed_attempt(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """Track failed login attempt, return attempts count"""
        from database.models import User
        
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return 0
        
        attempts = (user.failed_login_attempts or 0) + 1
        
        locked_until = None
        if attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = (datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()
        
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                failed_login_attempts=attempts,
                locked_until=locked_until
            )
        )
        await session.commit()
        
        return attempts
    
    @staticmethod
    async def reset_failed_attempts(
        session: AsyncSession,
        user_id: int
    ):
        """Reset failed login attempts after successful login"""
        from database.models import User
        
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                failed_login_attempts=0,
                locked_until=None
            )
        )
        await session.commit()
    
    @staticmethod
    async def is_account_locked(
        session: AsyncSession,
        user_id: int
    ) -> bool:
        """Check if account is locked due to failed attempts"""
        from database.models import User
        
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.locked_until:
            return False
        
        locked_until = datetime.fromisoformat(user.locked_until)
        if datetime.utcnow() > locked_until:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(locked_until=None)
            )
            await session.commit()
            return False
        
        return True
