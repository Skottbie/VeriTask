#!/usr/bin/env python3
import json

with open("session_v345.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Raw examination of line 26
obj = json.loads(lines[26].strip())
print(f"Line 26 type: {obj.get('type')}")
if obj.get("type") == "message":
    msg = obj.get("message", {})
    print(f"  role: {msg.get('role')}")
    contents = msg.get("content", [])
    for ci, c in enumerate(contents):
        print(f"  content[{ci}] type={c.get('type')}")
        if c.get("type") == "toolResult":
            inner = c.get("content", [])
            print(f"    inner_len={len(inner)}")
            for ii, ic in enumerate(inner):
                print(f"    inner[{ii}] type={ic.get('type')} text_len={len(ic.get('text',''))}")
                print(f"    text: {ic.get('text','')[:2000]}")
        elif c.get("type") == "text":
            print(f"    text: {c.get('text','')[:2000]}")
else:
    print(f"  full: {json.dumps(obj, ensure_ascii=False)[:1000]}")
