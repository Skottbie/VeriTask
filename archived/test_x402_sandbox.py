#!/usr/bin/env python3
"""
VeriTask — Test with Sandbox API Key from AGENTS.md
The sandbox key might have different permissions than the user's key.
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

# Sandbox API keys — set via environment or .env file
SANDBOX_API_KEY = os.getenv("OKX_API_KEY", "<YOUR_OKX_API_KEY>")
SANDBOX_SECRET = os.getenv("OKX_SECRET_KEY", "<YOUR_OKX_SECRET_KEY>")
SANDBOX_PASSPHRASE = os.getenv("OKX_PASSPHRASE", "<YOUR_OKX_PASSPHRASE>")

# User's real API key for comparison
USER_API_KEY = os.getenv("OKX_API_KEY")
USER_SECRET = os.getenv("OKX_SECRET_KEY")
USER_PASSPHRASE = os.getenv("OKX_PASSPHRASE")


def get_timestamp():
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def make_request(label, api_key, secret, passphrase, method, path, body_dict=None):
    ts = get_timestamp()
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=True) if body_dict else ""
    prehash = ts + method.upper() + path + body_str
    sig = base64.b64encode(
        hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    headers = {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "OK-ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json",
    }
    url = f"https://web3.okx.com{path}"
    if method.upper() == "GET":
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
    else:
        r = requests.post(url, headers=headers, data=body_str, timeout=15, allow_redirects=False)

    is_html = r.text.strip().startswith("<!")
    body = "HTML 404" if is_html else r.text[:200]
    try:
        j = r.json()
        body = f"code={j.get('code')} msg={j.get('msg')}"
        if j.get('data'):
            body += f" data={json.dumps(j['data'], ensure_ascii=False)[:100]}"
    except Exception:
        pass
    print(f"  [{label}] {method} {path} → {r.status_code} | {body}")
    return r


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
        "description": "test",
        "mimeType": "application/json",
        "payTo": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
        "asset": "0x779ded0c9e1022225f8e0630b35a9b54be713736",
        "extra": {},
    },
}

print("=" * 64)
print("Comparing Sandbox Key vs User Key")
print("=" * 64)
print()

# Control: gas-price with both keys
print("--- Control: gas-price ---")
make_request("sandbox", SANDBOX_API_KEY, SANDBOX_SECRET, SANDBOX_PASSPHRASE,
             "GET", "/api/v6/dex/pre-transaction/gas-price?chainIndex=196")
make_request("user   ", USER_API_KEY, USER_SECRET, USER_PASSPHRASE,
             "GET", "/api/v6/dex/pre-transaction/gas-price?chainIndex=196")
print()

# Test: supported endpoint
print("--- GET /api/v6/payments/supported ---")
make_request("sandbox", SANDBOX_API_KEY, SANDBOX_SECRET, SANDBOX_PASSPHRASE,
             "GET", "/api/v6/payments/supported")
make_request("user   ", USER_API_KEY, USER_SECRET, USER_PASSPHRASE,
             "GET", "/api/v6/payments/supported")
print()

print("--- GET /api/v6/wallet/payments/supported ---")
make_request("sandbox", SANDBOX_API_KEY, SANDBOX_SECRET, SANDBOX_PASSPHRASE,
             "GET", "/api/v6/wallet/payments/supported")
make_request("user   ", USER_API_KEY, USER_SECRET, USER_PASSPHRASE,
             "GET", "/api/v6/wallet/payments/supported")
print()

# Test: verify endpoint
print("--- POST /api/v6/payments/verify ---")
make_request("sandbox", SANDBOX_API_KEY, SANDBOX_SECRET, SANDBOX_PASSPHRASE,
             "POST", "/api/v6/payments/verify", verify_body)
make_request("user   ", USER_API_KEY, USER_SECRET, USER_PASSPHRASE,
             "POST", "/api/v6/payments/verify", verify_body)
print()

print("--- POST /api/v6/wallet/payments/verify ---")
make_request("sandbox", SANDBOX_API_KEY, SANDBOX_SECRET, SANDBOX_PASSPHRASE,
             "POST", "/api/v6/wallet/payments/verify", verify_body)
make_request("user   ", USER_API_KEY, USER_SECRET, USER_PASSPHRASE,
             "POST", "/api/v6/wallet/payments/verify", verify_body)
print()

print("=" * 64)
print("DONE — Check if sandbox key gets a different result")
print("=" * 64)
