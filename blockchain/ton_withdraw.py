"""
Вывод TON и USDT (Jetton) on-chain.

Стек:
  - tonsdk  — подпись транзакций, формирование BOC
  - TON Center API v2 — получение seqno, отправка BOC (/sendBoc)

Архитектура:
  Все пользовательские адреса управляются одним мастер-ключом
  (subwallet_id = user_id, как в ton_wallet.py).
  При выводе: подписываем от имени пользовательского кошелька → отправляем BOC.

Важно:
  USDT на TON — это Jetton (аналог ERC-20).
  Для перевода Jetton нужно:
    1. Найти адрес Jetton-кошелька пользователя (не мастер-контракт).
    2. Отправить internal message на этот Jetton-кошелёк с инструкцией transfer.
    3. Приложить ~0.05 TON на газ.

NOTE: tonsdk требует Microsoft C++ Build Tools. Этот модуль временно заглушен.
TODO: Установить C++ Build Tools для работы вывода на блокчейн.
"""

import asyncio
import aiohttp
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Попытка импорта tonsdk (требует MSVC Build Tools)
try:
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    from tonsdk.contract.token.ft import JettonWallet
    from tonsdk.utils import to_nano, bytes_to_b64str, Address
    from tonsdk.crypto import mnemonic_to_wallet_key
    TONSDK_AVAILABLE = True
except ImportError:
    TONSDK_AVAILABLE = False
    logger.warning("⚠️ tonsdk не установлен (требует Microsoft C++ Build Tools). Функции вывода TON заглушены.")


# ─── Retry logic with exponential backoff ─────────────────────────────────────

async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Exponential backoff retry helper for blockchain operations.
    Delays: 1s, 2s, 4s
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)

# ─── Константы ────────────────────────────────────────────────────────────────

TONCENTER_V2 = "https://toncenter.com/api/v2"
TONCENTER_V3 = "https://toncenter.com/api/v3"

# Официальный мастер-контракт USDT (Tether) на TON mainnet
# Источник: https://tonviewer.com/EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
USDT_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# Газ для Jetton-перевода (TON списывается с отправителя, не из USDT)
JETTON_GAS_TON = Decimal("0.05")       # ~0.05 TON на газ для USDT перевода
MIN_WITHDRAW_TON = Decimal("0.05")     # минимальный вывод TON (должен покрывать сеть ~0.01)
MIN_WITHDRAW_USDT = Decimal("1.0")     # минимальный вывод USDT

# Комиссия сервиса при выводе
WITHDRAW_FEE_TON = Decimal("0.01")     # фиксированная комиссия в TON
WITHDRAW_FEE_USDT = Decimal("0.5")     # фиксированная комиссия в USDT

# USDT имеет 6 знаков после запятой (как USDT везде)
USDT_DECIMALS = 6


# ─── Клиент TON Center ────────────────────────────────────────────────────────

