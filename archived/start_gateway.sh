#!/bin/bash
cd /home/skottbie
nohup /home/skottbie/.local/share/pnpm/openclaw gateway > /home/skottbie/.openclaw/gateway.log 2>&1 &
GW_PID=$!
echo "Gateway started with PID: $GW_PID"
sleep 4
if ps -p $GW_PID > /dev/null 2>&1; then
    echo "Process alive: YES"
else
    echo "Process alive: NO — check gateway.log"
    tail -20 /home/skottbie/.openclaw/gateway.log
    exit 1
fi
HEALTH=$(curl -s http://127.0.0.1:18789/health 2>/dev/null)
echo "Health: $HEALTH"
