#!/bin/bash
cd /home/skottbie/.openclaw
nohup /home/skottbie/.local/share/pnpm/openclaw gateway --port 18789 --verbose > /tmp/openclaw_v33.log 2>&1 &
echo "PID=$!"
sleep 3
echo "Health check:"
curl -s http://127.0.0.1:18789/health
echo ""
echo "Log tail:"
tail -5 /tmp/openclaw_v33.log
