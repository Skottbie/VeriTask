#!/bin/bash
set -e

echo "=== VeriTask v3.3 文件同步 ==="

# 1. 同步 SKILL.md
echo "[1/2] 同步 SKILL.md v3.3.0..."
cp /mnt/d/VeriTask/client_node/skills/task-delegator/SKILL.md /home/skottbie/.openclaw/workspace/task-delegator/SKILL.md
echo "  ✅ SKILL.md 已同步 ($(wc -l < /home/skottbie/.openclaw/workspace/task-delegator/SKILL.md) 行)"

# 2. 验证版本
echo ""
echo "[2/2] 验证同步结果..."
echo "  SKILL.md version: $(grep 'version:' /home/skottbie/.openclaw/workspace/task-delegator/SKILL.md | head -1)"
echo "  SKILL.md 双模型路由: $(grep -c '双模型' /home/skottbie/.openclaw/workspace/task-delegator/SKILL.md) 处引用"
echo "  SKILL.md sessions_spawn: $(grep -c 'sessions_spawn' /home/skottbie/.openclaw/workspace/task-delegator/SKILL.md) 处引用"

echo ""
echo "=== 同步完成 ==="
