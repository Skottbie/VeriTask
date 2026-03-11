#!/bin/bash
echo "=== Check GitHub Copilot provider thinking support ==="
grep -B5 -A15 'github.copilot.*think\|copilot.*thinking\|thinking.*copilot\|github.*think' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/model-selection-L7RMwsG-.js 2>/dev/null | head -40

echo ""
echo "=== Check how thinking is passed to provider API ==="
grep -B5 -A15 'thinking.*provider\|provider.*thinking\|thinkingLevel.*api\|api.*thinking\|thinking.*request\|request.*thinking' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -80

echo ""
echo "=== Check ACP (Agent Communication Protocol) thinking handling ==="
grep -B3 -A10 'thinking' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/acp-cli-xAOqC5cs.js 2>/dev/null | head -60

echo ""
echo "=== Check github-copilot token/provider module ==="
head -100 /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/github-copilot-token-BQoM_VEX.js 2>/dev/null

echo ""
echo "=== Check if GitHub Copilot uses OpenAI-compatible API ==="
grep -i 'copilot.*openai\|copilot.*api\|copilot.*endpoint\|copilot.*completions\|copilot.*chat' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/github-copilot-token-BQoM_VEX.js 2>/dev/null | head -20
