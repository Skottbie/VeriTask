#!/usr/bin/env python3
import json

log_file = "/home/skottbie/.openclaw/agents/main/sessions/3bb570da-a3b4-47b7-815d-db0fc9b7e97d.jsonl.reset.2026-03-10T05-32-14.290Z"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line)
        # Stringify entire obj and search
        s = json.dumps(obj)
        if 'task-delegator' in s or 'task_delegator' in s:
            # Found it - extract relevant content
            msg = obj.get('message', {})
            if isinstance(msg, dict):
                content = msg.get('content', '')
                if isinstance(content, str):
                    print(f"L{i}: {content[:1500]}")
                elif isinstance(content, list):
                    for j, p in enumerate(content):
                        ps = json.dumps(p)
                        if 'task' in ps.lower():
                            print(f"L{i} part[{j}]: {ps[:800]}")
                else:
                    print(f"L{i}: content type={type(content)}")
            else:
                print(f"L{i}: msg type={type(msg)}, raw={s[:500]}")
            print("===")
