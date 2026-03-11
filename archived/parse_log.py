#!/usr/bin/env python3
import sys, json

log_file = "/home/skottbie/.openclaw/agents/main/sessions/5b621d08-c38a-4f1a-b3b8-fb6ba3e1e80e.jsonl"

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line.strip())
        role = obj.get('role', '?')
        ts = obj.get('ts', '')
        if role == 'tool_call':
            tool = obj.get('tool', '?')
            args_str = json.dumps(obj.get('args', {}))[:300]
            print(f'[L{i}] [{ts}] TOOL_CALL: {tool} | args: {args_str}')
        elif role == 'tool_result':
            tool = obj.get('tool', '?')
            out = str(obj.get('output', ''))[:400]
            print(f'[L{i}] [{ts}] TOOL_RESULT: {tool} | output: {out}')
        elif role == 'assistant':
            text = str(obj.get('text', ''))[:400]
            print(f'[L{i}] [{ts}] ASSISTANT: {text}')
        elif role == 'user':
            text = str(obj.get('text', ''))[:300]
            print(f'[L{i}] [{ts}] USER: {text}')
        else:
            keys = list(obj.keys())
            print(f'[L{i}] [{ts}] {role}: keys={keys}')
