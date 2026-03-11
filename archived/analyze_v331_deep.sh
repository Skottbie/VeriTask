#!/bin/bash
# Deep analysis of v3.3.1 spawn behavior
SESSIONS_DIR="/home/skottbie/.openclaw/agents/main/sessions"
MAIN_SESSION="$SESSIONS_DIR/df328501-c6c3-418c-a9e8-4908f3150c67.jsonl"

echo "=== 1. Subagent session details ==="
python3 -c "
import json
with open('$MAIN_SESSION', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            s = json.dumps(obj, ensure_ascii=False)
            if 'subagent' in s.lower() or 'session_key' in s:
                print(json.dumps(obj, indent=2, ensure_ascii=False)[:1000])
                print('===')
        except:
            pass
"

echo ""
echo "=== 2. Find ALL session files created around test time ==="
ls -la "$SESSIONS_DIR"/*.jsonl 2>/dev/null | tail -10
echo ""

echo "=== 3. Subagent session files (if any) ==="
# Subagent sessions might be in subdirectories
find "$SESSIONS_DIR" -name "*.jsonl" -newer "$MAIN_SESSION" -o -name "4374f8de*" 2>/dev/null
find /home/skottbie/.openclaw/agents/ -name "4374f8de*" 2>/dev/null
find /home/skottbie/.openclaw/ -name "4374f8de*" 2>/dev/null
echo ""

echo "=== 4. Check subagent session by ID ==="
# The subagent session ID was 4374f8de-29e3-4e2e-9ea9-e565cf9e5841
SUBAGENT_FILE=$(find /home/skottbie/.openclaw/ -name "4374f8de*" 2>/dev/null | head -1)
if [ -n "$SUBAGENT_FILE" ]; then
    echo "Found: $SUBAGENT_FILE"
    echo "Size: $(wc -c < "$SUBAGENT_FILE") bytes"
    echo "Models used:"
    grep -o '"model":"[^"]*"' "$SUBAGENT_FILE" | sort | uniq -c | sort -rn
    echo ""
    echo "Tool calls:"
    python3 -c "
import json
with open('$SUBAGENT_FILE', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            if 'choices' in obj:
                for c in obj.get('choices', []):
                    msg = c.get('delta', {}) or c.get('message', {})
                    for tc in msg.get('tool_calls', []):
                        fn = tc.get('function', {})
                        print(f\"Tool: {fn.get('name', '')}, Args: {fn.get('arguments', '')[:200]}\")
        except:
            pass
" 2>/dev/null
else
    echo "No subagent session file found with ID 4374f8de"
fi

echo ""
echo "=== 5. sessions_spawn full call + result ==="
python3 -c "
import json
with open('$MAIN_SESSION', 'r') as f:
    lines = [json.loads(l.strip()) for l in f if l.strip()]

for i, obj in enumerate(lines):
    s = json.dumps(obj, ensure_ascii=False)
    if 'sessions_spawn' in s:
        print(f'--- Entry {i} ---')
        print(json.dumps(obj, indent=2, ensure_ascii=False)[:2000])
        print()
" 2>/dev/null

echo ""
echo "=== 6. OnchainOS command outputs (for MORPHO token) ==="
python3 -c "
import json
with open('$MAIN_SESSION', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            s = json.dumps(obj, ensure_ascii=False)
            if 'toolResult' in s and ('onchainos' in s or 'price-info' in s or 'market price' in s):
                msg = obj.get('message', {})
                content = msg.get('content', [])
                for c in content:
                    if isinstance(c, dict) and 'text' in c:
                        print(f\"Tool: {msg.get('toolName', 'unknown')}\")
                        print(f\"Output: {c['text'][:500]}\")
                        print('---')
        except:
            pass
" 2>/dev/null

echo ""
echo "=== 7. Check subagents.model config still active ==="
/home/skottbie/.local/share/pnpm/openclaw config get agents.defaults.subagents 2>/dev/null
