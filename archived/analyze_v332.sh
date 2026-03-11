#!/bin/bash
cd /home/skottbie/.openclaw

echo "=== 1. Latest session files ==="
find sessions/ -name "*.json" -newer agents/pro/agent -type f 2>/dev/null | head -20

echo ""
echo "=== 2. Subagent runs (latest) ==="
cat subagents/runs.json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, list):
    runs = data
elif isinstance(data, dict) and 'runs' in data:
    runs = data['runs']
else:
    runs = [data]
for r in runs[-3:]:
    print(f'runId: {r.get(\"runId\",\"?\")[:12]}')
    print(f'agentId: {r.get(\"agentId\",\"?\")}')
    print(f'model: {r.get(\"model\",\"?\")}')
    print(f'outcome: {r.get(\"outcome\",\"?\")}')
    print(f'endedReason: {r.get(\"endedReason\",\"?\")}')
    print(f'startedAt: {r.get(\"startedAt\",\"?\")}')
    print(f'error: {r.get(\"error\",\"?\")}')
    print('---')
" 2>/dev/null || echo "Failed to parse runs.json"

echo ""
echo "=== 3. Session logs with spawn ==="
find sessions/ -name "*.json" -mmin -60 -type f 2>/dev/null | while read f; do
    if grep -q "spawn\|subagent\|pro" "$f" 2>/dev/null; then
        echo "File: $f"
        python3 -c "
import json, sys
with open('$f') as fh:
    data = json.load(fh)
if isinstance(data, dict):
    for k in ['agentId','model','status','error','endedReason']:
        if k in data:
            print(f'  {k}: {data[k]}')
" 2>/dev/null
    fi
done

echo ""
echo "=== 4. Check Pro agent config ==="
ls -la agents/pro/agent/ 2>/dev/null
echo "---"
echo "agent.json:"
cat agents/pro/agent/agent.json 2>/dev/null || echo "(not found)"
echo ""
echo "config.json:"
cat agents/pro/agent/config.json 2>/dev/null || echo "(not found)"

echo ""
echo "=== 5. Check if Pro agent has auth ==="
ls -la agents/pro/agent/auth* 2>/dev/null || echo "(no auth files)"
echo "auth-profiles.json:"
cat agents/pro/agent/auth-profiles.json 2>/dev/null || echo "(not found)"

echo ""
echo "=== 6. Compare main vs pro agent dirs ==="
echo "--- main ---"
ls -la agents/main/agent/ 2>/dev/null
echo "--- pro ---"
ls -la agents/pro/agent/ 2>/dev/null

echo ""
echo "=== 7. Gateway stderr (recent spawn/pro) ==="
if [ -f /tmp/gw_v332.log ]; then
    grep -i "spawn\|pro\|agent\|error\|fail\|subagent" /tmp/gw_v332.log | tail -40
else
    echo "(no gateway log file)"
fi

echo ""
echo "=== 8. All recent session data ==="
find sessions/ -name "*.json" -mmin -60 -type f 2>/dev/null | sort | while read f; do
    echo "--- $f ---"
    python3 -c "
import json, sys
with open('$f') as fh:
    data = json.load(fh)
if isinstance(data, dict):
    keys = list(data.keys())[:15]
    for k in keys:
        v = data[k]
        if isinstance(v, str) and len(v) > 200:
            v = v[:200] + '...'
        print(f'  {k}: {v}')
" 2>/dev/null
done
