#!/usr/bin/env python3
"""Parse v3.4.6 session JSONL to analyze Pro raw JSON output issue."""
import json
import sys

def truncate(s, maxlen=300):
    s = str(s)
    return s[:maxlen] + "..." if len(s) > maxlen else s

with open("D:/VeriTask/session_v346.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")

for i, line in enumerate(lines):
    try:
        obj = json.loads(line.strip())
    except json.JSONDecodeError:
        print(f"[L{i+1}] PARSE ERROR")
        continue

    t = obj.get("type", "?")
    
    if t == "message":
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        content = msg.get("content", [])
        # Show content parts
        parts_summary = []
        for part in content:
            ptype = part.get("type", "?")
            if ptype == "text":
                text = part.get("text", "")
                parts_summary.append(f"TEXT({len(text)}ch): {truncate(text, 200)}")
            elif ptype == "tool_use":
                name = part.get("name", "?")
                inp = part.get("input", {})
                parts_summary.append(f"TOOL_USE({name}): {truncate(json.dumps(inp, ensure_ascii=False), 200)}")
            elif ptype == "tool_result":
                tid = part.get("tool_use_id", "?")
                cont = part.get("content", "")
                parts_summary.append(f"TOOL_RESULT({tid[:12]}...): {truncate(cont, 200)}")
            else:
                parts_summary.append(f"{ptype}: {truncate(str(part), 150)}")
        
        print(f"[L{i+1}] {t} | role={role} | {len(content)} parts")
        for ps in parts_summary:
            print(f"       {ps}")
        print()

    elif t == "metadata":
        agent = obj.get("agent", "?")
        model = obj.get("model", "?")
        print(f"[L{i+1}] {t} | agent={agent} | model={model}")
        print()

    elif t == "tool_exec":
        name = obj.get("name", "?")
        result = obj.get("result", "")
        print(f"[L{i+1}] {t} | name={name}")
        print(f"       result: {truncate(result, 300)}")
        print()

    elif t == "subagent_spawn":
        sub = obj.get("subagent", "?")
        print(f"[L{i+1}] {t} | subagent={sub}")
        print()

    elif t == "subagent_result":
        sub = obj.get("subagent", "?")
        result = obj.get("result", "")
        print(f"[L{i+1}] {t} | subagent={sub}")
        print(f"       result: {truncate(result, 400)}")
        print()

    else:
        print(f"[L{i+1}] {t}: {truncate(json.dumps(obj, ensure_ascii=False), 200)}")
        print()
