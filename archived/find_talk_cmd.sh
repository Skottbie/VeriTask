#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo "=== OpenClaw commands ==="
openclaw --help 2>&1 | grep -E "^\s+\w"
echo ""

echo "=== Try 'ask' or 'chat' command ==="
openclaw ask --help 2>&1 | head -10
echo "---"
openclaw chat --help 2>&1 | head -10
echo "---"
openclaw prompt --help 2>&1 | head -10
echo "---"
openclaw run --help 2>&1 | head -10
