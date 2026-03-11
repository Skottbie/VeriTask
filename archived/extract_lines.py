#!/usr/bin/env python3
import json

session_file = "/home/skottbie/.openclaw/agents/main/sessions/1cad7336-f77e-4ffc-a5ca-0cd1ff6dfd35.jsonl"

with open(session_file) as f:
    lines = f.readlines()

# Look at lines around the second swap swap call (line 31)
for idx in range(31, min(36, len(lines))):
    line = lines[idx].strip()
    obj = json.loads(line)
    msg = obj.get("message", {})
    role = msg.get("role", "")
    tool_name = msg.get("toolName", "")
    tool_call_id = msg.get("toolCallId", "")
    
    print(f"=== LINE {idx} | role={role} | toolName={tool_name} | callId={tool_call_id} ===")
    
    content = msg.get("content", [])
    for part in content:
        ptype = part.get("type", "")
        if ptype == "text":
            text = part.get("text", "")
            print("TEXT:", text[:3000])
        elif ptype == "toolCall":
            name = part.get("name", "")
            args = part.get("arguments", {})
            args_str = json.dumps(args, ensure_ascii=False)
            print("TOOLCALL:", name, "|", args_str[:500])
    print()
