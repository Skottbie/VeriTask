#!/usr/bin/env python3
import sys, json

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except:
        continue
    if obj.get('type') == 'message':
        msg = obj.get('message', {})
        for part in msg.get('content', []):
            if part.get('type') == 'toolCall' and 'swap swap' in part.get('arguments', ''):
                print('=== SWAP CALL ===')
                print(f"name: {part.get('name')}")
                print(f"arguments: {part.get('arguments')}")
                print()
            if part.get('type') == 'toolResult':
                text = part.get('output', '') or part.get('text', '')
                if 'routerResult' in text or ('swap' in text.lower() and 'required arguments' in text.lower()):
                    print('=== SWAP RESULT (full) ===')
                    print(text[:5000])
                    print('=== END ===')
                    print()
