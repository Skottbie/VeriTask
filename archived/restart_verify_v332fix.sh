#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/share/pnpm/global/5/node_modules/.bin:$HOME/.local/bin:$PATH"

echo "=== 1. Kill existing gateway ==="
pkill -f "openclaw gateway" 2>/dev/null || true
sleep 2

echo ""
echo "=== 2. Start gateway ==="
nohup openclaw gateway --port 18789 --verbose > /tmp/openclaw_gw_v332_fix.log 2>&1 &
GW_PID=$!
echo "Gateway PID: $GW_PID"
sleep 4

echo ""
echo "=== 3. Health check ==="
curl -s http://127.0.0.1:18789/health

echo ""
echo ""
echo "=== 4. Verify agents list ==="
openclaw agents list 2>/dev/null

echo ""
echo "=== 5. Check skills status ==="
openclaw skills status 2>/dev/null | head -15

echo ""
echo "=== 6. Verify allowAgents in config ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/openclaw.json', 'r') as f:
    cfg = json.load(f)
sa = cfg['agents']['defaults']['subagents']
print('subagents config:')
print(json.dumps(sa, indent=2))
print()
if 'allowAgents' in sa and 'pro' in sa['allowAgents']:
    print('✅ allowAgents contains \"pro\" - Flash can now spawn Pro subagent!')
else:
    print('❌ allowAgents NOT configured correctly!')
"

echo ""
echo "=== DONE ==="
