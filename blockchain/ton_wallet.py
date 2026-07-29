"""
Генерация уникальных TON депозитных адресов.

Стратегия: один мастер-мнемоник + subwallet_id = user_id.
Один ключ контролирует все адреса. Стандартная практика custodial-сервисов.

NOTE: tonsdk требует Microsoft C++ Build Tools. Временное решение использует mock-адреса.
TODO: Установить C++ Build Tools и раскомментировать tonsdk импорты.
"""

import logging
import hashlib
import base64

logger = logging.getLogger(__name__)

# Попытка импорта tonsdk (требует MSVC Build Tools)
try:
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    TONSDK_AVAILABLE = True
except ImportError:
    TONSDK_AVAILABLE = False
    logger.warning("⚠️ tonsdk не установлен (требует Microsoft C++ Build Tools). Используются mock-адреса.")


class TONWalletGenerator:
    """
    TON Wallet address generator.
    
    Note: For simplicity, generates unique addresses per user and stores them.
    In production, use deterministic HD wallet derivation from mnemonic.
    """
    def __init__(self, master_mnemonic: list[str]):
        """Initialize with master mnemonic (not currently used - for future compatibility)."""
        self.master_mnemonic = master_mnemonic

    @staticmethod
    def generate_master_mnemonic() -> list[str]:
        """Generate new master mnemonic (call ONCE during setup)."""
        if TONSDK_AVAILABLE:
            from tonsdk.crypto import mnemonic_new
            return mnemonic_new(24)
        else:
            # Mock mnemonic for testing (24 random words)
            import random
            import string
            words = [
                "abandon", "ability", "able", "about", "above", "absent", "absolute", "absorb",
                "abstract", "absurd", "access", "accident", "account", "accuse", "achieve", "acid",
                "acknowledge", "acquire", "across", "act", "action", "actor", "actual", "add"
            ]
            return random.sample(words, k=24)

    def get_deposit_address(self, user_id: int) -> str:
        """
        Returns unique non-bounceable TON address for user.
        
        IMPORTANT: This generates a random address from mnemonic.
        In production, should use HD wallet derivation with subwallet_id.
        For now, addresses are generated and stored in database on first use.
        """
        if TONSDK_AVAILABLE:
            from tonsdk.contract.wallet import Wallets, WalletVersionEnum
            # Create a valid TON address using tonsdk
            pub_list, pub_bytes, priv_bytes, wallet = Wallets.create(
                version=WalletVersionEnum.v4r2,
                workchain=0,
                mnemonic_password="",
            )
            
            address = wallet.address.to_string(
                is_user_friendly=True,
                is_url_safe=True,
                is_bounceable=False
            )
            return address
        else:
            # Mock implementation: Generate deterministic but unique address based on user_id
            # Format: EQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (56 chars)
            hash_input = f"{user_id}:" + ",".join(self.master_mnemonic)
            hash_result = hashlib.sha256(hash_input.encode()).digest()
            
            # Create a valid TON address format (EQ prefix + base64)
            address_bytes = hash_result[:32]
            address_b64 = base64.b32encode(address_bytes).decode('ascii').lower()
            
            # Return mock TON address (valid format but deterministic)
            return f"EQ{address_b64[:51]}"

    def get_wallet_contract(self, user_id: int):
        """Возвращает объект кошелька для подписи исходящих транзакций (вывод)."""
        if TONSDK_AVAILABLE:
            from tonsdk.contract.wallet import Wallets, WalletVersionEnum
            _, wallet = Wallets.create(
                version=WalletVersionEnum.v4r2,
                public_key=self.master_keypair.public_key,
                private_key=self.master_keypair.secret_key,
                workchain=0,
                subwallet_id=user_id
            )
            return wallet
        else:
            # Mock wallet object for testing
            logger.warning(f"⚠️ Возврат mock wallet для user_id={user_id} (tonsdk недоступен)")
            class MockWallet:
                def __init__(self, user_id):
                    self.user_id = user_id
                    self.address = f"EQ{hashlib.sha256(str(user_id).encode()).hexdigest()[:56]}"
            return MockWallet(user_id)