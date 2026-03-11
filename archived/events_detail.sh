#!/bin/bash
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"

python3 -c "
import json

with open('$MAIN_SESSION', 'r') as f:
    lines = f.readlines()

# Show events 13-17 in FULL RAW JSON
for idx in [5, 7, 9, 11, 13, 15, 16, 17]:
    if idx < len(lines):
        try:
            event = json.loads(lines[idx])
            msg = event.get('message', {})
            role = msg.get('role', '')
            content = msg.get('content', '')
            tool_calls = msg.get('toolCalls', [])
            
            print(f'===== EVENT [{idx}] role={role} =====')
            
            # Show tool calls in detail
            for tc in tool_calls:
                name = tc.get('toolName', '')
                args = tc.get('args', {})
                if name == 'exec':
                    print(f'TOOL CALL: exec command={args.get(\"command\", \"\")[:300]}')
                elif name == 'sessions_spawn':
                    print(f'TOOL CALL: sessions_spawn agentId={args.get(\"agentId\", \"\")}')
                    print(f'  task: {args.get(\"task\", \"\")[:500]}')
                else:
                    print(f'TOOL CALL: {name} args={json.dumps(args, ensure_ascii=False)[:200]}')
            
            # Show content
            if isinstance(content, str) and content:
                print(f'TEXT ({len(content)} chars):')
                print(content[:3000])
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict):
                        ctype = c.get('type', '')
                        text = c.get('text', '')
                        if text:
                            print(f'CONTENT type={ctype} ({len(text)} chars):')
                            print(text[:3000])
            
            if not content and not tool_calls:
                # Show raw message keys
                print(f'MSG KEYS: {list(msg.keys())}')
                # Check for announceType
                if 'announceType' in msg:
                    print(f'announceType: {msg[\"announceType\"]}')
                    print(f'runStatus: {msg.get(\"runStatus\", \"\")}')
                    print(f'childSessionKey: {msg.get(\"childSessionKey\", \"\")}')
            
            print()
        except Exception as e:
            print(f'EVENT [{idx}] ERROR: {e}')
            print()
"
