
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str

    # БД
    DATABASE_URL: str
    REDIS_URL: str

    # TON
    TONCENTER_API_KEY: str
    TON_MASTER_MNEMONIC: str  # 24 слова через запятую

    # Опциональные
    CRYPTO_PAY_TOKEN: str = ""
    ETH_RPC_URL: str = ""
    BTC_RPC_URL: str = ""
    SUMSUB_APP_TOKEN: str = ""
    SUMSUB_SECRET_KEY: str = ""

    @property
    def ton_mnemonic_list(self) -> List[str]:
        return [w.strip() for w in self.TON_MASTER_MNEMONIC.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()