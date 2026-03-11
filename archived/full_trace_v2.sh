#!/bin/bash
echo "=== MAIN SESSION: ALL events with tool calls ==="
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
        print(f'[{i}] PARSE ERROR')
        continue
    
    msg = event.get('message', {})
    role = msg.get('role', '')
    ts = event.get('timestamp', '')
    
    if role == 'assistant':
        tool_calls = msg.get('toolCalls', [])
        content = msg.get('content', '')
        for tc in tool_calls:
            name = tc.get('toolName', '')
            args = tc.get('args', {})
            if name == 'exec':
                cmd = args.get('command', '')
                print(f'[{i}] CALL exec: {cmd[:300]}')
            elif name == 'sessions_spawn':
                aid = args.get('agentId', '')
                mode = args.get('mode', '')
                task = args.get('task', '')[:500]
                print(f'[{i}] CALL sessions_spawn: agentId={aid} mode={mode}')
                print(f'    task: {task}')
            elif name == 'read':
                print(f'[{i}] CALL read: {json.dumps(args, ensure_ascii=False)[:200]}')
            else:
                print(f'[{i}] CALL {name}: {json.dumps(args, ensure_ascii=False)[:200]}')
        if content and isinstance(content, str) and len(content) > 5:
            print(f'[{i}] ASSISTANT TEXT ({len(content)} chars): {content[:500]}')
    
    elif role == 'announce':
        content = msg.get('content', '')
        ann_type = msg.get('announceType', '')
        child_key = msg.get('childSessionKey', event.get('childSessionKey', ''))
        if isinstance(content, str):
            text = content[:800]
        elif isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    parts.append(c.get('text', ''))
            text = ' '.join(parts)[:800]
        else:
            text = str(content)[:800]
        print(f'[{i}] ANNOUNCE type={ann_type} child={str(child_key)[:50]}')
        print(f'    {text}')
    
    print()

print('=' * 60)
print()
"

echo ""
echo "=== PRO SESSION: What did Pro actually do? ==="
PRO_SESSION="/home/skottbie/.openclaw/agents/pro/sessions/7d6fdb69-87ea-4b6b-b5bb-77ebb1fa89ac.jsonl"

python3 -c "
import json

with open('$PRO_SESSION', 'r') as f:
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
    
    if role == 'assistant':
        tool_calls = msg.get('toolCalls', [])
        content = msg.get('content', '')
        for tc in tool_calls:
            name = tc.get('toolName', '')
            args = tc.get('args', {})
            if name == 'exec':
                cmd = args.get('command', '')
                print(f'[{i}] PRO CALL exec: {cmd[:300]}')
            else:
                print(f'[{i}] PRO CALL {name}: {json.dumps(args, ensure_ascii=False)[:200]}')
        if content and isinstance(content, str) and len(content) > 5:
            print(f'[{i}] PRO TEXT ({len(content)} chars): {content[:800]}')
    
    elif role == 'user' or role == 'system':
        content = msg.get('content', '')
        if isinstance(content, str):
            text = content[:300]
        elif isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    parts.append(c.get('text', ''))
            text = ' '.join(parts)[:300]
        else:
            text = str(content)[:300]
        if len(text) > 5:
            print(f'[{i}] PRO {role.upper()}: {text}')
    
    elif role == 'toolResult':
        tname = msg.get('toolName', '')
        content = msg.get('content', [])
        text = ''
        for c in content:
            if isinstance(c, dict) and c.get('type') == 'text':
                text = c.get('text', '')
                break
        status = msg.get('details', {}).get('status', '')
        print(f'[{i}] PRO RESULT {tname}: status={status} | {text[:300]}')
    
    print()
" 2>&1 | head -80
