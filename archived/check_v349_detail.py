#!/usr/bin/env python3
"""Check specific lines from v3.4.9 session"""
import json

with open("session_v349.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in [17, 24, 48]:  # L18, L25, L49 (0-indexed)
    msg = json.loads(lines[idx]).get("message", {})
    content = msg.get("content", [])
    text = ""
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            text += c["text"]
    
    print(f"===== L{idx+1} ({len(text)}ch) =====")
    print(text[:600])
    print()

# Also check L17 (announce event) to see the Action instruction
msg17 = json.loads(lines[16]).get("message", {})
content17 = msg17.get("content", [])
text17 = ""
for c in content17:
    if isinstance(c, dict) and c.get("type") == "text":
        text17 += c["text"]
print(f"===== L17 announce ({len(text17)}ch) =====")
# Show the last 500 chars (Action instruction)
print("...last 500 chars:")
print(text17[-500:])
