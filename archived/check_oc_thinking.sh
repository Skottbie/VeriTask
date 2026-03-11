#!/bin/bash
# Check OpenClaw model parameters / thinking level support
echo "=== Full openclaw.json models section ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/openclaw.json') as f:
    config = json.load(f)
models = config.get('agents', {}).get('defaults', {}).get('models', {})
model_primary = config.get('agents', {}).get('defaults', {}).get('model', {})
print('Primary model:', json.dumps(model_primary, indent=2))
print('Models config:', json.dumps(models, indent=2))
"

echo ""
echo "=== Check if /model command exists in OpenClaw ==="
export PATH="$HOME/.local/share/pnpm:$PATH"
openclaw help model 2>&1 || echo "(no help for model command)"

echo ""
echo "=== Check OpenClaw version for features ==="
openclaw --version 2>&1 || echo "(version unknown)"

echo ""
echo "=== Search for thinkingLevel/thinking_config in OpenClaw node_modules ==="
grep -r "thinkingLevel\|thinking_config\|thinking_level\|thinkingBudget" ~/.local/share/pnpm/global/*/node_modules/openclaw*/  2>/dev/null | head -10 || echo "(not found in openclaw modules)"
find ~/.local/share/pnpm -name "openclaw*" -type d 2>/dev/null | head -5