class TonCenterClient:
    """Тонкая обёртка над TON Center API v2/v3."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key}

    async def get_seqno(self, address: str) -> int:
        """
        Получаем текущий seqno кошелька.
        seqno = счётчик исходящих транзакций, нужен для подписи.
        Если кошелёк ещё не инициализирован (нет транзакций) → seqno = 0.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{TONCENTER_V3}/wallet",
                    params={"address": address},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    # Если кошелёк не инициализирован — seqno = 0
                    if data.get("status") == "uninit":
                        return 0
                    return int(data.get("seqno", 0))
            except Exception as e:
                logger.error(f"get_seqno error for {address[:12]}: {e}")
                raise

    async def send_boc(self, boc_b64: str) -> bool:
        """
        Отправляем подписанную транзакцию в сеть через TON Center API v2.
        boc_b64 — base64-encoded BOC (Bag of Cells).
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{TONCENTER_V2}/sendBoc",
                    json={"boc": boc_b64},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("ok"):
                        return True
                    logger.error(f"sendBoc failed: {data}")
                    return False
            except Exception as e:
                logger.error(f"send_boc error: {e}")
                return False

    async def get_jetton_wallet_address(self, owner_address: str, jetton_master: str
    ) -> str | None:
        """
        Получаем адрес Jetton-кошелька пользователя.

        На TON каждый пользователь имеет отдельный смарт-контракт для каждого Jetton.
        Адрес этого контракта вычисляется через get-метод мастер-контракта.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{TONCENTER_V2}/runGetMethod",
                    json={
                        "address": jetton_master,
                        "method": "get_wallet_address",
                        "stack": [["tvm.Slice", owner_address]]
                    },
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    # Парсим результат стека TVM
                    stack = data.get("result", {}).get("stack", [])
                    if stack and len(stack) > 0:
                        # Адрес возвращается как tvm.Slice
                        raw_addr = stack[0][1].get("value", "")
                        if raw_addr:
                            # Конвертируем raw address в user-friendly формат
                            addr = Address(raw_addr)
                            return addr.to_string(
                                is_user_friendly=True,
                                is_url_safe=True,
                                is_bounceable=True   # Jetton кошельки — bounceable
                            )
                    return None
            except Exception as e:
                logger.error(f"get_jetton_wallet_address error: {e}")
                return None

    async def wait_for_seqno_change(
        self, address: str, expected_seqno: int, timeout: int = 60
    ) -> bool:
        """Ждём пока seqno увеличится — подтверждение что транзакция принята."""
        elapsed = 0
        while elapsed < timeout:
            await asyncio.sleep(3)
            elapsed += 3
            try:
                current_seqno = await self.get_seqno(address)
                if current_seqno > expected_seqno:
                    return True
            except Exception:
                pass
        return False


# ─── Сервис вывода средств ────────────────────────────────────────────────────

