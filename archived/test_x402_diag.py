#!/usr/bin/env python3
"""
VeriTask — x402 Deep Diagnostic
Tests redirect behavior, auth methods, and URL variants systematically.
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


def raw_request(method, path, body_dict=None, follow_redirects=True, use_auth=True):
    """Make request with explicit redirect control."""
    ts = get_timestamp()
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=True) if body_dict else ""
    
    headers = {"Content-Type": "application/json"}
    
    if use_auth:
        prehash = ts + method.upper() + path + body_str
        sig = base64.b64encode(
            hmac.new(SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
        ).decode()
        headers.update({
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": sig,
            "OK-ACCESS-PASSPHRASE": PASSPHRASE,
            "OK-ACCESS-TIMESTAMP": ts,
        })
    
    url = BASE_URL + path
    if method.upper() == "GET":
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=follow_redirects)
    else:
        r = requests.post(url, headers=headers, data=body_str, timeout=15, allow_redirects=follow_redirects)
    return r


def diagnose(label, r):
    print(f"  [{label}]")
    print(f"    Status: {r.status_code}")
    print(f"    URL: {r.url}")
    
    # Check redirect history
    if r.history:
        print(f"    Redirect chain ({len(r.history)} hops):")
        for h in r.history:
            loc = h.headers.get("Location", "?")
            print(f"      {h.status_code} → {loc}")
    
    # Check Location header (for non-followed redirects)
    if "Location" in r.headers:
        print(f"    Location: {r.headers['Location']}")
    
    is_html = r.text.strip().startswith("<!")
    if is_html:
        print(f"    Body: HTML page (404/error)")
    else:
        try:
            data = r.json()
            print(f"    JSON: code={data.get('code')} msg={data.get('msg')}")
            if data.get("data"):
                print(f"    Data: {json.dumps(data['data'], ensure_ascii=False)[:200]}")
        except Exception:
            print(f"    Body: {r.text[:200]}")
    print()


# Minimal verify body
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

# ============================================================
print("=" * 64)
print("PART 1: Control test")
print("=" * 64)
r = raw_request("GET", "/api/v6/dex/pre-transaction/gas-price?chainIndex=196")
diagnose("gas-price (control)", r)

# ============================================================
print("=" * 64)
print("PART 2: SUPPORTED — no-redirect test (check for 3xx)")
print("=" * 64)
for path in ["/api/v6/payments/supported", "/api/v6/payments/supported/",
             "/api/v6/wallet/payments/supported", "/api/v6/wallet/payments/supported/"]:
    r = raw_request("GET", path, follow_redirects=False)
    diagnose(f"GET {path} (no-redirect)", r)

# ============================================================
print("=" * 64)
print("PART 3: VERIFY — no-redirect test (check for 3xx)")
print("=" * 64)
for path in ["/api/v6/payments/verify", "/api/v6/wallet/payments/verify"]:
    r = raw_request("POST", path, verify_body, follow_redirects=False)
    diagnose(f"POST {path} (no-redirect)", r)

# ============================================================
print("=" * 64)
print("PART 4: VERIFY — WITH redirect (default behavior)")
print("=" * 64)
for path in ["/api/v6/payments/verify", "/api/v6/wallet/payments/verify"]:
    r = raw_request("POST", path, verify_body, follow_redirects=True)
    diagnose(f"POST {path} (follow-redirect)", r)

# ============================================================
print("=" * 64)
print("PART 5: SUPPORTED — try without auth (public endpoint?)")
print("=" * 64)
for path in ["/api/v6/payments/supported", "/api/v6/wallet/payments/supported"]:
    r = raw_request("GET", path, use_auth=False)
    diagnose(f"GET {path} (no-auth)", r)

# ============================================================
print("=" * 64)
print("PART 6: Try POST for supported (maybe docs wrong about method?)")
print("=" * 64)
for path in ["/api/v6/payments/supported", "/api/v6/wallet/payments/supported"]:
    r = raw_request("POST", path, {}, follow_redirects=False)
    diagnose(f"POST {path} (no-redirect)", r)

print("=" * 64)
print("DONE — analyze redirect chains and status codes above")
print("=" * 64)
