"""
Фоновый воркер мониторинга TON депозитов.

Алгоритм:
  1. Каждые POLL_INTERVAL секунд запрашиваем транзакции через TON Center API v3.
  2. Фильтруем: только входящие, без bounce, сумма > DUST_THRESHOLD.
  3. Проверяем tx_hash в таблице processed_transactions.
  4. Новые → зачисляем баланс, помечаем как обработанные.
"""

import asyncio
import aiohttp
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.crud import (
    get_all_deposit_addresses,
    credit_deposit,
    is_tx_processed,
    mark_tx_processed
)

logger = logging.getLogger(__name__)

TONCENTER_API_URL = "https://toncenter.com/api/v3"
POLL_INTERVAL = 15          # секунд между полными циклами опроса
BATCH_SIZE = 10             # адресов за раз (rate-limit защита)
BATCH_PAUSE = 1.0           # пауза между батчами в секундах
TON_NANO = Decimal("1000000000")
DUST_THRESHOLD = Decimal("0.01")   # игнорируем переводы < 0.01 TON


class TONDepositMonitor:
    def __init__(self, session_factory: async_sessionmaker, api_key: str):
        self.session_factory = session_factory
        self.headers = {"X-Api-Key": api_key}

    async def _fetch_transactions(
        self,
        http: aiohttp.ClientSession,
        address: str,
        limit: int = 20
    ) -> list[dict]:
        try:
            async with http.get(
                f"{TONCENTER_API_URL}/transactions",
                params={"account": address, "limit": limit, "sort": "desc"},
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"TON API {resp.status} for {address[:12]}...")
                    return []
                data = await resp.json()
                return data.get("transactions", [])
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {address[:12]}...")
            return []
        except Exception as e:
            logger.error(f"Fetch error {address[:12]}...: {e}")
            return []

    @staticmethod
    def _parse_incoming_amount(tx: dict) -> Decimal | None:
        """
        Возвращает сумму входящего перевода в TON или None.

        Фильтруем:
          - только тип 'ord' (обычная транзакция)
          - только у которых есть in_msg с created_lt (не внешние сообщения)
          - исключаем bounce-фазы (деньги вернулись отправителю)
          - исключаем нулевые и dust суммы
        """
        desc = tx.get("description", {})
        if desc.get("type") != "ord":
            return None

        in_msg = tx.get("in_msg")
        if not in_msg or in_msg.get("created_lt") is None:
            return None

        bounce = desc.get("bounce")
        if bounce and bounce.get("type") in ("negFunds", "noFunds"):
            return None

        value = in_msg.get("value")
        if not value or int(value) <= 0:
            return None

        return Decimal(str(value)) / TON_NANO

    async def _process_address(
        self,
        http: aiohttp.ClientSession,
        db: object,           # AsyncSession
        address: str,
        user_id: int
    ):
        """Process address with full error handling to prevent monitor crash."""
        try:
            txs = await self._fetch_transactions(http, address)
            for tx in txs:
                tx_hash = tx.get("hash")
                if not tx_hash:
                    continue
                
                try:
                    if await is_tx_processed(db, tx_hash):
                        continue

                    amount = self._parse_incoming_amount(tx)
                    if amount is None or amount < DUST_THRESHOLD:
                        continue

                    success = await credit_deposit(db, user_id, "TON", amount, tx_hash)
                    if success:
                        await mark_tx_processed(db, tx_hash)
                        logger.info(
                            f"✅ Deposit: user={user_id} +{amount} TON tx={tx_hash[:16]}..."
                        )
                except Exception as e:
                    logger.error(f"Error processing tx {tx_hash[:16]}... for user {user_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error processing address {address[:12]}... for user {user_id}: {e}")

    async def run(self):
        logger.info("TON deposit monitor started")
        async with aiohttp.ClientSession() as http:
            while True:
                try:
                    async with self.session_factory() as db:
                        addresses = await get_all_deposit_addresses(db)
                        for i in range(0, len(addresses), BATCH_SIZE):
                            batch = addresses[i:i + BATCH_SIZE]
                            await asyncio.gather(
                                *[self._process_address(http, db, addr, uid)
                                  for addr, uid in batch],
                                return_exceptions=True
                            )
                            if i + BATCH_SIZE < len(addresses):
                                await asyncio.sleep(BATCH_PAUSE)
                except Exception as e:
                    logger.error(f"Monitor cycle error: {e}", exc_info=True)

                await asyncio.sleep(POLL_INTERVAL)