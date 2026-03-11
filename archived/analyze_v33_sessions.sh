#!/bin/bash
echo "========================================="
echo "=== TEST 1: Lido (a1b86b8c) ==="
echo "========================================="
SESSION1="/home/skottbie/.openclaw/agents/main/sessions/a1b86b8c-de2f-44cf-9e95-a91ee58d1274.jsonl.reset.2026-03-10T07-46-33.491Z"

echo ""
echo "--- sessions_spawn 调用 ---"
grep -i "sessions_spawn\|session.*spawn\|spawn" "$SESSION1" | head -20

echo ""
echo "--- subagent / pro 模型引用 ---"
grep -i "subagent\|gemini.*pro\|3.1-pro\|model.*pro" "$SESSION1" | head -20

echo ""
echo "--- tool_call / function_call 类型 ---"
grep -o '"type":"[^"]*"\|"name":"[^"]*"\|"function":{[^}]*}' "$SESSION1" | sort | uniq -c | sort -rn | head -30

echo ""
echo "========================================="
echo "=== TEST 2: Morpho (8166c925) ==="
echo "========================================="
SESSION2="/home/skottbie/.openclaw/agents/main/sessions/8166c925-47e6-415f-8fc3-ce2cd1343ce4.jsonl"

echo ""
echo "--- sessions_spawn 调用 ---"
grep -i "sessions_spawn\|session.*spawn\|spawn" "$SESSION2" | head -20

echo ""
echo "--- subagent / pro 模型引用 ---"
grep -i "subagent\|gemini.*pro\|3.1-pro\|model.*pro" "$SESSION2" | head -20

echo ""
echo "--- tool_call / function_call 类型 ---"
grep -o '"type":"[^"]*"\|"name":"[^"]*"\|"function":{[^}]*}' "$SESSION2" | sort | uniq -c | sort -rn | head -30

echo ""
echo "========================================="
echo "=== 两个 session 的模型使用 ==="
echo "========================================="
echo "Test 1 model mentions:"
grep -o '"model":"[^"]*"' "$SESSION1" | sort | uniq -c | sort -rn
echo ""
echo "Test 2 model mentions:"
grep -o '"model":"[^"]*"' "$SESSION2" | sort | uniq -c | sort -rn
