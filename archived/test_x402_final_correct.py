#!/usr/bin/env python3
"""
VeriTask — x402 Real Payment with CORRECT EIP-712 Domain
- Endpoint: /api/v6/x402/verify → /api/v6/x402/settle
- Domain name: "USD₮0" (NOT "Tether USD")
- Domain version: "1"
- Amount: 0.01 USDT = 10000 (6 decimals)
"""

import hmac
import hashlib
import base64
import json
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from eth_account import Account

load_dotenv()

# ─── Config ─────────────────────────────────────────────
CLIENT_PRIVATE_KEY = os.getenv("CLIENT_PRIVATE_KEY", "")
if CLIENT_PRIVATE_KEY and not CLIENT_PRIVATE_KEY.startswith("0x"):
    CLIENT_PRIVATE_KEY = "0x" + CLIENT_PRIVATE_KEY

WORKER_WALLET = os.getenv("WORKER_WALLET_ADDRESS", "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb")
API_KEY = os.getenv("OKX_API_KEY", "")
SECRET = os.getenv("OKX_SECRET_KEY", "")
PASSPHRASE = os.getenv("OKX_PASSPHRASE", "")

USDT_CONTRACT = "0x779ded0c9e1022225f8e0630b35a9b54be713736"
CHAIN_INDEX = "196"
CHAIN_ID = 196
AMOUNT_WEI = 10000  # 0.01 USDT (6 decimals)
BASE_URL = "https://web3.okx.com"


# ─── Auth ───────────────────────────────────────────────
def get_timestamp():
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def hmac_headers(method, path, body_str=""):
    ts = get_timestamp()
    prehash = ts + method.upper() + path + body_str
    sig = base64.b64encode(
        hmac.new(SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "OK-ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json",
    }


# ═══════════════════════════════════════════════════════
# STEP 1: Build EIP-3009 signature with CORRECT domain
# ═══════════════════════════════════════════════════════
print("=" * 64)
print("STEP 1: Sign TransferWithAuthorization (CORRECT domain)")
print("=" * 64)

account = Account.from_key(CLIENT_PRIVATE_KEY)
from_address = account.address

nonce = os.urandom(32)
nonce_hex = "0x" + nonce.hex()
valid_after = 0
valid_before = int(time.time()) + 3600  # 1 hour

# ★ CORRECT domain: name = "USD₮0", version = "1"
domain_data = {
    "name": "USD₮0",
    "version": "1",
    "chainId": CHAIN_ID,
    "verifyingContract": USDT_CONTRACT,
}

types = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ],
}

message = {
    "from": from_address,
    "to": WORKER_WALLET,
    "value": AMOUNT_WEI,
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce,
}

signed = Account.sign_typed_data(CLIENT_PRIVATE_KEY, domain_data, types, message)
signature = "0x" + signed.signature.hex()

print(f"  From:   {from_address}")
print(f"  To:     {WORKER_WALLET}")
print(f"  Amount: 0.01 USDT ({AMOUNT_WEI})")
print(f"  Domain: name='USD₮0', version='1', chainId={CHAIN_ID}")
print(f"  Sig:    {signature[:42]}...")
print(f"  Nonce:  {nonce_hex[:24]}...")
print()

# ═══════════════════════════════════════════════════════
# STEP 2: Verify
# ═══════════════════════════════════════════════════════
print("=" * 64)
print("STEP 2: POST /api/v6/x402/verify")
print("=" * 64)

verify_body = {
    "x402Version": 1,
    "chainIndex": CHAIN_INDEX,
    "paymentPayload": {
        "x402Version": 1,
        "scheme": "exact",
        "chainIndex": CHAIN_INDEX,
        "payload": {
            "signature": signature,
            "authorization": {
                "from": from_address,
                "to": WORKER_WALLET,
                "value": str(AMOUNT_WEI),
                "validAfter": str(valid_after),
                "validBefore": str(valid_before),
                "nonce": nonce_hex,
            },
        },
    },
    "paymentRequirements": {
        "scheme": "exact",
        "chainIndex": CHAIN_INDEX,
        "maxAmountRequired": str(AMOUNT_WEI),
        "resource": "https://veritask.xyz/api/v1/tasks",
        "description": "VeriTask C2C verified data procurement",
        "mimeType": "application/json",
        "payTo": WORKER_WALLET,
        "asset": USDT_CONTRACT,
        "maxTimeoutSeconds": 30,
        "extra": {"gasLimit": "1000000"},
    },
}

verify_path = "/api/v6/x402/verify"
body_str = json.dumps(verify_body, separators=(",", ":"), sort_keys=True)
headers = hmac_headers("POST", verify_path, body_str)

print(f"  URL: {BASE_URL}{verify_path}")
print(f"  Body length: {len(body_str)} bytes")

r = requests.post(f"{BASE_URL}{verify_path}", headers=headers, data=body_str, timeout=15)
print(f"  Status: {r.status_code}")
try:
    j = r.json()
    print(f"  Response: {json.dumps(j, ensure_ascii=False, indent=2)}")
except Exception:
    print(f"  Response: {r.text[:300]}")

# ═══════════════════════════════════════════════════════
# STEP 3: Settle (only if verify was valid)
# ═══════════════════════════════════════════════════════
verify_valid = False
try:
    data = r.json().get("data", [{}])
    if data and data[0].get("isValid"):
        verify_valid = True
except Exception:
    pass

if verify_valid:
    print("\n" + "=" * 64)
    print("STEP 3: POST /api/v6/x402/settle (REAL PAYMENT!)")
    print("=" * 64)

    settle_path = "/api/v6/x402/settle"
    settle_body_str = json.dumps(verify_body, separators=(",", ":"), sort_keys=True)
    settle_headers = hmac_headers("POST", settle_path, settle_body_str)

    r2 = requests.post(f"{BASE_URL}{settle_path}", headers=settle_headers, data=settle_body_str, timeout=30)
    print(f"  Status: {r2.status_code}")
    try:
        j2 = r2.json()
        print(f"  Response: {json.dumps(j2, ensure_ascii=False, indent=2)}")
        
        # Extract txHash if present
        settle_data = j2.get("data", [{}])
        if settle_data and settle_data[0].get("txHash"):
            tx_hash = settle_data[0]["txHash"]
            print(f"\n  🎉 TX HASH: {tx_hash}")
            print(f"  Explorer: https://www.oklink.com/xlayer/tx/{tx_hash}")
    except Exception:
        print(f"  Response: {r2.text[:300]}")
else:
    print(f"\n⚠ Verify returned isValid=false — checking reason...")
    try:
        reason = r.json().get("data", [{}])[0].get("invalidReason", "unknown")
        print(f"  Reason: {reason}")
    except Exception:
        pass

print("\n" + "=" * 64)
print("DONE")
print("=" * 64)
