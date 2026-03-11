#!/usr/bin/env python3
"""Deep parse v3.2 session: extract full tool calls and results."""
import json

LOG_FILE = r"D:\VeriTask\session_v32.jsonl"

with open(LOG_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except:
        continue
    
    typ = obj.get("type", "")
    msg = obj.get("message", {})
    role = msg.get("role", "")
    
    if role == "assistant":
        content = msg.get("content", [])
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "toolCall":
                        name = c.get("name", "?")
                        args_raw = c.get("arguments", {})
                        args = args_raw if isinstance(args_raw, dict) else json.loads(args_raw) if isinstance(args_raw, str) else {}
                        print(f"\n{'='*80}")
                        print(f"[L{i+1}] TOOL_CALL: {name}")
                        # Pretty print args
                        for k, v in args.items():
                            val = str(v)
                            if len(val) > 2000:
                                val = val[:2000] + "...[TRUNCATED]"
                            print(f"  {k}: {val}")
                    elif c.get("type") == "text":
                        text = c.get("text", "")
                        print(f"\n{'='*80}")
                        print(f"[L{i+1}] ASSISTANT TEXT:")
                        # Print first 2000 chars
                        print(text[:2000])
    
    elif role == "toolResult":
        tool_name = msg.get("toolName", "?")
        tool_call_id = msg.get("toolCallId", "?")
        content = msg.get("content", [])
        print(f"\n{'-'*80}")
        print(f"[L{i+1}] TOOL_RESULT: {tool_name} (callId: {tool_call_id[:20]}...)")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    text = c.get("text", "")
                    if len(text) > 3000:
                        print(f"  [Content: {len(text)} chars]")
                        print(f"  FIRST 1500 chars: {text[:1500]}")
                        print(f"  ...[TRUNCATED]...")
                        print(f"  LAST 1000 chars: {text[-1000:]}")
                    else:
                        print(f"  {text}")
        elif isinstance(content, str):
            print(f"  {content[:3000]}")
    
    elif role == "user":
        content = msg.get("content", [])
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    text = c.get("text", "")
                    print(f"\n{'='*80}")
                    print(f"[L{i+1}] USER: {text[:500]}")
