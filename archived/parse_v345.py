#!/usr/bin/env python3
import json

with open("session_v345.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines):
    try:
        obj = json.loads(line.strip())
        if obj.get("type") == "message":
            msg = obj.get("message", {})
            role = msg.get("role", "?")
            contents = msg.get("content", [])
            for c in contents:
                ctype = c.get("type", "")
                if ctype == "toolCall":
                    args_str = json.dumps(c.get("arguments", {}), ensure_ascii=False)[:300]
                    print(f"\nL{i}: TOOLCALL [{role}] name={c.get('name','?')}")
                    print(f"  args: {args_str}")
                elif ctype == "toolResult":
                    inner = c.get("content", [{}])
                    text = inner[0].get("text", "")[:500] if inner else ""
                    print(f"\nL{i}: TOOLRESULT")
                    print(f"  text: {text}")
                elif ctype == "text":
                    text = c.get("text", "")[:400]
                    print(f"\nL{i}: TEXT [{role}]")
                    print(f"  {text}")
    except Exception as e:
        pass
