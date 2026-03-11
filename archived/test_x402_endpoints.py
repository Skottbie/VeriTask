#!/usr/bin/env python3
"""Test all OKX x402 Payment API endpoints with proper auth."""
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

API_KEY = os.getenv('OKX_API_KEY')
SECRET = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')
BASE_URL = "https://web3.okx.com"

print(f"API_KEY: {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"PASSPHRASE: {PASSPHRASE[:4]}...{PASSPHRASE[-2:]}")
print()


def get_timestamp():
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    ts = dt.strftime('%Y-%m-%dT%H:%M:%S.') + f"{ms:03d}Z"
    return ts


def signed_request(method, path, body_dict=None):
    """Make a signed request to OKX API."""
    ts = get_timestamp()
    body_str = json.dumps(body_dict) if body_dict else ""
    prehash = ts + method.upper() + path + body_str
    sig = base64.b64encode(
        hmac.new(SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sig,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'OK-ACCESS-TIMESTAMP': ts,
        'Content-Type': 'application/json',
    }
    url = BASE_URL + path
    if method.upper() == 'GET':
        r = requests.get(url, headers=headers, timeout=15)
    else:
        r = requests.post(url, headers=headers, data=body_str, timeout=15)
    return r


def show_result(name, r):
    print(f"  Status: {r.status_code}")
    is_html = r.text.strip().startswith('<!')
    if is_html:
        print(f"  → HTML 404 page (endpoint not found)")
    elif r.status_code == 405:
        print(f"  → 405 Method Not Allowed")
        print(f"  → Headers: {dict((k,v) for k,v in r.headers.items() if 'ratelimit' in k.lower())}")
    else:
        try:
            data = r.json()
            print(f"  → Code: {data.get('code')} | Msg: {data.get('msg')}")
            if data.get('data'):
                print(f"  → Data: {json.dumps(data['data'], indent=2)[:300]}")
        except:
            print(f"  → Body: {r.text[:300]}")
    print()


# === Control test: should return 200 ===
print("=" * 60)
print("TEST 0: Control - gas-price (must return 200)")
print("=" * 60)
r0 = signed_request('GET', '/api/v6/dex/pre-transaction/gas-price?chainIndex=196')
show_result("gas-price", r0)

# === Test 1: GET /api/v6/payments/supported ===
print("=" * 60)
print("TEST 1: GET /api/v6/payments/supported")
print("=" * 60)
r1 = signed_request('GET', '/api/v6/payments/supported')
show_result("supported", r1)

# === Test 2: POST /api/v6/payments/verify ===
print("=" * 60)
print("TEST 2: POST /api/v6/payments/verify")
print("=" * 60)
body = {
    "x402Version": 1,
    "paymentPayload": {
        "x402Version": 1,
        "scheme": "exact",
        "chainIndex": "196",
        "payload": {
            "signature": "0xf3746613c2d920b5fdabc0856f2aeb2d4f88ee6037b8cc5d04a71a4462f13480",
            "authorization": {
                "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "value": "1000000",
                "validAfter": "0",
                "validBefore": "9999999999",
                "nonce": "0x1234567890abcdef1234567890abcdef12345678"
            }
        }
    },
    "paymentRequirements": {
        "scheme": "exact",
        "chainIndex": "196",
        "maxAmountRequired": "1000000",
        "resource": "https://veritask.example.com/api/data",
        "description": "VeriTask DeFi data verification",
        "mimeType": "application/json",
        "payTo": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "asset": "0x779ded0c9e1022225f8e0630b35a9b54be713736",
        "extra": {}
    }
}
r2 = signed_request('POST', '/api/v6/payments/verify', body)
show_result("verify", r2)

# === Test 3: POST /api/v6/payments/settle ===
print("=" * 60)
print("TEST 3: POST /api/v6/payments/settle")
print("=" * 60)
r3 = signed_request('POST', '/api/v6/payments/settle', body)
show_result("settle", r3)

# === Test 4: Try with chainIndex in top level ===
print("=" * 60)
print("TEST 4: POST /api/v6/payments/verify (chainIndex at top)")
print("=" * 60)
body2 = dict(body)
body2["chainIndex"] = "196"
r4 = signed_request('POST', '/api/v6/payments/verify', body2)
show_result("verify-v2", r4)

# === Summary ===
print("=" * 60)
print("SUMMARY")
print("=" * 60)
results = {
    "gas-price (control)": r0.status_code,
    "GET supported": r1.status_code,
    "POST verify": r2.status_code,
    "POST settle": r3.status_code,
    "POST verify-v2": r4.status_code,
}
for name, code in results.items():
    status = "✓" if code == 200 else "✗"
    print(f"  {status} {name}: {code}")
