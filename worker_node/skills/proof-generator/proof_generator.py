#!/usr/bin/env python3
"""
VeriTask 3.0 — Proof Generator Skill
Generates a ProofBundle with two layers of cryptographic proof:
  Layer 1: Reclaim zkFetch (data provenance via zkTLS) or SHA256 fallback
  Layer 2: Phala dstack TEE Attestation (Intel TDX quote) or mock fallback

Usage:
    python proof_generator.py --protocol aave [--json]
"""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent paths so we can import sibling skills
SKILL_DIR = Path(__file__).parent
WORKER_SKILLS_DIR = SKILL_DIR.parent
sys.path.insert(0, str(WORKER_SKILLS_DIR / "defi-scraper"))

from defi_scraper import fetch_tvl  # noqa: E402

# Path to zkfetch bridge script
ZKFETCH_BRIDGE = SKILL_DIR / "zkfetch_bridge.js"


def generate_zk_proof(data_result: dict) -> dict:
    """
    Layer 1: Call zkfetch_bridge.js via subprocess to get zkProof.
    Falls back to SHA256 mock if the bridge fails.
    """
    url = data_result["source_url"]
    data_json = json.dumps(data_result, sort_keys=True)
    data_hash = hashlib.sha256(data_json.encode()).hexdigest()

    stderr_log = ""
    try:
        result = subprocess.run(
            ["node", "--max-old-space-size=4096", str(ZKFETCH_BRIDGE), url],
            capture_output=True,
            text=True,
            timeout=30,  # 30s to fit within proxy timeouts; zkFetch may need more
            cwd=str(SKILL_DIR.parent.parent.parent),  # monorepo root for node_modules
        )
        stderr_log = (result.stderr or "")[-500:]  # last 500 chars of stderr
        if result.returncode != 0:
            raise RuntimeError(f"zkfetch_bridge exited with {result.returncode}: {stderr_log}")

        bridge_output = json.loads(result.stdout)

        return {
            "type": bridge_output.get("type", "sha256_mock"),
            "hash": data_hash,
            "proof": bridge_output.get("proof") if bridge_output.get("type") == "reclaim_zkfetch" else None,
            "response_body": bridge_output.get("response_body"),
            "note": bridge_output.get("note", "zkProof generated successfully"),
            "diag_stderr": stderr_log if stderr_log else None,
        }
    except subprocess.TimeoutExpired as e:
        stderr_log = (e.stderr or "")[-500:] if e.stderr else ""
        stdout_data = (e.stdout or "").strip() if e.stdout else ""
        # Even on timeout, the process may have already written valid output to stdout
        if stdout_data:
            try:
                bridge_output = json.loads(stdout_data)
                if bridge_output.get("type") == "reclaim_zkfetch":
                    print(f"\033[32m[Worker-zkTLS] ✅ zkProof recovered from timed-out subprocess\033[0m", file=sys.stderr)
                    return {
                        "type": bridge_output["type"],
                        "hash": data_hash,
                        "proof": bridge_output.get("proof"),
                        "response_body": bridge_output.get("response_body"),
                        "note": "zkProof OK (process exited slow due to open handles)",
                        "diag_stderr": stderr_log if stderr_log else None,
                    }
            except (json.JSONDecodeError, KeyError):
                pass  # stdout was incomplete or invalid, fall through to sha256_mock
        print(f"\033[33m[Worker-zkTLS] ⚠️  zkFetch timeout (30s). stderr: {stderr_log}\033[0m", file=sys.stderr)
        return {
            "type": "sha256_mock",
            "hash": data_hash,
            "proof": None,
            "response_body": None,
            "note": f"fallback: subprocess timeout 30s",
            "diag_stderr": stderr_log,
        }
    except Exception as e:
        print(f"\033[33m[Worker-zkTLS] ⚠️  zkFetch failed, using SHA256 fallback: {e}\033[0m", file=sys.stderr)
        return {
            "type": "sha256_mock",
            "hash": data_hash,
            "proof": None,
            "note": f"fallback: {e}",
            "diag_stderr": stderr_log,
        }


