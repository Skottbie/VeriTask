#!/usr/bin/env python3
"""Parse v3.4.8 session - find duplicate Step 0a output"""
import json

with open("session_v348.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")

for i, line in enumerate(lines, 1):
    obj = json.loads(line)
    t = obj.get("type", "?")
    
    if t == "message":
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        content = msg.get("content", [])
        parts_info = []
        for c in content:
            ct = c.get("type", "?")
            if ct == "text":
                txt = c.get("text", "")
                # Check for Step 0a duplicates
                if "Step 0a" in txt or "Pro 验证策略" in txt:
                    print(f"\n[L{i}] {role}: TEXT({len(txt)}ch) *** CONTAINS Step 0a ***")
                    print(f"  First 300ch: {txt[:300]}")
                    continue
                parts_info.append(f"TEXT({len(txt)}ch)")
            elif ct == "toolCall":
                parts_info.append(f"TOOL({c.get('name','?')})")
        if parts_info:
            print(f"[L{i}] {role}: {' | '.join(parts_info[:3])}")
    elif t in ("session", "thinking_level_change", "custom"):
        if t == "session":
            print(f"[L{i}] session")
        # skip others
    else:
        pass
