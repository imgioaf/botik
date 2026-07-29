
"""
CRUD операции специфичные для вывода средств.
Отдельный файл чтобы не раздувать основной crud.py.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime
from database.models import Wallet, Transaction, User
from database.crud import get_wallet

# Комиссии при выводе (фиксированные)
WITHDRAW_FEE = {
    "TON":  Decimal("0.01"),
    "USDT": Decimal("0.5"),
    "ETH":  Decimal("0.003"),
    "BTC":  Decimal("0.0001"),
}

# Газ для Jetton (USDT) перевода — списывается из TON баланса
JETTON_GAS_TON = Decimal("0.05")


async def check_and_reserve_withdraw(
    session: AsyncSession,
    user_id: int,
    currency: str,
    amount: Decimal
) -> tuple[bool, str, Decimal]:
    """
    Проверяет достаточность средств и резервирует их для вывода.

    Для USDT дополнительно проверяет наличие TON на газ.

    Возвращает (успех, сообщение_об_ошибке, итого_к_списанию).
    """
    fee = WITHDRAW_FEE.get(currency, Decimal("0"))
    total = amount + fee

    wallet = await get_wallet(session, user_id, currency)
    if not wallet:
        return False, "Кошелёк не найден", Decimal("0")

    if wallet.balance < total:
        return False, (
            f"Недостаточно средств.\n"
            f"Нужно: {total} {currency} (включая комиссию {fee} {currency})\n"
            f"Доступно: {wallet.balance} {currency}"
        ), Decimal("0")

    # Для USDT дополнительно проверяем TON на газ
    if currency == "USDT":
        ton_wallet = await get_wallet(session, user_id, "TON")
        if not ton_wallet or ton_wallet.balance < JETTON_GAS_TON:
            return False, (
                f"Для вывода USDT нужно ~{JETTON_GAS_TON} TON на газ.\n"
                f"Твой баланс TON: {ton_wallet.balance if ton_wallet else 0}"
            ), Decimal("0")

    # Резервируем средства (списываем сразу, вернём если транзакция упадёт)
    wallet.balance -= total

    # Если USDT — списываем TON на газ
    if currency == "USDT":
        ton_wallet = await get_wallet(session, user_id, "TON")
        ton_wallet.balance -= JETTON_GAS_TON

    # Создаём pending транзакцию
    session.add(Transaction(
        user_id=user_id,
        type="withdraw",
        currency=currency,
        amount=amount,
        fee=fee,
        status="pending"
    ))
    await session.commit()
    return True, "", total


async def finalize_withdraw(
    session: AsyncSession,
    user_id: int,
    currency: str,
    amount: Decimal,
    tx_hash: str,
    success: bool,
    error_msg: str = ""
):
    """
    Финализируем вывод после отправки в сеть.

    Если успех → помечаем транзакцию как done.
    Если провал → возвращаем средства и помечаем как failed.
    """
    # Находим последнюю pending транзакцию вывода
    result = await session.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == "withdraw",
            Transaction.currency == currency,
            Transaction.amount == amount,
            Transaction.status == "pending"
        ).order_by(Transaction.created_at.desc()).limit(1)
    )
    tx = result.scalar_one_or_none()

    if not tx:
        return

    if success:
        tx.status = "done"
        tx.tx_hash = tx_hash
    else:
        tx.status = "failed"
        # Возвращаем средства пользователю
        wallet = await get_wallet(session, user_id, currency)
        fee = WITHDRAW_FEE.get(currency, Decimal("0"))
        if wallet:
            wallet.balance += amount + fee

        # Возвращаем TON газ если это был USDT
        if currency == "USDT":
            ton_wallet = await get_wallet(session, user_id, "TON")
            if ton_wallet:
                ton_wallet.balance += JETTON_GAS_TON

        # Логируем возврат
        session.add(Transaction(
            user_id=user_id,
            type="withdraw_refund",
            currency=currency,
            amount=amount + fee,
            fee=Decimal("0"),
            status="done"
        ))

    await session.commit()