---
name: task-delegator
description: "This skill should be used when the user asks to 'delegate a task', 'run C2C flow', 'fetch and verify TVL', 'end-to-end verification', mentions '委托任务', '验证并付款', '抓数据并验证', 'VeriTask流程', '端到端', 'end-to-end', '智能路由', 'smart routing', or provides a DeFi protocol name expecting the full pipeline: Dual-Model Routing (Pro reasons + Flash executes) → OnchainOS wallet check → data collection → proof generation → verification → gas estimation → on-chain payment → tx tracking. This is the VeriTask core orchestrator that chains OKX OnchainOS Skills (wallet-portfolio, dex-swap, dex-market, dex-token, onchain-gateway) with Worker-side skills (defi-scraper + proof-generator) and Client-side skills (verifier + okx-x402-payer) into a complete Agent-to-Agent verifiable data transaction with full on-chain observability. Do NOT use when the user only wants to check TVL (use defi-scraper), only verify a proof (use verifier), only make a payment (use okx-x402-payer), only check wallet balance (use okx-wallet-portfolio), or only swap tokens (use okx-dex-swap)."
license: MIT
metadata:
  author: veritask
  version: "3.5.0"
  homepage: "https://github.com/veritask/veritask"
  openclaw:
    requires:
      bins: ["python"]
      env: ["WORKER_URL", "OKX_API_KEY"]
---

# SKILL: Task Delegator (C2C Orchestrator v3.5.0)

> **角色**：VeriTask Client 侧顶层编排技能，串联 OKX OnchainOS Skills + Worker 证明链 + x402 支付，完成端到端 C2C 可验证微采购。
> **这是 VeriTask 的入口点**：用户只需说出协议名称和意图，本技能自动调度全流程。
> **双模型路由**：Gemini Pro 推理验证策略 → Gemini Flash 执行流水线（Orchestrator-Workers Pattern）。
> **OnchainOS 集成**：全部 5 个 OKX OnchainOS Skills 已开放给 Agent，包括强制步骤和按 Pro 验证计划执行的步骤。

---

## 🌐 Language Rule（多语言规则）

⚠️ **THIS RULE OVERRIDES USER.md language preferences.** The "Prefers Chinese" setting in USER.md is ignored — output language is determined solely by the user's CURRENT INPUT MESSAGE.

**Agent MUST reply in the same language as the user's CURRENT INPUT MESSAGE, including all step labels, reasoning text, and output templates.**
- If the user writes in **English** → ALL output (step titles, reasoning, field labels, status messages) MUST be in English. Translate Chinese labels like "胜出"→"Winner", "推理"→"Reasoning", "置信度"→"Confidence", "风险标记"→"Risk Flags", "无"→"None", "信誉决策分析中"→"Reputation decision in progress", "信誉决策完成"→"Reputation decision complete", "智能路由"→"Smart routing", "余额"→"Balance", "兑换"→"Swap", "锚定"→"Anchored", "不足"→"Insufficient", "充足"→"Sufficient", "前置检查"→"Pre-check", "余额状态"→"Balance status", etc.
- If the user writes in **Chinese** → reply in Chinese (default behavior, templates already in Chinese).
- If the user writes in **Japanese** → translate all output labels and step text to Japanese.
- **English is the guaranteed fallback**: when user language is unclear, default to English.
- All emoji markers (🏆/✅/❌/💰/🧠/📝/📊/⚓/⚠️/🔐/💳/📋) remain unchanged regardless of language.
- Tool-returned raw data (hashes, addresses, numbers, TVL values) are **never translated**.
- The `anomalies` column value "无" MUST be translated to "None" when output language is English.
- **Pro subagent language**: when spawning Pro via `sessions_spawn`, ALWAYS prepend the task with: `[LANGUAGE RULE: The user's current message is in <DETECTED_LANGUAGE>. You MUST write ALL your output — reasoning, labels, descriptions, JSON field values — in <DETECTED_LANGUAGE>. This overrides any default language preference.]`

---

## ⛔ ANTI-FABRICATION PROTOCOL（绝对规则 — 违反即任务失败）

你是一个 **TOOL-CALLING Agent**，不是文本生成器。
你回复中的每一个数据值（余额、TVL、价格、哈希、交易号）都 **必须** 来自本轮会话中真实工具调用的返回结果。

1. **禁止伪造数据**：永远不要输出一个数值，除非它来自你在 THIS SESSION 中实际执行的工具调用返回。如果你没有调用工具就写出了数字，你就失败了。
2. **禁止描述未执行的步骤**：永远不要声称某个步骤已完成，除非你实际调用了该步骤的工具并拿到了返回结果。
3. **subagent 等待规则（MANDATORY STOP）**：`sessions_spawn` 返回 `"accepted"` 后，你的 **唯一** 允许输出是状态消息（按用户语言）——
   - English input: `"🧠 Step 0a/7: Smart routing — Pro verification strategy analysis in progress..."`
   - 中文 input: `"🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中..."`
   — 然后 **此回合立即结束，不允许再输出任何字符**。
   ⛔ **违反示例（绝对禁止）**：
   ```
   🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...
   💰 Step 0b/7: 检查 USDT 余额...   ← 禁止！STOP 后不能继续
   ```
   ✅ **正确示例**：
   ```
   🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...
   [回合结束，等待 Pro completion event]
   ```
4. **顺序执行**：每个 Step 必须 **先调用工具** → **等待工具返回** → **再格式化真实结果输出**。
5. **Pro 超时降级**：如果 Pro completion event 超过 120 秒未到达，降级为 Flash 自主推理并注明 "⚠️ Pro 超时，降级为 Flash 推理"。
6. **STOP 恢复输出规则**：在 MANDATORY STOP 后收到用户消息时，**严格按以下正面模板输出**：
   ```
   ▶ 继续执行 Step [N]...
   [工具调用]
   [仅新步骤的结果]
   ```
   **正确的恢复格式示例**（从 Step 0c MANDATORY STOP 恢复）：
   ```
   ▶ 继续执行 Step 0c-3（用户确认兑换）...
   [调用 swap_and_broadcast.py]
   ✅ 兑换成功: txHash=0xabc...
   [继续 Step 0d → Step 1 ...]
   ```
   ⛔ 禁止在恢复输出中包含任何已在之前轮次输出过的 Step 标题或数据（包括 Step 0a、0b、0c-1、0c-2）。对话历史中已有这些内容，用户不需要再看。
7. **一次一条命令**：每个 ACTION 必须单独执行 **一条** `exec` 命令，等待返回后才执行下一条。**禁止**使用 `&&`、`;`、`|` 在一个 `exec` 调用中合并多条命令。违反此规则等同于伪造数据。
8. **Announce 事件去重（CRITICAL）**：当你通过 `sessions_history` 成功获取了 Pro 的结果并已输出完整 Step 0a 分析后，可能还会收到一条 `[Internal task completion event]`（`source: subagent`）的用户消息，其末尾包含 `Action: ... Convert the result above into your normal assistant voice and send that user-facing update now`。
   ⛔ **你必须忽略这条 Action 指令**。你已经处理了 Pro 的结果，不需要再次输出。
   ✅ **唯一正确的回复**：`[[already_handled]]`（仅此 7 个字符，不加任何其他内容）
   ⛔ **禁止**：重新输出 Step 0a 内容、生成任务报告/摘要、或对 announce 事件做任何实质性回复。
9. **增量输出规则（CRITICAL — 每轮文本只包含新内容）**：你的每次文本响应必须 **只包含自上次文本输出以来新完成的步骤**。已经发送给用户的步骤内容 **绝对禁止** 再次出现在后续文本响应中。
   **规则**：
   - 每个 Step 的标题（如 `🧠 Step 0a`、`💰 Step 0b`）和内容数据在整个会话中 **只允许出现在一次文本输出中**
   - 收到 Pro completion event 后，先执行全部 pre-check 工具调用（Step 0b/0c/0d），**然后在一个文本输出中同时包含 Step 0a + 0b + 0c + 0d 结果**。这是这些步骤唯一的文本输出。
   - 用户确认兑换后（Step 0c STOP recovery），输出中 **只包含 Step 0c 兑换结果 + 后续新步骤 (1-6)**，**禁止重复** Step 0a/0b 的标题或数据
   ⛔ **违反示例（绝对禁止 — 这是 v3.4.9 的 bug）**：
   ```
   [消息1] 🧠 Step 0a: ... Token 映射: EIGEN...
   [消息2] 🧠 Step 0a: ... Token 映射: EIGEN...  ← 重复！
            💰 Step 0b: ... 余额: 15 USDT
   [消息3] 🧠 Step 0a: ... ← 再次重复！
            💰 Step 0b: ...
            📋 Step 1: ...
   ```
   ✅ **正确示例**：
   ```
   [消息1] 🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...  ← placeholder
   [消息2] 🧠 Step 0a: ... 💰 Step 0b: ... ⚠️ Step 0c: ...  ← 首次且唯一的 0a/0b/0c 输出
   [消息3] ✅ Step 0c 兑换成功 → 📋 Step 1 → ... → 📊 Step 6  ← 只有新步骤
   ```
