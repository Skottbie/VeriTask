#!/usr/bin/env python3
import json, sys

log_file = "/home/skottbie/.openclaw/agents/main/sessions/3bb570da-a3b4-47b7-815d-db0fc9b7e97d.jsonl.reset.2026-03-10T05-32-14.290Z"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line)
        msg = obj.get('message', {})
        if not isinstance(msg, dict):
            continue
        content = msg.get('content', '')
        if isinstance(content, str) and 'name: task-delegator' in content:
            # Print first 800 chars to see metadata
            print(f"L{i}: {content[:800]}")
            break
