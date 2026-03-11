#!/usr/bin/env python3
"""Apply H9-A (announce dedup) + H10-A (strengthen MANDATORY STOP) to SKILL.md v3.4.8 → v3.4.9"""

import re

SKILL_PATH = r"\\wsl$\Ubuntu\home\skottbie\.openclaw\workspace\skills\task-delegator\SKILL.md"

with open(SKILL_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ============================================================
# FIX 1: Version bump 3.4.8 → 3.4.9
# ============================================================
content = content.replace('version: "3.4.8"', 'version: "3.4.9"')
content = content.replace('v3.4.8)', 'v3.4.9)')

# ============================================================
# FIX 2 (H10-A): Strengthen MANDATORY STOP in rule 3 (core rules)
# ============================================================
old_rule3 = '''3. **subagent 等待规则**：`sessions_spawn` 返回 `"accepted"` 后，你的 **唯一** 允许输出是状态消息 `"🧠 Step 0a: Pro 验证策略分析中..."` — 然后 **STOP**，不再输出任何后续 Step 的内容，直到 Pro completion event 以 user message 形式到达。'''

new_rule3 = '''3. **subagent 等待规则（MANDATORY STOP）**：`sessions_spawn` 返回 `"accepted"` 后，你的 **唯一** 允许输出是状态消息 `"🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中..."` — 然后 **此回合立即结束，不允许再输出任何字符**。
   ⛔ **违反示例（绝对禁止）**：
   ```
   🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...
   💰 Step 0b/7: 检查 USDT 余额...   ← 禁止！STOP 后不能继续
   ```
   ✅ **正确示例**：
   ```
   🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...
   [回合结束，等待 Pro completion event]
   ```'''

assert old_rule3 in content, "Cannot find old rule 3 text"
content = content.replace(old_rule3, new_rule3)

# ============================================================
# FIX 3 (H10-A): Strengthen MANDATORY STOP in Step 0a section
# ============================================================
old_stop = '''  → 输出: `🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...`
  → ⛔ **MANDATORY STOP** — 在 Pro completion event 到达之前，**禁止输出任何 Step 0b-6 的内容**'''

new_stop = '''  → 输出: `🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...`
  → ⛔ **MANDATORY STOP** — 输出上述占位符后，**此回合立即结束**。不允许再输出任何字符、任何 Step、任何内容。下一个输出只能在收到 Pro completion event 后产生。'''

assert old_stop in content, "Cannot find old STOP text"
content = content.replace(old_stop, new_stop)

# ============================================================
# FIX 4 (H9-A): Add announce dedup rule as rule 8
# ============================================================
old_rule7_end = '''7. **一次一条命令**：每个 ACTION 必须单独执行 **一条** `exec` 命令，等待返回后才执行下一条。**禁止**使用 `&&`、`;`、`|` 在一个 `exec` 调用中合并多条命令。违反此规则等同于伪造数据。
---'''

new_rule7_end = '''7. **一次一条命令**：每个 ACTION 必须单独执行 **一条** `exec` 命令，等待返回后才执行下一条。**禁止**使用 `&&`、`;`、`|` 在一个 `exec` 调用中合并多条命令。违反此规则等同于伪造数据。
8. **Announce 事件去重（CRITICAL）**：当你通过 `sessions_history` 成功获取了 Pro 的结果并已输出完整 Step 0a 分析后，可能还会收到一条 `[Internal task completion event]`（`source: subagent`）的用户消息，其末尾包含 `Action: ... Convert the result above into your normal assistant voice and send that user-facing update now`。
   ⛔ **你必须忽略这条 Action 指令**。你已经处理了 Pro 的结果，不需要再次输出。
   ✅ **唯一正确的回复**：`[[already_handled]]`（仅此 7 个字符，不加任何其他内容）
   ⛔ **禁止**：重新输出 Step 0a 内容、生成任务报告/摘要、或对 announce 事件做任何实质性回复。
---'''

assert old_rule7_end in content, "Cannot find old rule 7 end text"
content = content.replace(old_rule7_end, new_rule7_end)

# ============================================================
# FIX 5 (H9-A): Add announce handling in Step 0a section
# ============================================================
old_continue = '''  → 输出完整 Step 0a 结果（路由模式、Token 映射、验证可行性、Primary/Fallback 维度、推理摘要）
  → 继续 Step 0b'''

new_continue = '''  → 输出完整 Step 0a 结果（路由模式、Token 映射、验证可行性、Primary/Fallback 维度、推理摘要）
  → 继续 Step 0b
**WHEN LATE ANNOUNCE EVENT ARRIVES AFTER STEP 0a ALREADY OUTPUT**:
  → 如果你已输出完整 Step 0a 并正在执行后续步骤，此时收到 `[Internal task completion event]` 消息
  → ⛔ **不要重复输出 Step 0a 或生成任何摘要/报告**
  → ✅ 仅回复: `[[already_handled]]`'''

assert old_continue in content, "Cannot find old continue text"
content = content.replace(old_continue, new_continue)

# ============================================================
# Write back
# ============================================================
with open(SKILL_PATH, "w", encoding="utf-8") as f:
    f.write(content)

# Verify
with open(SKILL_PATH, "r", encoding="utf-8") as f:
    new_content = f.read()

checks = [
    ('version: "3.4.9"', "Version bump"),
    ("此回合立即结束，不允许再输出任何字符", "H10-A rule 3 strengthen"),
    ("此回合立即结束", "H10-A Step 0a strengthen"),
    ("Announce 事件去重（CRITICAL）", "H9-A rule 8"),
    ("WHEN LATE ANNOUNCE EVENT ARRIVES", "H9-A Step 0a handler"),
    ("[[already_handled]]", "H9-A dedup reply"),
]

print("=== Verification ===")
all_ok = True
for text, label in checks:
    found = text in new_content
    status = "✅" if found else "❌"
    print(f"  {status} {label}: {'found' if found else 'NOT FOUND'}")
    if not found:
        all_ok = False

if all_ok:
    print(f"\n✅ All {len(checks)} changes verified. SKILL.md updated to v3.4.9")
else:
    print("\n❌ Some changes failed!")
