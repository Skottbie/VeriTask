#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== openclaw models set --help ==="
openclaw models set --help 2>&1

echo ""
echo "=== Search for thinking-related config patterns ==="
# Check how thinkingLevel is stored — look for 'thinking' near config/model/set patterns
grep -o '"thinking[A-Za-z]*"[^;}\n]*' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | sort -u | head -30

echo ""
echo "=== Check if thinkingLevel is in model config schema ==="
grep -B2 -A5 'thinkingLevel.*patch\|thinking.*model\|model.*thinking\|setThinking\|thinking.*config\|thinking.*level' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -60

echo ""
echo "=== Try openclaw config set to add thinking level ==="
echo "(dry run - just checking available config keys)"
openclaw config get agents.defaults.models 2>&1
