#!/bin/bash
set -e
cd /home/skottbie/.openclaw

echo "=== Fix: Create Pro agent dir and copy auth ==="

# Create agent dir
mkdir -p agents/pro/agent
echo "Created agents/pro/agent/"

# Copy auth-profiles.json from main
cp agents/main/agent/auth-profiles.json agents/pro/agent/auth-profiles.json
echo "Copied auth-profiles.json"

# Copy models.json from main  
cp agents/main/agent/models.json agents/pro/agent/models.json
echo "Copied models.json"

# Verify
echo ""
echo "=== Pro agent dir now ==="
ls -la agents/pro/agent/

echo ""
echo "=== Auth content ==="
cat agents/pro/agent/auth-profiles.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for p in d.get('profiles',{}):
    print(f'  Profile: {p}')
"

echo ""
echo "=== Now check session for spawn attempt ==="
# Check the main agent's latest session for spawn evidence
SESS_FILE="agents/main/sessions/sessions.json"
if [ -f "$SESS_FILE" ]; then
    python3 -c "
import json
with open('$SESS_FILE') as f:
    data = json.load(f)
sessions = data if isinstance(data, list) else data.get('sessions', [data])
for s in sessions[-2:]:
    sid = str(s.get('id','?'))[:12]
    print(f'Session: {sid}')
    msgs = s.get('messages', s.get('conversation', []))
    if isinstance(msgs, list):
        for m in msgs:
            role = m.get('role','?')
            content = str(m.get('content',''))
            if 'spawn' in content.lower() or 'pro' in content.lower() or 'subagent' in content.lower():
                print(f'  [{role}] ...{content[:300]}...')
    print('---')
" 2>/dev/null || echo "Could not parse sessions"
fi

echo ""
echo "=== Restart gateway ==="
# Kill old
pkill -f openclaw-gateway 2>/dev/null || true
sleep 2

# Restart
cd /home/skottbie/.openclaw
nohup openclaw gateway --port 18789 --verbose > /tmp/gw_v332_fix.log 2>&1 &
GW_PID=$!
echo "Gateway starting, PID=$GW_PID"
sleep 5

# Health
HEALTH=$(curl -s http://127.0.0.1:18789/health 2>/dev/null)
echo "Health: $HEALTH"

# Verify agents
AGENTS=$(curl -s http://127.0.0.1:18789/agents 2>/dev/null)
echo "Agents: $AGENTS"

echo ""
echo "=== DONE ==="
