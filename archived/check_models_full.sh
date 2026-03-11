#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo "=== Full models list ==="
openclaw models list 2>&1
echo ""
echo "=== Models list with --all flag ==="
openclaw models list --all 2>&1
echo ""
echo "=== Models list with --provider github-copilot ==="
openclaw models list --provider github-copilot 2>&1
