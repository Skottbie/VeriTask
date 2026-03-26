#!/usr/bin/env python3
"""Pre-seed 9 reputation edges for demo. Run from WSL."""
import json
import os
import subprocess
import sys
import time

# Worker addresses
ALPHA = "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb"
BETA  = "0x6c6Fd021Ff91842408c91c7752764da97AEc9Bc4"
GAMMA = "0x51cCB8E0F814679D5328bF37E4Dd96Fe2e436C40"

# Client addresses (from X Layer leaderboard)
CLIENT_A = "0xbf004bff64725914ee36d03b87d6965b0ced4903"  # high PnL
CLIENT_B = "0xfd43949e7a6f86f5d6d59ceb1b0545d6b8cf94d4"  # medium
CLIENT_C = "0x07cca5374b11c668e0f424b7ed6d68c768721d3d"  # low PnL

now = int(time.time())
DAY = 86400

# 9 edges as per design_PCEG.md
EDGES = [
    # Worker Alpha (5 edges — strongest)
    {"worker": ALPHA, "client": CLIENT_A, "amount": "5",   "tee": "real", "age_days": 2},
    {"worker": ALPHA, "client": CLIENT_A, "amount": "3",   "tee": "real", "age_days": 1},
    {"worker": ALPHA, "client": CLIENT_B, "amount": "2",   "tee": "real", "age_days": 2},
    {"worker": ALPHA, "client": CLIENT_B, "amount": "1",   "tee": "real", "age_days": 3},
    {"worker": ALPHA, "client": CLIENT_C, "amount": "0.5", "tee": "real", "age_days": 1},
    # Worker Beta (3 edges — medium)
    {"worker": BETA,  "client": CLIENT_A, "amount": "1",   "tee": "real", "age_days": 5},
    {"worker": BETA,  "client": CLIENT_B, "amount": "2",   "tee": "real", "age_days": 6},
    {"worker": BETA,  "client": CLIENT_C, "amount": "0.1", "tee": "mock", "age_days": 7},
    # Worker Gamma (1 edge — weakest)
    {"worker": GAMMA, "client": CLIENT_C, "amount": "0.1", "tee": "mock", "age_days": 20},
]

ANCHOR_SCRIPT = os.environ.get(
    "ANCHOR_SCRIPT",
    os.path.join(os.path.dirname(__file__), "client_node", "skills", "graph-anchor", "graph_anchor.py")
)

def make_bundle(edge):
    ts = now - edge["age_days"] * DAY
    if edge["tee"] == "real":
        tee_quote = f"real_tdx_quote_demo_{edge['worker'][:10]}_{ts}"
        proof_hash = f"{ts:064x}"  # 64-char hex
    else:
        tee_quote = "mock_tdx_quote"
        proof_hash = f"{ts:064x}"

    return {
        "worker_pubkey": edge["worker"],
        "data": {"task_type": "defi_tvl"},
        "zk_proof": {"hash": proof_hash},
        "tee_attestation": {"quote": tee_quote},
        "amount_usdt": edge["amount"],
        "ts": ts,
    }

def main():
    results = []
    for i, edge in enumerate(EDGES):
        bundle = make_bundle(edge)
        bundle_path = f"/tmp/preseed_bundle_{i}.json"
        with open(bundle_path, "w") as f:
            json.dump(bundle, f)

        cmd = [
            sys.executable, ANCHOR_SCRIPT,
            "--bundle", bundle_path,
            "--client-override", edge["client"],
            "--json",
        ]
        print(f"\n[{i+1}/9] {edge['client'][:10]}... → {edge['worker'][:10]}... "
              f"amt={edge['amount']} tee={edge['tee']} age={edge['age_days']}d")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  ERROR: {result.stderr.strip()}")
                results.append({"edge": i+1, "status": "error", "err": result.stderr.strip()})
            else:
                # Find JSON object in stdout (skip [Graph-Anchor] log lines)
                lines = result.stdout.strip().split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("{"):
                        in_json = True
                    if in_json:
                        json_lines.append(line)
                out = json.loads("\n".join(json_lines))
                tx = out.get("tx_hash", "")
                print(f"  ✅ tx={tx}")
                results.append({"edge": i+1, "status": "ok", "tx_hash": tx})
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results.append({"edge": i+1, "status": "exception", "err": str(e)})

        # Small delay between txs to avoid nonce collision
        time.sleep(3)

    print(f"\n{'='*60}")
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"Pre-seed complete: {ok}/{len(EDGES)} successful")
    for r in results:
        print(f"  Edge {r['edge']}: {r['status']} {r.get('tx_hash', r.get('err', ''))}")

if __name__ == "__main__":
    main()
