#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo "=== 1. agent command help ==="
openclaw agent --help 2>&1
echo ""

echo "=== 2. models set help ==="
openclaw models set --help 2>&1
echo ""

echo "=== 3. models status (current model) ==="
openclaw models status 2>&1
echo ""

echo "=== 4. Try setting model to Pro ==="
openclaw models set github-copilot/gemini-3.1-pro-preview 2>&1
echo ""

echo "=== 5. Verify model changed ==="
openclaw models status 2>&1
echo ""

echo "=== 6. Switch back to Flash ==="
openclaw models set github-copilot/gemini-3-flash-preview 2>&1
echo ""

echo "=== 7. Verify model back to Flash ==="
openclaw models status 2>&1
