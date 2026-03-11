#!/bin/bash
# Search for how allowSet is populated in OpenClaw source
OPENCLAW_DIR="/home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_@discordjs+opus@0.10.0_@napi-rs+canvas@0.1.95_@types+express@5.0.6_hono@4.12.2_node-llama-cpp@3.16.2/node_modules/openclaw/dist"

echo "=== 1. Search for allowSet construction ==="
grep -n "allowSet" "$OPENCLAW_DIR/compact-B247y5Qt.js" | head -20

echo ""
echo "=== 2. Get context around allowSet error message ==="
grep -n -B 30 "agentId is not allowed for sessions_spawn" "$OPENCLAW_DIR/compact-B247y5Qt.js" | head -80

echo ""
echo "=== 3. Search for subagents config with allowedAgentIds ==="
grep -n -B 5 -A 5 "allowedAgentIds" "$OPENCLAW_DIR/compact-B247y5Qt.js" | head -60

echo ""
echo "=== 4. Search for maxSpawnDepth config ==="  
grep -n -B 5 -A 5 "maxSpawnDepth\|spawnDepth\|spawn.*depth" "$OPENCLAW_DIR/compact-B247y5Qt.js" | head -60

echo ""
echo "=== 5. Search for subagents config block ==="
grep -n "subagents" "$OPENCLAW_DIR/config-koj5M_EO.js" | head -20

echo ""
echo "=== 6. Get context around subagents config ==="
grep -n -B 2 -A 10 "subagents" "$OPENCLAW_DIR/config-koj5M_EO.js" | head -80

echo ""
echo "=== 7. Check current openclaw.json ==="
cat /home/skottbie/.openclaw/openclaw.json
