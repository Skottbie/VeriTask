#!/usr/bin/env python3
"""Parse v3.4.7 Pro session log to find ANNOUNCE_SKIP behavior"""
import json

with open("session_v347_pro.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")

for i, line in enumerate(lines, 1):
    obj = json.loads(line)
    t = obj.get("type", "?")
    
    if t == "message":
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        content = msg.get("content", [])
        parts = []
        for c in content:
            ct = c.get("type", "?")
            if ct == "text":
                txt = c.get("text", "")
                parts.append(f"TEXT({len(txt)}ch)")
                # Show key text content
                if "ANNOUNCE" in txt or "announce" in txt.lower() or "skip" in txt.lower():
                    print(f"[L{i}] {role}: {parts[-1]}")
                    print(f"  >>> ANNOUNCE-RELATED TEXT:")
                    print(f"  {txt[:500]}")
                    print()
                    continue
                if len(txt) < 200 or i >= len(lines) - 5:
                    parts.append(f": {txt[:150]}")
            elif ct == "toolCall":
                parts.append(f"TOOL({c.get('name','?')})")
        summary = " | ".join(parts)
        print(f"[L{i}] {role}: {summary[:200]}")
    elif t == "session":
        print(f"[L{i}] session: {obj.get('id','')}")
    else:
        print(f"[L{i}] {t}")

# Also find the last assistant message (should be ANNOUNCE_SKIP or not)
print("\n" + "="*60)
print("Last 5 lines details:")
for i in range(max(0, len(lines)-5), len(lines)):
    obj = json.loads(lines[i])
    t = obj.get("type", "?")
    if t == "message":
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        content = msg.get("content", [])
        for c in content:
            if c.get("type") == "text":
                txt = c.get("text", "")
                print(f"\n[L{i+1}] {role} text ({len(txt)}ch):")
                print(txt[:1000])
