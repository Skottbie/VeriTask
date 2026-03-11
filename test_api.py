#!/usr/bin/env python3
import hmac
import hashlib
import base64
import time
import json
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('OKX_API_KEY')
SECRET = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')

BASE_URL = "https://web3.okx.com"

def get_timestamp():
    # 更可靠的方式：用 time.time() 转 ISO + 毫秒
    now = time.time()
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    ms = int((now - int(now)) * 1000)
    ts = dt.strftime('%Y-%m-%dT%H:%M:%S.') + f"{ms:03d}Z"
    return ts

def generate_signature(method: str, path: str, body: str = ""):
    ts = get_timestamp()
    prehash = ts + method.upper() + path + body
    print(f"Debug prehash: {prehash}")  # 加这个看拼接对不对
    digest = hmac.new(SECRET.encode('utf-8'), prehash.encode('utf-8'), hashlib.sha256).digest()
    sig = base64.b64encode(digest).decode('utf-8')
    return ts, sig

def signed_request(method: str, endpoint: str, params=None, json_body=None):
    query = ''
    if params:
        query = '?' + '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
    full_path = endpoint + query

    body_str = json.dumps(json_body, separators=(',', ':'), sort_keys=True) if json_body else ''

    ts, sig = generate_signature(method, full_path, body_str)

    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sig,
        'OK-ACCESS-TIMESTAMP': ts,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json',
    }

    print(f"Debug headers - TS: {ts}")
    print(f"Debug sign: {sig[:20]}...")

    url = BASE_URL + full_path
    if method.upper() == 'GET':
        r = requests.get(url, headers=headers, timeout=15)
    elif method.upper() == 'POST':
        r = requests.post(url, headers=headers, json=json_body, timeout=15)
    return r

print("=== OKX x402 测试 - 修复 timestamp 版 ===")

# Test 1: 你手动成功的端点
print("\nTest 1: gas-price (必须通，否则 Key/timestamp 有问题)")
r_gas = signed_request('GET', '/api/v6/dex/pre-transaction/gas-price', params={'chainIndex': '196'})
print(f"Status: {r_gas.status_code}")
if r_gas.status_code == 200:
    print("→ Key + 签名 OK！gas-price 成功，和你手动一样。")
    print("Data sample:", r_gas.json().get('data', [{}])[0])
else:
    print("Body:", r_gas.text)
    print("→ 如果还是 50112，检查：1. 系统时间同步（NTP） 2. .env Key 是否最新 3. 电脑时区/UTC")

# Test 2: 试 payments/verify (POST) 测试 x402 auth
print("\nTest 2: x402 verify endpoint (测试是否支持 payments)")
minimal_body = {
    "x402Version": 1,
    "paymentPayload": {
        "x402Version": 1,
        "scheme": "exact",
        "chainIndex": "196",
        "payload": {}  # 最小结构，只测 auth
    }
}
r_verify = signed_request('POST', '/api/v6/payments/verify', json_body=minimal_body)
print(f"Status: {r_verify.status_code}")
print("Body:", r_verify.text[:400])
if r_verify.status_code in (200, 400, 402):
    print("→ 你的 Key 支持 x402！（405/400 是 payload 问题，auth 已通过）")
else:
    print("→ 如果 401/50112 → timestamp/Key 问题；如果 404 → 这个端点可能需真 payment 先")

print("\n下一步：")
print("1. 如果 Test 1 通了 → 你的 API 可以跑 x402（payments 部分用在 DEX pay-per-use 中）。")
print("2. 如果还 50112 → 手动 curl 用脚本生成的 ts/sig 测试（复制 prehash/sign 去 curl）。")
print("3. 同步时间：Windows → 设置 → 时间 → 自动设置时间；或命令 `w32tm /resync`")
print("4. x402 实际用：调用 DEX API → 收 402 → 用 OKX SDK 付 → verify/settle → 重试。")