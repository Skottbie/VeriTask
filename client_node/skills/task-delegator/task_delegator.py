#!/usr/bin/env python3
"""
VeriTask 3.0 — Task Delegator Skill
Orchestrates the full C2C flow:
  1. Construct TaskIntent and send to Worker
  2. Receive ProofBundle from Worker
  3. Verify proofs via verifier Skill
  4. Pay Worker via okx-x402-payer Skill

Usage:
    python task_delegator.py --protocol aave --worker-url http://127.0.0.1:8001
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from eth_account import Account

# Load .env
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

# Add sibling skills to path
CLIENT_SKILLS = Path(__file__).parent.parent
sys.path.insert(0, str(CLIENT_SKILLS / "verifier"))
sys.path.insert(0, str(CLIENT_SKILLS / "okx-x402-payer"))

from verifier import verify_proof_bundle        # noqa: E402
from okx_x402_payer import execute_payment       # noqa: E402


def delegate_task(
    protocol: str,
    worker_url: str,
    amount_usdt: float = 1.0,
    skip_payment: bool = False,
) -> dict:
    """
    Execute full C2C verifiable micro-procurement flow.
    """
    # Derive client wallet address
    pk = os.getenv("CLIENT_PRIVATE_KEY", "")
    client_wallet = "0x0000000000000000000000000000000000000000"
    if pk:
        pk_hex = pk if pk.startswith("0x") else f"0x{pk}"
        client_wallet = Account.from_key(pk_hex).address

    # Step 1: Construct TaskIntent
    task_id = str(uuid.uuid4())
    task_intent = {
        "task_id": task_id,
        "type": "defi_tvl",
        "params": {"protocol": protocol},
        "client_wallet": client_wallet,
    }

    print(f"\033[36m{'='*60}\033[0m")
    print(f"\033[36m[Client] 📋 VeriTask 3.0 — C2C Verifiable Micro-Procurement\033[0m")
    print(f"\033[36m{'='*60}\033[0m")
    print(f"\033[36m[Client] 📤 Delegating task to Worker...\033[0m")
    print(f"    Task ID:  {task_id}")
    print(f"    Protocol: {protocol}")
    print(f"    Worker:   {worker_url}")

    # Step 2: Send to Worker
    try:
        resp = requests.post(
            f"{worker_url}/execute",
            json=task_intent,
            timeout=45,
        )
        resp.raise_for_status()
        proof_bundle = resp.json()
    except requests.RequestException as e:
        print(f"\033[31m[Client] ❌ Worker request failed: {e}\033[0m", file=sys.stderr)
        return {"success": False, "error": str(e)}

    print(f"\033[32m[Client] 📦 Received ProofBundle from Worker\033[0m")
    tvl = proof_bundle.get("data", {}).get("tvl_usd", 0)
    print(f"    TVL: ${tvl:,.2f}")

    # Step 3: Verify proofs
    print(f"\n\033[36m[Client] 🔍 Verifying cryptographic proofs...\033[0m")
    verification = verify_proof_bundle(proof_bundle)

    if not verification["is_valid"]:
        print(f"\033[31m[Client] ❌ Proof verification failed! Payment aborted.\033[0m")
        return {"success": False, "error": "Proof verification failed", "verification": verification}

    # Step 4: Pay Worker (if not skipped)
    payment_result = None
    worker_address = proof_bundle.get("worker_pubkey", "")

    if skip_payment:
        print(f"\n\033[33m[Client] ⏭️  Payment skipped (--skip-payment flag)\033[0m")
    elif not worker_address or worker_address == "0x0000000000000000000000000000000000000000":
        print(f"\n\033[33m[Client] ⚠️  Worker address not set, skipping payment\033[0m")
    else:
        print(f"\n\033[36m[Client] 💰 Initiating x402 payment to Worker...\033[0m")
        try:
            payment_result = execute_payment(worker_address, amount_usdt)
        except Exception as e:
            print(f"\033[31m[Client] ❌ Payment failed: {e}\033[0m", file=sys.stderr)
            payment_result = {"success": False, "error": str(e)}

    # Summary
    print(f"\n\033[36m{'='*60}\033[0m")
    print(f"\033[36m[Client] 📊 Mission Summary\033[0m")
    print(f"\033[36m{'='*60}\033[0m")
    print(f"  Task:        {task_id}")
    print(f"  Protocol:    {protocol}")
    print(f"  TVL:         ${tvl:,.2f}")
    print(f"  ZK Proof:    {'✅' if verification['zk_valid'] else '❌'} {proof_bundle.get('zk_proof', {}).get('type', '?')}")
    print(f"  TEE:         {'✅' if verification['tee_valid'] else '❌'} {proof_bundle.get('tee_attestation', {}).get('type', '?')}")
    if payment_result and payment_result.get("success"):
        print(f"  Payment:     ✅ {payment_result.get('tx_hash', 'N/A')}")
        print(f"  Explorer:    {payment_result.get('explorer_url', 'N/A')}")
    elif skip_payment:
        print(f"  Payment:     ⏭️ Skipped")
    else:
        print(f"  Payment:     ⚠️ Not executed")

    return {
        "success": True,
        "task_id": task_id,
        "data": proof_bundle.get("data"),
        "proof_details": {
            "zk_proof": {
                "type": proof_bundle.get("zk_proof", {}).get("type"),
                "hash": proof_bundle.get("zk_proof", {}).get("hash"),
            },
            "tee_attestation": {
                "type": proof_bundle.get("tee_attestation", {}).get("type"),
                "report_data": proof_bundle.get("tee_attestation", {}).get("report_data"),
                "has_quote": bool(proof_bundle.get("tee_attestation", {}).get("quote")),
            },
            "worker_pubkey": proof_bundle.get("worker_pubkey"),
            "timestamp": proof_bundle.get("timestamp"),
        },
        "verification": verification,
        "payment": payment_result,
    }


def main():
    parser = argparse.ArgumentParser(description="VeriTask C2C Task Delegator")
    parser.add_argument("--protocol", default="aave", help="DeFi protocol slug")
    parser.add_argument("--worker-url", default=os.getenv("WORKER_URL", "http://127.0.0.1:8001"))
    parser.add_argument("--amount", type=float, default=1.0, help="USDT payment amount")
    parser.add_argument("--skip-payment", action="store_true", help="Skip x402 payment step")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    result = delegate_task(
        protocol=args.protocol,
        worker_url=args.worker_url,
        amount_usdt=args.amount,
        skip_payment=args.skip_payment,
    )

    if args.json:
        safe = {k: v for k, v in result.items() if k != "payment" or v is None or isinstance(v, dict)}
        print(json.dumps(safe, indent=2, default=str))


if __name__ == "__main__":
    main()
