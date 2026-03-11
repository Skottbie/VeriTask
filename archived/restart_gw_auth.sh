#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/bin:$PATH"

echo "=== Kill existing gateway ==="
pkill -f openclaw-gateway 2>/dev/null || true
sleep 3

echo "=== Verify killed ==="
ps aux | grep openclaw-gateway | grep -v grep && echo "STILL RUNNING!" || echo "Killed OK"

echo "=== Start new gateway ==="
cd /home/skottbie/.openclaw
nohup openclaw gateway --port 18789 --verbose > /tmp/gw_v332_auth.log 2>&1 &
echo "PID: $!"
sleep 5

echo "=== Health ==="
curl -s http://127.0.0.1:18789/health

echo ""
echo "=== Gateway process ==="
ps aux | grep openclaw-gateway | grep -v grep

echo ""
echo "=== Verify Pro agent auth recognized ==="
openclaw models list --agent pro 2>&1 | head -5
