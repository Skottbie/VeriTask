#!/bin/bash
cd /home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_*/node_modules/openclaw/dist

# Find where streamFn is resolved based on provider/api type
echo "=== resolveStreamFn / selectStreamFn ==="
grep -n 'resolveStreamFn\|selectStreamFn\|buildStreamFn\|getStreamFn\|createStreamFn' compact-B247y5Qt.js 2>/dev/null | head -20

echo ""
echo "=== How api type determines stream function ==="
grep -n 'model\.api\|modelApi' compact-B247y5Qt.js 2>/dev/null | grep -i 'stream\|switch\|case\|copilot' | head -20

echo ""
echo "=== Where reasoning parameter is injected before API call ==="
grep -n 'onPayload\|beforePayload' compact-B247y5Qt.js 2>/dev/null | grep -i 'copilot\|reason\|think' | head -20

echo ""
echo "=== applyExtraParamsToAgent ==="
grep -n 'applyExtraParamsToAgent' compact-B247y5Qt.js 2>/dev/null | head -5

echo ""
echo "=== Copilot-specific wrapper creation ==="
grep -n 'Copilot\|copilot' compact-B247y5Qt.js 2>/dev/null | grep -i 'wrapper\|create\|stream\|fn' | head -20
