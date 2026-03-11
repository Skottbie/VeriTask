#!/bin/bash
# Analyze v3.3.1 Morpho test session
SESSIONS_DIR="/home/skottbie/.openclaw/agents/main/sessions"

echo "=== Finding latest session (v3.3.1 Morpho test) ==="
LATEST=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1)
echo "Latest session file: $LATEST"
echo "Size: $(wc -c < "$LATEST") bytes"
echo ""

echo "=== 1. sessions_spawn calls ==="
grep -o '"tool_name":"sessions_spawn"[^}]*' "$LATEST" 2>/dev/null | head -5
echo ""

echo "=== 2. sessions_spawn parameters (agentId, mode, model) ==="
grep -o '"sessions_spawn".*"agentId"[^,]*' "$LATEST" 2>/dev/null | head -5
echo ""

echo "=== 3. Full sessions_spawn tool_call blocks ==="
python3 -c "
import json, sys
with open('$LATEST', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            # Check for tool calls
            if 'choices' in obj:
                for choice in obj.get('choices', []):
                    msg = choice.get('delta', {}) or choice.get('message', {})
                    tcs = msg.get('tool_calls', [])
                    for tc in tcs:
                        fn = tc.get('function', {})
                        if 'sessions_spawn' in fn.get('name', ''):
                            print('FOUND sessions_spawn call:')
                            print(json.dumps(fn, indent=2, ensure_ascii=False))
                            print('---')
            # Check for tool results with spawn
            if 'tool_call_id' in str(obj) and 'spawn' in str(obj).lower():
                print('SPAWN RESULT:', json.dumps(obj, ensure_ascii=False)[:500])
                print('---')
        except:
            pass
" 2>/dev/null
echo ""

echo "=== 4. All model references ==="
grep -o '"model":"[^"]*"' "$LATEST" | sort | uniq -c | sort -rn
echo ""

echo "=== 5. All tool names called ==="
python3 -c "
import json
tools = []
with open('$LATEST', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            if 'choices' in obj:
                for c in obj.get('choices', []):
                    msg = c.get('delta', {}) or c.get('message', {})
                    for tc in msg.get('tool_calls', []):
                        fn = tc.get('function', {})
                        name = fn.get('name', '')
                        if name:
                            tools.append(name)
        except:
            pass
for t in tools:
    print(t)
" 2>/dev/null
echo ""

echo "=== 6. Any error messages ==="
grep -i '"error"' "$LATEST" 2>/dev/null | head -5
echo ""

echo "=== 7. Subagent/spawn session IDs ==="
grep -o '"session_id":"[^"]*"' "$LATEST" 2>/dev/null | head -5
echo ""

echo "=== 8. onchainos exec commands (checking OnchainOS calls) ==="
python3 -c "
import json
with open('$LATEST', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            if 'choices' in obj:
                for c in obj.get('choices', []):
                    msg = c.get('delta', {}) or c.get('message', {})
                    for tc in msg.get('tool_calls', []):
                        fn = tc.get('function', {})
                        args = fn.get('arguments', '')
                        if 'onchainos' in args.lower() or 'exec' in fn.get('name', ''):
                            print(f\"Tool: {fn.get('name', '')}\")
                            print(f\"Args: {args[:300]}\")
                            print('---')
        except:
            pass
" 2>/dev/null
echo ""

echo "=== 9. onchainos exec results (checking API responses) ==="
python3 -c "
import json
with open('$LATEST', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            s = json.dumps(obj, ensure_ascii=False)
            if 'onchainos' in s.lower() and ('result' in s.lower() or 'output' in s.lower() or 'content' in s.lower()):
                if 'tool_call_id' in s or 'role' in s:
                    print(s[:500])
                    print('---')
        except:
            pass
" 2>/dev/null
