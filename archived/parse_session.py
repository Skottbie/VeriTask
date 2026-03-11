#!/usr/bin/env python3
"""Extract toolCall name+arguments and toolResult from OpenClaw JSONL."""
import sys, json

for i, line in enumerate(sys.stdin):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    t = d.get("type", "")
    if t != "message":
        continue
    msg = d.get("message", {})
    role = msg.get("role", "")
    content = msg.get("content", [])
    if not isinstance(content, list):
        continue
    for part in content:
        pt = part.get("type", "")
        if pt == "toolCall":
            name = part.get("name", "")
            args = part.get("arguments", "")
            if isinstance(args, dict):
                args = json.dumps(args, ensure_ascii=False)[:500]
            else:
                args = str(args)[:500]
            print(f">>> [{name}]: {args}")
        elif pt == "toolResult":
            tid = part.get("id", part.get("tool_use_id", ""))[:12]
            out = part.get("output", part.get("content", part.get("text", "")))
            if isinstance(out, dict):
                out = json.dumps(out, ensure_ascii=False)[:2000]
            elif isinstance(out, list):
                texts = []
                for sub in out:
                    if isinstance(sub, dict):
                        texts.append(sub.get("text", json.dumps(sub, ensure_ascii=False))[:1000])
                    else:
                        texts.append(str(sub)[:400])
                out = " | ".join(texts)[:2000]
            else:
                out = str(out)[:2000]
            print(f"<<< RESULT: {out}")
        elif pt == "text":
            txt = part.get("text", "")[:300]
            if txt.strip():
                print(f"[{role}]: {txt}")
