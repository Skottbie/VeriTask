#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:$PATH"

echo "=== 1. Available models with full details ==="
openclaw models list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data:
    name = m.get('id', m.get('name', ''))
    if 'pro' in name.lower() or 'flash' in name.lower():
        print(json.dumps(m, indent=2, ensure_ascii=False))
        print('---')
" 2>/dev/null || echo "JSON parse failed, trying text:"
openclaw models list 2>/dev/null | grep -i "pro\|flash"

echo ""
echo "=== 2. Test model switch command ==="
openclaw model --help 2>&1 | head -15
echo ""

echo "=== 3. Current model ==="
openclaw model 2>&1
echo ""

echo "=== 4. Try setting model to Pro and check ==="
openclaw model gemini-3.1-pro-preview 2>&1
echo "---"
openclaw model 2>&1
echo "---"
# Switch back to Flash
openclaw model gemini-3-flash-preview 2>&1
echo ""

echo "=== 5. Check if patchChildSession actually changes model in session configs ==="
# Look at the subagent session config for model info
python3 -c "
import json
with open('/home/skottbie/.openclaw/agents/main/sessions/4374f8de-29e3-4e2e-9ea9-e565cf9e5841.jsonl', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            t = obj.get('type', '')
            if t in ('model_change', 'custom', 'session', 'thinking_level_change'):
                print(json.dumps(obj, indent=2, ensure_ascii=False))
                print('---')
        except:
            pass
" 2>/dev/null

echo ""
echo "=== 6. Check if there's a model_change to Pro after initial Flash ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/agents/main/sessions/4374f8de-29e3-4e2e-9ea9-e565cf9e5841.jsonl', 'r') as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line.strip())
            if 'model' in json.dumps(obj) and obj.get('type') != 'message':
                print(f'Entry {i}: type={obj.get(\"type\")}, data={json.dumps(obj, ensure_ascii=False)[:500]}')
        except:
            pass
" 2>/dev/null
