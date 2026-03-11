#!/bin/bash
# Check OpenClaw source for sessions_spawn model handling
OPENCLAW_BIN=$(which openclaw 2>/dev/null || echo "/home/skottbie/.local/share/pnpm/openclaw")

echo "=== 1. sessions_spawn help (check for model flag) ==="
$OPENCLAW_BIN sessions spawn --help 2>&1 | head -30
echo ""

echo "=== 2. Search for modelApplied in OpenClaw source ==="
OPENCLAW_DIR=$(dirname $(readlink -f "$OPENCLAW_BIN" 2>/dev/null || echo "$OPENCLAW_BIN"))
# Try to find the actual JS source
find /home/skottbie/.local/share/pnpm -name "*.js" -path "*/openclaw*" 2>/dev/null | head -5
echo ""

echo "=== 3. Search for resolveSubagentSpawnModelSelection ==="
GLOBAL_MODULES="/home/skottbie/.local/share/pnpm/global/5/.pnpm"
grep -rl "modelApplied" "$GLOBAL_MODULES" 2>/dev/null | head -5
grep -rl "resolveSubagentSpawnModel" "$GLOBAL_MODULES" 2>/dev/null | head -5
echo ""

echo "=== 4. Try sessions_spawn with explicit --model flag ==="
echo "(just checking if the flag exists)"
$OPENCLAW_BIN sessions spawn --help 2>&1 | grep -i "model"
echo ""

echo "=== 5. Check the actual model request in gateway verbose log ==="
tail -50 /tmp/openclaw_v331.log 2>/dev/null
