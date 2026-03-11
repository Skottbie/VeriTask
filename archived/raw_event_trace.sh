#!/bin/bash
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"

python3 -c "
import json

with open('$MAIN_SESSION', 'r') as f:
    lines = f.readlines()

# Show EACH event with raw details
for i, line in enumerate(lines):
    try:
        event = json.loads(line.strip())
    except:
        print(f'[{i}] PARSE ERROR: {line[:100]}')
        print()
        continue
    
    msg = event.get('message', {})
    role = msg.get('role', '')
    event_type = event.get('type', '')
    ts = event.get('timestamp', '')
    
    # Show every event regardless of role
    print(f'[{i}] type={event_type} role={role} ts={ts}')
    
    if role == 'assistant':
        content = msg.get('content', '')
        tool_calls = msg.get('toolCalls', [])
        if tool_calls:
            for tc in tool_calls:
                print(f'  TOOL_CALL: {tc.get(\"toolName\", \"\")} args_keys={list(tc.get(\"args\", {}).keys())}')
                if tc.get('toolName') == 'exec':
                    print(f'    cmd: {tc[\"args\"].get(\"command\", \"\")[:300]}')
        if content and isinstance(content, str):
            print(f'  TEXT ({len(content)} chars):')
            print(f'  {content[:1500]}')
    
    elif role == 'announce':
        ann_type = msg.get('announceType', '')
        run_status = msg.get('runStatus', '')
        child_key = msg.get('childSessionKey', '')
        content = msg.get('content', '')
        print(f'  announceType={ann_type} runStatus={run_status} childKey={str(child_key)[:60]}')
        if isinstance(content, str):
            print(f'  content ({len(content)} chars): {content[:600]}')
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    t = c.get('text', '')
                    print(f'  content ({len(t)} chars): {t[:600]}')
    
    elif role == 'user':
        content = msg.get('content', '')
        if isinstance(content, str):
            print(f'  {content[:200]}')
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    print(f'  {c.get(\"text\", \"\")[:200]}')
    
    elif role == 'system':
        content = msg.get('content', '')
        if isinstance(content, str):
            print(f'  system: {content[:200]}')
    
    elif role == 'toolResult':
        tname = msg.get('toolName', '')
        status = msg.get('details', {}).get('status', '')
        error = msg.get('details', {}).get('error', '')
        print(f'  {tname} status={status} error={error[:100] if error else \"\"}')
    
    print()

print('=' * 60)
print('MAIN SESSION SUMMARY:')
print(f'Total events: {len(lines)}')

# Count by type
from collections import Counter
roles = []
for line in lines:
    try:
        e = json.loads(line)
        roles.append(e.get('message', {}).get('role', 'unknown'))
    except:
        pass
print(f'Role counts: {dict(Counter(roles))}')
"
