#!/bin/bash
# Read OpenClaw source for model selection and subagent spawn
BASE="/home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_@discordjs+opus@0.10.0_@napi-rs+canvas@0.1.95_@types+express@5.0.6_hono@4.12.2_node-llama-cpp@3.16.2/node_modules/openclaw/dist"

echo "=== 1. subagent-spawn.d.ts (type defs) ==="
cat "$BASE/plugin-sdk/agents/subagent-spawn.d.ts" 2>/dev/null
echo ""

echo "=== 2. model-selection source (search for key functions) ==="
# Check the smaller model-selection file first
grep -n "resolveSubagentSpawnModel\|modelApplied\|subagents.*model\|applyModel\|changeModel" "$BASE/model-selection-BGlGpPgM.js" 2>/dev/null | head -30
echo ""

echo "=== 3. Extract resolveSubagentSpawnModelSelection context ==="
python3 -c "
import re
with open('$BASE/model-selection-BGlGpPgM.js', 'r') as f:
    content = f.read()
# Find the function and extract ~500 chars around it
matches = [(m.start(), m.end()) for m in re.finditer(r'resolveSubagentSpawnModel', content)]
for start, end in matches[:3]:
    begin = max(0, start - 200)
    finish = min(len(content), end + 500)
    print(f'--- Match at {start} ---')
    print(content[begin:finish])
    print()
" 2>/dev/null

echo ""
echo "=== 4. Check how modelApplied is set ==="
python3 -c "
import re
with open('$BASE/compact-B247y5Qt.js', 'r') as f:
    content = f.read()
matches = [(m.start(), m.end()) for m in re.finditer(r'modelApplied', content)]
for start, end in matches[:3]:
    begin = max(0, start - 300)
    finish = min(len(content), end + 300)
    print(f'--- Match at {start} ---')
    print(content[begin:finish])
    print()
" 2>/dev/null

echo ""
echo "=== 5. Check how github-copilot provider handles model changes ==="
grep -n "github.copilot\|copilot.*model\|changeModel.*copilot\|copilot.*change" "$BASE/model-selection-BGlGpPgM.js" 2>/dev/null | head -20
echo ""

echo "=== 6. Check model-selection for github-copilot specific handling ==="
python3 -c "
import re
with open('$BASE/model-selection-BGlGpPgM.js', 'r') as f:
    content = f.read()
matches = [(m.start(), m.end()) for m in re.finditer(r'github.copilot|copilot', content, re.IGNORECASE)]
for start, end in matches[:5]:
    begin = max(0, start - 200)
    finish = min(len(content), end + 300)
    print(f'--- Match at {start} ---')
    print(content[begin:finish])
    print()
" 2>/dev/null
