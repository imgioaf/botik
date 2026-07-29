from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
import secrets, random, logging
from datetime import datetime

logger = logging.getLogger(__name__)

from database.models import (
    User, Wallet, Transaction,
    Check, Invoice, ProcessedTransaction,
    Giveaway, GiveawayParticipant,
    Subscription, SubscriptionMember
)

SUPPORTED_CURRENCIES = ["TON", "USDT", "ETH", "BTC", "BNB", "SOL", "ADA", "XRP", "DOGE", "MATIC"]
TRANSFER_FEE_PERCENT = Decimal("0.005")   # 0.5%
REF_PERCENT          = Decimal("0.20")    # 20% от комиссии — рефереру
DUST_THRESHOLD       = Decimal("0.01")


# ═══════════════════════ ПОЛЬЗОВАТЕЛИ ═══════════════════════════════════

async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: str,
    first_name: str,
    referrer_id: int | None = None
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=user_id,
            username=username or "",
            first_name=first_name,
            referrer_id=referrer_id if referrer_id != user_id else None
        )
        session.add(user)
        for currency in SUPPORTED_CURRENCIES:
            session.add(Wallet(user_id=user_id, currency=currency))
        await session.commit()
    else:
        changed = False
        if user.username != (username or ""):
            user.username = username or ""
            changed = True
        if changed:
            await session.commit()

    return user


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username.lstrip("@"))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).where(User.referrer_id == user_id)
    )
    return result.scalar() or 0


# ═══════════════════════ КОШЕЛЬКИ ════════════════════════════════════════

async def get_wallet(
    session: AsyncSession, user_id: int, currency: str
) -> Wallet | None:
    result = await session.execute(
        select(Wallet).where(Wallet.user_id == user_id, Wallet.currency == currency)
    )
    return result.scalar_one_or_none()


async def get_all_wallets(session: AsyncSession, user_id: int) -> list[Wallet]:
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    return list(result.scalars().all())


async def set_deposit_address(
    session: AsyncSession, user_id: int, currency: str, address: str
):
    wallet = await get_wallet(session, user_id, currency)
    if wallet:
        wallet.deposit_address = address
        await session.commit()


async def get_all_deposit_addresses(session: AsyncSession) -> list[tuple[str, int]]:
    result = await session.execute(
        select(Wallet.deposit_address, Wallet.user_id).where(
            Wallet.currency == "TON",
            Wallet.deposit_address.is_not(None)
        )
    )
    return [(row[0], row[1]) for row in result.fetchall()]


# ═══════════════════════ ТРАНЗАКЦИИ ══════════════════════════════════════

async def credit_deposit(
    session: AsyncSession, user_id: int, currency: str,
    amount: Decimal, tx_hash: str
) -> bool:
    wallet = await get_wallet(session, user_id, currency)
    if not wallet:
        return False
    wallet.balance += amount
    session.add(Transaction(
        user_id=user_id, type="deposit",
        currency=currency, amount=amount,
        fee=Decimal("0"), status="done", tx_hash=tx_hash
    ))
    await session.commit()
    return True


async def transfer_internal(
    session: AsyncSession,
    from_id: int, to_id: int,
    currency: str, amount: Decimal
) -> tuple[bool, str]:
    try:
        fee = (amount * TRANSFER_FEE_PERCENT).quantize(Decimal("0.000001"))
        total_deduct = amount + fee
        
        # FIX: Use FOR UPDATE to prevent race conditions (pessimistic lock)
        result = await session.execute(
            select(Wallet)
            .where(Wallet.user_id == from_id, Wallet.currency == currency)
            .with_for_update(nowait=False)
        )
        from_wallet = result.scalar_one_or_none()
        
        result = await session.execute(
            select(Wallet)
            .where(Wallet.user_id == to_id, Wallet.currency == currency)
            .with_for_update(nowait=False)
        )
        to_wallet = result.scalar_one_or_none()

        if not from_wallet:
            logger.warning(f"Transfer failed: sender {from_id} wallet not found")
            return False, "Кошелёк отправителя не найден"
        if not to_wallet:
            logger.warning(f"Transfer failed: receiver {to_id} wallet not found")
            return False, "Кошелёк получателя не найден"
        if from_wallet.balance < total_deduct:
            logger.warning(f"Transfer failed: insufficient balance {from_id} needs {total_deduct}")
            return False, f"Недостаточно средств (нужно {total_deduct} {currency})"

        from_wallet.balance -= total_deduct
        to_wallet.balance   += amount

        session.add(Transaction(user_id=from_id, type="transfer_out",
            currency=currency, amount=amount, fee=fee, status="done"))
        session.add(Transaction(user_id=to_id, type="transfer_in",
            currency=currency, amount=amount, fee=Decimal("0"), status="done"))

        # Реферальная награда — 20% от комиссии
        sender = await get_user_by_id(session, from_id)
        if sender and sender.referrer_id:
            ref_bonus = (fee * REF_PERCENT).quantize(Decimal("0.000001"))
            if ref_bonus > Decimal("0"):
                ref_wallet = await get_wallet(session, sender.referrer_id, currency)
                if ref_wallet:
                    ref_wallet.balance += ref_bonus
                    ref_user = await get_user_by_id(session, sender.referrer_id)
                    if ref_user:
                        ref_user.ref_earnings += ref_bonus
                    session.add(Transaction(
                        user_id=sender.referrer_id, type="referral_bonus",
                        currency=currency, amount=ref_bonus,
                        fee=Decimal("0"), status="done"
                    ))

        await session.commit()
        logger.info(f"Transfer successful: {from_id} → {to_id}, amount={amount} {currency}, fee={fee}")
        return True, ""
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        await session.rollback()
        return False, f"Ошибка транзакции: {str(e)}"


