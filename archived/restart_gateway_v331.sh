#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:$PATH"
nohup openclaw gateway --port 18789 --verbose > /tmp/openclaw_v331.log 2>&1 &
echo "NEW_PID=$!"
sleep 3
curl -s http://127.0.0.1:18789/health
echo ""
ps aux | grep 'openclaw gateway' | grep -v grep
