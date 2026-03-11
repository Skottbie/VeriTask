#!/bin/bash
echo "=== MAIN SESSION: Full event sequence ==="
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"

python3 -c "
import json

with open('$MAIN_SESSION', 'r') as f:
    lines = f.readlines()

print(f'Total events: {len(lines)}')
print()

for i, line in enumerate(lines):
    try:
        event = json.loads(line.strip())
    except:
        continue
    
    msg = event.get('message', {})
    role = msg.get('role', '')
    ts = event.get('timestamp', '')
    
    # Compact summary of each event
    if role == 'user':
        content = msg.get('content', '')
        if isinstance(content, list):
            text = ''
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    text = c.get('text', '')[:100]
                    break
        else:
            text = str(content)[:100]
        print(f'[{i}] {ts} USER: {text}')
    
    elif role == 'assistant':
        tool_calls = msg.get('toolCalls', [])
        content = msg.get('content', '')
        if tool_calls:
            for tc in tool_calls:
                name = tc.get('toolName', '')
                args = tc.get('args', {})
                if name == 'exec':
                    cmd = args.get('command', '')[:150]
                    print(f'[{i}] {ts} CALL {name}: {cmd}')
                elif name == 'sessions_spawn':
                    aid = args.get('agentId', '')
                    mode = args.get('mode', '')
                    print(f'[{i}] {ts} CALL {name}: agentId={aid} mode={mode}')
                elif name == 'read':
                    path = args.get('path', args.get('file', ''))
                    print(f'[{i}] {ts} CALL {name}: {path}')
                else:
                    print(f'[{i}] {ts} CALL {name}: {json.dumps(args, ensure_ascii=False)[:150]}')
        if content and isinstance(content, str) and len(content) > 5:
            print(f'[{i}] {ts} TEXT: {content[:200]}...' if len(content) > 200 else f'[{i}] {ts} TEXT: {content}')
    
    elif role == 'toolResult':
        tname = msg.get('toolName', '')
        status = msg.get('details', {}).get('status', '')
        error = msg.get('details', {}).get('error', '')
        content = msg.get('content', [])
        text = ''
        for c in content:
            if isinstance(c, dict) and c.get('type') == 'text':
                text = c.get('text', '')
                break
        
        if error:
            print(f'[{i}] {ts} RESULT {tname}: ERROR: {error[:200]}')
        elif status:
            print(f'[{i}] {ts} RESULT {tname}: status={status} | {text[:200]}')
        else:
            print(f'[{i}] {ts} RESULT {tname}: {text[:200]}')
    
    elif role == 'system':
        content = msg.get('content', '')
        if isinstance(content, str):
            print(f'[{i}] {ts} SYSTEM: {content[:200]}')
    
    elif role == 'announce':
        content = msg.get('content', '')
        ann_type = msg.get('announceType', '')
        if isinstance(content, str):
            print(f'[{i}] {ts} ANNOUNCE({ann_type}): {content[:300]}')
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    print(f'[{i}] {ts} ANNOUNCE({ann_type}): {c.get(\"text\", \"\")[:300]}')
    
    else:
        print(f'[{i}] {ts} {role}: ...')
    
    print()
"
