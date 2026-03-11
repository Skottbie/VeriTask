#!/bin/bash
cd /home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_*/node_modules/openclaw/dist

# 1. Find all Gemini 3 models in catalog
echo "=== Gemini 3.x models in catalog ==="
grep -on 'gemini-3[^"]*' compact-B247y5Qt.js 2>/dev/null | sort -u | head -30

echo ""
echo "=== Gemini 3.1 Pro specifically ==="
grep -n 'gemini-3.1-pro' compact-B247y5Qt.js 2>/dev/null | head -10

echo ""
echo "=== Available Copilot model list ==="
grep -n 'github-copilot.*gemini\|gemini.*github-copilot' model-selection-BGlGpPgM.js 2>/dev/null | head -10

echo ""
echo "=== All copilot models in catalog ==="
grep -B2 -A5 '"github-copilot"' model-selection-BGlGpPgM.js 2>/dev/null | grep -i 'gemini\|gpt\|claude\|model\|id' | head -20

echo ""
echo "=== openclaw config get models ==="
openclaw config get agents.defaults.models 2>/dev/null || echo "(not available via CLI)"

echo ""
echo "=== openclaw models list ==="
openclaw models 2>/dev/null | head -40 || echo "(not available via CLI)"
