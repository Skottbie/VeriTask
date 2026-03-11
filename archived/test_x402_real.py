#!/usr/bin/env python3
"""
VeriTask — REAL x402 Payment Test (0.01 USDT)
Strictly follows OKX official documentation.

- Uses REAL EIP-3009 TransferWithAuthorization signature from CLIENT_PRIVATE_KEY
- Tests ALL auth combinations (Bearer, HMAC) for both verify and settle
- Tests with and without top-level chainIndex
- Amount: 0.01 USDT = 10000 (6 decimals) on X Layer
"""

import hmac
import hashlib
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from eth_account import Account

load_dotenv()

# ─── Configuration ──────────────────────────────────────────
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

# ─── Step 1: Build & Sign real EIP-712 TransferWithAuthorization ───
print("=" * 64)
print("STEP 1: Build Real EIP-3009 Signature")
print("=" * 64)

account = Account.from_key(CLIENT_PRIVATE_KEY)
from_address = account.address
print(f"  From: {from_address}")
print(f"  To:   {WORKER_WALLET}")
print(f"  Amount: 0.01 USDT ({AMOUNT_WEI} smallest unit)")

# Random nonce (32 bytes)
nonce = os.urandom(32)
nonce_hex = "0x" + nonce.hex()

# Time bounds
valid_after = 0
valid_before = int(time.time()) + 3600  # 1 hour from now

# EIP-712 domain for USDT on X Layer
domain_data = {
    "name": "Tether USD",
    "version": "1",
    "chainId": CHAIN_ID,
    "verifyingContract": USDT_CONTRACT,
}

# EIP-712 types
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

# Message data
message = {
    "from": from_address,
    "to": WORKER_WALLET,
    "value": AMOUNT_WEI,
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce,
}

# Sign with eth_account
signed = Account.sign_typed_data(CLIENT_PRIVATE_KEY, domain_data, types, message)
signature = "0x" + signed.signature.hex()

print(f"  Signature: {signature[:42]}...")
print(f"  Nonce: {nonce_hex[:24]}...")
print(f"  validBefore: {valid_before}")
print()

# ─── Step 2: Build request bodies ──────────────────────────
print("=" * 64)
print("STEP 2: Build Request Bodies (2 variants)")
print("=" * 64)

# Variant A: With top-level chainIndex (per schema table)
body_with_chain = {
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
        "extra": {
            "gasLimit": "1000000"
        },
    },
}

# Variant B: Without top-level chainIndex (per curl example in docs)
body_no_chain = dict(body_with_chain)
del body_no_chain["chainIndex"]

print(f"  Variant A: With top-level chainIndex")
print(f"  Variant B: Without top-level chainIndex")
print()


# ─── Utility: HMAC auth headers ─────────────────────────
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


def send_request(label, method, path, body_dict=None, auth_type="hmac"):
    """Send request with given auth and return (status, body_text)."""
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=True) if body_dict else ""
    url = f"{BASE_URL}{path}"

    if auth_type == "hmac":
        headers = hmac_headers(method, path, body_str)
    elif auth_type == "bearer_apikey":
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    elif auth_type == "bearer_secret":
        headers = {
            "Authorization": f"Bearer {SECRET}",
            "Content-Type": "application/json",
        }
    else:
        headers = {"Content-Type": "application/json"}

    try:
        if method.upper() == "GET":
            r = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
        else:
            r = requests.post(url, headers=headers, data=body_str, timeout=15, allow_redirects=False)

        # Parse response
        is_html = r.text.strip().startswith("<!")
        if is_html:
            display = "HTML (404 page)"
        else:
            try:
                j = r.json()
                display = f"code={j.get('code')} msg={j.get('msg')}"
                if j.get("data"):
                    display += f" | data={json.dumps(j['data'], ensure_ascii=False)[:120]}"
            except Exception:
                display = r.text[:200]

        print(f"  [{label}] {r.status_code} | {display}")
        return r.status_code, r.text
    except Exception as e:
        print(f"  [{label}] ERROR: {e}")
        return 0, str(e)


