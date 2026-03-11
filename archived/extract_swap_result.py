#!/usr/bin/env python3
import json

with open("session_v345.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract FULL content of lines 25, 26, 27 (swap execution and next action)
for i in [25, 26, 27]:
    try:
        obj = json.loads(lines[i].strip())
        if obj.get("type") == "message":
            msg = obj.get("message", {})
            role = msg.get("role", "?")
            contents = msg.get("content", [])
            for c in contents:
                ctype = c.get("type", "")
                if ctype == "toolCall":
                    print(f"\n=== L{i}: TOOLCALL ===")
                    print(f"  name: {c.get('name','?')}")
                    print(f"  args: {json.dumps(c.get('arguments',{}), ensure_ascii=False)}")
                elif ctype == "toolResult":
                    inner = c.get("content", [{}])
                    text = inner[0].get("text", "") if inner else ""
                    print(f"\n=== L{i}: TOOLRESULT (full, {len(text)} chars) ===")
                    print(text)
    except Exception as e:
        print(f"L{i}: ERROR: {e}")
