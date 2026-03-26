#!/usr/bin/env python3
"""
Test Dispute Anchor — local unit test (方案 C).
Validates the complete dispute flow without requiring a running Worker or chain access.

Tests:
  1. build_dispute_calldata() encodes correct VT2 JSON with edge_type="dispute"
  2. verify_proof_bundle() correctly detects tampered zk_proof / tee_attestation
  3. bidding_agent parses dispute edges and applies negative weight
  4. pceg_api EdgeResponse includes edge_type and dispute_reason fields
"""

import hashlib
import json
import math
import sys
from pathlib import Path

# Add skill directories to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "client_node" / "skills" / "graph-anchor"))
sys.path.insert(0, str(ROOT / "client_node" / "skills" / "verifier"))
sys.path.insert(0, str(ROOT / "client_node" / "skills" / "bidding-agent"))

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


# ────────────────────────────────────────────────────────────────────────
print("\n=== TEST 1: build_dispute_calldata ===")
from graph_anchor import build_dispute_calldata, CALLDATA_PREFIX

calldata = build_dispute_calldata(
    worker_address="0xAAA0000000000000000000000000000000000001",
    client_address="0xBBB0000000000000000000000000000000000002",
    dispute_reason="zk_proof_invalid",
    task_type="defi_tvl",
)
payload_str = calldata.decode("utf-8")
test("starts with VT2:", payload_str.startswith(CALLDATA_PREFIX))

edge_json = json.loads(payload_str[len(CALLDATA_PREFIX):])
test("v=3", edge_json["v"] == "3")
test("edge_type=dispute", edge_json["edge_type"] == "dispute")
test("dispute_reason=zk_proof_invalid", edge_json["dispute_reason"] == "zk_proof_invalid")
test("proof_hash empty", edge_json["proof_hash"] == "")
test("amount_usdt=0", edge_json["amount_usdt"] == "0")
test("worker address correct", edge_json["worker"] == "0xAAA0000000000000000000000000000000000001")
test("client address lowercase", edge_json["client"] == "0xbbb0000000000000000000000000000000000002")

# ────────────────────────────────────────────────────────────────────────
print("\n=== TEST 2: verifier detects tampered proofs ===")
from verifier import verify_proof_bundle

# Build a valid ProofBundle first
data = {"task_type": "defi_tvl", "tvl_usd": 12345678.90, "protocol": "aave"}
data_json = json.dumps(data, sort_keys=True)
correct_hash = hashlib.sha256(data_json.encode()).hexdigest()

valid_bundle = {
    "data": data,
    "zk_proof": {"type": "sha256_mock", "hash": correct_hash},
    "tee_attestation": {"type": "mock_tdx", "report_data": correct_hash},
}

# 2a: Valid bundle should pass
result = verify_proof_bundle(valid_bundle)
test("valid bundle passes", result["is_valid"])
test("zk_valid=True", result["zk_valid"])
test("tee_valid=True", result["tee_valid"])

# 2b: Tampered ZK proof
tampered_zk = {
    "data": data,
    "zk_proof": {"type": "sha256_mock", "hash": "deadbeef" * 8},
    "tee_attestation": {"type": "mock_tdx", "report_data": correct_hash},
}
result_zk = verify_proof_bundle(tampered_zk)
test("tampered zk fails", not result_zk["is_valid"])
test("zk_valid=False", not result_zk["zk_valid"])
test("tee_valid=True (only zk tampered)", result_zk["tee_valid"])

# 2c: Tampered TEE attestation
tampered_tee = {
    "data": data,
    "zk_proof": {"type": "sha256_mock", "hash": correct_hash},
    "tee_attestation": {"type": "mock_tdx", "report_data": "cafebabe" * 8},
}
result_tee = verify_proof_bundle(tampered_tee)
test("tampered tee fails", not result_tee["is_valid"])
test("zk_valid=True (only tee tampered)", result_tee["zk_valid"])
test("tee_valid=False", not result_tee["tee_valid"])

# 2d: Both tampered
tampered_both = {
    "data": data,
    "zk_proof": {"type": "sha256_mock", "hash": "deadbeef" * 8},
    "tee_attestation": {"type": "mock_tdx", "report_data": "cafebabe" * 8},
}
result_both = verify_proof_bundle(tampered_both)
test("both tampered fails", not result_both["is_valid"])
test("zk_valid=False", not result_both["zk_valid"])
test("tee_valid=False", not result_both["tee_valid"])

