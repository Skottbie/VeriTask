#!/bin/bash
echo "=== Test 1 (Lido): 所有工具调用详情 ==="
SESSION1="/home/skottbie/.openclaw/agents/main/sessions/a1b86b8c-de2f-44cf-9e95-a91ee58d1274.jsonl.reset.2026-03-10T07-46-33.491Z"

# 提取所有 toolCall 的名称和参数摘要
grep -o '"type":"toolCall"[^}]*"name":"[^"]*"' "$SESSION1"

echo ""
echo "=== Test 1: agents_list 返回结果 ==="
grep "agents_list" "$SESSION1" | grep -o '"content":\[.*\]' | head -1 | python3 -c "import sys,json; data=sys.stdin.read(); print(data[:500] if data else 'no match')"

echo ""
echo "=== Test 2 (Morpho): sessions_spawn 调用详情 ==="
SESSION2="/home/skottbie/.openclaw/agents/main/sessions/8166c925-47e6-415f-8fc3-ce2cd1343ce4.jsonl"

# 提取 sessions_spawn 调用参数
grep "sessions_spawn" "$SESSION2" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        msg = data.get('message', {})
        content = msg.get('content', [])
        for item in content:
            if isinstance(item, dict):
                if item.get('name') == 'sessions_spawn':
                    print('=== sessions_spawn CALL ===')
                    print(json.dumps(item.get('arguments', {}), indent=2, ensure_ascii=False))
                if item.get('toolName') == 'sessions_spawn':
                    print('=== sessions_spawn RESULT ===')
                    for t in item.get('content', []):
                        print(t.get('text', '')[:500])
    except:
        pass
"

echo ""
echo "=== Test 2: agents_list 返回 ==="
grep "agents_list" "$SESSION2" | grep -o '"text":"[^"]*"' | head -3
