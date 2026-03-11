#!/usr/bin/env python3
"""Quick test of Worker /execute endpoint."""
import requests
import json

body = {
    "type": "defi_tvl",
    "params": {"protocol": "aave"},
    "client_wallet": "0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85",
}
r = requests.post("http://127.0.0.1:8001/execute", json=body, timeout=30)
d = r.json()
print(f"Status: {r.status_code}")
tvl = d["data"]["tvl_usd"]
print(f"TVL: ${tvl:,.2f}")
print(f"ZK: {d['zk_proof']['type']}")
print(f"TEE: {d['tee_attestation']['type']}")
print(f"Worker: {d['worker_pubkey']}")
print(f"Timestamp: {d['timestamp']}")
