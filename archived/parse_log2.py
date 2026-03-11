#!/usr/bin/env python3
import sys, json

log_file = "/home/skottbie/.openclaw/agents/main/sessions/5b621d08-c38a-4f1a-b3b8-fb6ba3e1e80e.jsonl"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line.strip())
        t = obj.get('type', '?')
        msg = obj.get('message', {})
        
        if t == 'session_start':
            print(f"[L{i}] SESSION_START cwd={obj.get('cwd')}")
        elif t == 'turn':
            role = msg.get('role', '?')
            content = ''
            parts = msg.get('parts', [])
            for p in parts:
                if isinstance(p, dict):
                    if p.get('type') == 'text':
                        content += p.get('text', '')[:200]
                    elif p.get('type') == 'tool_call':
                        content += f"[TOOL_CALL: {p.get('name', '?')}({json.dumps(p.get('input', {}))[:200]})]"
                    elif p.get('type') == 'tool_result':
                        content += f"[TOOL_RESULT: {p.get('name', '?')} => {str(p.get('output', ''))[:200]}]"
                    else:
                        content += f"[{p.get('type', '?')}]"
            print(f"[L{i}] {t} role={role}: {content[:500]}")
        elif t == 'agent_event':
            ct = obj.get('customType', '')
            data = obj.get('data', {})
            print(f"[L{i}] AGENT_EVENT: {ct} data_keys={list(data.keys())[:10]}")
        else:
            print(f"[L{i}] {t}: msg_keys={list(msg.keys()) if isinstance(msg, dict) else '?'}")
