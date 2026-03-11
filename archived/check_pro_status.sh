#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/bin:$PATH"

echo "=== Gateway process ==="
ps aux | grep openclaw | grep -v grep

echo ""
echo "=== agents list ==="
openclaw agents list 2>&1

echo ""
echo "=== agents list --json ==="
openclaw agents list --json 2>&1 | head -30

echo ""
echo "=== Pro agent files ==="
ls -la ~/.openclaw/agents/pro/agent/

echo ""
echo "=== Gateway health ==="
curl -s http://127.0.0.1:18789/health 2>&1

echo ""
echo "=== Gateway log (last lines) ==="
tail -30 /tmp/gw_v332_fix.log 2>/dev/null || echo "no log"

echo ""
echo "=== Try models for pro ==="
openclaw models list --agent pro 2>&1 | head -10
