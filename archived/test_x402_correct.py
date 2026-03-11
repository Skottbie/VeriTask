#!/usr/bin/env python3
"""
VeriTask — x402 Correct Endpoint Test
Uses the REAL endpoints from OKX developer console:
  /api/v6/x402/supported
  /api/v6/x402/verify
  /api/v6/x402/settle

Step 1: GET /supported — check what chains/tokens are available
Step 2: POST /verify — real EIP-3009 signed 0.01 USDT transfer
(Step 3: settle only if verify succeeds)
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


# ─── Auth helper ────────────────────────────────────────
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


def send(label, method, path, body_dict=None):
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=True) if body_dict else ""
    url = f"{BASE_URL}{path}"
    headers = hmac_headers(method, path, body_str)

    if method.upper() == "GET":
        r = requests.get(url, headers=headers, timeout=15)
    else:
        r = requests.post(url, headers=headers, data=body_str, timeout=15)

    is_html = r.text.strip().startswith("<!")
    if is_html:
        display = "HTML page (likely 404)"
    else:
        try:
            j = r.json()
            display = json.dumps(j, ensure_ascii=False, indent=2)[:500]
        except Exception:
            display = r.text[:300]

    print(f"\n[{label}] {method} {path}")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {display}")
    return r


# ═══════════════════════════════════════════════════════
print("=" * 64)
print("TEST 1: GET /api/v6/x402/supported (check available chains)")
print("=" * 64)
r1 = send("supported", "GET", "/api/v6/x402/supported")

# ═══════════════════════════════════════════════════════
print("\n" + "=" * 64)
print("TEST 2: POST /api/v6/x402/verify (real 0.01 USDT signature)")
print("=" * 64)

# Build real EIP-3009 TransferWithAuthorization signature
account = Account.from_key(CLIENT_PRIVATE_KEY)
from_address = account.address
nonce = os.urandom(32)
nonce_hex = "0x" + nonce.hex()
valid_after = 0
valid_before = int(time.time()) + 3600

domain_data = {
    "name": "Tether USD",
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

print(f"  From: {from_address}")
print(f"  To:   {WORKER_WALLET}")
print(f"  Amount: 0.01 USDT ({AMOUNT_WEI})")
print(f"  Sig: {signature[:42]}...")

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

r2 = send("verify", "POST", "/api/v6/x402/verify", verify_body)

# ═══════════════════════════════════════════════════════
# Only attempt settle if verify returned 200
if r2.status_code == 200:
    print("\n" + "=" * 64)
    print("TEST 3: POST /api/v6/x402/settle (complete payment)")
    print("=" * 64)

    settle_body = dict(verify_body)  # same structure for now
    r3 = send("settle", "POST", "/api/v6/x402/settle", settle_body)
else:
    print(f"\n⚠ Skipping settle — verify returned {r2.status_code}")

print("\n" + "=" * 64)
print("DONE")
print("=" * 64)
