#!/bin/bash
MAIN_SESSION="/home/skottbie/.openclaw/agents/main/sessions/409508d6-e72e-4bbd-8e5f-7ea7ac967dcb.jsonl"

python3 -c "
import json

with open('$MAIN_SESSION', 'r') as f:
    lines = f.readlines()

for idx in [7, 9, 11, 13, 15]:
    if idx < len(lines):
        event = json.loads(lines[idx])
        msg = event.get('message', {})
        # Print ALL keys of message
        print(f'===== EVENT [{idx}] =====')
        print(f'msg keys: {list(msg.keys())}')
        # Print raw message (truncated)
        raw = json.dumps(msg, ensure_ascii=False)
        if len(raw) > 2000:
            print(f'raw ({len(raw)} chars): {raw[:800]}...{raw[-400:]}')
        else:
            print(f'raw: {raw}')
        print()
"
