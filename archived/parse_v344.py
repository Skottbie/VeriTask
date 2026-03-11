#!/usr/bin/env python3
import json, sys

with open("session_v344.jsonl", "r", encoding="utf-8") as f:
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
                    args_str = json.dumps(c.get("arguments", {}), ensure_ascii=False)[:200]
                    print(f"L{i}: TOOLCALL [{role}] name={c.get('name','?')} args={args_str}")
                elif ctype == "toolResult":
                    inner = c.get("content", [{}])
                    text = inner[0].get("text", "")[:300] if inner else ""
                    print(f"L{i}: TOOLRESULT text={text}")
                elif ctype == "text":
                    text = c.get("text", "")[:300]
                    print(f"L{i}: TEXT [{role}] {text}")
    except Exception as e:
        pass
