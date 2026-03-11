#!/bin/bash
# Detailed subagent session analysis
SUBAGENT_SESSION="/home/skottbie/.openclaw/agents/main/sessions/4374f8de-29e3-4e2e-9ea9-e565cf9e5841.jsonl"

echo "=== 1. Full subagent session content (model + usage) ==="
python3 -c "
import json
with open('$SUBAGENT_SESSION', 'r') as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line.strip())
            msg = obj.get('message', {})
            role = msg.get('role', '')
            model = msg.get('model', '')
            provider = msg.get('provider', '')
            api = msg.get('api', '')
            usage = msg.get('usage', {})
            
            # Print summary of each entry
            content_preview = ''
            if msg.get('content'):
                if isinstance(msg['content'], list):
                    for c in msg['content']:
                        if isinstance(c, dict):
                            if c.get('type') == 'text':
                                content_preview = c.get('text', '')[:200]
                            elif c.get('type') == 'toolCall':
                                content_preview = f\"TOOL: {c.get('name', '')} args={str(c.get('arguments', ''))[:200]}\"
                elif isinstance(msg['content'], str):
                    content_preview = msg['content'][:200]
            
            print(f'Entry {i}: role={role}, model={model}, provider={provider}, api={api}')
            if usage:
                print(f'  Usage: input={usage.get(\"input\",0)}, output={usage.get(\"output\",0)}, total={usage.get(\"totalTokens\",0)}')
            print(f'  Content: {content_preview}')
            print()
        except Exception as e:
            print(f'Entry {i}: parse error: {e}')
" 2>/dev/null

echo ""
echo "=== 2. Check if model REQUEST differs from RESPONSE ==="
python3 -c "
import json
with open('$SUBAGENT_SESSION', 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            # Look for any field containing 'pro' or 'gemini-3.1'
            s = json.dumps(obj, ensure_ascii=False)
            if 'pro' in s.lower() or '3.1' in s or '3-1' in s:
                print('PRO REFERENCE FOUND:')
                print(s[:500])
                print('---')
        except:
            pass
" 2>/dev/null

echo ""
echo "=== 3. Check gateway log for model routing details ==="
if [ -f /tmp/openclaw_v331.log ]; then
    echo "Gateway log size: $(wc -c < /tmp/openclaw_v331.log) bytes"
    grep -i 'model\|subagent\|spawn\|gemini.*pro\|3\.1.*pro' /tmp/openclaw_v331.log | tail -20
else
    echo "No gateway log found"
fi

echo ""
echo "=== 4. Check if model was in spawn request details ==="
python3 -c "
import json
# Check main session for the spawn result details
MAIN='/home/skottbie/.openclaw/agents/main/sessions/df328501-c6c3-418c-a9e8-4908f3150c67.jsonl'
with open(MAIN, 'r') as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            s = json.dumps(obj, ensure_ascii=False)
            if 'modelApplied' in s:
                print('modelApplied found:')
                print(json.dumps(obj, indent=2, ensure_ascii=False)[:1500])
                print('---')
        except:
            pass
" 2>/dev/null
