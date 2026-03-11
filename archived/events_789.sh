#!/bin/bash
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"

python3 -c "
import json

with open('$MAIN_SESSION', 'r') as f:
    lines = f.readlines()

# Show events 7, 9, 11, 13 tool calls (which were blank in previous output)
for idx in [7, 9, 11, 13]:
    if idx < len(lines):
        event = json.loads(lines[idx])
        msg = event.get('message', {})
        role = msg.get('role', '')
        tool_calls = msg.get('toolCalls', [])
        content = msg.get('content', '')
        
        print(f'===== EVENT [{idx}] role={role} =====')
        for tc in tool_calls:
            name = tc.get('toolName', '')
            args = tc.get('args', {})
            print(f'  TOOL: {name}')
            print(f'  ARGS: {json.dumps(args, ensure_ascii=False)[:500]}')
        if content:
            if isinstance(content, str):
                print(f'  TEXT: {content[:500]}')
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get('type') == 'text':
                        print(f'  TEXT: {c.get(\"text\", \"\")[:500]}')
        print()
"
