from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Numeric, DateTime, ForeignKey, Boolean, Integer, Text
from datetime import datetime
from decimal import Decimal


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    first_name: Mapped[str] = mapped_column(String(128))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(8), default="ru")
    referrer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    ref_earnings: Mapped[Decimal] = mapped_column(Numeric(36, 18), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Security fields (Advanced)
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_fa_secret: Mapped[str | None] = mapped_column(String(32))
    backup_codes: Mapped[str | None] = mapped_column(Text)  # JSON array
    trusted_devices: Mapped[str | None] = mapped_column(Text)  # JSON array of fingerprints
    whitelisted_ips: Mapped[str | None] = mapped_column(Text)  # JSON array of IPs
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[str | None] = mapped_column(String(32))  # ISO datetime string

    wallets: Mapped[list["Wallet"]] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10))
    balance: Mapped[Decimal] = mapped_column(Numeric(36, 18), default=Decimal("0"))
    deposit_address: Mapped[str | None] = mapped_column(String(256), unique=True)

    user: Mapped["User"] = relationship(back_populates="wallets")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    fee: Mapped[Decimal] = mapped_column(Numeric(36, 18), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    tx_hash: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_activated: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    description: Mapped[str | None] = mapped_column(String(512))
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)


class ProcessedTransaction(Base):
    __tablename__ = "processed_transactions"

    tx_hash: Mapped[str] = mapped_column(String(256), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Giveaway(Base):
    """Розыгрыши — аирдропы в каналах/чатах"""
    __tablename__ = "giveaways"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10))
    amount_per_winner: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    winners_count: Mapped[int] = mapped_column(Integer, default=1)
    # total = amount_per_winner * winners_count — заморожено при создании
    total_amount: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    caption: Mapped[str | None] = mapped_column(String(512))
    # pending | active | finished | cancelled
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    participants: Mapped[list["GiveawayParticipant"]] = relationship(back_populates="giveaway")


class GiveawayParticipant(Base):
    __tablename__ = "giveaway_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    giveaway_id: Mapped[int] = mapped_column(Integer, ForeignKey("giveaways.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    giveaway: Mapped["Giveaway"] = relationship(back_populates="participants")


class Subscription(Base):
    """Платные подписки на каналы"""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_title: Mapped[str] = mapped_column(String(256))
    currency: Mapped[str] = mapped_column(String(10))
    price_month: Mapped[Decimal] = mapped_column(Numeric(36, 18))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SubscriptionMember(Base):
    __tablename__ = "subscription_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)