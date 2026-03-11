#!/usr/bin/env python3
"""Parse v3.4.7 session JSONL."""
import json

with open("D:/VeriTask/session_v347.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")

for i, line in enumerate(lines):
    obj = json.loads(line.strip())
    t = obj.get("type", "?")

    if t == "message":
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        content = msg.get("content", [])
        parts = []
        for part in content:
            ptype = part.get("type", "?")
            if ptype == "text":
                text = part.get("text", "")
                preview = text[:200].replace("\n", "\\n")
                parts.append(f"TEXT({len(text)}ch): {preview}")
            elif ptype == "toolCall":
                tc = part if "name" in part else part.get("toolCall", {})
                name = tc.get("name", "?")
                parts.append(f"TOOL({name})")
            else:
                parts.append(f"{ptype}")
        joined = " | ".join(parts)
        print(f"[L{i+1}] {role}: {joined}")
    else:
        print(f"[L{i+1}] {t}")
