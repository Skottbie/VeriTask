#!/usr/bin/env python3
"""
VeriTask — x402 Final Diagnostic
1. Check 405 response headers (especially Allow header)
2. Test standard x402.org facilitator
3. Test with different request body formats (x402 v1 vs v2)
4. Try GET for verify/settle endpoints
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


def get_timestamp():
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def okx_headers(method, path, body_str=""):
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


# === TEST 1: Check 405 response headers ===
print("=" * 64)
print("TEST 1: POST /api/v6/payments/verify — check response headers")
print("=" * 64)
path = "/api/v6/payments/verify"
body = {"x402Version": 1, "paymentPayload": {}, "paymentRequirements": {}}
body_str = json.dumps(body, separators=(",", ":"), sort_keys=True)
headers = okx_headers("POST", path, body_str)
r = requests.post(f"https://web3.okx.com{path}", headers=headers, data=body_str, timeout=15,
                   allow_redirects=False)
print(f"  Status: {r.status_code}")
print(f"  ALL Response Headers:")
for k, v in r.headers.items():
    print(f"    {k}: {v}")
print(f"  Body: {r.text[:300]}")
print()

# === TEST 2: Test standard x402.org facilitator ===
print("=" * 64)
print("TEST 2: Standard x402.org facilitator — GET /supported")
print("=" * 64)
try:
    r2 = requests.get("https://x402.org/facilitator/supported", timeout=15)
    print(f"  Status: {r2.status_code}")
    print(f"  Body: {r2.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# === TEST 3: Test with GET for verify ===
print("=" * 64)
print("TEST 3: GET /api/v6/payments/verify (wrong method test)")
print("=" * 64)
path3 = "/api/v6/payments/verify"
headers3 = okx_headers("GET", path3)
r3 = requests.get(f"https://web3.okx.com{path3}", headers=headers3, timeout=15, allow_redirects=False)
print(f"  Status: {r3.status_code}")
is_html = r3.text.strip().startswith('<!')
print(f"  Body type: {'HTML' if is_html else 'Text/JSON'}")
if not is_html:
    print(f"  Body: {r3.text[:300]}")
print()

# === TEST 4: Test with OK-ACCESS-PROJECT header ===
print("=" * 64)
print("TEST 4: POST /api/v6/payments/verify with OK-ACCESS-PROJECT header")
print("=" * 64)
path4 = "/api/v6/payments/verify"
body4 = json.dumps(body, separators=(",", ":"), sort_keys=True)
headers4 = okx_headers("POST", path4, body4)
headers4["OK-ACCESS-PROJECT"] = ""  # Empty but present
r4 = requests.post(f"https://web3.okx.com{path4}", headers=headers4, data=body4, timeout=15,
                    allow_redirects=False)
print(f"  Status: {r4.status_code}")
print(f"  Body: {r4.text[:300]}")
print()

# === TEST 5: Try with json= instead of data= (different Content-Type behavior) ===
print("=" * 64)
print("TEST 5: POST /api/v6/payments/verify using requests json= param")
print("=" * 64)
path5 = "/api/v6/payments/verify"
# When using json=, requests auto-sets Content-Type and serializes
# But we need to sign the body as the requests library will serialize it
body5_dict = {
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
body5_str = json.dumps(body5_dict)  # standard json.dumps (with spaces)
headers5 = okx_headers("POST", path5, body5_str)
r5 = requests.post(f"https://web3.okx.com{path5}", headers=headers5, data=body5_str, timeout=15,
                    allow_redirects=False)
print(f"  Status: {r5.status_code}")
print(f"  Body: {r5.text[:300]}")
print()

# === TEST 6: Try BOTH wallet/payments paths ===
print("=" * 64)
print("TEST 6: POST /api/v6/wallet/payments/verify — check response headers")
print("=" * 64)
path6 = "/api/v6/wallet/payments/verify"
body6_str = json.dumps(body5_dict, separators=(",", ":"), sort_keys=True)
headers6 = okx_headers("POST", path6, body6_str)
r6 = requests.post(f"https://web3.okx.com{path6}", headers=headers6, data=body6_str, timeout=15,
                    allow_redirects=False)
print(f"  Status: {r6.status_code}")
print(f"  ALL Response Headers:")
for k, v in r6.headers.items():
    print(f"    {k}: {v}")
print(f"  Body: {r6.text[:300]}")
print()

# === TEST 7: Try x402 standard HEADER-based authentication ===
print("=" * 64)
print("TEST 7: POST /api/v6/payments/verify with Authorization: Bearer")
print("=" * 64)
path7 = "/api/v6/payments/verify"
body7_str = json.dumps(body5_dict)
headers7 = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}
r7 = requests.post(f"https://web3.okx.com{path7}", headers=headers7, data=body7_str, timeout=15,
                    allow_redirects=False)
print(f"  Status: {r7.status_code}")
print(f"  Body: {r7.text[:300]}")
print()

print("=" * 64)
print("DONE")
print("=" * 64)
