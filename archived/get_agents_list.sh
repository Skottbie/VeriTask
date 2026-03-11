#!/bin/bash
SESSION2="/home/skottbie/.openclaw/agents/main/sessions/8166c925-47e6-415f-8fc3-ce2cd1343ce4.jsonl"
grep 'agents_list' "$SESSION2" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        msg = data.get('message', {})
        content = msg.get('content', [])
        for item in content:
            if isinstance(item, dict) and item.get('toolName') == 'agents_list':
                for t in item.get('content', []):
                    text = t.get('text', '')
                    if text:
                        print(text[:2000])
    except:
        pass
"
