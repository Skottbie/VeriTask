#!/usr/bin/env python3
import json

with open("session_v344.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract full content for lines 15-20 (tool calls and results after Pro completion)
for i in [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
    try:
        obj = json.loads(lines[i].strip())
        if obj.get("type") == "message":
            msg = obj.get("message", {})
            role = msg.get("role", "?")
            contents = msg.get("content", [])
            for c in contents:
                ctype = c.get("type", "")
                if ctype == "toolCall":
                    print(f"\n=== L{i}: TOOLCALL [{role}] ===")
                    print(f"  name: {c.get('name','?')}")
                    print(f"  args: {json.dumps(c.get('arguments',{}), ensure_ascii=False)}")
                elif ctype == "toolResult":
                    inner = c.get("content", [{}])
                    text = inner[0].get("text", "") if inner else ""
                    print(f"\n=== L{i}: TOOLRESULT ===")
                    print(f"  text: {text[:1500]}")
                elif ctype == "text":
                    text = c.get("text", "")
                    print(f"\n=== L{i}: TEXT [{role}] ===")
                    print(f"  {text[:1500]}")
    except Exception as e:
        print(f"L{i}: ERROR: {e}")
