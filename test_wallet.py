from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.crypto import mnemonic_to_wallet_key

mnemonic = ['sketch','inherit','pole','dial','grant','first','timber','all','general','inspire','dash','coast','another','transfer','ladder','joy','glad','myself','light','wrong','any','double','panther','close']
public_key_bytes, secret_key_bytes = mnemonic_to_wallet_key(mnemonic)

# Try with mnemonic parameter instead
try:
    pub_list, pub_bytes, priv_bytes, wallet = Wallets.create(
        version=WalletVersionEnum.v4r2,
        workchain=0,
        mnemonic_password="",  # empty password
    )
    print(f"Address: {wallet.address.to_string(is_user_friendly=True, is_url_safe=True)}")
except Exception as e:
    print(f"Error: {e}")
    
# Try basic approach
try:
    from tonsdk.contract.wallet._wallet_contract_v4 import WalletV4ContractR2
    from tonsdk.utils import Address
    
    wallet = WalletV4ContractR2(
        address=Address("EQBnbBqPZm2ySjEHBPPrgvjGnKYDL_P3K8nqZvUYM-WFM-N0"),
        public_key=public_key_bytes,
    )
    print(f"WalletV4 created")
except Exception as e:
    print(f"Error 2: {e}")
