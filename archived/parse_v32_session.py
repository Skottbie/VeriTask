#!/usr/bin/env python3
"""Parse v3.2 session log to understand Agent behavior in detail."""
import json
import sys
import textwrap

LOG_FILE = r"D:\VeriTask\session_v32.jsonl"

with open(LOG_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")

for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        print(f"[L{i+1}] PARSE ERROR: {line[:200]}")
        continue
    
    role = obj.get("role", "?")
    ts = obj.get("timestamp", "?")
    
    # Metadata / session init
    if "metadata" in obj:
        meta = obj["metadata"]
        print(f"[L{i+1}] METADATA | skills_loaded: {meta.get('skills_loaded', '?')}")
        print(f"         model: {meta.get('model', '?')}")
        skills = meta.get("skills_snapshot", [])
        if skills:
            print(f"         skills_snapshot ({len(skills)}):")
            for s in skills:
                print(f"           - {s.get('name', '?')} (v{s.get('version', '?')})")
        continue
    
    # User message
    if role == "user":
        content = obj.get("content", "")
        if isinstance(content, list):
            content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
        print(f"[L{i+1}] USER | {content[:200]}")
        continue
    
    # Assistant message
    if role == "assistant":
        content = obj.get("content", "")
        tool_calls = obj.get("tool_calls", [])
        
        if content:
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                content = " ".join(texts)
            print(f"[L{i+1}] ASSISTANT | {content[:300]}")
        
        if tool_calls:
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "?")
                args_str = fn.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except:
                    args = args_str
                
                # For file reads, show the path
                if name in ("read_file", "read_skill"):
                    path = args.get("path", args.get("file", args.get("skill", "?")))
                    print(f"[L{i+1}] TOOL_CALL | {name}({path})")
                # For exec, show command
                elif name in ("exec", "run_command", "execute_command", "terminal"):
                    cmd = args.get("command", args.get("cmd", str(args)[:200]))
                    print(f"[L{i+1}] TOOL_CALL | {name}: {cmd[:300]}")
                else:
                    print(f"[L{i+1}] TOOL_CALL | {name}: {json.dumps(args, ensure_ascii=False)[:300]}")
        continue
    
    # Tool response
    if role == "tool":
        name = obj.get("name", obj.get("tool_call_id", "?"))
        content = obj.get("content", "")
        if isinstance(content, str) and len(content) > 500:
            # Check if it's a SKILL.md content
            if "SKILL" in content or "---" in content[:50]:
                print(f"[L{i+1}] TOOL_RESULT | {name}: [SKILL.md content, {len(content)} chars]")
                # Show first few lines to identify which skill
                first_lines = content[:200].replace("\n", " | ")
                print(f"         First 200 chars: {first_lines}")
            else:
                print(f"[L{i+1}] TOOL_RESULT | {name}: {content[:400]}")
        else:
            print(f"[L{i+1}] TOOL_RESULT | {name}: {str(content)[:400]}")
        continue
    
    # System message
    if role == "system":
        content = obj.get("content", "")
        if isinstance(content, str):
            print(f"[L{i+1}] SYSTEM | {content[:300]}")
        continue
    
    # Fallback
    print(f"[L{i+1}] {role} | {json.dumps(obj, ensure_ascii=False)[:300]}")
