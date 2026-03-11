#!/usr/bin/env python3
import json

log_file = "/home/skottbie/.openclaw/agents/main/sessions/3bb570da-a3b4-47b7-815d-db0fc9b7e97d.jsonl.reset.2026-03-10T05-32-14.290Z"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line)
        msg = obj.get('message', {})
        if not isinstance(msg, dict):
            continue
        # Check all string fields for task-delegator
        for key in ['content', 'toolName']:
            val = msg.get(key, '')
            if isinstance(val, str) and 'task-delegator' in val:
                content = msg.get('content', '')
                if isinstance(content, str):
                    print(f"L{i} key={key}: {content[:1000]}")
                elif isinstance(content, list):
                    for p in content:
                        if isinstance(p, dict):
                            t = p.get('text', p.get('input', ''))
                            if isinstance(t, str) and len(t) > 0:
                                print(f"L{i} key={key} part: {str(t)[:500]}")
                            elif isinstance(t, dict):
                                print(f"L{i} key={key} part: {json.dumps(t)[:500]}")
                print("---")