async def generate_tee_attestation(data_result: dict) -> dict:
    """
    Layer 2: Generate TEE attestation using Phala dstack-sdk.
    Falls back to mock if not running in a real CVM environment.
    """
    data_json = json.dumps(data_result, sort_keys=True)
    report_data_bytes = hashlib.sha256(data_json.encode()).digest()
    report_data_hex = report_data_bytes.hex()

    try:
        from dstack_sdk import AsyncDstackClient

        client = AsyncDstackClient()
        quote_response = await client.get_quote(report_data_bytes)

        print("\033[32m[Worker-TEE] 🔐 Intel TDX quote generated\033[0m")
        return {
            "type": "intel_tdx",
            "report_data": report_data_hex,
            "quote": quote_response.quote if quote_response else None,
            "event_log": quote_response.event_log if quote_response else None,
            "note": "Real Intel TDX attestation from Phala Cloud CVM",
        }
    except Exception as e:
        print(
            f"\033[33m[Worker-TEE] ⚠️  TDX not available, using mock: {e}\033[0m",
            file=sys.stderr,
        )
        return {
            "type": "mock_tdx",
            "report_data": report_data_hex,
            "quote": None,
            "note": "Deploy to Phala Cloud CVM for real Intel TDX attestation",
        }


async def generate_proof_bundle(protocol: str, worker_address: str = "0x0000000000000000000000000000000000000000") -> dict:
    """
    Generate complete ProofBundle: fetch data, create Layer 1 + Layer 2 proofs.
    """
    # Step 1: Fetch real data
    print(f"\033[36m[Worker] 🌐 Fetching {protocol} TVL from DefiLlama...\033[0m")
    data_result = fetch_tvl(protocol)
    tvl_formatted = f"${data_result['tvl_usd']:,.2f}"
    print(f"\033[32m[Worker] ✅ {protocol.upper()} TVL = {tvl_formatted}\033[0m")

    # Step 2: Layer 1 — zkFetch proof
    print("\033[36m[Worker-zkTLS] 🔗 Generating data provenance proof...\033[0m")
    zk_proof = generate_zk_proof(data_result)
    zk_status = "✅ zkProof" if zk_proof["type"] == "reclaim_zkfetch" else "🟡 SHA256 fallback"
    print(f"\033[32m[Worker-zkTLS] {zk_status}\033[0m")

    # Step 3: Layer 2 — TEE attestation
    print("\033[36m[Worker-TEE] 🔐 Generating TEE attestation...\033[0m")
    tee_attestation = await generate_tee_attestation(data_result)
    tee_status = "✅ Intel TDX" if tee_attestation["type"] == "intel_tdx" else "🟡 Mock TDX"
    print(f"\033[32m[Worker-TEE] {tee_status}\033[0m")

    # Assemble ProofBundle
    proof_bundle = {
        "task_id": "",  # Will be set by server.py when handling a TaskIntent
        "data": data_result,
        "zk_proof": zk_proof,
        "tee_attestation": tee_attestation,
        "worker_pubkey": worker_address,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return proof_bundle


def main():
    parser = argparse.ArgumentParser(description="Generate ProofBundle for a DeFi TVL task")
    parser.add_argument("--protocol", default="aave", help="DefiLlama protocol slug")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    bundle = asyncio.run(generate_proof_bundle(args.protocol))

    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print("\n\033[36m━━━ ProofBundle Summary ━━━\033[0m")
        print(f"  Protocol:  {bundle['data']['protocol']}")
        print(f"  TVL:       ${bundle['data']['tvl_usd']:,.2f}")
        print(f"  ZK Proof:  {bundle['zk_proof']['type']} (hash: {bundle['zk_proof']['hash'][:16]}...)")
        print(f"  TEE:       {bundle['tee_attestation']['type']}")
        print(f"  Timestamp: {bundle['timestamp']}")


if __name__ == "__main__":
    main()