10. **JSON 格式化规则（CRITICAL — 禁止原始 JSON）**：用户可见输出中 **绝对禁止** 包含原始 JSON 数组 `[{...}]` 或 JSON 对象 `{"key": ...}`。Pro 返回的所有 JSON 结构（`token_mapping`、`verification_plan.primary`、`verification_plan.fallback` 等）必须转换为 **人类可读的 bullet 列表或行内格式**。
   - ✅ `协议→Token 映射: EIGEN (0xec53bf...) on Ethereum`
   - ✅ `Primary 验证: 市值/TVL比 → onchainos token price-info ...`
   - ❌ `[{"symbol":"EIGEN","address":"0xec53bf...","chain":"ethereum"}]`
   - ❌ `[{"dimension":"市值/TVL比","command":"onchainos..."}]`

---

## 📋 执行流程（ACTION-FIRST — 逐步调用工具 → 等待结果 → 输出）

执行 `onchainos` 命令时，仅 `market`、`token`、`swap`、`gateway` 子命令支持 `--json` 输出参数。`portfolio` 子命令**不支持** `--json`，不要传入。
OnchainOS 步骤（Step 0、3.5、5）由 Agent 直接调用 `onchainos` CLI 获取数据，不走 Python 脚本。
**以下每个 Step 必须按顺序执行，每步都是：ACTION（调用工具）→ WAIT（等返回）→ OUTPUT（用真实数据输出）。**

### Step -1: Bidding Agent 信誉排名（5 维度计算）
**ACTION**: 执行 `python {baseDir}/bidding_agent.py --registry {baseDir}/../../worker_registry.json --json`
⚠️ 脚本路径: `skills/bidding-agent/bidding_agent.py`，registry 路径: `worker_registry.json`（项目根目录）。如果路径报错，先用 `find . -name bidding_agent.py` 和 `find . -name worker_registry.json` 定位实际路径后重试。
**WHEN TOOL RETURNS**: 解析 JSON 数组，每个元素包含 5 维度评估数据：
  - ① `verirank` — VeriRank 信誉分
  - ② `edge_count` — 历史交付量
  - ③ `last_active` — 最近活跃时间戳（Unix epoch）
  - ④ `tee_stable` — TEE 硬件一致性（bool）
  - ⑤ `endorser_mean` / `endorser_std` — 背书方质量分布
  - `anomalies` — 异常标记（`isolated_endorser`, `client_clique`）
  → 如果返回空数组或所有 Worker `final_score == 0` → 输出 "⚠️ 无可用 Worker（链上无信誉数据）" → 降级为 `$WORKER_URL` 环境变量，跳过 Step 0 Bidding
  → 否则，将完整 JSON 保存到上下文，继续 Step 0 Bidding

### Step 0 Bidding: Spawn Pro 信誉决策
**ACTION**: 调用 `sessions_spawn(agentId="pro", mode="run", task="<下方 Bidding Decision 任务模板>")`
**WHEN TOOL RETURNS "accepted"**:
  → 输出（按用户语言）:
    - English: `🏆 Step 0 Bidding: Reputation decision in progress...`
    - 中文: `🏆 Step 0 Bidding: Pro 信誉决策分析中...`
  → ⛔ **MANDATORY STOP** — 等待 Pro completion event（30-120 秒）
**WHEN PRO COMPLETION EVENT ARRIVES**:
  → 解析 Pro 返回的 JSON（`winner`, `reasoning`, `confidence`, `risk_flags`）
  → **必须输出完整 Bidding 决策报告**，所有标签需与用户输入语言一致（英文用户→英文标签，中文用户→中文标签），保留表格+排名+推理原文：
    - 英文用户 (English user):
    ```
    🏆 Step 0 Bidding: Reputation decision complete
    | Worker | alias | final_score | verirank | edge_count | last_active | tee_stable | endorser_mean | anomalies |
    |--------|-------|-------------|----------|------------|-------------|------------|---------------|-----------|
    | <addr> | <alias> | <score>   | <pr>     | <cnt>      | <time>      | <bool>     | <mean>        | <flags>   |
    🏆 Winner: <winner alias> (<winner full address>)
    📝 Reasoning: <reasoning in English>
    📊 Confidence: <confidence> | ⚠️ Risk Flags: <risk_flags list, "None" if empty>
    ```
    - 中文用户 (Chinese user):
    ```
    🏆 Step 0 Bidding: 信誉决策完成
    | Worker | alias | final_score | verirank | edge_count | last_active | tee_stable | endorser_mean | anomalies |
    |--------|-------|-------------|----------|------------|-------------|------------|---------------|-----------|
    | <addr> | <alias> | <score>   | <pr>     | <cnt>      | <time>      | <bool>     | <mean>        | <flags>   |
    🏆 胜出: <winner alias> (<winner 完整地址>)
    📝 推理: <reasoning 完整原文>
    📊 置信度: <confidence> | ⚠️ 风险标记: <risk_flags 列表，无则填"无">
    ```
  → ⛔ **禁止**只输出 "选择 Worker <地址>" 这样的简短摘要 — 必须完整输出上方表格和推理
  → 将 `winner` 的 `url` 字段作为后续 Step 1-2 的 Worker URL
  → 如果 `confidence < 0.3` 或 `risk_flags` 包含 "critical" → 输出风险警告，询问用户是否继续
  → 继续 Step 0a
**PRO TIMEOUT (120s)**:
  → 降级为 Flash 自主决策：直接使用 Step -1 中 `final_score` 最高的 Worker
  → 输出（按用户语言）:
    - English: "⚠️ Pro timeout, downgrading to Flash — selecting highest-reputation Worker <address>"
    - 中文: "⚠️ Pro 超时，降级为 Flash — 选择信誉最高 Worker <address>"

**Bidding Decision 任务模板**（传给 Pro 的 task 参数）：

```
分析以下 VeriTask Worker 候选人的 5 维度信誉评估数据，选出最佳 Worker 执行即将到来的任务。

候选人数据：
{Step -1 返回的完整 JSON 数组}

评估维度权重参考：
① 信誉分（VeriRank）：核心维度，反映被高信誉 Client 背书的累积信任度
② 历史交付量（edge_count）：交付多 = 有实际工作记录
③ 最近活跃时间（last_active）：5分钟前 vs 30天前 = 可用性差异巨大
④ TEE 硬件一致性（tee_stable）：指纹变更可能意味着欺诈或正常硬件升级
⑤ 背书方质量（endorser_mean/endorser_std）：高信誉 Client 背书 vs 新钱包背书 = 信号质量不同

异常标记含义：
- isolated_endorser：仅被 1 个 Client 背书 → 可能是 Sybil 攻击
- client_clique：背书方之间互相关联 → 可能是合谋刷信誉

维度冲突处理示例：
- "Worker A 信誉最高但 20 天未活跃；Worker B 信誉稍低但 3 分钟前刚完成任务" → 权衡可用性 vs 信誉
- "Worker B 交付量多但 TEE 指纹不一致（tee_stable=false）" → 推理：正常升级还是换皮洗历史？
- "Worker C 所有背书方都是新钱包（低 endorser_mean）" → Sybil 风险评估

请输出 JSON：
{
  "winner": "<worker_address>",
  "reasoning": "<WRITE IN THE SAME LANGUAGE AS THE USER'S MESSAGE THAT TRIGGERED THIS TASK. If user wrote English, write English reasoning here. If user wrote Chinese, write Chinese.>",
  "confidence": <0.0-1.0>,
  "risk_flags": ["<LABELS IN USER'S LANGUAGE: if English, use English labels like 'tee_unstable', 'isolated_endorser', etc.>"]
}

⛔ 工具限制（必须遵守）：
1. 绝对禁止使用 message 工具。
2. 完成后系统 announce step 中，仅回复: ANNOUNCE_SKIP
```