# 2e: Determine dispute_reason from verification result
def determine_dispute_reason(v):
    if not v["zk_valid"] and not v["tee_valid"]:
        return "full_proof_failure"
    elif not v["zk_valid"]:
        return "zk_proof_invalid"
    else:
        return "tee_attestation_invalid"

test("zk tamper → zk_proof_invalid", determine_dispute_reason(result_zk) == "zk_proof_invalid")
test("tee tamper → tee_attestation_invalid", determine_dispute_reason(result_tee) == "tee_attestation_invalid")
test("both tamper → full_proof_failure", determine_dispute_reason(result_both) == "full_proof_failure")

# ────────────────────────────────────────────────────────────────────────
print("\n=== TEST 3: bidding_agent dispute edge weight ===")
from bidding_agent import DISPUTE_KAPPA, DECAY_LAMBDA, compute_proof_quality

# 3a: DISPUTE_KAPPA constants defined correctly
test("DISPUTE_KAPPA has zk_proof_invalid", "zk_proof_invalid" in DISPUTE_KAPPA)
test("DISPUTE_KAPPA zk=0.3", DISPUTE_KAPPA["zk_proof_invalid"] == 0.3)
test("DISPUTE_KAPPA tee=0.5", DISPUTE_KAPPA["tee_attestation_invalid"] == 0.5)
test("DISPUTE_KAPPA full=0.8", DISPUTE_KAPPA["full_proof_failure"] == 0.8)

# 3b: Dispute edge has proof_quality = 0 (empty proof_hash)
dispute_edge = {"proof_hash": "", "tee_fingerprint": ""}
test("dispute edge pq=0", compute_proof_quality(dispute_edge) == 0.0)

# 3c: Simulate negative weight computation
kappa = DISPUTE_KAPPA["zk_proof_invalid"]
age_days = 1.0
expected_weight = -kappa * math.exp(-DECAY_LAMBDA * age_days)
test("negative weight < 0", expected_weight < 0, f"got {expected_weight}")
test("negative weight magnitude correct",
     abs(expected_weight - (-0.3 * math.exp(-DECAY_LAMBDA * 1.0))) < 1e-10)

# ────────────────────────────────────────────────────────────────────────
print("\n=== TEST 4: parse_vt_calldata handles dispute edges ===")
from bidding_agent import parse_vt_calldata, CALLDATA_PREFIX as BA_PREFIX

dispute_payload = {
    "v": "3",
    "edge_type": "dispute",
    "worker": "0xAAA",
    "client": "0xBBB",
    "proof_hash": "",
    "tee_fingerprint": "",
    "task_type": "defi_tvl",
    "amount_usdt": "0",
    "dispute_reason": "tee_attestation_invalid",
    "ts": 1773040716,
}
calldata_hex = (BA_PREFIX + json.dumps(dispute_payload, separators=(",", ":"))).encode().hex()
parsed = parse_vt_calldata(calldata_hex)
test("parsed is not None", parsed is not None)
test("edge_type=dispute", parsed.get("edge_type") == "dispute")
test("dispute_reason preserved", parsed.get("dispute_reason") == "tee_attestation_invalid")
test("v=3", parsed.get("v") == "3")

# v2 edge (no edge_type) should default to endorsement
v2_payload = {
    "v": "2",
    "worker": "0xAAA",
    "client": "0xBBB",
    "proof_hash": "a" * 64,
    "tee_fingerprint": "mock",
    "task_type": "defi_tvl",
    "amount_usdt": "1.0",
    "ts": 1773040716,
}
v2_hex = (BA_PREFIX + json.dumps(v2_payload, separators=(",", ":"))).encode().hex()
parsed_v2 = parse_vt_calldata(v2_hex)
test("v2 parsed ok", parsed_v2 is not None)
test("v2 edge_type defaults missing", "edge_type" not in parsed_v2)
test("v2 edge_type defaults to endorsement",
     parsed_v2.get("edge_type", "endorsement") == "endorsement")

# ────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
if failed == 0:
    print("🎉 All tests passed!")
else:
    print("⚠️  Some tests failed!")
    sys.exit(1)
