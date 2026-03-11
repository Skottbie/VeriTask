#!/usr/bin/env python3
"""
VeriTask 3.0 — OKX API Authentication Utility
Generates HMAC-SHA256 headers required by OKX x402 Payment REST API.

Headers generated:
    OK-ACCESS-KEY        — API key
    OK-ACCESS-SIGN       — HMAC-SHA256 signature (base64)
    OK-ACCESS-TIMESTAMP  — ISO 8601 UTC timestamp with milliseconds
    OK-ACCESS-PASSPHRASE — API passphrase

Signature formula (official OKX docs):
    prehash = timestamp + METHOD + requestPath + body
    sign = base64( hmac_sha256(secret_key, prehash) )

Ref: https://www.okx.com/docs-v5/en/#overview-api-key-creation-api-key-security
"""

import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone


def build_okx_headers(
    api_key: str,
    secret_key: str,
    passphrase: str,
    method: str,
    request_path: str,
    body: str = "",
) -> dict:
    """
    Build OKX API authentication headers.

    Args:
        api_key: OKX API key
        secret_key: OKX API secret key
        passphrase: OKX API passphrase
        method: HTTP method (GET, POST)
        request_path: Full API path including query string
                      e.g., "/api/v6/x402/verify" or "/api/v6/dex/...?chainIndex=196"
        body: Request body string (empty "" for GET, JSON string for POST)

    Returns:
        dict with all required OKX auth headers
    """
    # Use time.time() for reliable millisecond precision (matching proven test_api.py)
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S.') + f"{ms:03d}Z"

    # prehash = timestamp + METHOD + requestPath + body
    # - GET: body is always ""
    # - POST: body is the raw JSON string (not URL-encoded, not minified)
    prehash = timestamp + method.upper() + request_path + body

    signature = base64.b64encode(
        hmac.new(
            secret_key.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }
