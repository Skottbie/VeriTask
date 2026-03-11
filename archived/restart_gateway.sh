#!/bin/bash
cd /home/skottbie
nohup /home/skottbie/.local/share/pnpm/openclaw gateway --port 18789 --verbose > /tmp/openclaw_gateway.log 2>&1 &
echo $! > /tmp/openclaw_gateway.pid
echo "PID=$(cat /tmp/openclaw_gateway.pid)"
sleep 5
curl -s http://127.0.0.1:18789/health
echo ""
echo "GATEWAY_STARTED"
