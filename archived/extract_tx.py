#!/usr/bin/env python3
"""Extract the full tx object from the onchainos swap swap result."""
import json

session_file = "/home/skottbie/.openclaw/agents/main/sessions/1cad7336-f77e-4ffc-a5ca-0cd1ff6dfd35.jsonl"

with open(session_file) as f:
    lines = f.readlines()

# Line 32 is the toolResult for the second swap swap call (with --wallet)
line = lines[32].strip()
obj = json.loads(line)
msg = obj.get("message", {})
content = msg.get("content", [])

for part in content:
    if part.get("type") == "text":
        text = part.get("text", "")
        try:
            data = json.loads(text)
            if "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    if "tx" in item:
                        tx = item["tx"]
                        print("=== TX OBJECT KEYS ===")
                        print(json.dumps(list(tx.keys())))
                        print()
                        # Print each field except 'data' (too long)
                        for k, v in tx.items():
                            if k == "data":
                                print(f"  data: {str(v)[:100]}... (length: {len(str(v))})")
                            else:
                                print(f"  {k}: {v}")
                    if "routerResult" in item:
                        rr = item["routerResult"]
                        print()
                        print("=== ROUTER RESULT KEYS ===")
                        print(json.dumps(list(rr.keys())))
                        print(f"  fromTokenAmount: {rr.get('fromTokenAmount')}")
                        print(f"  toTokenAmount: {rr.get('toTokenAmount')}")
                        print(f"  estimateGasFee: {rr.get('estimateGasFee')}")
        except json.JSONDecodeError:
            pass
