#!/usr/bin/env python3
import json

with open("session_v345.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Full text of line 26 with no truncation
obj = json.loads(lines[26].strip())
msg = obj.get("message", {})
for c in msg.get("content", []):
    if c.get("type") == "text":
        print(c.get("text", ""))
