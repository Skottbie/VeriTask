#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/share/pnpm/global/5/node_modules/.bin:$HOME/.local/bin:$PATH"

echo "=== 1. Find latest session log ==="
SESSIONS_DIR="/home/skottbie/.openclaw/agents/main/sessions"
echo "Session files (sorted by modification time):"
ls -lt "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -5

echo ""
echo "=== 2. Get latest session file ==="
LATEST=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1)
echo "Latest: $LATEST"
echo "Size: $(wc -c < "$LATEST") bytes"
echo "Lines: $(wc -l < "$LATEST")"

echo ""
echo "=== 3. Extract ALL tool calls and results ==="
# Show every tool call and its result in the session
python3 -c "
import json
import sys

with open('$LATEST', 'r') as f:
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
    
    # Tool calls from assistant
    if role == 'assistant':
        tool_calls = msg.get('toolCalls', [])
        for tc in tool_calls:
            name = tc.get('toolName', '')
            args = tc.get('args', {})
            tcid = tc.get('id', '')
            print(f'--- TOOL CALL [{i}]: {name} (id={tcid[:20]}) ---')
            if name == 'sessions_spawn':
                print(f'  agentId: {args.get(\"agentId\", \"(none)\")}')
                print(f'  mode: {args.get(\"mode\", \"\")}')
                task_text = args.get('task', '')
                print(f'  task: {task_text[:200]}...' if len(task_text) > 200 else f'  task: {task_text}')
            elif name == 'run':
                cmd = args.get('command', '')
                print(f'  command: {cmd[:300]}')
            else:
                args_str = json.dumps(args, ensure_ascii=False)
                print(f'  args: {args_str[:300]}')
            print()
    
    # Tool results
    if role == 'toolResult':
        tcid = msg.get('toolCallId', '')
        tname = msg.get('toolName', '')
        content = msg.get('content', [])
        is_error = msg.get('isError', False)
        details = msg.get('details', {})
        
        # Extract text content
        text = ''
        for c in content:
            if isinstance(c, dict) and c.get('type') == 'text':
                text = c.get('text', '')
                break
            elif isinstance(c, str):
                text = c
                break
        
        status = details.get('status', '')
        error = details.get('error', '')
        
        print(f'--- TOOL RESULT [{i}]: {tname} (id={tcid[:20]}) ---')
        if status:
            print(f'  status: {status}')
        if error:
            print(f'  error: {error}')
        if is_error:
            print(f'  IS_ERROR: True')
        if text:
            # Truncate long results but show more for run commands
            max_len = 500 if tname == 'run' else 300
            print(f'  result: {text[:max_len]}')
            if len(text) > max_len:
                print(f'  ... ({len(text)} total chars)')
        print()
    
    # Text messages (assistant output)
    if role == 'assistant' and msg.get('content'):
        content = msg.get('content', '')
        if isinstance(content, str) and len(content) > 10:
            print(f'--- ASSISTANT TEXT [{i}] ---')
            print(f'  {content[:300]}')
            if len(content) > 300:
                print(f'  ... ({len(content)} total chars)')
            print()
"

echo ""
echo "=== 4. Also check Pro agent sessions ==="
PRO_SESSIONS="/home/skottbie/.openclaw/agents/pro/sessions"
if [ -d "$PRO_SESSIONS" ]; then
    echo "Pro sessions:"
    ls -lt "$PRO_SESSIONS"/*.jsonl 2>/dev/null | head -3
else
    echo "No pro sessions directory"
fi
