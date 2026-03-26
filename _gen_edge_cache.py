#!/usr/bin/env python3
"""
Fast edge cache generator using JSON-RPC batch requests.
Instead of 1879 individual calls (~25 min), sends batches of 50 → ~38 requests (~3 min).
"""
import json, time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "client_node", "skills", "bidding-agent"))

import bidding_agent as ba
import requests as http_requests

BATCH_SIZE = 50   # number of eth_getLogs per batch RPC call
PAGE_SIZE = 99    # blocks per eth_getLogs (X Layer limit)
SLEEP = 0.1       # sleep between individual calls (aggressive for local gen)
_batch_supported = False  # X Layer doesn't support batch RPC — skip it

def batch_rpc(rpc_url, requests_list):
    """Send a batch JSON-RPC request, return list of results."""
    payload = [
        {"jsonrpc": "2.0", "method": r["method"], "params": r["params"], "id": i}
        for i, r in enumerate(requests_list)
    ]
    resp = http_requests.post(rpc_url, json=payload, timeout=60)
    resp.raise_for_status()
    results = resp.json()
    # Sort by id to maintain order
    if isinstance(results, list):
        results.sort(key=lambda x: x.get("id", 0))
        return [r.get("result", []) for r in results]
    # Some RPCs don't support batch — fallback
    return None

def main():
    rpc = ba.XLAYER_RPC
    deploy = ba.VT_REGISTRY_DEPLOY_BLOCK
    latest = int(ba._rpc_call(rpc, "eth_blockNumber", []), 16)
    gap = latest - deploy
    pages = gap // PAGE_SIZE + 1
    
    registry = ba.VT_REGISTRY
    if not registry:
        print("ERROR: VT_REGISTRY not set", file=sys.stderr)
        sys.exit(1)
    
    from web3 import Web3
    registry_addr = Web3.to_checksum_address(registry)
    
    print(f"Deploy={deploy} Latest={latest} Gap={gap} Pages={pages}", flush=True)
    print(f"Registry={registry_addr} EdgeTopic={ba.EDGE_TOPIC}", flush=True)
    print(f"Batch size={BATCH_SIZE} → ~{pages//BATCH_SIZE+1} batch requests", flush=True)
    
    # Build all page filters
    page_filters = []
    cursor = deploy
    while cursor <= latest:
        page_end = min(cursor + PAGE_SIZE, latest)
        page_filters.append({
            "method": "eth_getLogs",
            "params": [{
                "address": registry_addr,
                "topics": [ba.EDGE_TOPIC],
                "fromBlock": hex(cursor),
                "toBlock": hex(page_end),
            }]
        })
        cursor = page_end + 1
    
    print(f"Total pages: {len(page_filters)}", flush=True)
    
    all_logs = []
    total_batches = (len(page_filters) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for bi in range(0, len(page_filters), BATCH_SIZE):
        batch = page_filters[bi:bi+BATCH_SIZE]
        batch_num = bi // BATCH_SIZE + 1
        
        # Sequential scan (X Layer doesn't support batch RPC)
        for req in batch:
            try:
                result = ba._rpc_call(rpc, req["method"], req["params"])
                if isinstance(result, list):
                    all_logs.extend(result)
            except Exception as e:
                print(f"  Warning: page failed ({e}), skipping", flush=True)
            time.sleep(SLEEP)
        print(f"  Batch {batch_num}/{total_batches}: done, total={len(all_logs)}", flush=True)
    
    print(f"\nTotal raw logs: {len(all_logs)}", flush=True)
    
    # Save in edge_cache format
    cache = {"last_scanned_block": latest, "edges": all_logs}
    cache_path = ba.EDGE_CACHE_FILE
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    
    sz = os.path.getsize(cache_path)
    print(f"Saved: {cache_path} ({sz} bytes)", flush=True)
    print("DONE", flush=True)

if __name__ == "__main__":
    main()
