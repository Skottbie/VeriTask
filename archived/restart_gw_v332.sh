#!/bin/bash
# Kill old gateway
pkill -f "openclaw gateway" 2>/dev/null
sleep 2
echo "Old gateway killed"

# Start new gateway
cd /home/skottbie/.openclaw
nohup /home/skottbie/.local/share/pnpm/openclaw gateway --port 18789 --verbose > gateway.log 2>&1 &
NEW_PID=$!
echo "New gateway PID: $NEW_PID"

# Wait and health check
sleep 3
HEALTH=$(curl -s http://127.0.0.1:18789/health 2>/dev/null)
echo "Health: $HEALTH"

# List agents
/home/skottbie/.local/share/pnpm/openclaw agents list --json 2>/dev/null