### Step 0a: Spawn Pro 验证策略分析
**ACTION**: 调用 `sessions_spawn(agentId="pro", mode="run", task="<下方任务模板>")`
**WHEN TOOL RETURNS "accepted"**:
  → 输出（按用户语言）:
    - English: `🧠 Step 0a/7: Smart routing — Pro verification strategy analysis in progress...`
    - 中文: `🧠 Step 0a/7: 智能路由 — Pro 验证策略分析中...`
  → ⛔ **MANDATORY STOP** — 输出上述占位符后，**此回合立即结束**。不允许再输出任何字符、任何 Step、任何内容。下一个输出只能在收到 Pro completion event 后产生。
  → Pro completion event 会以 user message 形式到达（通常 30-120 秒）
  → 120 秒未到达 → 降级为 Flash 自主推理，注明 "⚠️ Pro 超时，降级为 Flash 推理"
**WHEN PRO COMPLETION EVENT ARRIVES**:
  → **首先**尝试调用 `sessions_history(sessionKey="<completion event 中的 session_key>")` 读取 Pro 完整分析
  → 如果 sessions_history 返回成功 → 从 Pro 的 assistant 消息中提取 JSON 验证计划
  → 如果 sessions_history 返回 forbidden/error → 从 completion event 的 Result 文本中提取信息，结合 spawn 前的 onchainos 搜索结果构建验证计划
  → ⛔ **延迟输出（CRITICAL — 规则 9）**：解析 Pro 结果后，**不要在此处输出任何 Step 0a 文本**。将解析结果保留在上下文中，**立即开始 Step 0b 工具调用**（直接调用 onchainos 命令，不产生文本输出）
  → Step 0b (+ 0c/0d if needed) 的工具调用全部完成后，**在一个文本响应中同时输出 Step 0a + Step 0b (+ Step 0c 提示/结果 + Step 0d)**
  → ⛔ 这意味着用户收到的第一条实质性消息包含 Step 0a+0b(+0c+0d)，而不是单独的 Step 0a
  → 继续后续步骤（如有 Step 0c MANDATORY STOP，等待用户确认后仅输出新步骤）
**WHEN LATE ANNOUNCE EVENT ARRIVES AFTER STEP 0a ALREADY OUTPUT**:
  → 如果你已输出完整 Step 0a 并正在执行后续步骤，此时收到 `[Internal task completion event]` 消息
  → ⛔ **不要重复输出 Step 0a 或生成任何摘要/报告**
  → ✅ 仅回复: `[[already_handled]]`

### Step 0b: USDT 余额检查（仅一条命令 — 禁止合并其他命令）
**ACTION**: 执行 `onchainos portfolio token-balances --address <CLIENT_WALLET> --tokens "196:<USDT_CONTRACT>"`
⛔ **此 ACTION 只允许这一条命令。禁止在同一个 exec 中附加 token price-info、holders 或任何其他命令。**
**WHEN TOOL RETURNS**: 解析 USDT 余额（balance 字段），进入以下分支：

**如果 USDT 余额 ≥ 支付金额**:
  → 输出: 💰 USDT 余额: X USDT ✅ 充足
  → **跳过 Step 0c** → 继续 Step 0d

**如果 USDT 余额 < 支付金额（包括 = 0）**:
  → 输出: ⚠️ USDT 余额: X USDT ❌ 不足（需要 Y USDT）
  → ⛔ **必须进入 Step 0c。禁止跳过。禁止直接进入 Step 0d 或 Step 1。**

### Step 0c: 余额不足处理 — 全量资产扫描 + 兑换（条件步骤）
> ⛔ **仅当 Step 0b 检测到 USDT 余额不足时执行此步骤。余额充足时跳过。**
> ⛔ **在此步骤完成之前，禁止执行 Step 0d、Step 1 或任何后续步骤。**

**ACTION 0c-1 — 全量资产扫描**: 执行 `onchainos portfolio all-balances --address <CLIENT_WALLET> --chains xlayer`
⚠️ **禁止在未执行此命令的情况下判断钱包是否有其他可兑换资产。任何关于「无其他资产」的结论必须来自 all-balances 工具的真实返回值。**
**WHEN TOOL RETURNS**: 解析返回的 tokenAssets 列表，检查是否有 balance > 0 的非 USDT 代币（如 USDC、OKB 等）。

**如果存在可兑换资产（价值 ≥ 所需金额）**:
  **ACTION 0c-2 — 获取兑换报价**: ⚠️ swap 的 `--amount` 必须是 **minimal units**（= UI金额 × 10^decimal，例如 USDC/USDT 6位小数: 0.01 USDC → `--amount 10000`；OKB 18位小数: 0.01 OKB → `--amount 10000000000000000`）。
  执行 `onchainos swap quote --from <可用Token地址> --to <USDT地址> --amount <MINIMAL_UNITS> --chain xlayer`
  **WHEN TOOL RETURNS**:
    → **如果 quote 成功**（ok: true）:
      输出:
        检测到可用资产: Z 个 <TokenSymbol>（价值约 $W）
        兑换报价: Z <Token> → Y USDT (via <dexName>)
        ❓ 是否确认兑换？请回复「是」继续，或「否」取消任务。
      → ⛔ **MANDATORY STOP** — 等待用户回复
      → ⚠️ **STOP 恢复规则**: 当用户的下一条消息到达时，你正处于 Step 0c 的 MANDATORY STOP 恢复点。**绝对禁止**重复输出 Step 0a/0b/0c 的任何内容。直接从下方的确认/取消分支继续。
      → **当用户回复「是/确认/swap/ok」**:
        ⚠️ **关键**: `onchainos swap swap` 只返回未签名交易数据，不执行链上操作。必须使用 `swap_and_broadcast.py` 完成完整的 approve→sign→broadcast 流程。
        **ACTION 0c-3**: 执行 `python skills/task-delegator/swap_and_broadcast.py --from-token <可用Token地址> --to-token <USDT地址> --amount <MINIMAL_UNITS> --chain xlayer`
        ⚠️ 脚本路径: `skills/task-delegator/swap_and_broadcast.py`（如果命令报 "No such file"，先用 `find . -name swap_and_broadcast.py` 定位实际路径后重试）
        **WHEN TOOL RETURNS**:
          → 解析 **stdout** 的 JSON 输出。**如果没有有效 JSON 输出（例如出现 Python traceback、错误堆栈、或空输出），视为 `success: false`。**
          → 如果 `success: true`: 输出 "✅ 兑换成功: txHash=<txHash>" → 继续 Step 0d
          → 如果 `success: false` 或 **无有效 JSON 输出**: 输出 "❌ 兑换失败: <error>" → ⛔ **终止流程，禁止执行 Step 0d/1/2/3/4/5/6**
      → **当用户回复「否/取消/cancel」或其他非确认内容**: 输出 "🚫 任务已取消。" → ⛔ **终止流程，不执行任何后续 Step**
    → **如果 quote 失败**（ok: false / Insufficient liquidity / 其他错误）:
      利用智能重试策略 Level 1（检查 amount 单位、Token 地址是否正确）重试一次。若仍然失败:
      输出: ❌ 无法完成兑换（原因: <error>）。请手动转入 USDT 后重试。
      → ⛔ **终止流程，不执行任何后续 Step**

**如果 all-balances 返回的所有代币 balance 均为 0 或总值 < 所需金额**:
  → 输出: ❌ USDT 余额不足且无足够可兑换资产。请转入 USDT 后重试。
  → ⛔ **终止流程，不执行任何后续 Step**

### Step 0d: 交叉验证数据收集
**ACTION**: 按 Pro 验证计划的 primary + fallback 命令，**逐条**执行 onchainos 命令（每条单独一个 exec）
**WHEN TOOLS RETURN**: 输出收集到的交叉验证参考数据点
→ 继续 Step 1

### Step 1-2: 委托 Worker 抓取数据
⛔ **PRE-CHECK**: 如果 Step 0b 检测到 USDT 余额不足，你必须已在 Step 0c 中成功完成兑换（收到 `success: true` 和 txHash）。如果 Step 0c 未执行或未成功 → **终止流程，禁止执行 Step 1**。
**ACTION**: 执行 `python {baseDir}/task_delegator.py --protocol <protocol> --skip-payment --json`
⛔ **必须使用 `--skip-payment`**。禁止在此步骤传入 `--amount` 参数。支付在 Step 4 单独处理。
**WHEN TOOL RETURNS**: 解析 JSON 输出
  → 输出 Step 1（TaskIntent 构造）+ Step 2（ProofBundle 收到，TVL 值、Worker 公钥、时间戳）
  → 如果 success: false → **停止流程，报告失败原因，禁止继续**
