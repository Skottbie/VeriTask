#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/share/pnpm/global/5/node_modules/.bin:$HOME/.local/bin:$PATH"

echo "=== 1. Kill existing gateway ==="
pkill -f "openclaw gateway" 2>/dev/null || true
sleep 2

echo "=== 2. Start gateway ==="
nohup openclaw gateway --port 18789 --verbose > /tmp/openclaw_gw_v332_fix2.log 2>&1 &
echo "Gateway PID: $!"
sleep 4

echo "=== 3. Health check ==="
curl -s http://127.0.0.1:18789/health
echo ""

echo "=== 4. Agents list (check for warnings) ==="
openclaw agents list 2>&1

echo ""
echo "=== 5. Skills ==="
openclaw skills status 2>&1 | grep -E "ready|error|loaded" | head -12

echo ""
echo "=== 6. Config summary ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
print('Main agent subagents:', json.dumps(cfg['agents']['list'][0].get('subagents',{}), indent=2))
print('Defaults subagents:', json.dumps(cfg['agents']['defaults']['subagents'], indent=2))
print()
main_sa = cfg['agents']['list'][0].get('subagents',{})
if 'allowAgents' in main_sa and 'pro' in main_sa['allowAgents']:
    print('✅ main agent can spawn pro subagent')
else:
    print('❌ allowAgents not set')
"
