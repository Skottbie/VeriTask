#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/bin:$PATH"
cd /home/skottbie/.openclaw

echo "=== 1. Full openclaw.json ==="
cat openclaw.json | python3 -m json.tool 2>/dev/null

echo ""
echo "=== 2. Search for spawn/agentId/permission/allow/restrict/security config ==="
grep -i "spawn\|agentId\|permission\|allow\|restrict\|security\|acl\|sandbox\|subagent" openclaw.json 2>/dev/null

echo ""
echo "=== 3. OpenClaw help for sessions_spawn / subagents ==="
openclaw help sessions 2>&1 | head -30
openclaw help subagent 2>&1 | head -30

echo ""
echo "=== 4. OpenClaw config help ==="
openclaw config --help 2>&1 | head -30

echo ""
echo "=== 5. Search onclaw source for 'allowed' or 'agentId is not allowed' ==="
grep -r "agentId is not allowed\|allowed.*sessions_spawn\|sessions_spawn.*allowed\|allowedAgentIds\|spawnAllow" /home/skottbie/.local/share/pnpm/global/5/.pnpm/ 2>/dev/null | head -20

echo ""
echo "=== 6. Search openclaw bin for spawn permission ==="
OPENCLAW_PATH=$(which openclaw)
echo "OpenClaw path: $OPENCLAW_PATH"

# Check if it's a symlink
ls -la "$OPENCLAW_PATH" 2>/dev/null
readlink -f "$OPENCLAW_PATH" 2>/dev/null

echo ""
echo "=== 7. Search OpenClaw config for agent-related settings ==="
openclaw config list 2>&1 | head -50
