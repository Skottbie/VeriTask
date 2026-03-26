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
import time
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
sys.path.insert(0, str(CLIENT_SKILLS / "graph-anchor"))
sys.path.insert(0, str(CLIENT_SKILLS / "bidding-agent"))

from verifier import verify_proof_bundle        # noqa: E402
from okx_x402_payer import execute_payment       # noqa: E402
from graph_anchor import anchor_proof, anchor_dispute  # noqa: E402
from bidding_agent import rank_workers, load_registry  # noqa: E402


def is_retryable_worker_error(exc: requests.RequestException) -> bool:
    """Retry only transient transport or 5xx Worker failures."""
    if isinstance(exc, (requests.ConnectionError, requests.Timeout, requests.exceptions.SSLError)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code >= 500
    return False


def delegate_task(
    protocol: str,
    worker_url: str,
    amount_usdt: float = 1.0,
    skip_payment: bool = False,
    skip_anchor: bool = False,
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
    proof_bundle = None
    last_error = None
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.post(
                f"{worker_url}/execute",
                json=task_intent,
                timeout=45,
            )
            resp.raise_for_status()
            proof_bundle = resp.json()
            break
        except requests.RequestException as e:
            last_error = e
            if attempt >= max_attempts or not is_retryable_worker_error(e):
                print(f"\033[31m[Client] ❌ Worker request failed: {e}\033[0m", file=sys.stderr)
                return {"success": False, "error": str(e)}

            print(
                f"\033[33m[Client] ⚠️  Worker request attempt {attempt} failed, retrying: {e}\033[0m",
                file=sys.stderr,
            )
            time.sleep(attempt)

    if proof_bundle is None:
        print(f"\033[31m[Client] ❌ Worker request failed: {last_error}\033[0m", file=sys.stderr)
        return {"success": False, "error": str(last_error)}

    print(f"\033[32m[Client] 📦 Received ProofBundle from Worker\033[0m")
    tvl = proof_bundle.get("data", {}).get("tvl_usd", 0)
    print(f"    TVL: ${tvl:,.2f}")

    # Step 3: Verify proofs
    print(f"\n\033[36m[Client] 🔍 Verifying cryptographic proofs...\033[0m")
    verification = verify_proof_bundle(proof_bundle)

    if not verification["is_valid"]:
        print(f"\033[31m[Client] ❌ Proof verification failed! Payment aborted.\033[0m")

        # Anchor a dispute edge for cryptographically verifiable failures
        dispute_result = None
        worker_address = proof_bundle.get("worker_pubkey", "")
        if worker_address and not skip_anchor:
            # Determine dispute_reason from verification details
            zk_ok = verification.get("zk_valid", False)
            tee_ok = verification.get("tee_valid", False)
            if not zk_ok and not tee_ok:
                dispute_reason = "full_proof_failure"
            elif not zk_ok:
                dispute_reason = "zk_proof_invalid"
            else:
                dispute_reason = "tee_attestation_invalid"

            print(f"\033[33m[Client] ⚠️  Anchoring dispute edge (reason: {dispute_reason})...\033[0m")
            try:
                dispute_result = anchor_dispute(worker_address, dispute_reason)
            except Exception as e:
                print(f"\033[33m[Client] ⚠️  Dispute anchor failed (non-blocking): {e}\033[0m",
                      file=sys.stderr)
                dispute_result = {"status": "failed", "error": str(e)}

        return {
            "success": False,
            "error": "Proof verification failed",
            "verification": verification,
            "dispute": dispute_result,
        }

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

    # Step 3.5: Anchor reputation edge on X Layer (Graph Anchor)
    anchor_result = None
    if skip_anchor:
        print(f"\n\033[33m[Client] ⏭️  Graph Anchor skipped (--skip-anchor flag)\033[0m")
    elif not verification["is_valid"]:
        pass  # never anchor a failed verification
    elif skip_payment:
        print(f"\n\033[33m[Client] ⏭️  Graph Anchor skipped (no payment = no reputation edge)\033[0m")
    else:
        print(f"\n\033[36m[Client] ⚓ Anchoring reputation edge to X Layer...\033[0m")
        try:
            anchor_bundle = {**proof_bundle, "amount_usdt": str(amount_usdt)}
            anchor_result = anchor_proof(anchor_bundle)
        except Exception as e:
            print(f"\033[33m[Client] ⚠️  Graph Anchor failed (non-blocking): {e}\033[0m", file=sys.stderr)
            anchor_result = {"status": "failed", "error": str(e)}

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

    if anchor_result and anchor_result.get("status") == "anchored":
        print(f"  Anchor:      ✅ {anchor_result.get('tx_hash', 'N/A')}")
    elif anchor_result and anchor_result.get("dry_run"):
        print(f"  Anchor:      🔍 Dry-run (calldata built)")
    elif skip_anchor or skip_payment:
        print(f"  Anchor:      ⏭️ Skipped")
    else:
        print(f"  Anchor:      ⚠️ Not executed")

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
        "anchor": anchor_result,
    }


def main():
    parser = argparse.ArgumentParser(description="VeriTask C2C Task Delegator")
    parser.add_argument("--protocol", default="aave", help="DeFi protocol slug")
    parser.add_argument("--worker-url", default="")
    parser.add_argument("--registry", default="", help="Path to worker_registry.json for auto-selection")
    parser.add_argument("--amount", type=float, default=1.0, help="USDT payment amount")
    parser.add_argument("--skip-payment", action="store_true", help="Skip x402 payment step")
    parser.add_argument("--skip-anchor", action="store_true", help="Skip Graph Anchor step")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    worker_url = args.worker_url

    # Auto-select worker via Bidding Agent if --registry is provided
    if args.registry and not worker_url:
        registry_data = load_registry(args.registry)
        if not registry_data:
            print("\033[31m[Client] ❌ No workers in registry\033[0m", file=sys.stderr)
            sys.exit(1)
        addresses = [w["address"] for w in registry_data if w.get("address")]
        url_map = {w["address"].lower(): w.get("url", "") for w in registry_data}
        print(f"\033[36m[Client] 🏆 Running Bidding Agent on {len(addresses)} candidates...\033[0m")
        ranked = rank_workers(addresses)
        if ranked:
            winner = ranked[0]["worker"]
            worker_url = url_map.get(winner.lower(), "")
            print(f"\033[32m[Client] ✅ Best Worker: {winner} (score={ranked[0]['final_score']:.6f})\033[0m")
        else:
            print("\033[31m[Client] ❌ Bidding Agent returned no results\033[0m", file=sys.stderr)
            sys.exit(1)

    if not worker_url:
        worker_url = os.getenv("WORKER_URL", "http://127.0.0.1:8001")

    result = delegate_task(
        protocol=args.protocol,
        worker_url=worker_url,
        amount_usdt=args.amount,
        skip_payment=args.skip_payment,
        skip_anchor=args.skip_anchor,
    )

    if args.json:
        safe = {k: v for k, v in result.items() if k != "payment" or v is None or isinstance(v, dict)}
        print(json.dumps(safe, indent=2, default=str))


if __name__ == "__main__":
    main()