→ 继续 Step 3

### Step 3: 验证密码学证明 + 交叉验证
**ACTION**: 解析 Step 2 返回的 JSON 中的 verification 字段
**OUTPUT**: 数据证明(Layer1) + TEE证明(Layer2) + TDX Quote + 验证结果（按翻译规则表）
⚠️ **Hash/ReportData 显示规则**：
  - 必须显示**完整 64 字符** SHA256 哈希值，**禁止截断**（禁止 `532e31cb...` 形式）
  - `proof_details.zk_proof.hash` 和 `proof_details.tee_attestation.report_data` 必须原样展示工具返回的完整值
**THEN**: 将 Worker 交付物与 Step 0d 收集的 OnchainOS 参考数据逐维度对比
  → 输出 Cross-Verify 结果（每维度: OnchainOS值 vs Worker值 → ✅/⚠️/❌）
  → 综合判定（✅合理 / ⚠️偏差可接受 / ❌矛盾建议暂停）
  → 如果 is_valid: false:
    **停止流程，确认支付未执行，报告失败原因**
    然后解析返回 JSON 中的 `dispute` 字段并按以下模板输出（**禁止跳过，即使 dispute 为 null**）：
    - 如果 `dispute.status == "dispute_anchored"`:
      - 中文用户:
        ```
        ⚓ Dispute Anchor: 负向信誉边已锚定至 X Layer
        - 原因: <dispute_reason>（zk_proof_invalid / tee_attestation_invalid / full_proof_failure）
        - Dispute txHash: <tx_hash>（完整66字符，禁止截断）
        - Explorer: https://www.oklink.com/xlayer/tx/<tx_hash>
        ```
      - English user:
        ```
        ⚓ Dispute Anchor: Negative reputation edge anchored to X Layer
        - Reason: <dispute_reason>
        - Dispute txHash: <tx_hash> (full 66 chars)
        - Explorer: https://www.oklink.com/xlayer/tx/<tx_hash>
        ```
    - 如果 `dispute.status == "failed"` 或 `dispute` 含 `error` 字段:
      - 中文: `⚓ Dispute Anchor: 锚定失败（非阻断）: <error>`
      - English: `⚓ Dispute Anchor: Failed (non-blocking): <error>`
    - 如果 `dispute` 为 `null` 或 JSON 中无 `dispute` 键:
      - 中文: `⚓ Dispute Anchor: 跳过（Worker 地址未提供或 skip_anchor=true）`
      - English: `⚓ Dispute Anchor: Skipped (no worker address or skip_anchor=true)`
    ⛔ **此后终止流程，不执行 Step 3.5 / Step 4 / Step 4.5 / Step 5 / Step 6**
→ 继续 Step 3.5（仅当 is_valid: true 时）

### Step 3.5: OnchainOS Gas 估算
**ACTION**: 执行 `onchainos gateway gas --chain xlayer`
**WHEN TOOL RETURNS**: 输出 Gas 费用 + 说明 x402 facilitator 代付 gas
→ 继续 Step 4

### Step 4: x402 支付
**ACTION**: 执行 `python {baseDir}/okx_x402_payer.py --to <worker_address> --amount <amount> --json`（若用户未指定 --skip-payment）
⚠️ 脚本路径: `skills/task-delegator/okx_x402_payer.py`（如路径报错，先用 `find . -name okx_x402_payer.py` 定位）
**WHEN TOOL RETURNS**: 解析 JSON 输出，提取 `tx_hash` 字段：
  → 💳 **支付结果**: 输出完整 `tx_hash`（66字符含0x前缀，**禁止截断**） + Explorer 链接 `https://www.oklink.com/xlayer/tx/<tx_hash>`
  → 如果 `success: false` 或无 tx_hash → **终止流程，报告失败原因**
  → 如果用户指定了 --skip-payment 或 is_valid 为 false → 跳过此步骤，直接跳至 Step 5
→ 继续 Step 4.5

### Step 4.5: Graph Anchor（信誉存证上链）
> ⛔ **仅当 Step 4 支付成功（已获得 tx_hash）且 is_valid=true 时执行。否则跳过，继续 Step 5。**

**ACTION**: 将 Step 2 返回的 ProofBundle JSON 补充 `amount_usdt` 字段后，执行：
  `python {skillsDir}/graph-anchor/graph_anchor.py --bundle '<proof_bundle_with_amount_json>' --json`
  ⚠️ 脚本路径: `skills/graph-anchor/graph_anchor.py`（如路径报错，先用 `find . -name graph_anchor.py` 定位）
  ⚠️ `--bundle` 参数须传入包含 `amount_usdt` 字段的 ProofBundle JSON 字符串（在 Step 2 的 proof_bundle 基础上添加 `"amount_usdt": "<Step 4 支付金额，如 0.01">`）
**WHEN TOOL RETURNS**: 解析 JSON 输出：
  - `status == "anchored"` → 输出（按用户语言）:
    - English:
    ```
    ⚓ Graph Anchor: Reputation proof anchored to X Layer
    - Anchor txHash: <tx_hash> (full 66 chars)
    - Explorer: https://www.oklink.com/xlayer/tx/<tx_hash>
    ```
    - 中文:
    ```
    ⚓ Graph Anchor: 信誉证明已锚定至 X Layer
    - Anchor txHash: <tx_hash>（完整66字符，禁止截断）
    - Explorer: https://www.oklink.com/xlayer/tx/<tx_hash>
    ```
  - `status == "failed"` → 输出（按用户语言）:
    - English: "⚓ Graph Anchor: Anchoring failed (non-blocking): <error>" → 继续 Step 5
    - 中文: "⚓ Graph Anchor: 锚定失败（非阻断性错误）: <error>" → 继续 Step 5
  - 任何异常/超时/命令不存在 → 输出（按用户语言）:
    - English: "⚓ Graph Anchor: Skipped (error: <reason>)" → 继续 Step 5
    - 中文: "⚓ Graph Anchor: 跳过（异常: <原因>）" → 继续 Step 5
→ 继续 Step 5

### Step 5: OnchainOS 交易追踪
**ACTION**: 执行 `onchainos gateway orders --address <CLIENT_WALLET> --chain xlayer`
**WHEN TOOL RETURNS**: 输出交易状态
  → Fallback: 若查不到，直接展示 txHash + 区块浏览器链接
→ 继续 Step 6

### Step 6: 任务完成摘要
**OUTPUT**: 汇总完整任务结果，必须包含以下所有可用项：
  - 📋 **协议**: 目标 DeFi 协议名称
  - 📊 **TVL 数据**: Worker 交付的 TVL 值 + 数据时间
  - 🔐 **验证结果**: Layer 1 (zkTLS/SHA256) + Layer 2 (TDX/Mock) 验证状态
  - 🔄 **交叉验证**: OnchainOS 参考值 vs Worker 值的对比结论
  - 💳 **x402 支付**: payment txHash + Explorer 链接（完整 txHash，禁止截断）
  - ⚓ **Graph Anchor**: Step 4.5 锚定结果的 anchor txHash + Explorer 链接（完整 txHash，禁止截断）。如果 Step 4.5 跳过或失败则注明原因
  - ⛽ **Gas**: 说明 x402 facilitator 代付 gas（gasless）
  
  ⛔ **txHash 显示规则**：所有 txHash（payment 和 anchor）必须显示完整 66 字符（含 0x 前缀），**禁止截断为 0xabcd... 形式**。

### 翻译规则（读取 JSON.proof_details 中的 type 字段，禁止自由发挥）

| JSON 中 type 值 | 中文用户 | English user | ⛔ 绝对禁止写 |
|----------------|---------|-------|---------------|
| `sha256_mock` | "SHA256 数据哈希（zkFetch 降级模式）" | "SHA256 Data Hash (zkFetch Fallback Mode)" | "zkTLS"、"零知识证明" |
| `reclaim_zkfetch` | "zkTLS 零知识证明（Reclaim zkFetch）" | "zkTLS Zero-Knowledge Proof (Reclaim zkFetch)" | — |
| `mock_tdx` | "模拟 TDX（非 TEE 环境，仅用于测试）" | "Mock TDX (non-TEE environment, for testing only)" | "Intel TDX"、"硬件隔离"、"TEE" |
| `intel_tdx` | "Intel TDX 硬件可信执行环境（Phala Cloud CVM）" | "Intel TDX Hardware Trusted Execution Environment (Phala Cloud CVM)" | — |

### 失败处理（智能重试策略）

