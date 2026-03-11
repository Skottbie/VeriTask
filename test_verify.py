#!/usr/bin/env python3
"""Test x402 verify endpoint with real EIP-712 signed payload."""
import os, json, time, hmac, hashlib, base64, requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from eth_account import Account

load_dotenv()

API_KEY = os.getenv('OKX_API_KEY')
SECRET = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')
PK = os.getenv('CLIENT_PRIVATE_KEY')
BASE = 'https://web3.okx.com'

pk = PK if PK.startswith('0x') else f'0x{PK}'
from_addr = Account.from_key(pk).address
to_addr = '0x608e7c9307dB7F70668d48B892AB3D7e748231C3'
value_wei = 10000  # 0.01 USDT (6 decimals)
token_contract = '0x779ded0c9e1022225f8e0630b35a9b54be713736'
chain_id = 196
chain_index = '196'
nonce = os.urandom(32)

print(f'From: {from_addr}')

# EIP-712 sign
domain = {
    'name': 'Tether USD', 'version': '1',
    'chainId': chain_id, 'verifyingContract': token_contract,
}
types = {
    'TransferWithAuthorization': [
        {'name': 'from', 'type': 'address'},
        {'name': 'to', 'type': 'address'},
        {'name': 'value', 'type': 'uint256'},
        {'name': 'validAfter', 'type': 'uint256'},
        {'name': 'validBefore', 'type': 'uint256'},
        {'name': 'nonce', 'type': 'bytes32'},
    ]
}
msg = {
    'from': from_addr, 'to': to_addr, 'value': value_wei,
    'validAfter': 0, 'validBefore': int(time.time()) + 3600,
    'nonce': nonce,
}
signed = Account.sign_typed_data(pk, domain, types, msg)
sig = '0x' + signed.signature.hex()
nonce_hex = '0x' + nonce.hex()

print(f'Sig: {sig[:24]}...')

# Build x402 body
body_dict = {
    'x402Version': 1,
    'paymentPayload': {
        'x402Version': 1,
        'scheme': 'exact',
        'chainIndex': chain_index,
        'payload': {
            'signature': sig,
            'authorization': {
                'from': from_addr,
                'to': to_addr,
                'value': str(value_wei),
                'validAfter': str(msg['validAfter']),
                'validBefore': str(msg['validBefore']),
                'nonce': nonce_hex,
            }
        }
    },
    'paymentRequirements': {
        'scheme': 'exact',
        'chainIndex': chain_index,
        'maxAmountRequired': str(value_wei),
        'resource': 'https://veritask.xyz/api/v1/tasks',
        'description': 'VeriTask test',
        'mimeType': 'application/json',
        'payTo': to_addr,
        'asset': token_contract,
        'maxTimeoutSeconds': 30,
    }
}

body_str = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)

# HMAC sign
path = '/api/v6/payments/verify'
now = time.time()
dt = datetime.fromtimestamp(now, tz=timezone.utc)
ms = int((now - int(now)) * 1000)
ts = dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{ms:03d}Z'
prehash = ts + 'POST' + path + body_str
sig_hmac = base64.b64encode(
    hmac.new(SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
).decode()

headers = {
    'OK-ACCESS-KEY': API_KEY,
    'OK-ACCESS-SIGN': sig_hmac,
    'OK-ACCESS-TIMESTAMP': ts,
    'OK-ACCESS-PASSPHRASE': PASSPHRASE,
    'Content-Type': 'application/json',
}

print(f'TS: {ts}')
print(f'Path: {path}')
print(f'Body length: {len(body_str)}')
print(f'Body preview: {body_str[:150]}...')
print()

r = requests.post(BASE + path, headers=headers, data=body_str, timeout=15)
print(f'Status: {r.status_code}')
# Show relevant headers
for k, v in r.headers.items():
    if k.lower().startswith(('x-', 'ok-', 'retry')):
        print(f'  Header {k}: {v}')
print(f'Body: {r.text[:600]}')
