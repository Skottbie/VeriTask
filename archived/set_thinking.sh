#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== Method 1: Try per-model params.thinking ==="
openclaw config set 'agents.defaults.models.github-copilot/gemini-3-flash-preview.params.thinking' high 2>&1

echo ""
echo "=== Method 2: Try global thinkingDefault ==="
openclaw config set 'agents.defaults.thinkingDefault' high 2>&1

echo ""
echo "=== Verify config ==="
openclaw config get agents.defaults 2>&1
