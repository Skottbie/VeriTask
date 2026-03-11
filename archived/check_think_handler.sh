#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== Looking for /think and /thinking command handlers ==="
# Search for command handling that specifically matches /think or /thinking
grep -B5 -A15 '"think".*command\|command.*"think"\|handleThink\|thinkCommand\|think.*handler\|handler.*think' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -80

echo ""
echo "=== Check how /think is parsed from messages ==="
grep -B3 -A10 'parseThink\|extractThink\|think.*parse\|\/think\s\|"\/think"' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -80

echo ""
echo "=== Check session thinking persistence ==="
grep -B3 -A8 'session.*thinking\|thinking.*session\|persist.*think\|thinking.*persist\|session.*thinkingLevel' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -60

echo ""
echo "=== Check if /thinking is a slash command ==="
grep -B2 -A10 '"\/thinking"\|\/thinking\b\|thinking.*slash\|slash.*thinking' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -40