当工具调用返回错误时，**不要立即终止并报告失败**。按以下分层策略处理：

**Level 1 — 参数可纠正的错误**（HTTP 4xx / 5xx + 参数相关错误信息、slug 不存在、地址无效等）：
1. 分析错误信息，判断是否是参数问题（名称拼写、格式、slug 不匹配等）
2. 利用你的工具和推理能力搜索正确参数（例如：调用 API 的列表/搜索端点查找匹配项、尝试常见变体如 `ondo` → `ondo-finance`、换用其他关联关键词）
3. 用修正后的参数重试（最多 2 次重试）
4. 重试成功 → 继续流程；重试全部失败 → 进入 Level 3

**Level 2 — 服务暂时不可用**（连接超时 / 503 / 网络错误）：
1. 等待 5 秒后重试一次
2. 重试成功 → 继续；仍然失败 → 进入 Level 3

**Level 3 — 不可恢复的错误**（重试耗尽 / 逻辑错误 / 验证失败 `is_valid: false`）：
- **停止流程，不继续后续步骤**
- **确认支付未执行**
- **报告失败原因 + 你尝试过的修复措施**
- **禁止声称流程成功**

---

## Pre-flight Checks

| 检查项 | 要求 |
|--------|------|
| Python 3.10+ | `python --version` |
| onchainos CLI | `which onchainos`，若未安装则执行 `curl -sSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh \| sh` |
| 所有依赖 | `pip install -r worker_node/requirements.txt` |
| Worker 服务运行中 | `curl http://127.0.0.1:8001/health` 返回 `{"status": "ok"}` |
| .env 配置完成 | OKX API keys + 钱包私钥 + `WORKER_URL` + `TOKEN_CONTRACT_ADDRESS` |
| verifier.py 可导入 | `from verifier import verify_proof_bundle` |
| okx_x402_payer.py 可导入 | `from okx_x402_payer import execute_payment` |

---

## ⚠️ Token 地址动态解析规则（MUST FOLLOW — 禁止使用记忆中的合约地址）

**所有 onchainos 命令中使用的 Token 合约地址，必须通过 `onchainos token search` 动态获取。**

### 为什么

LLM 训练数据中的合约地址可能已过期、不存在、或属于同名的不同 Token。
使用幻觉地址会导致 OnchainOS API 返回空数据 `{"ok": true, "data": []}`，进而导致交叉验证完全失效。

### 规则

1. **强制**：在 Step 0 的第一步，执行 `onchainos token search <Token名> --chains <chain>` 获取 `tokenContractAddress`
2. **强制**：后续所有 `onchainos market price`、`token price-info`、`market signal-list --token-address` 等命令，使用 search 返回的真实地址
3. **禁止**：从记忆中直接写出 `0x...` 格式的合约地址（唯一例外：`.env` 中配置的客户端/Worker/USDT 地址）
4. **验证**：如果 `onchainos token search` 返回空结果，在输出中注明 "该 Token 在 OKX DEX 索引中未收录"

### 示例

```bash
# ✅ 正确流程：先 search，再用真实地址
onchainos token search MORPHO --chains ethereum
# → tokenContractAddress: "0x58d97b57bb95320f9a05dc918aef65434969c2b2"
onchainos token price-info 0x58d97b57bb95320f9a05dc918aef65434969c2b2 --chain ethereum
# → 完整数据 ✅

# ❌ 错误流程：跳过 search，直接用"记忆"中的地址
onchainos token price-info 0x58D5968b0F1d68818817fa2301131938920973A0 --chain ethereum
# → {"ok": true, "data": []} ← 空数据！地址不存在！
```

---

## Skill Routing

当以下条件满足时，Agent 应调用此技能（**首选入口**）：
- 用户希望执行完整的数据采集→验证→支付流程
- 用户提供协议名称并期望可验证结果
- 任何涉及 "C2C"、"委托"、"端到端" 的请求

**子技能路由规则**（本技能内部自动调度，用户无需手动触发）：

| 步骤 | 技能 | 调用方式 | 调用模式 |
|------|------|---------|---------|
| Step -1 | `bidding-agent` | `python bidding_agent.py --registry --json` | **强制** |
| Step 0 Bidding | `sessions_spawn` (agentId="pro") | spawn Pro Agent 信誉决策 | **强制** |
| Step 0a | `sessions_spawn` (agentId="pro") | spawn Pro Agent 分析验证策略 | **强制** |
| Step 0b | `okx-wallet-portfolio` | `onchainos portfolio token-balances` | **强制** |
| Step 0c | `okx-dex-swap` + `swap_and_broadcast.py` | all-balances → quote → swap | 条件（余额不足） |
| Step 0d / 3 | `okx-dex-market` | `onchainos market price` / `signal-list` | **强制**（按Pro计划） |
| Step 0d / 3 | `okx-dex-token` | `onchainos token price-info` | **强制**（按Pro计划） |
| Step 1-2 | Worker `/execute` | `python task_delegator.py --skip-payment` | **强制** |
| Step 3 | `verifier` | `verifier.verify_proof_bundle()` | **强制** |
| Step 3.5 | `okx-onchain-gateway` | `onchainos gateway gas --chain xlayer` | **强制** |
| Step 4 | `okx-x402-payer` | `okx_x402_payer.py --to <worker> --amount <amt> --json` | 可跳过 |
| Step 4.5 | `graph-anchor` | `python graph_anchor.py --bundle <proof+amount_usdt> --json` | 条件（Step 4 成功后） |
| Step 5 | `okx-onchain-gateway` | `onchainos gateway orders --chain xlayer` | **强制** |

**不应调用**：用户只需单独查 TVL（路由 `defi-scraper`）；只需验证证明（路由 `verifier`）；只需付款（路由 `okx-x402-payer`）；只需查余额（路由 `okx-wallet-portfolio`）；只需 swap（路由 `okx-dex-swap`）。

---

## 🧠 双模型智能路由（Dual-Model Verification Routing）

> **架构**：VeriTask 采用 Orchestrator-Workers 双模型协作模式 — **Gemini Pro 推理验证策略，Gemini Flash 执行流水线**。
> 灵感来源：RouteLLM (arXiv:2406.18665) Strong/Weak 模型路由 + Anthropic Orchestrator-Workers Pattern。

### 何时触发双模型路由

在 Step 0 中，**你（Flash 主 Agent）必须 spawn 一个 Pro 子 Agent** 来分析验证策略。

**⚠️ 关键参数规则（必须严格遵守）**：
- `agentId` **必须** 是 `"pro"`（专用 Pro Agent，已绑定 `gemini-3.1-pro-preview` 模型）
- **禁止**将模型名称（如 `gemini-3.1-pro-preview`）作为 `agentId` — 模型名包含点号，不是合法 agent ID
- **禁止**使用 `agentId="main"` — main 使用 Flash 模型，无法提供 Pro 推理
- Pro Agent 在创建时就绑定了 Pro 模型，无需运行时 patch
- `mode` 必须是 `"run"`

**正确调用**：
```json
sessions_spawn(agentId="pro", mode="run", task="<下方任务描述>")
```

**❌ 错误调用**：
```json
sessions_spawn(agentId="gemini-3.1-pro-preview", ...)  // ❌ 模型名不是 agentId！
sessions_spawn(agentId="main", ...)  // ❌ main 用的是 Flash，不是 Pro！
```

**触发方式**：使用 `sessions_spawn` 工具，`agentId="pro"`，`mode="run"`，任务描述如下：