class TONWithdrawService:
    """
    Сервис для отправки on-chain транзакций вывода TON и USDT.
    
    NOTE: Требует tonsdk (Microsoft C++ Build Tools)
    """

    def __init__(self, master_mnemonic: list[str], api_key: str):
        self.master_mnemonic = master_mnemonic
        self.api_key = api_key
        self.client = TonCenterClient(api_key)
        
        if TONSDK_AVAILABLE:
            _, self.master_keypair = mnemonic_to_wallet_key(master_mnemonic)
        else:
            self.master_keypair = None
            logger.warning("⚠️ TONWithdrawService инициализирован без tonsdk. Вывод TON/USDT недоступен.")

    def _get_wallet(self, user_id: int):
        """Восстанавливаем объект кошелька для пользователя (по subwallet_id)."""
        if not TONSDK_AVAILABLE:
            logger.error("❌ tonsdk не установлен. Невозможно создать кошелёк.")
            class MockWallet:
                address = type('obj', (object,), {
                    'to_string': lambda *args, **kwargs: f"EQ{user_id:064x}"
                })()
            return MockWallet()
        
        _, wallet = Wallets.create(
            version=WalletVersionEnum.v4r2,
            public_key=self.master_keypair.public_key,
            private_key=self.master_keypair.secret_key,
            workchain=0,
            subwallet_id=user_id
        )
        return wallet

    def _wallet_address(self, user_id: int) -> str:
        """Возвращает user-friendly адрес кошелька пользователя."""
        wallet = self._get_wallet(user_id)
        return wallet.address.to_string(
            is_user_friendly=True,
            is_url_safe=True,
            is_bounceable=False
        )

    async def withdraw_ton(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        comment: str = ""
    ) -> tuple[bool, str]:
        """
        Отправка TON on-chain.

        Возвращает (успех, tx_hash_or_error).
        При успехе — (True, "ok").
        При ошибке — (False, "описание ошибки").
        """
        if not TONSDK_AVAILABLE:
            return False, "❌ tonsdk не установлен. Требуется установка Microsoft C++ Build Tools."
        
        if amount < MIN_WITHDRAW_TON:
            return False, f"Минимальный вывод TON: {MIN_WITHDRAW_TON}"

        wallet = self._get_wallet(user_id)
        sender_address = self._wallet_address(user_id)

        try:
            seqno = await self.client.get_seqno(sender_address)
        except Exception as e:
            return False, f"Ошибка получения seqno: {e}"

        try:
            # Формируем и подписываем транзакцию
            # send_mode=3: PAY_GAS_SEPARATELY + IGNORE_ERRORS
            # bounce=False: средства не вернутся если адрес не существует
            query = wallet.create_transfer_message(
                to_addr=to_address,
                amount=to_nano(float(amount), "ton"),
                seqno=seqno,
                payload=comment,   # комментарий к транзакции
                send_mode=3,
                dummy_signature=False
            )
            boc = bytes_to_b64str(query["message"].to_boc(False))
        except Exception as e:
            return False, f"Ошибка подписи транзакции: {e}"

        # Отправляем в сеть
        success = await self.client.send_boc(boc)
        if not success:
            return False, "Ошибка отправки в сеть TON"

        # Ждём подтверждения (не блокируем — опционально)
        logger.info(f"TON withdraw sent: user={user_id} amount={amount} to={to_address[:12]}...")
        return True, "ok"

    async def withdraw_usdt(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal
    ) -> tuple[bool, str]:
        """
        Отправка USDT (Jetton) on-chain.

        USDT на TON — это Jetton. Алгоритм:
          1. Находим Jetton-кошелёк отправителя.
          2. Формируем Jetton transfer message.
          3. Отправляем internal message на Jetton-кошелёк (~0.05 TON на газ).

        ⚠️ Газ списывается из баланса TON пользователя (не из USDT).
        """
        if not TONSDK_AVAILABLE:
            return False, "❌ tonsdk не установлен. Требуется установка Microsoft C++ Build Tools."
        
        if amount < MIN_WITHDRAW_USDT:
            return False, f"Минимальный вывод USDT: {MIN_WITHDRAW_USDT}"

        wallet = self._get_wallet(user_id)
        sender_address = self._wallet_address(user_id)

        # 1. Получаем адрес Jetton-кошелька отправителя
        jetton_wallet_address = await self.client.get_jetton_wallet_address(
            owner_address=sender_address,
            jetton_master=USDT_MASTER_ADDRESS
        )
        if not jetton_wallet_address:
            return False, "Не удалось получить адрес Jetton-кошелька. Возможно USDT не поступали на адрес."

        try:
            seqno = await self.client.get_seqno(sender_address)
        except Exception as e:
            return False, f"Ошибка получения seqno: {e}"

        try:
            # USDT имеет 6 decimals, поэтому умножаем на 10^6
            usdt_amount_nano = int(amount * Decimal("1000000"))

            # Формируем тело сообщения для Jetton transfer
            # Стандарт TEP-74: https://github.com/ton-blockchain/TEPs/blob/master/text/0074-jettons-standard.md
            jetton_body = JettonWallet().create_transfer_body(
                to_address=Address(to_address),
                jetton_amount=usdt_amount_nano,
                forward_amount=to_nano(0.001, "ton"),   # уведомление получателю
                response_address=Address(sender_address) # вернуть излишек газа сюда
            )

            # Внешнее сообщение: с кошелька пользователя → на его Jetton-кошелёк
            # с инструкцией перевести USDT получателю
            query = wallet.create_transfer_message(
                to_addr=jetton_wallet_address,         # → Jetton-кошелёк
                amount=to_nano(float(JETTON_GAS_TON), "ton"),  # газ на выполнение
                seqno=seqno,
                payload=jetton_body,                   # инструкция для Jetton
                send_mode=3,
                dummy_signature=False
            )
            boc = bytes_to_b64str(query["message"].to_boc(False))
        except Exception as e:
            return False, f"Ошибка подписи Jetton транзакции: {e}"

        success = await self.client.send_boc(boc)
        if not success:
            return False, "Ошибка отправки Jetton транзакции в сеть"

        logger.info(f"USDT withdraw sent: user={user_id} amount={amount} to={to_address[:12]}...")
        return True, "ok"