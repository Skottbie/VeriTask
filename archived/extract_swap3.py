#!/usr/bin/env python3
import json

session_file = "/home/skottbie/.openclaw/agents/main/sessions/1cad7336-f77e-4ffc-a5ca-0cd1ff6dfd35.jsonl"

with open(session_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except:
            continue
        if obj.get("type") != "message":
            continue
        msg = obj.get("message", {})
        content = msg.get("content", [])
        for i, part in enumerate(content):
            pt = part.get("type", "")
            if pt == "toolCall":
                args = part.get("arguments", "")
                if "swap" in args:
                    name = part.get("name", "")
                    print("CALL:", name, "|", args[:300])
            if pt == "toolResult" and i > 0:
                prev = content[i - 1]
                if prev.get("type") == "toolCall" and "swap" in prev.get("arguments", ""):
                    result = json.dumps(part, ensure_ascii=False)
                    print("RESULT:", result[:4000])
                    print()
