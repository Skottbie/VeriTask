#!/usr/bin/env python3
"""
VeriTask 3.5 — Graph Anchor Agent
Writes a reputation edge to X Layer after a successful C2C task.

Flow:
  1. Receive ProofBundle (from verifier output or stdin)
  2. Encode reputation edge as calldata (JSON + VeriTask prefix)
  3. Build an EIP-1559 self-transfer tx with calldata
  4. Sign with CLIENT_PRIVATE_KEY
  5. Broadcast via `onchainos gateway broadcast`

Calldata format (7 fields, Best Practice):
  VT2:{json}
  where json = {v, worker, client, proof_hash, tee_fingerprint, task_type, amount_usdt, ts}
  For dispute edges: {v, edge_type, worker, client, dispute_reason, task_type, amount_usdt, ts}

Usage:
    python graph_anchor.py --bundle <proof_bundle.json>
    echo '<proof_bundle_json>' | python graph_anchor.py --stdin
    python graph_anchor.py --bundle <proof_bundle.json> --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

# ── bootstrap ──────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

XLAYER_RPC = os.getenv("XLAYER_RPC_URL", "https://xlayerrpc.okx.com")
CHAIN_ID = 196  # X Layer mainnet
ONCHAINOS_BIN = os.getenv("ONCHAINOS_BIN", "onchainos")
VT_REGISTRY = os.getenv("VT_REGISTRY_ADDRESS", "")

# Calldata prefix — used by Bidding Agent to filter VeriTask edges
CALLDATA_PREFIX = "VT2:"

# VTRegistry ABI: anchor(address,bytes) = keccak256("anchor(address,bytes)")[:4]
ANCHOR_SELECTOR = bytes.fromhex("37a7742b")


# ── calldata encoding ──────────────────────────────────────────────────────

def build_calldata(proof_bundle: dict, client_address: str) -> bytes:
    """
    Encode a reputation edge as calldata bytes.

    Format: VT2:<json>
    JSON fields: v, worker, client, proof_hash, tee_fingerprint,
                 task_type, amount_usdt, ts

    proof_quality encoding in tee_fingerprint:
      - Real TDX quote present → tee_fingerprint = first 16 hex chars of quote hash
      - Mock attestation       → tee_fingerprint = "mock"
    """
    # Support both root-level fields and task_delegator's proof_details nesting
    proof_details = proof_bundle.get("proof_details", {})
    data = proof_bundle.get("data", {})
    zk_proof = proof_bundle.get("zk_proof", proof_details.get("zk_proof", {}))
    tee_attestation = proof_bundle.get("tee_attestation", proof_details.get("tee_attestation", {}))
    worker_pubkey = (
        proof_bundle.get("worker_pubkey")
        or proof_bundle.get("worker_address")
        or proof_details.get("worker_pubkey")
        or proof_details.get("worker_address")
        or ""
    )

    proof_hash = zk_proof.get("hash", "")

    # Derive tee_fingerprint: prefer real TDX quote hash, else use report_data hash, else "mock"
    import hashlib
    tdx_quote = tee_attestation.get("quote", tee_attestation.get("tdx_quote", ""))
    if tdx_quote and tdx_quote != "mock_tdx_quote":
        tee_fingerprint = hashlib.sha256(tdx_quote.encode()).hexdigest()[:16]
    elif tee_attestation.get("has_quote") and tee_attestation.get("report_data"):
        # Real TDX ran but quote bytes not serialized; use report_data as fingerprint
        tee_fingerprint = hashlib.sha256(tee_attestation["report_data"].encode()).hexdigest()[:16]
    else:
        tee_fingerprint = "mock"

    edge = {
        "v": "2",
        "worker": worker_pubkey,
        "client": client_address.lower(),
        "proof_hash": proof_hash,
        "tee_fingerprint": tee_fingerprint,
        "task_type": data.get("task_type", "defi_tvl"),
        "amount_usdt": str(proof_bundle.get("amount_usdt", "0")),
        "ts": int(proof_bundle.get("ts") or proof_details.get("ts") or int(time.time())),
    }
    payload = CALLDATA_PREFIX + json.dumps(edge, separators=(",", ":"))
    return payload.encode("utf-8")


def build_dispute_calldata(worker_address: str, client_address: str,
                           dispute_reason: str, task_type: str = "defi_tvl") -> bytes:
    """
    Encode a negative reputation edge (dispute) as calldata bytes.

    Format: VT2:<json>
    Fields: v, edge_type, worker, client, proof_hash, tee_fingerprint,
            task_type, amount_usdt, dispute_reason, ts
    """
    edge = {
        "v": "3",
        "edge_type": "dispute",
        "worker": worker_address,
        "client": client_address.lower(),
        "proof_hash": "",
        "tee_fingerprint": "",
        "task_type": task_type,
        "amount_usdt": "0",
        "dispute_reason": dispute_reason,
        "ts": int(time.time()),
    }
    payload = CALLDATA_PREFIX + json.dumps(edge, separators=(",", ":"))
    return payload.encode("utf-8")


# ── RPC helpers ────────────────────────────────────────────────────────────

def get_nonce(w3: Web3, address: str) -> int:
    return w3.eth.get_transaction_count(Web3.to_checksum_address(address))


def get_gas_price(w3: Web3) -> dict:
    """Return EIP-1559 fee params for X Layer."""
    latest = w3.eth.get_block("latest")
    base_fee = latest.get("baseFeePerGas", 0)
    # X Layer tip: 1 gwei minimum
    max_priority = w3.to_wei(1, "gwei")
    max_fee = base_fee * 2 + max_priority
    return {"maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority}


# ── transaction builder ────────────────────────────────────────────────────

def encode_anchor_call(worker_address: str, vt2_data: bytes) -> bytes:
    """ABI-encode a call to VTRegistry.anchor(address worker, bytes data)."""
    worker_bytes = bytes.fromhex(worker_address[2:].lower().zfill(64))
    # ABI: selector(4) + address(32) + offset(32) + length(32) + data(padded)
    offset = 64  # bytes offset to dynamic `data` param
    data_len = len(vt2_data)
    # Pad data to 32-byte boundary
    padded_len = ((data_len + 31) // 32) * 32
    padded_data = vt2_data + b'\x00' * (padded_len - data_len)

    return (
        ANCHOR_SELECTOR
        + worker_bytes
        + offset.to_bytes(32, "big")
        + data_len.to_bytes(32, "big")
        + padded_data
    )


def build_and_sign_tx(private_key: str, calldata: bytes, w3: Web3,
                       worker_address: str = "") -> tuple[str, str]:
    """
    Build and sign a tx. If VT_REGISTRY is set, calls VTRegistry.anchor().
    Otherwise falls back to self-transfer with raw calldata.

    Returns:
        (raw_hex, sender_address)
    """
    account = Account.from_key(private_key)
    sender = account.address

    if VT_REGISTRY and worker_address:
        # Route through VTRegistry contract
        to_addr = Web3.to_checksum_address(VT_REGISTRY)
        tx_data = encode_anchor_call(worker_address, calldata)
    else:
        # Legacy: self-transfer with calldata
        to_addr = sender
        tx_data = calldata

    nonce = get_nonce(w3, sender)
    fees = get_gas_price(w3)

    gas_estimate = w3.eth.estimate_gas({
        "from": sender,
        "to": to_addr,
        "data": tx_data,
        "value": 0,
    })
    gas_limit = int(gas_estimate * 1.2)

    tx = {
        "type": 2,
        "chainId": CHAIN_ID,
        "nonce": nonce,
        "to": to_addr,
        "value": 0,
        "gas": gas_limit,
        "maxFeePerGas": fees["maxFeePerGas"],
        "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
        "data": tx_data,
    }
    signed = account.sign_transaction(tx)
    return signed.raw_transaction.hex(), sender


# ── broadcast via onchainos ────────────────────────────────────────────────

def broadcast_via_onchainos(raw_hex: str, sender: str) -> dict:
    """
    Call `onchainos gateway broadcast` and return parsed JSON result.
    """
    env = os.environ.copy()
    cmd = [
        ONCHAINOS_BIN,
        "gateway", "broadcast",
        "--signed-tx", raw_hex,
        "--address", sender,
        "--chain", "xlayer",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            f"onchainos broadcast failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return json.loads(result.stdout)


# ── main ───────────────────────────────────────────────────────────────────

def anchor_proof(proof_bundle: dict, dry_run: bool = False,
                 client_override: str = "") -> dict:
    """
    Full Graph Anchor flow.

    Returns a result dict with tx_hash (or dry_run calldata preview).
    """
    private_key = os.getenv("CLIENT_PRIVATE_KEY", "")
    if not private_key:
        raise EnvironmentError("CLIENT_PRIVATE_KEY not set in .env")

    client_address = client_override if client_override else Account.from_key(private_key).address
    calldata = build_calldata(proof_bundle, client_address)
    calldata_hex = "0x" + calldata.hex()
    proof_details = proof_bundle.get("proof_details", {})
    worker_address = (
        proof_bundle.get("worker_pubkey")
        or proof_bundle.get("worker_address")
        or proof_details.get("worker_pubkey")
        or proof_details.get("worker_address")
        or ""
    )

    print(f"[Graph-Anchor] Client:      {client_address}")
    print(f"[Graph-Anchor] Worker:      {worker_address}")
    print(f"[Graph-Anchor] Calldata:    {calldata_hex[:80]}...")
    print(f"[Graph-Anchor] Calldata sz: {len(calldata)} bytes")
    if VT_REGISTRY:
        print(f"[Graph-Anchor] VTRegistry:  {VT_REGISTRY}")

    if dry_run:
        print("[Graph-Anchor] --dry-run: skipping broadcast")
        return {"dry_run": True, "calldata_hex": calldata_hex}

    w3 = Web3(Web3.HTTPProvider(XLAYER_RPC))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to X Layer RPC: {XLAYER_RPC}")

    raw_hex, sender = build_and_sign_tx(private_key, calldata, w3, worker_address)
    print(f"[Graph-Anchor] Signed tx:   {raw_hex[:20]}...")

    result = broadcast_via_onchainos(raw_hex, sender)

    # onchainos gateway broadcast returns {"ok": true, "data": [{"txHash": ..., "orderId": ...}]}
    tx_hash = ""
    order_id = ""
    data = result.get("data", [])
    if isinstance(data, list) and data:
        tx_hash = data[0].get("txHash", "")
        order_id = data[0].get("orderId", "")
    elif isinstance(data, dict):
        tx_hash = data.get("txHash", "")
        order_id = data.get("orderId", "")
    print(f"[Graph-Anchor] ✅ Anchored  txHash={tx_hash}  orderId={order_id}")

    return {
        "status": "anchored",
        "tx_hash": tx_hash,
        "order_id": order_id,
        "calldata_hex": calldata_hex,
    }


def anchor_dispute(worker_address: str, dispute_reason: str,
                   task_type: str = "defi_tvl", dry_run: bool = False,
                   client_override: str = "") -> dict:
    """
    Anchor a negative reputation edge (dispute) to X Layer.

    Called when Veri Agent detects a cryptographically verifiable failure
    (zk_proof_invalid, tee_attestation_invalid, full_proof_failure).
    """
    private_key = os.getenv("CLIENT_PRIVATE_KEY", "")
    if not private_key:
        raise EnvironmentError("CLIENT_PRIVATE_KEY not set in .env")

    client_address = client_override if client_override else Account.from_key(private_key).address
    calldata = build_dispute_calldata(worker_address, client_address, dispute_reason, task_type)
    calldata_hex = "0x" + calldata.hex()

    print(f"[Graph-Anchor] ⚠️  DISPUTE edge")
    print(f"[Graph-Anchor] Client:      {client_address}")
    print(f"[Graph-Anchor] Worker:      {worker_address}")
    print(f"[Graph-Anchor] Reason:      {dispute_reason}")
    print(f"[Graph-Anchor] Calldata:    {calldata_hex[:80]}...")
    if VT_REGISTRY:
        print(f"[Graph-Anchor] VTRegistry:  {VT_REGISTRY}")

    if dry_run:
        print("[Graph-Anchor] --dry-run: skipping broadcast")
        return {"dry_run": True, "edge_type": "dispute", "calldata_hex": calldata_hex}

    w3 = Web3(Web3.HTTPProvider(XLAYER_RPC))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to X Layer RPC: {XLAYER_RPC}")

    raw_hex, sender = build_and_sign_tx(private_key, calldata, w3, worker_address)
    print(f"[Graph-Anchor] Signed tx:   {raw_hex[:20]}...")

    result = broadcast_via_onchainos(raw_hex, sender)

    tx_hash = ""
    order_id = ""
    data = result.get("data", [])
    if isinstance(data, list) and data:
        tx_hash = data[0].get("txHash", "")
        order_id = data[0].get("orderId", "")
    elif isinstance(data, dict):
        tx_hash = data.get("txHash", "")
        order_id = data.get("orderId", "")
    print(f"[Graph-Anchor] ⚠️  Dispute anchored  txHash={tx_hash}  orderId={order_id}")

    return {
        "status": "dispute_anchored",
        "edge_type": "dispute",
        "dispute_reason": dispute_reason,
        "tx_hash": tx_hash,
        "order_id": order_id,
        "calldata_hex": calldata_hex,
    }


def main():
    parser = argparse.ArgumentParser(description="VeriTask Graph Anchor Agent")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--bundle", help="Path to ProofBundle JSON file")
    src.add_argument("--stdin", action="store_true", help="Read ProofBundle JSON from stdin")
    parser.add_argument("--dry-run", action="store_true", help="Build calldata but skip broadcast")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--client-override", default="",
                        help="Override client address in VT2 calldata (demo mode only)")
    args = parser.parse_args()

    if args.stdin:
        raw = sys.stdin.buffer.read().decode("utf-8-sig")
        proof_bundle = json.loads(raw)
    else:
        with open(args.bundle, "r", encoding="utf-8-sig") as f:
            proof_bundle = json.load(f)

    result = anchor_proof(proof_bundle, dry_run=args.dry_run,
                          client_override=args.client_override)

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
