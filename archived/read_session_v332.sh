#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/bin:$PATH"
cd /home/skottbie/.openclaw

SESS="agents/main/sessions/1fc691a0-8dbb-49aa-927b-a66cb54425a5.jsonl"

echo "=== File size ==="
ls -la "$SESS"

echo ""
echo "=== Last 80 lines ==="
tail -80 "$SESS"

echo ""
echo "=== Lines with spawn/subagent/pro ==="
grep -n -i "spawn\|subagent\|sessions_spawn\|agentId.*pro\|\"pro\"" "$SESS" | tail -20
