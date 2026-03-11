#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== Check session-level thinking level config ==="
# The /thinking command in chat
grep -o '/thinking[^"]*"\|"thinking"[^,}]*' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | sort -u | head -20

echo ""
echo "=== Check for chat commands that set thinkingLevel ==="
grep -B3 -A3 'command.*thinking\|thinking.*command\|think.*slash\|slash.*think' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -40

echo ""
echo "=== Check for /thinking as Telegram command ==="
grep 'registerCommand\|commandList\|nativeCommands\|slashCommand.*think' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -20

echo ""
echo "=== Check agents.defaults for thinkingLevel key ==="
grep -B2 -A5 'defaults.*thinking\|thinking.*default\|thinkingLevel.*model.*config\|agents.*thinking' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -30

echo ""
echo "=== Try setting thinking level via config ==="
openclaw config set agents.defaults.thinkingLevel high 2>&1 || echo "(failed)"