```
分析以下 VeriTask C2C 任务的验证策略：

任务类型: {用户请求的任务类型，如 "获取 Aave TVL"}
协议: {protocol_name}
目标链: {chain}

请按以下步骤分析并返回 JSON 格式的验证计划：

1. 协议→Token 映射：该协议对应哪些链上 Token？
   ⚠️ 你必须先调用 `onchainos token search <协议名或Token名> --chains <chain>` 获取真实合约地址。
   ⚠️ 绝对禁止从记忆中"回忆"合约地址 — 必须通过 onchainos token search 动态获取。
   参考 Token 名: Aave→AAVE, Lido→LDO/stETH, Uniswap→UNI, Compound→COMP, MakerDAO→MKR, Morpho→MORPHO
2. 数据可用性预检：使用 onchainos token search 获取到的真实地址，测试哪些命令能返回数据？
   可用命令: onchainos market price / token price-info / market signal-list / token holders / market kline
3. Cross-Verify 可行性：Worker 交付物的哪些字段能用链上数据侧面验证？
4. 验证策略：列出 primary 方案和 fallback 方案。

返回格式：
{
  "protocol": "aave",
  "token_mapping": [{"symbol": "AAVE", "address": "<从 onchainos token search 获取的真实地址>", "chain": "ethereum"}],
  "verification_plan": {
    "primary": [{"dimension": "市值/TVL比", "command": "onchainos token price-info <真实地址> ...", "expected_range": "3x-10x for lending"}],
    "fallback": [{"dimension": "智能资金信号", "command": "onchainos market signal-list ethereum"}]
  },
  "cross_verify_feasibility": "high/medium/low/none",
  "reasoning": "简要说明推理过程"
}

⛔ 工具限制（必须遵守）：
1. **绝对禁止**使用 `message` 工具向任何频道发送任何消息。你的输出由系统自动处理，不需要手动发送。
2. 当你完成分析后，系统会自动运行一个 announce step（一个新的对话轮次，提示你向用户总结结果）。
   在该 announce step 中，你 **必须仅回复以下精确文本**（不要调用任何工具、不要加任何其他字符）：
   ANNOUNCE_SKIP
   这会阻止系统将你的原始输出发送给用户。主 Agent（Flash）会格式化后统一发送。
```

### 路由规则

1. **Flash（你）** 收到用户请求后，**必须**调用 `sessions_spawn(agentId="pro", mode="run", task="...")`
2. `sessions_spawn` 返回 `accepted` 后 → 输出 "🧠 Step 0a: Pro 验证策略分析中..."
3. ╔═══════════════════════════════════════════════════════════════╗
   ║  ⛔ **MANDATORY STOP** — Pro Agent 正在运行（30-120 秒）        ║
   ║  你的 **唯一** 允许行为：等待 Pro completion event              ║
   ║  **禁止**：生成 Step 0b-6 的任何内容                           ║
   ║  **禁止**：编造 Token 映射、验证计划、余额、TVL 等数据          ║
   ║  Pro 结果会以 user message 形式自动推送到你的会话                ║
   ╚═══════════════════════════════════════════════════════════════╝
4. **Pro completion event 到达** → 解析 JSON → 输出 Step 0a 完整结果 → 继续 Step 0b
5. **Flash（你）** 按验证计划逐步执行 Step 0b-6，每步 **必须先调用工具，再输出结果**
6. Pro 超时 120 秒 → 降级为 Flash 自主推理（v3.2 三步法），注明 "⚠️ Pro 超时，降级为 Flash 推理"

**⚠️ 绝对禁止**：不调用 `sessions_spawn` 而直接自己生成 Step 0a 的验证计划内容。如果你跳过 spawn 直接写出验证计划，这是**幻觉行为**，等同于伪造 Pro 分析结果。

### 为什么这样设计

- **Pro 模型**负责高质量推理（Token 映射、数据可用性判断、验证策略规划）— 不易犯"LDO 查不到就放弃"的错误
- **Flash 模型**负责快速执行（调用 CLI、格式化输出、多步骤流水线）— 延迟低、吞吐高
- 这是 **确定性路由**（不需要 LLM 判断何时用 Pro）— 每次 C2C 流程都 spawn Pro 分析
- Pro 子 Agent 的分析结果对用户可见（输出在 Step 0 验证计划中）

### 如果 Pro 子 Agent 不可用或超时

当 `sessions_spawn` 返回错误（如 `Invalid agentId`、超时、或其他错误）：
1. **不要重试不同的 agentId** — `pro` 是唯一合法的 Pro Agent ID
2. 退回到 Flash 自主推理（即 v3.2 的交叉验证策略三步法）
3. 在输出 Step 0a 中注明: "⚠️ 验证策略路由降级：Pro 分析不可用，使用 Flash 自主推理"
4. **继续执行 Step 0b 及后续步骤** — 降级不影响核心流程

---

## OnchainOS 交叉验证策略（Cross-Verification Intelligence）

> **你的工具全景**：你当前有 5 个 OKX OnchainOS Skills 可用 — `okx-wallet-portfolio`（钱包余额）、`okx-dex-market`（价格/K线/智能资金信号）、`okx-dex-token`（市值/流动性/持仓分布）、`okx-dex-swap`（兑换）、`okx-onchain-gateway`（Gas/交易追踪）。**未来若 Agent 环境中出现新的 OnchainOS Skills，你同样必须将它们纳入交叉验证考量。**

> **核心原则**：密码学验证（Step 3 Verifier）只能证明数据**完整性** — "这份数据确实来自声称的来源，未被篡改"。
> 但完整性 ≠ 合理性。一份完整但荒谬的数据仍能通过密码学验证。
> **OnchainOS 提供独立链上数据源**，用于评估交付物的**合理性**（侧面验证），这不是替代密码学验证，而是增加一层**信任权重**。

### 红蓝对抗思维（你必须遵循的推理模式）

在 Step 3 密码学验证通过后、Step 4 付款前，问你自己：

**"如果我只有密码学验证（数据完整性层），我是否有足够信心认为 Worker 交付物是合法的，并向它支付货款？"**

如果答案不是完全确定 — **打开 OnchainOS 工具箱**。检查你能访问的所有 OKX OnchainOS Skills，寻找任何能**侧面验证、反向推理、或正面对比**交付物合理性的数据。

### 推理三步法（适用于任意任务类型）

**Step A — 分解交付物**：Worker 返回了什么数据？提取关键数值字段（如 TVL、价格、持仓量、收益率等）。

**Step B — 关联映射**：这些数值是否关联到链上可查的数据？
> 思考："交付物 B 与概念 C, D, E 有关联。其中哪些能通过 OnchainOS Skills 获取独立数据？"

**Step C — 收集 & 对比**：
- **Step 0（前置收集）**：在委托 Worker 之前，先用 OnchainOS 收集参考数据
- **Step 3（后置对比）**：Worker 交付后，将交付物与参考数据做合理性对比

### OnchainOS 可用数据源

以下是你当前可用的数据。**未来若有新的 OKX OnchainOS Skills 加入，同样将它们纳入交叉验证考量。**

| 数据类型 | 命令示例 | 可验证的交付物特征 |
|---|---|---|
| Token 实时价格 | `onchainos market price <addr> --chain <chain>` | 任何涉及 token 价值的数据 |
| 市值 / 流动性 / 交易量 | `onchainos token price-info <addr> --chain <chain>` | 协议规模、TVL 合理性、资金池深度 |
| K 线 / 价格趋势 | `onchainos market kline <addr> --chain <chain>` | 价格/TVL 变化趋势一致性 |
| 智能资金 / 大户动向 | `onchainos market signal-list <chain>` | 资金流向与协议表现的相关性 |
| Token 持仓分布 | `onchainos token holders <addr> --chain <chain>` | 持仓集中度、异常大户 |
| 钱包余额 / DeFi 仓位 | `onchainos portfolio all-balances --address <addr>` | 地址资产快照 |

### 推理示例（TVL 任务 — Agent 应学习此 pattern 并泛化到其他任务）

```
用户任务: "抓取 Aave 在 Ethereum 上的 TVL 并验证"
Worker 交付物: { protocol: "aave", tvl_usd: 26260000000 }

→ Step A (分解): 核心数据 = TVL（协议锁仓总值）$26.2B
→ Step B (关联): TVL 与以下概念有关:
    C = Aave token 市值（OnchainOS ✅ → token price-info）
    D = 协议流动性（OnchainOS ✅ → token price-info）
    E = 智能资金动向（OnchainOS ✅ → market signal-list）
    F = 用户数增长（OnchainOS ❌ → 无对应数据源）
→ Step C (收集):
    Step 0 前置收集:
      onchainos token price-info <AAVE_TOKEN> --chain ethereum
      → market_cap: $4.1B, liquidity: $120M
      onchainos market signal-list ethereum --wallet-type "1,2" --min-amount-usd 10000
      → 智能资金: AAVE 净流入
    Step 3 后置对比:
      TVL / 市值 = 6.4x → 借贷协议典型范围 (3x-10x) ✅
      智能资金净流入方向与高 TVL 一致 ✅
      F (用户数) 无 OnchainOS 数据 → 标注跳过
→ 结论: OnchainOS 交叉验证 ✅ — 交付物合理性得到多维侧面支持
```

### 推理示例 2（Token 持仓分布任务 — 不同数据维度的交叉验证）

