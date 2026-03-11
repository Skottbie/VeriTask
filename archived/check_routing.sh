#!/bin/bash
cd /home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_*/node_modules/openclaw/dist

# 1. Check /model command
echo "=== /model command implementation ==="
grep -n 'extractModelDirective\|modelDirective\|model.*command\|command.*model' compact-B247y5Qt.js 2>/dev/null | head -10

# 2. Check model fallback chain
echo ""
echo "=== model fallback config ==="
grep -n 'fallback.*model\|model.*fallback' compact-B247y5Qt.js 2>/dev/null | grep -i 'list\|chain\|resolve\|config' | head -10

# 3. Check sessions.patch API for model switching
echo ""  
echo "=== sessions patch model override ==="
grep -n 'modelOverride\|switchModel\|changeModel\|patchModel' compact-B247y5Qt.js 2>/dev/null | head -10

# 4. Check how subagent spawn uses model
echo ""
echo "=== subagent spawn with model ==="
grep -n 'subagent.*spawn\|spawn.*subagent\|spawnSubagent' compact-B247y5Qt.js 2>/dev/null | head -10

# 5. Models fallback list
echo ""
echo "=== models fallback list CLI ==="
/home/skottbie/.local/share/pnpm/openclaw models fallbacks 2>&1 | head -20