# ─── Step 3: Test ALL combinations ─────────────────────
print("=" * 64)
print("STEP 3: Test verify endpoint (all auth + body combos)")
print("=" * 64)

verify_path = "/api/v6/payments/verify"

# Test 1: HMAC + body with chainIndex
print("\n--- Test 1: HMAC auth + body with top-level chainIndex ---")
send_request("HMAC+chain", "POST", verify_path, body_with_chain, "hmac")

# Test 2: HMAC + body without chainIndex
print("\n--- Test 2: HMAC auth + body without top-level chainIndex ---")
send_request("HMAC-chain", "POST", verify_path, body_no_chain, "hmac")

# Test 3: Bearer <API_KEY> (per verify doc example)
print("\n--- Test 3: Bearer API_KEY + body with chainIndex ---")
send_request("Bearer-key", "POST", verify_path, body_with_chain, "bearer_apikey")

# Test 4: Bearer <SECRET> 
print("\n--- Test 4: Bearer SECRET + body with chainIndex ---")
send_request("Bearer-sec", "POST", verify_path, body_with_chain, "bearer_secret")

# Test 5: No auth at all
print("\n--- Test 5: No auth + body with chainIndex ---")
send_request("NoAuth", "POST", verify_path, body_with_chain, "none")

print()
print("=" * 64)
print("STEP 4: Test settle endpoint (HMAC auth per settle doc)")
print("=" * 64)

settle_path = "/api/v6/payments/settle"

# Test 6: HMAC + body with chainIndex
print("\n--- Test 6: HMAC auth + body with chainIndex (settle) ---")
send_request("HMAC+chain", "POST", settle_path, body_with_chain, "hmac")

# Test 7: HMAC + body without chainIndex
print("\n--- Test 7: HMAC auth + body without chainIndex (settle) ---")
send_request("HMAC-chain", "POST", settle_path, body_no_chain, "hmac")

print()
print("=" * 64)
print("STEP 5: Test supported endpoint")
print("=" * 64)

supported_path = "/api/v6/payments/supported"

# GET with HMAC
print("\n--- Test 8: GET supported with HMAC ---")
send_request("HMAC-GET", "GET", supported_path, auth_type="hmac")

# POST with HMAC (some APIs return data on POST even if docs say GET)
print("\n--- Test 9: POST supported with HMAC ---")
send_request("HMAC-POST", "POST", supported_path, auth_type="hmac")

# GET with no auth
print("\n--- Test 10: GET supported no auth ---")
send_request("NoAuth-GET", "GET", supported_path, auth_type="none")

print()
print("=" * 64)
print("STEP 6: Test alternative URL path /api/v6/wallet/payments/*")
print("=" * 64)

alt_verify = "/api/v6/wallet/payments/verify"
alt_settle = "/api/v6/wallet/payments/settle"
alt_supported = "/api/v6/wallet/payments/supported"

print("\n--- Test 11: POST wallet/verify HMAC ---")
send_request("wallet-verify", "POST", alt_verify, body_with_chain, "hmac")

print("\n--- Test 12: POST wallet/settle HMAC ---")
send_request("wallet-settle", "POST", alt_settle, body_with_chain, "hmac")

print("\n--- Test 13: GET wallet/supported HMAC ---")
send_request("wallet-supp", "GET", alt_supported, auth_type="hmac")

print()
print("=" * 64)
print("SUMMARY")
print("=" * 64)
print(f"  Real signature used: YES (from {from_address})")
print(f"  Amount: 0.01 USDT ({AMOUNT_WEI})")
print(f"  To: {WORKER_WALLET}")
print(f"  If all tests return 405/404, the endpoint is NOT DEPLOYED.")
print("=" * 64)
