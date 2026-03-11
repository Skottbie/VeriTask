#!/usr/bin/env python3
"""
VeriTask — x402 URL Path Diagnostic
Tests both /api/v6/payments/* and /api/v6/wallet/payments/* to find correct endpoints.

OKX docs inconsistency:
  - Introduction page says: /api/v6/wallet/payments/{supported,verify,settle}
  - Individual API refs say: /api/v6/payments/{supported,verify,settle}
  This script tests BOTH to determine which is live.
"""

import hmac
import hashlib
import base64
import time
import json
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OKX_API_KEY")
SECRET = os.getenv("OKX_SECRET_KEY")
PASSPHRASE = os.getenv("OKX_PASSPHRASE")
BASE_URL = "https://web3.okx.com"

print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
print()


def get_timestamp():
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def signed_request(method, path, body_dict=None):
    ts = get_timestamp()
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=True) if body_dict else ""
    prehash = ts + method.upper() + path + body_str
    sig = base64.b64encode(
        hmac.new(SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "OK-ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json",
    }
    url = BASE_URL + path
    if method.upper() == "GET":
        r = requests.get(url, headers=headers, timeout=15)
    else:
        r = requests.post(url, headers=headers, data=body_str, timeout=15)
    return r


def show(name, r):
    is_html = r.text.strip().startswith("<!")
    if is_html:
        print(f"  {name}: {r.status_code} → HTML 404 page")
    elif r.status_code == 405:
        print(f"  {name}: 405 Method Not Allowed")
    else:
        try:
            data = r.json()
            code = data.get("code", "?")
            msg = data.get("msg", "?")
            print(f"  {name}: HTTP {r.status_code} | code={code} | msg={msg}")
            if data.get("data"):
                snippet = json.dumps(data["data"], ensure_ascii=False)[:200]
                print(f"    data: {snippet}")
        except Exception:
            print(f"  {name}: {r.status_code} | body: {r.text[:200]}")
    print()


# ============================================================
# Control test
# ============================================================
print("=" * 64)
print("CONTROL: GET /api/v6/dex/pre-transaction/gas-price?chainIndex=196")
print("=" * 64)
r0 = signed_request("GET", "/api/v6/dex/pre-transaction/gas-price?chainIndex=196")
show("gas-price", r0)

# ============================================================
# Test SUPPORTED endpoint — all URL variants
# ============================================================
supported_paths = [
    "/api/v6/payments/supported",
    "/api/v6/payments/supported/",
    "/api/v6/wallet/payments/supported",
    "/api/v6/wallet/payments/supported/",
]
print("=" * 64)
print("SUPPORTED ENDPOINT — Testing all URL variants (GET)")
print("=" * 64)
for path in supported_paths:
    r = signed_request("GET", path)
    show(f"GET {path}", r)

# ============================================================
# Test VERIFY endpoint — all URL variants
# ============================================================
verify_body = {
    "x402Version": 1,
    "chainIndex": "196",
    "paymentPayload": {
        "x402Version": 1,
        "scheme": "exact",
        "chainIndex": "196",
        "payload": {
            "signature": "0x" + "ab" * 32,
            "authorization": {
                "from": "0x012e6cfbbd1fcf5751d08ec2919d1c7873a4bb85",
                "to": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
                "value": "10000",
                "validAfter": "0",
                "validBefore": "9999999999",
                "nonce": "0x" + "cd" * 20,
            },
        },
    },
    "paymentRequirements": {
        "scheme": "exact",
        "chainIndex": "196",
        "maxAmountRequired": "10000",
        "resource": "https://veritask.xyz/api/v1/tasks",
        "description": "VeriTask test",
        "mimeType": "application/json",
        "payTo": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
        "asset": "0x779ded0c9e1022225f8e0630b35a9b54be713736",
        "extra": {},
    },
}

verify_paths = [
    "/api/v6/payments/verify",
    "/api/v6/wallet/payments/verify",
]
print("=" * 64)
print("VERIFY ENDPOINT — Testing URL variants (POST)")
print("=" * 64)
for path in verify_paths:
    r = signed_request("POST", path, verify_body)
    show(f"POST {path}", r)

# ============================================================
# Summary
# ============================================================
print("=" * 64)
print("CONCLUSION: If /api/v6/wallet/payments/* returns code=0 or a")
print("recognizable error (not 404/405), that is the correct path.")
print("=" * 64)