async def get_transaction_history(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ═══════════════════════ ДЕПОЗИТ: ЗАЩИТА ══════════════════════════════════

async def is_tx_processed(session: AsyncSession, tx_hash: str) -> bool:
    result = await session.execute(
        select(ProcessedTransaction).where(ProcessedTransaction.tx_hash == tx_hash)
    )
    return result.scalar_one_or_none() is not None


async def mark_tx_processed(session: AsyncSession, tx_hash: str):
    session.add(ProcessedTransaction(tx_hash=tx_hash))
    await session.commit()


# ═══════════════════════ ЧЕКИ ════════════════════════════════════════════

async def create_check(
    session: AsyncSession,
    creator_id: int, currency: str, amount: Decimal
) -> Check | None:
    wallet = await get_wallet(session, creator_id, currency)
    if not wallet or wallet.balance < amount:
        return None
    wallet.balance -= amount
    code = secrets.token_urlsafe(16)
    check = Check(creator_id=creator_id, currency=currency, amount=amount, code=code)
    session.add(check)
    await session.commit()
    return check


async def activate_check(
    session: AsyncSession, code: str, user_id: int
) -> tuple[Check | None, str]:
    result = await session.execute(
        select(Check).where(Check.code == code, Check.is_activated == False)  # noqa
    )
    check = result.scalar_one_or_none()
    if not check:
        return None, "Чек не найден или уже активирован"
    if check.creator_id == user_id:
        return None, "Нельзя активировать свой чек"

    wallet = await get_wallet(session, user_id, check.currency)
    if not wallet:
        return None, "Кошелёк не найден"

    wallet.balance += check.amount
    check.is_activated = True
    check.activated_by = user_id
    session.add(Transaction(
        user_id=user_id, type="check_received",
        currency=check.currency, amount=check.amount,
        fee=Decimal("0"), status="done"
    ))
    await session.commit()
    return check, ""


async def get_user_checks(session: AsyncSession, user_id: int) -> list[Check]:
    result = await session.execute(
        select(Check).where(Check.creator_id == user_id)
        .order_by(Check.
created_at.desc()).limit(20)
    )
    return list(result.scalars().all())


# ═══════════════════════ СЧЕТА ════════════════════════════════════════════

async def create_invoice(
    session: AsyncSession,
    creator_id: int, currency: str,
    amount: Decimal, description: str | None = None
) -> Invoice:
    from datetime import timedelta
    invoice = Invoice(
        creator_id=creator_id, currency=currency,
        amount=amount, description=description,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    session.add(invoice)
    await session.commit()
    return invoice


async def pay_invoice(
    session: AsyncSession, invoice_id: int, payer_id: int
) -> tuple[bool, str]:
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_paid == False)  # noqa
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        return False, "Счёт не найден или уже оплачен"
    if invoice.expires_at and invoice.expires_at < datetime.utcnow():
        return False, "Срок действия счёта истёк"
    if invoice.creator_id == payer_id:
        return False, "Нельзя оплатить собственный счёт"

    ok, err = await transfer_internal(
        session, from_id=payer_id,
        to_id=invoice.creator_id,
        currency=invoice.currency,
        amount=invoice.amount
    )
    if not ok:
        return False, err

    invoice.is_paid = True
    invoice.paid_by = payer_id
    await session.commit()
    return True, ""


# ═══════════════════════ РОЗЫГРЫШИ ════════════════════════════════════════

async def create_giveaway(
    session: AsyncSession,
    creator_id: int,
    currency: str,
    amount_per_winner: Decimal,
    winners_count: int,
    caption: str | None = None
) -> Giveaway | None:
    total = amount_per_winner * winners_count
    wallet = await get_wallet(session, creator_id, currency)
    if not wallet or wallet.balance < total:
        return None

    wallet.balance -= total
    giveaway = Giveaway(
        creator_id=creator_id,
        currency=currency,
        amount_per_winner=amount_per_winner,
        winners_count=winners_count,
        total_amount=total,
        caption=caption,
        status="active"
    )
    session.add(giveaway)
    session.add(Transaction(
        user_id=creator_id, type="giveaway_created",
        currency=currency, amount=total,
        fee=Decimal("0"), status="done"
    ))
    await session.commit()
    return giveaway


async def join_giveaway(
    session: AsyncSession, giveaway_id: int, user_id: int
) -> tuple[bool, str]:
    result = await session.execute(
        select(Giveaway).where(Giveaway.id == giveaway_id, Giveaway.status == "active")
    )
    giveaway = result.scalar_one_or_none()
    if not giveaway:
        return False, "Розыгрыш не найден или уже завершён"
    if giveaway.creator_id == user_id:
        return False, "Нельзя участвовать в своём розыгрыше"

    # Проверяем уже не участвует ли
    already = await session.execute(
        select(GiveawayParticipant).where(
            GiveawayParticipant.giveaway_id == giveaway_id,
            GiveawayParticipant.user_id == user_id
        )
    )
    if already.scalar_one_or_none():
        return False, "Ты уже участвуешь в этом розыгрыше"

    session.add(GiveawayParticipant(giveaway_id=giveaway_id, user_id=user_id))
    await session.commit()
    return True, ""


async def finish_giveaway(
    session: AsyncSession, giveaway_id: int
) -> list[int]:
    """Завершаем розыгрыш — выбираем победителей случайно, зачисляем призы."""
    result = await session.execute(
        select(Giveaway).where(Giveaway.id == giveaway_id, Giveaway.status == "active")
    )
    giveaway = result.scalar_one_or_none()
    if not giveaway:
        return []

    parts_result = await session.execute(
        select(GiveawayParticipant).where(GiveawayParticipant.giveaway_id == giveaway_id)
    )
    participants = list(parts_result.scalars().all())

    if not participants:
        # Никто не участвовал — возвращаем средства создателю
        wallet = await get_wallet(session, giveaway.creator_id, giveaway.currency)
        if wallet:
            wallet.balance += giveaway.total_amount
        giveaway.status = "cancelled"
        await session.commit()
        return []

    # Выбираем победителей
    count = min(giveaway.winners_count, len(participants))
    winners = random.sample(participants, count)
    winner_ids = []

    for w in winners:
        w.is_winner = True
        wallet = await get_wallet(session, w.user_id, giveaway.currency)
        if wallet:
            wallet.balance += giveaway.amount_per_winner
            session.add(Transaction(
                user_id=w.user_id, type="giveaway_win",
                currency=giveaway.currency,
                amount=giveaway.amount_per_winner,
                fee=Decimal("0"), status="done"
            ))
            winner_ids.append(w.user_id)

    # Если победителей меньше чем мест — возвращаем остаток
    remainder = giveaway.total_amount - (giveaway.amount_per_winner * len(winners))
    if remainder > Decimal("0"):
        creator_wallet = await get_wallet(session, giveaway.creator_id, giveaway.currency)
        if creator_wallet:
            creator_wallet.balance += remainder

    giveaway.status = "finished"
    giveaway.finished_at = datetime.utcnow()
    await session.commit()
    return winner_ids


async def get_giveaway(session: AsyncSession, giveaway_id: int) -> Giveaway | None:
    result = await session.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    return result.scalar_one_or_none()


# ═══════════════════════ ПОДПИСКИ ════════════════════════════════════════

async def create_subscription(
    session: AsyncSession,
    owner_id: int,
    channel_id: int,
    channel_title: str,
    currency: str,
    price_month: Decimal
) -> Subscription:
    sub = Subscription(
        owner_id=owner_id,
        channel_id=channel_id,
        channel_title=channel_title,
        currency=currency,
        price_month=price_month
    )
    session.add(sub)
    await session.commit()
    return sub


async def pay_subscription(
    session: AsyncSession,
    subscription_id: int,
    user_id: int,
    months: int = 1
) -> tuple[bool, str]:
    result = await session.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.is_active == True  # noqa
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return False, "Подписка не найдена"

    amount = sub.price_month * months
    ok, err = await transfer_internal(
        session, from_id=user_id,
        to_id=sub.owner_id,
        currency=sub.currency,
        amount=amount
    )
    if not ok:
        return False, err

    from datetime import timedelta

    # Проверяем есть ли уже активная подписка
    mem_result = await session.execute(
        select(SubscriptionMember).where(
            SubscriptionMember.subscription_id == subscription_id,
            SubscriptionMember.user_id == user_id
        )
    )
    member = mem_result.scalar_one_or_none()
    now = datetime.utcnow()

    if member:
        # Продлеваем
        base = member.expires_at if member.expires_at > now else now
        member.expires_at = base + timedelta(days=30 * months)
    else:
        member = SubscriptionMember(
            subscription_id=subscription_id,
            user_id=user_id,
            expires_at=now + timedelta(days=30 * months)
        )
        session.add(member)

    await session.commit()
    return True, ""


async def get_active_subscriptions(
    session: AsyncSession, owner_id: int
) -> list[Subscription]:
    result = await session.execute(
        select(Subscription).where(
            Subscription.owner_id == owner_id,
            Subscription.is_active == True  # noqa
        )
    )
    return list(result.scalars().all())