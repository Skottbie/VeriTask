#!/usr/bin/env python3
"""
VeriTask 3.0 — OKX x402 Payer Skill
Executes real on-chain stablecoin payment on X Layer via OKX's x402 REST API.

Flow:
  1. Construct EIP-712 TransferWithAuthorization struct
  2. Sign with eth_account.sign_typed_data()
  3. POST /api/v6/x402/verify → assert isValid
  4. POST /api/v6/x402/settle → get txHash

Usage:
    python okx_x402_payer.py --to <worker_wallet> --amount <usdt_amount>

OKX x402 API: https://web3.okx.com/zh-hans/onchainos/dev-docs/payments/x402-api-reference
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from eth_account import Account

# Add sibling skill to path
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))
from okx_auth import build_okx_headers  # noqa: E402

# Load .env from monorepo root
load_dotenv(SKILL_DIR.parent.parent.parent / ".env")

# ─── Constants ────────────────────────────────────────────────────────

OKX_BASE_URL = "https://web3.okx.com"
VERIFY_PATH = "/api/v6/x402/verify"
SETTLE_PATH = "/api/v6/x402/settle"
SUPPORTED_PATH = "/api/v6/x402/supported"

# X Layer chain IDs (OKX x402 only supports mainnet as of 2026-03)
CHAIN_INDEX_MAINNET = "196"

# Token configurations for X Layer mainnet
# Each token needs its own EIP-712 domain for TransferWithAuthorization (EIP-3009)
TOKEN_CONFIG = {
    "USDT": {
        "contract": "0x779ded0c9e1022225f8e0630b35a9b54be713736",
        "domain_name": "USD\u20ae0",  # On-chain name() returns 'USD₮0', NOT 'Tether USD'
        "domain_version": "1",
        "decimals": 6,
    },
    "USDC": {
        "contract": "0x74b7f16337b8972027f6196a17a631ac6de26d22",
        "domain_name": "USD Coin",
        "domain_version": "2",
        "decimals": 6,
    },
    "USDG": {
        "contract": "0x4ae46a509f6b1d9056937ba4500cb143933d2dc8",
        "domain_name": "USDG",
        "domain_version": "1",
        "decimals": 6,
    },
}

# EIP-712 types for TransferWithAuthorization (EIP-3009)
TRANSFER_WITH_AUTHORIZATION_TYPES = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ],
}


def get_okx_credentials() -> tuple:
    """Load OKX API credentials from environment."""
    api_key = os.getenv("OKX_API_KEY", "")
    secret_key = os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_PASSPHRASE", "")
    if not all([api_key, secret_key, passphrase]):
        raise RuntimeError(
            "Missing OKX credentials. Set OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE in .env"
        )
    return api_key, secret_key, passphrase


def get_supported_tokens() -> dict:
    """
    GET /api/v6/x402/supported
    Query OKX x402 supported schemes and networks.
    Official docs: No request parameters.
    """
    api_key, secret_key, passphrase = get_okx_credentials()
    path = SUPPORTED_PATH
    headers = build_okx_headers(api_key, secret_key, passphrase, "GET", path)

    resp = requests.get(
        f"{OKX_BASE_URL}{path}",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def build_eip712_payload(
    from_address: str,
    to_address: str,
    value_wei: int,
    token_contract: str,
    chain_id: int,
    token_symbol: str = "USDT",
) -> tuple[dict, dict, dict]:
    """
    Construct EIP-712 domain, types, and message for TransferWithAuthorization.

    Args:
        token_symbol: "USDT", "USDC", or "USDG" — determines domain params

    Returns: (domain_data, message_types, message_data)
    """
    config = TOKEN_CONFIG.get(token_symbol, TOKEN_CONFIG["USDT"])

    # Nonce: random 32-byte value to prevent replay
    nonce = os.urandom(32)

    domain_data = {
        "name": config["domain_name"],
        "version": config["domain_version"],
        "chainId": chain_id,
        "verifyingContract": token_contract,
    }

    message_data = {
        "from": from_address,
        "to": to_address,
        "value": value_wei,
        "validAfter": 0,
        "validBefore": int(time.time()) + 3600,  # Valid for 1 hour
        "nonce": nonce,
    }

    return domain_data, TRANSFER_WITH_AUTHORIZATION_TYPES, message_data


def sign_transfer_authorization(
    private_key: str,
    from_address: str,
    to_address: str,
    value_wei: int,
    token_contract: str,
    chain_id: int,
    token_symbol: str = "USDT",
) -> dict:
    """
    Sign an EIP-712 TransferWithAuthorization using eth_account.

    Returns: dict with signature components and authorization data
    """
    domain_data, message_types, message_data = build_eip712_payload(
        from_address, to_address, value_wei, token_contract, chain_id, token_symbol
    )

    # Sign using eth_account's EIP-712 support
    signed = Account.sign_typed_data(
        private_key,
        domain_data,
        message_types,
        message_data,
    )

    # Convert nonce bytes to hex string for JSON serialization
    nonce_hex = "0x" + message_data["nonce"].hex()

    return {
        "domain": domain_data,
        "types": message_types,
        # Authorization data in the format expected by OKX x402 API
        # All numeric values as strings per API spec
        "authorization": {
            "from": from_address,
            "to": to_address,
            "value": str(value_wei),
            "validAfter": str(message_data["validAfter"]),
            "validBefore": str(message_data["validBefore"]),
            "nonce": nonce_hex,
        },
        "signature": "0x" + signed.signature.hex(),
        "v": signed.v,
        "r": hex(signed.r),
        "s": hex(signed.s),
    }


def _build_x402_request_body(
    signed_payload: dict,
    chain_index: str,
    token_contract: str,
    resource_description: str = "VeriTask C2C verified data procurement",
) -> dict:
    """
    Build the standard x402 request body expected by OKX's verify and settle endpoints.

    OKX API requires:
    - paymentPayload: {x402Version, scheme, chainIndex, payload: {signature, authorization}}
    - paymentRequirements: {scheme, chainIndex, maxAmountRequired, payTo, asset, ...}

    Ref: https://web3.okx.com/zh-hans/onchainos/dev-docs/payments/x402-api-reference
    """
    authorization = signed_payload["authorization"]

    return {
        "x402Version": 1,
        "chainIndex": chain_index,
        "paymentPayload": {
            "x402Version": 1,
            "scheme": "exact",
            "chainIndex": chain_index,
            "payload": {
                "signature": signed_payload["signature"],
                "authorization": authorization,
            },
        },
        "paymentRequirements": {
            "scheme": "exact",
            "chainIndex": chain_index,
            "maxAmountRequired": authorization["value"],
            "resource": f"https://veritask.xyz/api/v1/tasks",
            "description": resource_description,
            "mimeType": "application/json",
            "payTo": authorization["to"],
            "asset": token_contract,
            "maxTimeoutSeconds": 30,
        },
    }


def verify_payment(signed_payload: dict, chain_index: str, token_contract: str) -> dict:
    """
    POST /api/v6/x402/verify — Verify the signed payment is valid.

    Uses standard x402 request body format.
    """
    api_key, secret_key, passphrase = get_okx_credentials()
    request_body = _build_x402_request_body(signed_payload, chain_index, token_contract)
    body = json.dumps(request_body, separators=(',', ':'), sort_keys=True)

    headers = build_okx_headers(api_key, secret_key, passphrase, "POST", VERIFY_PATH, body)

    print(f"\033[36m[Client-x402] 🔍 Verifying payment signature with OKX...\033[0m")
    resp = requests.post(
        f"{OKX_BASE_URL}{VERIFY_PATH}",
        headers=headers,
        data=body,
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"\033[36m[Client-x402] Verify response: {json.dumps(result, indent=2)}\033[0m")

    # Check verification result
    data = result.get("data", [{}])
    if isinstance(data, list) and len(data) > 0:
        is_valid = data[0].get("isValid", False)
        if not is_valid:
            reason = data[0].get("invalidReason", "unknown")
            print(f"\033[31m[Client-x402] ❌ Verification FAILED: {reason}\033[0m")
    elif result.get("code") != "0":
        print(f"\033[31m[Client-x402] ❌ API error: code={result.get('code')}, msg={result.get('msg')}\033[0m")

    return result


def settle_payment(signed_payload: dict, chain_index: str, token_contract: str) -> dict:
    """
    POST /api/v6/x402/settle — Submit on-chain settlement.
    Returns: response with txHash.

    Uses standard x402 request body format.
    """
    api_key, secret_key, passphrase = get_okx_credentials()
    request_body = _build_x402_request_body(signed_payload, chain_index, token_contract)
    body = json.dumps(request_body, separators=(',', ':'), sort_keys=True)

    headers = build_okx_headers(api_key, secret_key, passphrase, "POST", SETTLE_PATH, body)

    print(f"\033[33m[Client-x402] 💸 Settling payment on X Layer (chainIndex={chain_index})...\033[0m")
    resp = requests.post(
        f"{OKX_BASE_URL}{SETTLE_PATH}",
        headers=headers,
        data=body,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"\033[33m[Client-x402] Settle response: {json.dumps(result, indent=2)}\033[0m")
    return result


def execute_payment(
    to_address: str,
    amount: float,
    chain_index: str = None,
    token_symbol: str = None,
) -> dict:
    """
    Full x402 payment flow: sign → verify → settle.

    Args:
        to_address: Worker wallet address (payee)
        amount: Amount in stablecoin (e.g., 0.01)
        chain_index: "196" (mainnet) — OKX x402 only supports mainnet
        token_symbol: "USDT", "USDC", or "USDG"

    Returns: dict with txHash and details
    """
    if chain_index is None:
        chain_index = os.getenv("CHAIN_INDEX", CHAIN_INDEX_MAINNET)

    if token_symbol is None:
        token_symbol = os.getenv("TOKEN_SYMBOL", "USDT")

    # Get token config
    config = TOKEN_CONFIG.get(token_symbol)
    if not config:
        raise RuntimeError(f"Unsupported token: {token_symbol}. Use USDT, USDC, or USDG")

    token_contract = os.getenv("TOKEN_CONTRACT_ADDRESS", config["contract"])
    chain_id = int(chain_index)

    # Load client private key
    private_key_hex = os.getenv("CLIENT_PRIVATE_KEY", "")
    if not private_key_hex or private_key_hex == "your_client_wallet_private_key_hex":
        raise RuntimeError("CLIENT_PRIVATE_KEY not set in .env (need real wallet private key)")

    pk = private_key_hex if private_key_hex.startswith("0x") else f"0x{private_key_hex}"
    from_address = Account.from_key(pk).address

    # Convert amount to smallest unit (6 decimals for stablecoins)
    value_wei = int(amount * 10 ** config["decimals"])

    print(f"\033[36m[Client-x402] 💰 Payment Details:\033[0m")
    print(f"    From:   {from_address}")
    print(f"    To:     {to_address}")
    print(f"    Amount: {amount} {token_symbol} ({value_wei} smallest unit)")
    print(f"    Token:  {token_symbol} ({token_contract})")
    print(f"    Chain:  X Layer mainnet (chainIndex={chain_index})")

    # Step 0: Pre-flight — check supported networks
    print(f"\n\033[36m[Client-x402] 📡 Checking OKX x402 supported networks...\033[0m")
    try:
        supported = get_supported_tokens()
        print(f"\033[32m[Client-x402] ✅ Supported: {json.dumps(supported.get('data', []), indent=2)}\033[0m")
    except Exception as e:
        print(f"\033[33m[Client-x402] ⚠️  Could not check supported networks: {e}\033[0m")

    # Step 1: Sign EIP-712 TransferWithAuthorization
    print(f"\n\033[36m[Client-x402] ✍️  Signing EIP-712 TransferWithAuthorization...\033[0m")
    signed_payload = sign_transfer_authorization(
        pk, from_address, to_address, value_wei, token_contract, chain_id, token_symbol
    )
    print(f"\033[32m[Client-x402] ✅ Signed. sig={signed_payload['signature'][:24]}...\033[0m")

    # Step 2: Verify with OKX
    verify_result = verify_payment(signed_payload, chain_index, token_contract)

    # Check if verification passed
    verify_data = verify_result.get("data", [{}])
    if isinstance(verify_data, list) and len(verify_data) > 0:
        if not verify_data[0].get("isValid", False):
            reason = verify_data[0].get("invalidReason", "unknown")
            return {
                "success": False,
                "error": f"Verification failed: {reason}",
                "verify_result": verify_result,
            }

    # Step 3: Settle on-chain
    settle_result = settle_payment(signed_payload, chain_index, token_contract)

    # Extract txHash from response
    settle_data = settle_result.get("data", [{}])
    if isinstance(settle_data, list) and len(settle_data) > 0:
        tx_hash = settle_data[0].get("txHash", "unknown")
        success = settle_data[0].get("success", False)
    else:
        tx_hash = "unknown"
        success = False

    explorer_url = f"https://www.oklink.com/xlayer/tx/{tx_hash}"

    print(f"\n\033[32m{'='*60}\033[0m")
    print(f"\033[32m[Client-x402] ✅ Payment {'Settled' if success else 'Submitted'}!\033[0m")
    print(f"\033[32m    txHash:   {tx_hash}\033[0m")
    print(f"\033[32m    Explorer: {explorer_url}\033[0m")
    print(f"\033[32m    Gas Fee:  0 (OKX facilitator pays gas on X Layer)\033[0m")
    print(f"\033[32m{'='*60}\033[0m")

    return {
        "success": success,
        "tx_hash": tx_hash,
        "from": from_address,
        "to": to_address,
        "amount": amount,
        "token": token_symbol,
        "chain_index": chain_index,
        "explorer_url": explorer_url,
        "verify_result": verify_result,
        "settle_result": settle_result,
    }


def main():
    parser = argparse.ArgumentParser(description="Pay Worker via OKX x402 on X Layer")
    parser.add_argument("--to", required=True, help="Worker wallet address (payee)")
    parser.add_argument("--amount", type=float, default=0.01, help="Stablecoin amount (default: 0.01)")
    parser.add_argument(
        "--token",
        choices=["USDT", "USDC", "USDG"],
        default=None,
        help="Token to pay with (default: from .env TOKEN_SYMBOL or USDT)",
    )
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check supported networks, don't execute payment",
    )
    args = parser.parse_args()

    # OKX x402 only supports X Layer mainnet (chainIndex=196)
    chain_index = CHAIN_INDEX_MAINNET

    if args.check_only:
        print("\033[36m[Client-x402] 📡 Querying OKX x402 supported networks...\033[0m")
        try:
            result = get_supported_tokens()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"\033[31m[Client-x402] ❌ Error: {e}\033[0m", file=sys.stderr)
            sys.exit(1)
        return

    try:
        result = execute_payment(
            args.to, args.amount, chain_index, args.token
        )
        if args.json:
            # Serialize for JSON output (remove non-serializable parts)
            print(json.dumps(
                {k: v for k, v in result.items() if k not in ("verify_result", "settle_result")},
                indent=2,
            ))
    except RuntimeError as e:
        print(f"\033[31m[Client-x402] ❌ Error: {e}\033[0m", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"\033[31m[Client-x402] ❌ API Error: {e}\033[0m", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"\033[31m    Response: {e.response.text}\033[0m", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
