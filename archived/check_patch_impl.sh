#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo "=== 1. OpenClaw help (commands only) ==="
openclaw --help 2>&1 | grep -A1 "Commands:"
openclaw --help 2>&1 | sed -n '/Commands:/,/^$/p'
echo ""

echo "=== 2. Try models test or models verify ==="
openclaw models --help 2>&1
echo ""

echo "=== 3. Check patchChildSession in source ==="
# Find the actual patchChildSession implementation
BASE="/home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_@discordjs+opus@0.10.0_@napi-rs+canvas@0.1.95_@types+express@5.0.6_hono@4.12.2_node-llama-cpp@3.16.2/node_modules/openclaw/dist"

python3 -c "
import re
with open('$BASE/compact-B247y5Qt.js', 'r') as f:
    content = f.read()

# Find patchChildSession definition
matches = list(re.finditer(r'patchChildSession', content))
if matches:
    m = matches[0]
    start = max(0, m.start() - 500)
    end = min(len(content), m.end() + 1000)
    print(content[start:end])
" 2>/dev/null

echo ""
echo "=== 4. Look for how model is sent to copilot API ==="
# Check how the github-copilot provider sends model
COPILOT_TOKEN_FILE="$BASE/github-copilot-token-PBo8Vdmp.js"
if [ -f "$COPILOT_TOKEN_FILE" ]; then
    grep -n "model\|body\|request\|headers\|completions" "$COPILOT_TOKEN_FILE" | head -30
fi
