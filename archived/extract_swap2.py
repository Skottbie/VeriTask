#!/usr/bin/env python3
"""Extract swap-related toolCalls and their results from session JSONL."""
import sys, json

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except:
        continue
    if obj.get('type') != 'message':
        continue
    msg = obj.get('message', {})
    content = msg.get('content', [])
    for i, part in enumerate(content):
        pt = part.get('type', '')
        # toolCall
        if pt == 'toolCall':
            args = part.get('arguments', '')
            if 'swap' in args:
                print(f"=== TOOL CALL: {part.get('name','')} ===")
                print(f"arguments: {args}")
                print()
        # toolResult that follows a swap call
        if pt == 'toolResult':
            # Check if the previous part was a swap call
            if i > 0 and content[i-1].get('type') == 'toolCall' and 'swap' in content[i-1].get('arguments', ''):
                result_text = json.dumps(part, indent=2)
                print(f"=== TOOL RESULT (for {content[i-1].get('name','')}) ===")
                print(result_text[:5000])
                print('=== END ===')
                print()