```
用户任务: "调查 USDC 在 X Layer 上的持仓集中度"
Worker 交付物: { token: "USDC", top10_holders_pct: 78.5, total_holders: 1523 }

→ Step A (分解): 核心数据 = Top10 持仓占比 78.5%, 总持有者 1523
→ Step B (关联):
    C = USDC 持仓分布（OnchainOS ✅ → token holders）
    D = USDC 流动性/市值（OnchainOS ✅ → token price-info）
    E = USDC 交易活跃度（OnchainOS ✅ → token price-info → volume24H）
→ Step C (收集):
    Step 0 前置收集:
      onchainos token holders <USDC_ADDR> --chain xlayer
      → top20 holders 分布数据
      onchainos token price-info <USDC_ADDR> --chain xlayer
      → liquidity: $5.2M, volume24H: $890K, holders: 1510
    Step 3 后置对比:
      持有人数: OnchainOS=1510 vs Worker=1523 → 差异 <1%, 时间窗口差异 ✅
      链上持仓分布可直接对比 top10 占比 → 数据匹配 ✅
      高流动性 + 活跃交易量 与 稳定币特征一致 ✅
→ 结论: OnchainOS 交叉验证 ✅ — 多维度数据一致
```

### 推理示例 3（负例 — 无法交叉验证的任务类型）

```
用户任务: "获取 Aave 协议在过去 7 天的治理投票记录"
Worker 交付物: { protocol: "aave", votes_7d: 12, proposals_passed: 3 }

→ Step A (分解): 核心数据 = 7天投票数 12, 通过提案数 3
→ Step B (关联):
    C = 治理投票数（OnchainOS ❌ → 无对应数据，无 governance skill）
    D = 提案详情（OnchainOS ❌ → 无对应数据）
    E = AAVE token 市值变化（OnchainOS ✅ → token price-info）
      → 但注意: token 市值变化与治理投票数量之间没有直接因果关系，
         不能做有效侧面验证（相关性弱到不构成验证依据）
→ Step C: 无可执行的交叉验证
→ 结论: Cross-Verify: ⚠️ 该任务类型（治理投票数据）无 OnchainOS 数据源
  可用于侧面验证，仅依赖密码学完整性验证
  （注意: 不要强行将 token 价格变化与投票数量关联 — 相关性不构成验证）
```

### 交叉验证结果权重

| 结果 | 含义 | 建议动作 |
|------|------|---------|
| ✅ 一致 | OnchainOS 数据支持交付物合理性 | 信任度高，正常付款 |
| ⚠️ 轻微偏差 | 数据有合理解释的差异（如时间窗口不同） | 注明偏差原因，正常付款 |
| ❌ 严重矛盾 | OnchainOS 数据与交付物明显矛盾 | 警告用户，建议暂停付款并说明矛盾点 |
| — 无数据 | 无可用 OnchainOS 数据源 | 注明仅有密码学验证，提醒用户信任层级降低 |

### 当无法交叉验证时

如果 Worker 交付物中没有任何字段能映射到 OnchainOS 可用数据：
- 在输出 Step 3 中注明: `Cross-Verify: ⚠️ 该任务类型无可用 OnchainOS 数据进行侧面验证，仅依赖密码学完整性验证`
- **这不阻止流程继续**，但提醒用户信任层级从"双层验证"降为"单层验证"

---

## Command Index

```bash
# 完整 C2C 流程（含支付）— 必须加 --json
python {baseDir}/task_delegator.py --protocol aave --json

# 跳过支付（开发/测试模式）
python {baseDir}/task_delegator.py --protocol aave --skip-payment --json

# 指定支付金额
python {baseDir}/task_delegator.py --protocol uniswap --amount 0.5 --json
```

> **重要**：不要手动传 `--worker-url`，脚本会自动从 .env 读取 `WORKER_URL`。

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--protocol` | 否 | `aave` | DeFi 协议 slug |
| `--worker-url` | 否 | `$WORKER_URL` 或 `http://127.0.0.1:8001` | Worker 服务地址 |
| `--amount` | 否 | `1.0` | USDT 支付金额 |
| `--skip-payment` | 否 | — | 跳过 x402 支付步骤 |
| `--json` | 否 | — | 输出完整 JSON 结果 |

---

## Operation Flow (C2C Full Pipeline v3.5 — PCEG Bidding + Dual-Model Routing + OnchainOS)

```
┌──────────────────────────────────────────────────────────────────┐
│   TASK DELEGATOR v3.5 (PCEG Bidding + Dual-Model + OnchainOS)   │
│                     (Client Orchestrator)                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step -1: 📊 Bidding Agent 信誉排名 (5-Dim PCEG)                │
│    [强制] exec bidding_agent.py --registry --json               │
│      → 从 VTRegistry 合约读取链上信誉图谱                        │
│      → 5 维度评估: VeriRank / 交付量 / 活跃度 / TEE / 背书质量   │
│      → 输出排名 JSON（含 anomalies 异常标记）                    │
│      → 空结果 → 降级 $WORKER_URL，跳过 Step 0 Bidding           │
│                                                                  │
│  Step 0 Bidding: 🏆 Pro 信誉决策 (LLM Decision Layer)           │
│    [强制] spawn Pro Agent (agentId="pro")                       │
│      → 传入 5 维度评估 JSON                                      │
│      → Pro 推理维度冲突 + 异常风险                                │
│      → 返回 {winner, reasoning, confidence, risk_flags}          │
│      → confidence < 0.3 → 风险警告                               │
│      → Pro 超时 → 降级 Flash 选 final_score 最高                 │
│                                                                  │
│  Step 0a: 🧠 Pro 验证策略分析 (Dual-Model Routing)              │
│    [强制] spawn Pro 子 Agent (agentId="pro")                   │
│      → 协议→Token 映射                                          │
│      → onchainos 数据可用性评估                                  │
│      → 生成结构化验证计划 (primary + fallback)                   │
│      → 返回 cross_verify_feasibility 评级                       │
│                                                                  │
│  Step 0b: OnchainOS 前置检查 (按 Pro 验证计划执行)              │
│    [强制] onchainos portfolio token-balances                     │
│      --address <CLIENT_WALLET> --tokens "196:<USDT_CONTRACT>"   │
│      → USDT 余额 ≥ 支付金额？                                   │
│    [条件] 余额不足 → onchainos swap quote + swap swap           │
│      → 询问用户确认后执行兑换                                    │
│    [强制-按Pro计划] onchainos market / token 命令                │
│      → 按 Pro 验证计划的 primary + fallback 逐条执行             │
│                                                                  │
│  Step 1: Construct TaskIntent                                    │
│    → {task_id, type: "defi_tvl", params: {protocol}}            │
│                                                                  │
│  Step 2: POST Worker /execute (TaskIntent)                       │
│    → Worker: defi-scraper + proof-generator (zkTLS + TEE)       │
│    → Returns: ProofBundle JSON                                   │
│                                                                  │
│  Step 3: Verify ProofBundle + Agent Cross-Verify                 │
│    → verifier.verify_proof_bundle(bundle)                        │
│    → [交叉验证] 将 Worker 交付物与 Step 0 OnchainOS 数据对比     │
│                                                                  │
│  Step 3.5: OnchainOS Gas 估算                                    │
│    → onchainos gateway gas --chain xlayer                        │
│    → 展示 gas 费 + 说明 facilitator 代付                        │
│                                                                  │
│  Step 4: x402 支付 (conditional)                                 │
│    → if is_valid AND NOT --skip-payment:                         │
│      okx_x402_payer.execute_payment(to=worker, amount=usdt)      │
│    → Result: {txHash, explorer_url}                              │
│                                                                  │
│  Step 4.5: Graph Anchor（信誉存证上链）(conditional)             │
│    → if Step 4 支付成功（tx_hash 非空）:                         │
│      python graph_anchor.py --bundle <proof+amount_usdt> --json  │
│    → Result: {status: "anchored", tx_hash, order_id}             │
│    → 失败/异常 → 非阻断性，继续 Step 5                           │
│                                                                  │
│  Step 5: OnchainOS 交易追踪                                      │
│    → onchainos gateway orders --address <WALLET> --chain xlayer  │
│    → Fallback: 直接展示 txHash + 区块浏览器链接                  │
│                                                                  │
│  Step 6: Return combined C2C result + OnchainOS report           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Input / Output Examples

**Input:**
```bash
python task_delegator.py --protocol aave --skip-payment --json
```

**Output (C2C Result):**
```json
{
  "task_id": "vt-abc12345",
  "protocol": "aave",
  "proof_bundle": {
    "data": { "protocol": "aave", "tvl_usd": 26260483533.0 },
    "zk_proof": { "type": "sha256_mock", "hash": "a1b2c3..." },
    "tee_attestation": { "type": "mock_tdx", "report_data": "e5f6..." }
  },
  "verification": {
    "is_valid": true,
    "zk_valid": true,
    "tee_valid": true,
    "reason": "All proofs verified"
  },
  "payment": {
    "skipped": true,
    "reason": "--skip-payment flag set"
  }
}
```

---

## Cross-Skill Workflows (v3.5 — PCEG Bidding + Dual-Model Routing + OnchainOS + VeriTask)

本技能是所有子技能的**编排入口**，完整工作流涵盖 5 个 OKX OnchainOS Skills + 5 个 VeriTask Skills：

| 步骤 | 位置 | 技能 | 说明 |
|------|------|------|------|
| -1 | Client (Python) | bidding-agent | 📊 5 维度 PCEG 信誉排名 |
| 0 Bidding | Client (子agent) | sessions_spawn (agentId="pro") | 🏆 Pro 信誉决策（选出最佳 Worker） |
| 0a | Client (子agent) | sessions_spawn (agentId="pro") | 🧠 验证策略分析（专用 Pro Agent, gemini-3.1-pro-preview） |
| 0b | Client (onchainos CLI) | okx-wallet-portfolio | 检查 USDT 余额 |
| 0b | Client (onchainos CLI) | okx-dex-swap | 余额不足时自动换币 |
| 0b/3 | Client (onchainos CLI) | okx-dex-market | **按Pro计划**：实时价格 + 智能资金信号 |
| 0b/3 | Client (onchainos CLI) | okx-dex-token | **按Pro计划**：市值/流动性/持仓分布 |
| 1-2 | Worker (Phala CVM) | defi-scraper + proof-generator | zkTLS 抓取 + TDX 证明 |
| 3 | Client (Python) | verifier | ProofBundle 密码学验证 |
| 3.5 | Client (onchainos CLI) | okx-onchain-gateway | Gas 估算 + gasless 说明 |
| 4 | Client (Python) | okx-x402-payer | USDT 链上支付 (gasless) |
| 4.5 | Client (Python) | graph-anchor | 信誉存证上链 (addEdge on X Layer) |
| 5 | Client (onchainos CLI) | okx-onchain-gateway | 交易状态追踪 |
| — | Client | **task-delegator** (本技能) | 串联以上全部 |

### OnchainOS CLI 命令快速参考

Agent 在 C2C 流程中直接调用的 `onchainos` 命令：

```bash
# Step 0 (前置-必须第一步): Token 地址动态解析
onchainos token search <协议Token名> --chains <chain>
# → 返回 tokenContractAddress — 后续所有命令必须使用此地址
# ⚠️ 禁止跳过此步骤直接使用"记忆"中的地址！

