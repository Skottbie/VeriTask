#!/usr/bin/env python3
"""
VeriTask 3.4.6 — swap_and_broadcast.py
Complete swap execution: approve → swap → sign locally → broadcast via onchainos.

Usage:
    python swap_and_broadcast.py \
        --from-token 0x74b7f16337b8972027f6196a17a631ac6de26d22 \
        --to-token   0x779ded0c9e1022225f8e0630b35a9b54be713736 \
        --amount 10000 \
        --chain xlayer

Requires:
    - CLIENT_PRIVATE_KEY in .env
    - onchainos CLI in PATH
    - eth_account, requests, python-dotenv packages

OKX onchainos workflow:
    1. onchainos swap approve  → get approve calldata
    2. Sign approve tx locally → broadcast via gateway
    3. onchainos swap swap     → get swap tx data
    4. Sign swap tx locally    → broadcast via gateway
    5. Return txHash

Reference:
    https://github.com/okx/onchainos-skills
    "Swap and Broadcast: okx-dex-swap (get tx data) → sign locally → okx-onchain-gateway (broadcast)"
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from eth_account import Account
from eth_utils import to_checksum_address

# ─── Configuration ──────────────────────────────────────────────────────

# Load .env from project root (VeriTask/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# X Layer chain config
CHAIN_CONFIG = {
    "xlayer": {"chain_id": 196, "rpc": "https://rpc.xlayer.tech"},
    "ethereum": {"chain_id": 1, "rpc": "https://eth.llamarpc.com"},
    "base": {"chain_id": 8453, "rpc": "https://mainnet.base.org"},
}

# onchainos binary path
ONCHAINOS_BIN = os.environ.get(
    "ONCHAINOS_BIN",
    os.path.expanduser("~/.local/bin/onchainos"),
)

# ─── Helpers ────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    """Color-coded log output."""
    print(f"\033[36m[Swap] {msg}\033[0m", file=sys.stderr)


def _err(msg: str) -> None:
    """Color-coded error output."""
    print(f"\033[31m[Swap] ❌ {msg}\033[0m", file=sys.stderr)


def _run_onchainos(args: list[str]) -> dict:
    """Run an onchainos CLI command and return parsed JSON."""
    cmd = [ONCHAINOS_BIN] + args
    _log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        _err(f"onchainos failed (exit {result.returncode}): {result.stderr.strip()}")
        return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        _err(f"Cannot parse onchainos output: {result.stdout[:500]}")
        return {"ok": False, "error": f"Invalid JSON: {result.stdout[:200]}"}


def _get_nonce(rpc_url: str, address: str) -> int:
    """Get the current nonce for an address via JSON-RPC."""
    resp = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [address, "latest"],
            "id": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return int(data["result"], 16)


def _sign_tx(tx_dict: dict, private_key: str) -> str:
    """Sign a transaction dict and return the raw signed tx hex.
    Auto-checksums address fields (to/from) per EIP-55 requirement.
    """
    # eth_account requires EIP-55 checksummed addresses
    for addr_key in ("to", "from"):
        if addr_key in tx_dict and isinstance(tx_dict[addr_key], str):
            tx_dict[addr_key] = to_checksum_address(tx_dict[addr_key])
    signed = Account.sign_transaction(tx_dict, private_key)
    return "0x" + signed.raw_transaction.hex()


def _broadcast(signed_tx_hex: str, wallet_address: str, chain: str) -> dict:
    """Broadcast a signed transaction via onchainos gateway."""
    return _run_onchainos([
        "gateway", "broadcast",
        "--signed-tx", signed_tx_hex,
        "--address", wallet_address,
        "--chain", chain,
    ])


# ─── Main Flow ──────────────────────────────────────────────────────────


def execute_swap(
    from_token: str,
    to_token: str,
    amount: int,
    chain: str,
    private_key: str,
) -> dict:
    """
    Execute a complete DEX swap: approve → swap → sign → broadcast.
    Returns: dict with success, txHash, etc.
    """
    try:
        return _execute_swap_inner(from_token, to_token, amount, chain, private_key)
    except Exception as e:
        _err(f"Unexpected error: {e}")
        return {"success": False, "error": f"Exception: {type(e).__name__}: {str(e)}"}


def _execute_swap_inner(
    from_token: str,
    to_token: str,
    amount: int,
    chain: str,
    private_key: str,
) -> dict:
    """Inner implementation — may raise exceptions, caught by execute_swap()."""
    chain_cfg = CHAIN_CONFIG.get(chain)
    if not chain_cfg:
        return {"success": False, "error": f"Unsupported chain: {chain}"}

    chain_id = chain_cfg["chain_id"]
    rpc_url = chain_cfg["rpc"]

    # Derive wallet address from private key
    pk_hex = private_key if private_key.startswith("0x") else f"0x{private_key}"
    wallet = Account.from_key(pk_hex).address
    _log(f"Wallet: {wallet}")
    _log(f"Swap: {from_token} → {to_token}, amount={amount}, chain={chain}")

    # ── Step 1: Approve ──────────────────────────────────────────────
    _log("Step 1/4: Getting approve calldata...")
    approve_result = _run_onchainos([
        "swap", "approve",
        "--token", from_token,
        "--amount", str(amount),
        "--chain", chain,
    ])

    if approve_result.get("ok") and approve_result.get("data"):
        approve_data = approve_result["data"]
        if isinstance(approve_data, list):
            approve_data = approve_data[0]

        approve_calldata = approve_data.get("data", "")
        gas_limit = int(approve_data.get("gasLimit", "200000"))
        gas_price = int(approve_data.get("gasPrice", "110000000"))

        if approve_calldata:
            _log("Step 2/4: Signing & broadcasting approve tx...")
            nonce = _get_nonce(rpc_url, wallet)
            _log(f"  Nonce: {nonce}")

            approve_tx = {
                "to": from_token,  # approve tx goes to the TOKEN contract
                "data": bytes.fromhex(
                    approve_calldata[2:]
                    if approve_calldata.startswith("0x")
                    else approve_calldata
                ),
                "value": 0,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": chain_id,
            }

            signed_approve = _sign_tx(approve_tx, pk_hex)
            approve_broadcast = _broadcast(signed_approve, wallet, chain)

            if approve_broadcast.get("ok"):
                approve_tx_hash = ""
                bd = approve_broadcast.get("data", [])
                if isinstance(bd, list) and bd:
                    approve_tx_hash = bd[0].get("txHash", "")
                elif isinstance(bd, dict):
                    approve_tx_hash = bd.get("txHash", "")
                _log(f"  Approve broadcast OK: txHash={approve_tx_hash}")
                # Wait for approve tx to confirm
                time.sleep(3)
            else:
                err_msg = approve_broadcast.get("error", "Unknown broadcast error")
                # Approve failure is non-fatal — may already be approved
                _log(f"  Approve broadcast warning: {err_msg}")
                _log("  Continuing (token may already be approved)...")
        else:
            _log("  No approve calldata needed (native token or already approved)")
    else:
        _log("  Approve step skipped (not required or error)")

    # ── Step 3: Swap ─────────────────────────────────────────────────
    _log("Step 3/4: Getting swap tx data...")
    swap_result = _run_onchainos([
        "swap", "swap",
        "--from", from_token,
        "--to", to_token,
        "--amount", str(amount),
        "--chain", chain,
        "--wallet", wallet,
        "--slippage", "1",
    ])

    if not swap_result.get("ok") or not swap_result.get("data"):
        error = swap_result.get("error", json.dumps(swap_result)[:300])
        _err(f"Swap failed: {error}")
        return {"success": False, "error": f"Swap data failed: {error}"}

    swap_data = swap_result["data"]
    if isinstance(swap_data, list):
        swap_data = swap_data[0]

    tx_obj = swap_data.get("tx", {})
    router_result = swap_data.get("routerResult", {})

    if not tx_obj.get("data"):
        _err("No tx data in swap response")
        return {"success": False, "error": "Missing tx.data in swap response"}

    # ── Step 4: Sign & Broadcast Swap ────────────────────────────────
    _log("Step 4/4: Signing & broadcasting swap tx...")
    nonce = _get_nonce(rpc_url, wallet)
    _log(f"  Nonce: {nonce}")

    swap_calldata = tx_obj["data"]
    swap_tx = {
        "to": tx_obj.get("to", ""),
        "data": bytes.fromhex(
            swap_calldata[2:]
            if swap_calldata.startswith("0x")
            else swap_calldata
        ),
        "value": int(tx_obj.get("value", "0")),
        "gas": int(tx_obj.get("gas", "500000")),
        "gasPrice": int(tx_obj.get("gasPrice", "110000000")),
        "nonce": nonce,
        "chainId": chain_id,
    }

    signed_swap = _sign_tx(swap_tx, pk_hex)
    swap_broadcast = _broadcast(signed_swap, wallet, chain)

    if not swap_broadcast.get("ok"):
        error = swap_broadcast.get("error", "Unknown broadcast error")
        _err(f"Swap broadcast failed: {error}")
        return {"success": False, "error": f"Broadcast failed: {error}"}

    # Extract txHash
    tx_hash = ""
    order_id = ""
    bd = swap_broadcast.get("data", [])
    if isinstance(bd, list) and bd:
        tx_hash = bd[0].get("txHash", "")
        order_id = bd[0].get("orderId", "")
    elif isinstance(bd, dict):
        tx_hash = bd.get("txHash", "")
        order_id = bd.get("orderId", "")

    from_symbol = router_result.get("fromToken", {}).get("tokenSymbol", "?")
    to_symbol = router_result.get("toToken", {}).get("tokenSymbol", "?")
    from_amount = router_result.get("fromTokenAmount", "?")
    to_amount = router_result.get("toTokenAmount", "?")

    _log(f"✅ Swap complete!")
    _log(f"  {from_symbol} ({from_amount}) → {to_symbol} ({to_amount})")
    _log(f"  txHash: {tx_hash}")

    return {
        "success": True,
        "txHash": tx_hash,
        "orderId": order_id,
        "fromToken": from_symbol,
        "toToken": to_symbol,
        "fromAmount": from_amount,
        "toAmount": to_amount,
        "chain": chain,
        "explorer_url": f"https://www.okx.com/web3/explorer/xlayer/tx/{tx_hash}"
        if chain == "xlayer" and tx_hash
        else "",
    }


# ─── CLI Entry Point ────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="VeriTask swap_and_broadcast: approve → swap → sign → broadcast"
    )
    parser.add_argument(
        "--from-token", required=True, help="Source token contract address"
    )
    parser.add_argument(
        "--to-token", required=True, help="Destination token contract address"
    )
    parser.add_argument(
        "--amount", required=True, type=int, help="Amount in minimal units"
    )
    parser.add_argument(
        "--chain", default="xlayer", help="Chain name (default: xlayer)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output only JSON (no logs)"
    )
    args = parser.parse_args()

    # Load private key
    private_key = os.getenv("CLIENT_PRIVATE_KEY", "")
    if not private_key:
        result = {"success": False, "error": "CLIENT_PRIVATE_KEY not set in .env"}
        print(json.dumps(result, indent=2))
        sys.exit(1)

    try:
        result = execute_swap(
            from_token=args.from_token,
            to_token=args.to_token,
            amount=args.amount,
            chain=args.chain,
            private_key=private_key,
        )
    except Exception as e:
        result = {"success": False, "error": f"Fatal: {type(e).__name__}: {str(e)}"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
