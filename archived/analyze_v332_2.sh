#!/bin/bash
cd /home/skottbie/.openclaw

echo "=== 1. Pro agent dir existence ==="
ls -laR agents/pro/ 2>/dev/null || echo "Pro agent directory does not exist!"

echo ""
echo "=== 2. Main agent auth ==="
cat agents/main/agent/auth-profiles.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -40

echo ""
echo "=== 3. openclaw.json agents section ==="
python3 -c "
import json
with open('openclaw.json') as f:
    data = json.load(f)
agents = data.get('agents', {})
print(json.dumps(agents, indent=2))
" 2>/dev/null

echo ""
echo "=== 4. subagent runs raw ==="
head -c 3000 subagents/runs.json 2>/dev/null || echo "No runs.json"

echo ""
echo "=== 5. Recent session files (any) ==="
find . -name "*.json" -path "*/sessions/*" -mmin -120 2>/dev/null | sort | tail -10

echo ""
echo "=== 6. All session dirs ==="
ls -la sessions/ 2>/dev/null | head -20

echo ""
echo "=== 7. Gateway process check ==="
ps aux | grep openclaw | grep -v grep
