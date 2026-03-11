#!/bin/bash
cd /home/skottbie/.local/share/pnpm/global/5/.pnpm/openclaw@2026.3.7_*/node_modules/openclaw/dist

# Find copilot API dispatch
echo "=== API dispatch case github-copilot ==="
grep -n 'case.*github.copilot' compact-B247y5Qt.js 2>/dev/null | head -10

echo ""
echo "=== thinkLevel usage in run loop ==="
grep -n 'thinkLevel' compact-B247y5Qt.js 2>/dev/null | head -30

echo ""
echo "=== streamCopilot function ==="
grep -n 'streamCopilot\|copilotStream\|streamGithubCopilot' compact-B247y5Qt.js 2>/dev/null | head -10

echo ""
echo "=== copilot reasoning in payload ==="
grep -n 'copilot.*reason\|reason.*copilot' compact-B247y5Qt.js 2>/dev/null | head -10

echo ""
echo "=== How thinking applied to openai-compatible providers === "
grep -n 'normalizeProxyReasoningPayload\|applyReasoningPayload' compact-B247y5Qt.js 2>/dev/null | head -10
