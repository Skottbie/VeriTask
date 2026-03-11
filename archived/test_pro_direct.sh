#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo "=== Test: Direct Pro model API call ==="
echo "Requesting github-copilot/gemini-3.1-pro-preview..."
openclaw talk --model github-copilot/gemini-3.1-pro-preview --no-stream "What model are you? Reply with ONLY your model name, nothing else." 2>&1 | head -20
echo ""
echo "=== Compare: Flash model ==="
echo "Requesting github-copilot/gemini-3-flash-preview..."
openclaw talk --model github-copilot/gemini-3-flash-preview --no-stream "What model are you? Reply with ONLY your model name, nothing else." 2>&1 | head -20
