#!/usr/bin/env python3
import json
with open("session_v348.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# L45 - check what triggered the duplicate
obj = json.loads(lines[44])
msg = obj.get("message", {})
content = msg.get("content", [])
role = msg.get("role", "?")
provenance = msg.get("provenance") or obj.get("provenance")
txt = content[0].get("text", "") if content else ""

print(f"L45 role: {role}")
print(f"L45 provenance: {json.dumps(provenance, indent=2)}")
print(f"L45 text ({len(txt)}ch):")
print(txt[:1500])
