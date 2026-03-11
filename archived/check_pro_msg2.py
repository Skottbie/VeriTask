#!/usr/bin/env python3
"""Check Pro session L26 and L28 message tool calls"""
import json

with open("session_v347_pro.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# L26
print("=== L26: First message tool call ===")
obj = json.loads(lines[25])
msg = obj.get("message", {})
for c in msg.get("content", []):
    if c.get("type") == "toolCall":
        args = c.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        print(f"Tool: {c.get('name')}")
        print(f"Arguments: {json.dumps(args, indent=2, ensure_ascii=False)}")

# L28
print("\n=== L28: Second message tool call ===")
obj = json.loads(lines[27])
msg = obj.get("message", {})
for c in msg.get("content", []):
    if c.get("type") == "toolCall":
        args = c.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        print(f"Tool: {c.get('name')}")
        print(f"Arguments: {json.dumps(args, indent=2, ensure_ascii=False)}")
