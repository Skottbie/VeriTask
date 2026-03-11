#!/bin/bash
echo "=== resolveThinkingDefault in model-selection ==="
grep -B5 -A20 'resolveThinkingDefault\|thinkingDefault\|defaultThinking' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/model-selection-L7RMwsG-.js 2>/dev/null | head -60

echo ""
echo "=== Check model config schema for thinking ==="
grep -B3 -A8 'thinking.*model\|model.*thinking\|"thinking"\s*:' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/model-selection-L7RMwsG-.js 2>/dev/null | head -40

echo ""
echo "=== Check if models config supports thinkingLevel per-model ==="
grep -B3 -A10 'models.*thinking\|thinking.*models\|modelConfig.*think' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/model-selection-L7RMwsG-.js 2>/dev/null | head -40

echo ""
echo "=== Check config schema for thinking-related fields ==="
grep -B2 -A5 'OpenClawSchema.*think\|schema.*think\|think.*schema' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/model-selection-L7RMwsG-.js 2>/dev/null | head -30
