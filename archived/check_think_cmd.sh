#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== Check /think command ==="
grep -B5 -A10 '\/think\b' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -60

echo ""
echo "=== Check thinking module ==="
ls -la /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/thinking-BYwvlJ3S.js 2>/dev/null
head -100 /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/thinking-BYwvlJ3S.js 2>/dev/null

echo ""
echo "=== Check native commands list ==="
grep -o '"/[a-z_]*"' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | sort -u | head -50
