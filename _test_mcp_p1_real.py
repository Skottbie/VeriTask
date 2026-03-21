#!/usr/bin/env python3
"""VeriTask MCP P1 Full Real Crypto Layer Acceptance Test.
Runs the full MCP pipeline: request_task → poll_status → get_result → verify → settle.
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Ensure we import from the client_node package
CLIENT_NODE_DIR = Path(__file__).resolve().parent / "client_node"
sys.path.insert(0, str(CLIENT_NODE_DIR))

# Import MCP server module to access its internal functions
sys.path.insert(0, str(CLIENT_NODE_DIR / "skills" / "task-delegator"))
sys.path.insert(0, str(CLIENT_NODE_DIR / "skills" / "verifier"))
sys.path.insert(0, str(CLIENT_NODE_DIR / "skills" / "okx-x402-payer"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

WORKER_URL = os.getenv("WORKER_URL", "https://2d29518d31fd53641b70a1754c79dce1450188b2-8001.dstack-pha-prod9.phala.network")

import requests
import time
import hashlib

def main():
    print("=" * 70)
    print("VeriTask MCP P1 — Full Real Crypto Layer Acceptance Test")
    print("=" * 70)

    # ──── Step 1: Request Task (via Worker /execute directly) ────
    print("\n[Step 1] Requesting task: aave TVL via Worker CVM...")
    start = time.time()
    resp = requests.post(
        f"{WORKER_URL}/execute",
        json={
            "task_id": f"mcp-p1-real-{int(time.time())}",
            "type": "defi_tvl",
            "params": {"protocol": "aave"},
            "client_wallet": "0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85",
        },
        timeout=120,
    )
    elapsed = time.time() - start
    assert resp.status_code == 200, f"Worker returned {resp.status_code}: {resp.text}"
    result = resp.json()
    print(f"  Worker responded in {elapsed:.1f}s")

    # ──── Step 2: Check ZK Proof Layer ────
    print("\n[Step 2] Checking Layer 1: zkFetch proof...")
    zk = result.get("zk_proof", {})
    zk_type = zk.get("type")
    print(f"  zk_proof.type = {zk_type}")
    print(f"  zk_proof.note = {zk.get('note')}")
    if zk_type == "reclaim_zkfetch":
        proof = zk.get("proof", {})
        print(f"  ✅ REAL zkFetch proof!")
        print(f"    claimData.provider = {proof.get('claimData', {}).get('provider')}")
        print(f"    claimData.owner    = {proof.get('claimData', {}).get('owner')}")
        print(f"    identifier         = {proof.get('identifier', '')[:32]}...")
        print(f"    signatures count   = {len(proof.get('signatures', []))}")
        print(f"    witnesses count    = {len(proof.get('witnesses', []))}")
        if proof.get("witnesses"):
            print(f"    attestor           = {proof['witnesses'][0].get('url')}")
        print(f"    response_body      = {zk.get('response_body', '')[:50]}")
    else:
        print(f"  ❌ MOCK! Still sha256_mock. This test FAILS.")
        sys.exit(1)

    # ──── Step 3: Check TEE Attestation Layer ────
    print("\n[Step 3] Checking Layer 2: TEE attestation...")
    tee = result.get("tee_attestation", {})
    tee_type = tee.get("type")
    print(f"  tee_attestation.type = {tee_type}")
    print(f"  tee_attestation.note = {tee.get('note')}")
    if tee_type == "intel_tdx":
        print(f"  ✅ REAL Intel TDX attestation!")
        print(f"    report_data     = {tee.get('report_data', '')[:32]}...")
        quote_str = str(tee.get("quote", ""))
        print(f"    quote length    = {len(quote_str)} chars")
        print(f"    event_log       = {'present' if tee.get('event_log') else 'absent'}")
    else:
        print(f"  ❌ MOCK! Not in real CVM. This test FAILS.")
        sys.exit(1)

    # ──── Step 4: Verify ProofBundle locally ────
    print("\n[Step 4] Running local verification...")
    from verifier import verify_proof_bundle
    import io
    from contextlib import redirect_stdout, redirect_stderr

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        verify_result = verify_proof_bundle(result)

    print(f"  is_valid   = {verify_result.get('is_valid')}")
    print(f"  zk_valid   = {verify_result.get('zk_valid')}")
    print(f"  tee_valid  = {verify_result.get('tee_valid')}")
    print(f"  reason     = {verify_result.get('reason')}")
    for d in verify_result.get("details", []):
        print(f"    {d}")

    if not verify_result.get("is_valid"):
        print("  ❌ Verification FAILED.")
        sys.exit(1)
    print("  ✅ All verification checks passed!")

    # ──── Step 5: Data summary ────
    print("\n[Step 5] Data summary...")
    data = result.get("data", {})
    tvl = data.get("tvl_usd", 0)
    print(f"  protocol   = {data.get('protocol')}")
    print(f"  TVL (USD)  = ${tvl:,.2f}")
    print(f"  source_url = {data.get('source_url')}")
    print(f"  timestamp  = {result.get('timestamp')}")

    # ──── Step 6: x402 Settlement ────
    print("\n[Step 6] Executing x402 settlement...")
    from okx_x402_payer import execute_payment

    worker_address = result.get("worker_pubkey", "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb")
    amount = 0.01

    buf_out2 = io.StringIO()
    buf_err2 = io.StringIO()
    with redirect_stdout(buf_out2), redirect_stderr(buf_err2):
        payment_result = execute_payment(
            to_address=worker_address,
            amount=amount,
            chain_index="196",
            token_symbol="USDT",
        )

    print(f"  payment success  = {payment_result.get('success')}")
    print(f"  tx_hash          = {payment_result.get('tx_hash')}")
    print(f"  explorer_url     = {payment_result.get('explorer_url')}")
    print(f"  payer            = {payment_result.get('payer')}")
    print(f"  payee            = {payment_result.get('payee')}")

    if not payment_result.get("success"):
        print(f"  ❌ Payment FAILED: {payment_result.get('error')}")
        sys.exit(1)
    print(f"  ✅ Payment settled on-chain!")

    # ──── Final Summary ────
    print("\n" + "=" * 70)
    print("✅ VeriTask MCP P1 Full Real Crypto Layer Test — ALL PASSED")
    print("=" * 70)
    print(f"  Layer 1 (zkFetch):  reclaim_zkfetch  — Reclaim Protocol attestor-signed")
    print(f"  Layer 2 (TEE):      intel_tdx        — Phala Cloud CVM real TDX quote")
    print(f"  Layer 3 (Payment):  OKX x402         — mainnet on-chain USDT settlement")
    print(f"  TVL:                ${tvl:,.2f}")
    print(f"  tx_hash:            {payment_result.get('tx_hash')}")
    print(f"  explorer:           {payment_result.get('explorer_url')}")
    print("=" * 70)

    # Save full result as JSON for documentation
    acceptance = {
        "test_name": "MCP_P1_Full_Real_Crypto_Layer",
        "timestamp": result.get("timestamp"),
        "protocol": data.get("protocol"),
        "tvl_usd": tvl,
        "zk_proof_type": zk_type,
        "zk_proof_attestor": zk.get("proof", {}).get("witnesses", [{}])[0].get("url") if zk.get("proof") else None,
        "zk_proof_identifier": zk.get("proof", {}).get("identifier"),
        "tee_type": tee_type,
        "tee_quote_length": len(str(tee.get("quote", ""))),
        "verification_passed": verify_result.get("verification_passed"),
        "payment_tx_hash": payment_result.get("tx_hash"),
        "payment_explorer_url": payment_result.get("explorer_url"),
        "payer": payment_result.get("payer"),
        "payee": payment_result.get("payee"),
    }
    with open("_acceptance_p1_real_crypto.json", "w") as f:
        json.dump(acceptance, f, indent=2)
    print(f"\nAcceptance JSON saved to _acceptance_p1_real_crypto.json")


if __name__ == "__main__":
    main()
