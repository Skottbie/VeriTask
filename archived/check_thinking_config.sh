#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$PATH"

echo "=== openclaw models help ==="
openclaw models --help 2>&1

echo ""
echo "=== openclaw models list ==="
openclaw models list 2>&1

echo ""
echo "=== openclaw config get agents ==="
openclaw config get agents 2>&1

echo ""
echo "=== Check thinkingLevel in full openclaw config ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/openclaw.json') as f:
    config = json.load(f)
# Deep search for anything thinking related
def search(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if 'think' in k.lower():
                print(f'{path}.{k} = {v}')
            search(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            search(v, f'{path}[{i}]')
search(config)
print('(done - no matches means thinkingLevel not yet configured)')
"

echo ""
echo "=== Search for thinkingLevel config options in gateway code ==="
grep -o '"thinkingLevel"[^,]*' /home/skottbie/.local/share/pnpm/global/5/node_modules/openclaw/dist/gateway-cli-B7fBU7gD.js 2>/dev/null | head -20
