#!/usr/bin/env python3
import os, sys
sys.path.insert(0, "/mnt/d/VeriTask")
from dotenv import load_dotenv
load_dotenv("/mnt/d/VeriTask/.env")
pk = os.getenv("CLIENT_PRIVATE_KEY", "")
print("PK set:", bool(pk), "starts with 0x:", pk[:4] if pk else "N/A")
from eth_account import Account
if pk:
    pk_hex = pk if pk.startswith("0x") else f"0x{pk}"
    acct = Account.from_key(pk_hex)
    print("Wallet:", acct.address)