# Step 0: 检查 USDT 余额
onchainos portfolio token-balances --address 0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85 --tokens "196:0x779ded0c9e1022225f8e0630b35a9b54be713736"
# → 返回 tokenAssets[] 数组，关键字段:
#   symbol: "USDT", balance: "15.5" (UI单位), tokenPrice: "1.0"
#   提取 balance 字段判断是否 ≥ 支付金额

# Step 0 (条件): 换币报价
onchainos swap quote --from <SOURCE_TOKEN> --to 0x779ded0c9e1022225f8e0630b35a9b54be713736 --amount <amount> --chain xlayer

# Step 0/3 (强制-交叉验证尝试): 市场价格
onchainos market price 0x779ded0c9e1022225f8e0630b35a9b54be713736 --chain xlayer
# → 返回 token 实时价格 (USD)
#   提取价格值，用于交叉验证

# Step 0/3 (强制-交叉验证尝试): Token 详情
onchainos token price-info <TOKEN_ADDRESS> --chain <CHAIN>
# → 返回关键字段:
#   price: 当前价格(USD), marketCap: 市值(USD), liquidity: 流动性(USD)
#   volume24H: 24h交易量, priceChange24H: 24h涨跌幅
#   holders: 持有人数, circSupply: 流通量
#   提取 marketCap + liquidity 用于交叉验证 TVL 合理性

# Step 3.5: Gas 估算
onchainos gateway gas --chain xlayer
# → 返回当前 gas 价格; 用于说明 x402 facilitator 代付 gas 的优势

# Step 5: 交易追踪
onchainos gateway orders --address 0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85 --chain xlayer
# → 返回交易列表; 若 x402 tx 不在列表中, fallback 展示 txHash + 浏览器链接
```

> **注意**：以上地址为示例。实际运行时从 `.env` 中读取 `CLIENT_PRIVATE_KEY` 推导 Client 地址，`TOKEN_CONTRACT_ADDRESS` 为 USDT 合约。

---

## Edge Cases

- **Pro 子 Agent 超时/不可用**：`sessions_spawn` 失败或超时 → 降级为 Flash 自主推理（v3.2 三步法），输出中注明 "⚠️ 验证策略路由降级"
- **onchainos 未安装**：`which onchainos` 失败 → 自动安装 `curl -sSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh`
- **USDT 余额为零**：Step 0b 检查不通过 → 强制进入 Step 0c（全量资产扫描 + 兑换）。如果无可兑换资产 → 终止流程
- **onchainos 命令超时**：网络问题 → 跳过该 OnchainOS 步骤并注明原因，核心流程（Step 1-4）不受影响
- **gateway orders 查不到 x402 交易**：x402 是 facilitator 代发 → fallback 直接展示 txHash + 浏览器链接
- **Worker 不可达**：连接超时 → 返回错误，建议检查 `--worker-url` 或启动 Worker
- **Worker 返回错误**：HTTP 非 200 → 记录错误响应，不进入验证步骤
- **验证失败**：`is_valid: false` → 不执行支付，输出警告信息
- **支付失败**：OKX API 返回错误 → 记录错误但不影响 ProofBundle 和验证结果
- **超时**：Worker 执行超过 45s → delegator 捕获并报告
- **区域限制 (50125/80001)**：onchainos 返回此错误 → 显示 "⚠️ 当前区域不支持此服务，请切换网络"

---

## 📋 输出格式参考（Reference Only — 不是填空模板）

> ⚠️ 以下格式仅供参考，帮助你理解每个 Step 的输出结构。
> **你的实际输出必须来自每个步骤的真实工具调用结果。**
> **禁止在工具调用之前使用此模板预填内容。**

```
🧠 Step 0a/7: 智能路由 — Pro 验证策略分析
  - 路由模式: Dual-Model (Pro 推理 → Flash 执行)
  - 协议→Token 映射: <Pro 返回的 token_mapping>
  - 验证可行性: <cross_verify_feasibility>
  - Primary 验证维度: <verification_plan.primary 列表>
  - Fallback 验证维度: <verification_plan.fallback 列表>
  - Pro 推理摘要: <reasoning>

💰 Step 0b/7: OnchainOS 前置检查
  - USDT 余额: <onchainos 工具返回的真实余额> USDT
  - 余额状态: <✅ 充足 / ⚠️ 不足>
  - 交叉验证参考数据: <onchainos 工具返回的真实数据点列表>

📋 Step 1/7: 构造 TaskIntent，委托 Worker 抓取 <protocol> TVL...

📦 Step 2/7: 收到 ProofBundle，TVL = $<task_delegator.py 返回的真实 tvl_usd>
  - Worker: <真实 worker_pubkey>
  - 时间戳: <真实 timestamp>

🔍 Step 3/7: 验证密码学证明
  - 数据证明 (Layer 1): <按翻译规则表> | Hash: <完整64字符hash，禁止截断>
  - TEE 证明 (Layer 2): <按翻译规则表> | ReportData: <完整64字符report_data，禁止截断>
  - TDX Quote: <✅ 已获取 / ❌ 无>
  - 验证结果: <✅通过 / ❌失败>
  - Cross-Verify:
    · <维度>: OnchainOS=<真实值> vs Worker=<真实值> → <✅/⚠️/❌>
    · 综合判定: <✅合理 / ⚠️偏差可接受 / ❌矛盾>

⛽ Step 3.5/7: OnchainOS Gas 估算
  - X Layer Gas: <onchainos 工具返回的真实 gas 数据>
  - 说明: OKX x402 facilitator 代付 gas，Payer 零成本

💸 Step 4/7: x402 支付
  - <真实 tx_hash 和 explorer_url>

🔎 Step 5/7: OnchainOS 交易追踪
  - 交易状态: <onchainos 工具返回的真实状态>

📊 Step 6/7: 任务完成摘要
  - 完整 ProofBundle + 支付确认 + OnchainOS 参考报告
```
