#!/usr/bin/env python3
"""Scan a session log for skill reads and tool calls to understand the Agent flow."""
import sys, json

log_file = sys.argv[1]

with open(log_file) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line.strip())
        t = obj.get('type', '?')
        msg = obj.get('message', {})
        if not isinstance(msg, dict):
            continue
        
        role = msg.get('role', '?')
        tool_name = msg.get('toolName', '')
        content = msg.get('content', '')
        
        if isinstance(content, str):
            content_str = content[:500]
        elif isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, dict):
                    if p.get('type') == 'text':
                        parts.append(p.get('text', '')[:300])
                    elif p.get('type') == 'tool_use':
                        parts.append(f"[TOOL_USE: {p.get('name', '?')}]")
            content_str = ' '.join(parts)[:500]
        else:
            content_str = str(content)[:300]
        
        # Filter: show tool-related and user/assistant messages
        if tool_name:
            # Check if it's a read of SKILL.md
            if 'SKILL.md' in content_str or 'task-delegator' in content_str or 'task_delegator' in content_str:
                print(f"[L{i}] {role} (tool={tool_name}): *** {content_str[:300]}")
            else:
                print(f"[L{i}] {role} (tool={tool_name}): {content_str[:200]}")
        elif role == 'user' and t == 'message':
            # Only show actual user message
            if 'Conversation info' not in content_str and 'session' not in content_str.lower()[:20]:
                print(f"[L{i}] USER: {content_str[:200]}")
        elif role == 'assistant' and t == 'message':
            # Show assistant tool calls and replies
            if '[TOOL_USE' in content_str or '[[reply' in content_str:
                print(f"[L{i}] ASSISTANT: {content_str[:300]}")
