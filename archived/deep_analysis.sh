#!/bin/bash
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"
PRO_SESSION="/home/skottbie/.openclaw/agents/pro/sessions/7d6fdb69-87ea-4b6b-b5bb-77ebb1fa89ac.jsonl"

echo "=== 1. Event 14: sessions_spawn FULL result ==="
python3 -c "
import json
with open('$MAIN_SESSION') as f:
    lines = f.readlines()
event = json.loads(lines[14])
msg = event['message']
content = msg.get('content', [])
for c in content:
    if isinstance(c, dict) and c.get('type') == 'text':
        print(c['text'])
details = msg.get('details', {})
if details:
    print('DETAILS:', json.dumps(details, indent=2, ensure_ascii=False))
"

echo ""
echo "=== 2. Event 13: sessions_spawn CALL args ==="
python3 -c "
import json
with open('$MAIN_SESSION') as f:
    lines = f.readlines()
event = json.loads(lines[13])
msg = event['message']
for tc in msg.get('toolCalls', []):
    print('toolName:', tc['toolName'])
    args = tc.get('args', {})
    for k, v in args.items():
        if k == 'task':
            print(f'  task ({len(str(v))} chars): {str(v)[:800]}')
        else:
            print(f'  {k}: {v}')
"

echo ""
echo "=== 3. Event 15: Flash text FULL (the fabricated output) ==="
python3 -c "
import json
with open('$MAIN_SESSION') as f:
    lines = f.readlines()
event = json.loads(lines[15])
msg = event['message']
content = msg.get('content', '')
if isinstance(content, list):
    for c in content:
        if isinstance(c, dict) and c.get('type') == 'text':
            print(f'TEXT ({len(c[\"text\"])} chars)')
            # Check: did it call any tools in this event?
tc = msg.get('toolCalls', [])
print(f'Tool calls in event 15: {len(tc)}')
for t in tc:
    print(f'  {t.get(\"toolName\", \"\")}')
"

echo ""
echo "=== 4. Pro session: ALL tool calls ==="
python3 -c "
import json
with open('$PRO_SESSION') as f:
    lines = f.readlines()
print(f'Pro session total events: {len(lines)}')
for i, line in enumerate(lines):
    event = json.loads(line)
    msg = event.get('message', {})
    role = msg.get('role', '')
    if role == 'assistant':
        for tc in msg.get('toolCalls', []):
            name = tc.get('toolName', '')
            args = tc.get('args', {})
            if name == 'exec':
                print(f'[{i}] Pro CALL exec: {args.get(\"command\", \"\")[:200]}')
            else:
                print(f'[{i}] Pro CALL {name}')
        content = msg.get('content', '')
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text' and len(c.get('text', '')) > 10:
                    print(f'[{i}] Pro TEXT ({len(c[\"text\"])} chars): {c[\"text\"][:300]}')
        elif isinstance(content, str) and len(content) > 10:
            print(f'[{i}] Pro TEXT ({len(content)} chars): {content[:300]}')
    elif role == 'toolResult':
        tname = msg.get('toolName', '')
        status = msg.get('details', {}).get('status', '')
        content_items = msg.get('content', [])
        text = ''
        for c in content_items:
            if isinstance(c, dict) and c.get('type') == 'text':
                text = c.get('text', '')[:200]
                break
        print(f'[{i}] Pro RESULT {tname}: {text[:200]}')
"
