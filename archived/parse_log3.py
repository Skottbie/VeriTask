#!/usr/bin/env python3
import sys, json

log_file = "/home/skottbie/.openclaw/agents/main/sessions/5b621d08-c38a-4f1a-b3b8-fb6ba3e1e80e.jsonl"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line.strip())
        t = obj.get('type', '?')
        msg = obj.get('message', {})
        
        if t != 'message' or not isinstance(msg, dict):
            continue
        
        role = msg.get('role', '?')
        content = msg.get('content', '')
        tool_name = msg.get('toolName', '')
        
        # For content that's a list of parts
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get('type') == 'text':
                        text_parts.append(part.get('text', '')[:300])
                    elif part.get('type') == 'tool_use':
                        name = part.get('name', '?')
                        inp = json.dumps(part.get('input', {}))[:300]
                        text_parts.append(f"[TOOL_USE: {name} | input: {inp}]")
                    elif part.get('type') == 'tool_result':
                        text_parts.append(f"[TOOL_RESULT]")
                    else:
                        text_parts.append(f"[{part.get('type', '?')}]")
            content_str = ' '.join(text_parts)
        elif isinstance(content, str):
            content_str = content[:500]
        else:
            content_str = str(content)[:300]
        
        ts = msg.get('timestamp', '')
        if tool_name:
            print(f"[L{i}] [{ts}] {role} (tool={tool_name}): {content_str[:500]}")
        else:
            print(f"[L{i}] [{ts}] {role}: {content_str[:500]}")
