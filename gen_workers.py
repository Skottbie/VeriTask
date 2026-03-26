from eth_account import Account
import secrets
for name in ["Beta", "Gamma"]:
    key = secrets.token_hex(32)
    acct = Account.from_key(key)
    print(f"Worker {name}: address={acct.address} key=0x{key}")
