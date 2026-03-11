#!/usr/bin/env python3
"""Check Pro session L26 and L28 message tool calls in detail"""
import json

with open("session_v347_pro.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# L26 (assistant TOOL(message) - first attempt)
print("=== L26: First message tool call ===")
obj26 = json.loads(lines[25])
msg26 = obj26.get("message", {})
for c in msg26.get("content", []):
    if c.get("type") == "toolCall":
        print(f"Tool: {c.get('name')}")
        print(f"Arguments: {json.dumps(json.loads(c.get('arguments', '{}')), indent=2, ensure_ascii=False)}")

print("\n=== L28: Second message tool call (SUCCESS) ===")
obj28 = json.loads(lines[27])
msg28 = obj28.get("message", {})
for c in msg28.get("content", []):
    if c.get("type") == "toolCall":
        print(f"Tool: {c.get('name')}")
        args = json.loads(c.get("arguments", "{}"))
        print(f"Arguments: {json.dumps(args, indent=2, ensure_ascii=False)}")
