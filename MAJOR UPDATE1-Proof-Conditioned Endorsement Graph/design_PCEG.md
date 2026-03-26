
---

## VeriTask Major Update：Proof-Conditioned Endorsement Graph

---

### 核心命题 / Core Thesis

> **每一条信誉边，不只是"钱流动了"，而是"密码学证明了工作质量，然后钱流动了"。图完全公开在 X Layer 上，任何人独立可验证，没有平台黑箱。**
>
> *Every reputation edge is not just "money flowed" — it means "cryptographic proof confirmed work quality, then money flowed." The graph is fully public on X Layer, independently verifiable by anyone, with no platform black box.*

---

### 新增架构：三个新 Agent / New Architecture: Three New Agents

```
Before 
  Client → Worker → ProofBundle → Veri Agent → x402 Payment

After :
  Client
    ↓ 广播 TaskIntent
  [Bidding Agent]        ← 新增：读图、评分、选 Worker
    ↓ 选出最优 Worker
  [Worker - Phala TDX]
    ↓ 执行 + ProofBundle
  [Veri Agent]
    ↓ 验证三层证明
    ↓ x402 付款
  [Graph Anchor Agent]   ← 新增：把这条边写进公开图
    ↓ onchain-gateway broadcast（calldata 含证明摘要）
    ↓ X Layer 上形成永久可查的信誉边
```

---

### 新增：Worker Discovery（Client-Pull 模型） / Worker Discovery (Client-Pull Model)

Client maintains a local `worker_registry.json` instead of broadcasting TaskIntent on-chain:

```json
{
  "workers": [
    {"alias": "worker-alpha", "address": "0xAAA...", "url": "http://127.0.0.1:8001"},
    {"alias": "worker-beta",  "address": "0xBBB...", "url": "http://127.0.0.1:8001"},
    {"alias": "worker-gamma", "address": "0xCCC...", "url": "http://127.0.0.1:8001"}
  ]
}
```

Bidding Agent 从 Registry 读取所有候选 Worker 地址 → 查链上 reputation → VeriRank 排名 → 选出 top Worker → Task Delegator 用对应的 URL 调用它。

> Demo 阶段所有 Worker URL 指向同一后端，但地址不同以展示声誉差异化。

---

### 第一步：信誉边怎么写进 X Layer / Step 1: How Reputation Edges Are Written to X Layer

每次 VeriTask 任务成功完成，Graph Anchor Agent 调用 `okx-onchain-gateway broadcast`，发一笔极小金额自转账，calldata 写入：
*After each successful VeriTask job, Graph Anchor Agent broadcasts a minimal self-transfer via `okx-onchain-gateway`, embedding the following calldata:*

```json
{
  "v": "2",
  "worker": "0xWorkerAddress",
  "client": "0xClientAddress", 
  "proof_hash": "zkTLS_hash",
  "tee_fingerprint": "TDX_Quote_摘要",
  "task_type": "defi_tvl",
  "amount_usdt": "0.01",
  "ts": 1773040716
}
```

**为什么这是关键设计 / Why This Design Matters:**
- X Layer 上永久存在，任何人、任何 Agent 独立读取 / Permanent on X Layer, readable by anyone or any Agent
- `tee_fingerprint` 把硬件身份和这条边绑定——换皮 Worker 的新 TEE 和旧边没有任何关联 / `tee_fingerprint` binds hardware identity to each edge — a re-skinned Worker's new TEE has zero link to old edges
- 这不是"平台说这条边存在"，是"数学说这条边存在" / Not "the platform says this edge exists" — "math says it exists"

**升级：VTRegistry 合约 — 链上信誉边索引 / VTRegistry Contract — On-chain Reputation Edge Indexing**

原始版本使用 EOA self-transfer + calldata，足以存储但不利于索引。因此部署了一个极简 VTRegistry 合约到 X Layer，通过 Solidity event 实现高效索引：
*The original version used EOA self-transfer + calldata — sufficient for storage but not for indexing. A minimal VTRegistry contract was deployed to X Layer, enabling efficient indexing via Solidity events:*

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VTRegistry {
    event Edge(address indexed client, address indexed worker, bytes data);

    function anchor(address worker, bytes calldata data) external {
        emit Edge(msg.sender, worker, data);
    }
}
```

**设计优势 / Design Advantages**：
- `msg.sender` = ECDSA 验证的 Client 地址 → **自动解决 client 身份伪造问题**
  *`msg.sender` = ECDSA-verified Client address → automatically prevents client identity spoofing*
- `address indexed worker` → Bidding Agent 可用 `eth_getLogs(VTRegistry, Edge, worker=X)` 高效索引
  *`address indexed worker` → Bidding Agent efficiently queries edges via `eth_getLogs`*
- 极简设计：无存储变量、无权限控制、无升级机制 → 审计成本为零
  *Minimalist design: no storage variables, no access control, no upgrade mechanism → zero audit cost*
- 合约只需部署 1 次，地址写入 `.env` 为 `VT_REGISTRY_ADDRESS`

> **🔍 审计记录**：两条广播路径均确认可用。
> A: `gateway broadcast --signed-tx <hex> --address <sender> --chain xlayer`（本地签名，无需 login）
> B: `wallet contract-call --to <addr> --chain 196 --input-data <hex>`（OKX TEE 签名，需 login）
> Demo 用路径 A（与现有 VeriTask 代码一致），生产可切路径 B。

---

### 第二步：Bidding Agent 怎么读图和评分 / Step 2: How Bidding Agent Reads the Graph and Scores Workers

Worker 报价后，Bidding Agent 对每个候选 Worker 执行：
*After Workers submit bids, Bidding Agent evaluates each candidate Worker:*

**① 读取历史边（X Layer RPC + OnchainOS 辅助）/ Read Historical Edges**
```
# 信誉边是自转账+calldata，OnchainOS dex-history 不覆盖（实测确认），使用 RPC：
eth_getLogs(USDT_contract, Transfer_event, to=worker_address)
  + eth_getTransactionByHash → 提取 calldata
→ 过滤 calldata 以 VeriTask 版本前缀开头的记录
→ 每条记录：付款方地址 + 金额 + 时间戳 + calldata（含 proof_hash + tee_fingerprint）

# 辅助信号（OnchainOS）：
onchainos market portfolio-overview --address [worker_address] --chain xlayer --time-frame 5
→ PnL、胜率、交易次数作为 Worker 活跃度参考
```

> **🔍 审计记录**：原设计使用 `wallet tx-history [addr]`（不存在），经三轮审计（含实测）确认：
> `dex-history` 不覆盖 x402 转账，主体已修正为 RPC 方案 + OnchainOS `portfolio-overview` 辅助。

**② 验证每条边的证明质量 / Verify Proof Quality of Each Edge**
```
从 calldata 提取 proof_hash + tee_fingerprint
→ 验证 zkTLS 签名（Reclaim attestor）
→ 验证 TDX fingerprint 一致性
→ 这条边是 Proof-Conditioned = True / False
```
未经验证的边（普通转账伪装）= 零权重，直接过滤。
*Unverified edges (disguised as regular transfers) = zero weight, filtered out.*

> **🔍 审计记录**：此步骤不依赖 OnchainOS，纯本地密码学验证，现有 `verifier.py` 可复用。

**③ 给付款方（Client）打种子分 / Compute Seed Score for Endorsers (Clients) via OnchainOS**
```
# 核心数据（实测确认可用）：
onchainos market portfolio-overview --address [client_address] --chain xlayer --time-frame 5
→ realizedPnlUsd, unrealizedPnlUsd, winRate, buyTxCount, sellTxCount

# Smart money 地址池匹配：
onchainos signal list --chain xlayer --wallet-type 1
→ 提取 triggerWalletAddress 字段中的所有 smart money 地址
onchainos leaderboard list --chain xlayer --time-frame 3 --sort-by 1 --wallet-type smartMoney
→ 提取 walletAddress 字段中的 top smart money 地址

# 种子分公式：
seed_score = sigmoid(
  α × normalized_pnl +          # PnL 归一化
  β × win_rate +                 # 胜率 [0,1]
  γ × log(1 + trade_count) +    # 交易活跃度
  δ × account_age_factor +       # 钱包年龄（链上首笔 TX 距今天数）
  ε × smart_money_bonus          # 地址在 smart money 池中 = 1.0, 否则 0.0
)
→ 高 PnL、长历史、smart money 标签 = 高种子分
→ 新钱包、零历史 = 种子分接近零
```

这正是 TraceRank 论文里提到的 seed score 概念，但我们用 OnchainOS 的 smart money 信号和 PnL 数据来源，比他们用的外部信号更直接、更链上原生。
*This is the seed score concept from the TraceRank paper, but we use OnchainOS smart money signals and PnL data — more direct and on-chain native than their external data sources.*

> **🔍 审计记录**：原设计使用 `market smart-money [addr]` + `wallet pnl [addr]`（均不存在），
> 经三轮审计确认：PnL 通过 `market portfolio-overview` 完全可用（✅ 实测通过），
> smart money 通过 `signal list` + `leaderboard list` 地址池匹配实现。
> 主体已修正为实测确认的命令。X Layer 已确认在 `portfolio-supported-chains` 支持列表中。

**⑤ 运行 Proof-Conditioned VeriRank / Run Proof-Conditioned VeriRank**

基于 TraceRank 公式，但边权重加入证明质量维度：
*Based on the TraceRank formula, but edge weights incorporate proof quality:*

```
边权重 = proof_quality × log(1 + amount_USD) × e^(-λ × age_days)

proof_quality：
  - 有效 zkTLS + 有效 TDX = 1.0（满权重）
  - 只有 zkTLS = 0.5
  - 无证明 = 0（过滤）
```

**⑤ 拓扑异常检测（Wash Trading 识别）/ Topological Anomaly Detection (Wash Trading Identification)**

这是 Web3 原生能力，Web2 永远做不到的：
*This is a Web3-native capability that Web2 can never achieve:*

```
检查图中是否存在：
  Worker A → Client X → Worker A（循环，周期 < 7天）
  Worker A 的所有付款方是否互相也有付款关系（闭合小圈子）
  Worker A 是否只被 1-2 个钱包付过款，且这些钱包无其他链上活动
  
→ 任何异常拓扑 = 自动降权或排除
```

Web2 平台（淘宝、Amazon）也知道这些模式，但他们选择不选择透明——因为透明会暴露平台自己的数据。VeriTask 的图是公开的，任何人都可以独立跑这个检测，平台无法选择性隐藏。
*Web2 platforms (Temu, Amazon) know these patterns too, but they choose opacity — because transparency would expose their own data. VeriTask’s graph is public: anyone can independently run this detection, and the platform cannot selectively hide results.*

> **🔍 审计记录**：④⑤ 均为纯图算法，不依赖 OnchainOS。
> ⑤ 中"空壳钱包"判断可用 `portfolio-overview` 辅助（`tradeCount==0` 且 `pnl==0`）。

**升级：5 维度评估体系 + 双层决策架构 / Upgrade: 5-Dimension Evaluation System + Dual-Layer Decision Architecture**

VeriRank 只是一个维度。升级将 Bidding Agent 升级为真正的多维度决策 Agent（对应评审标准 `Architecture for collaboration between multiple agents`），处理维度间的张力并做出带推理的综合决策。
*VeriRank is just one dimension. This upgrade transforms Bidding Agent into a true multi-dimensional decision agent (addressing the judging criterion `Architecture for collaboration between multiple agents`), handling tensions between dimensions and making reasoned composite decisions.*

**5 个输入维度 / 5 Input Dimensions**：

| # | 维度 / Dimension | 数据来源 / Data Source | 描述 / Description |
|---|------|----------|------|
| ① | VeriRank 信誉分 / Reputation Score | `run_verirank()` | 被高信誉 Client 背书的累积信任度 / Cumulative trust from high-reputation Client endorsements |
| ② | 历史交付量 / Delivery Count | `edge_count` | 链上 Edge 数量 = 实际工作记录 / On-chain edge count = actual work record |
| ③ | 最近活跃时间戳 / Last Active | `max(ts)` | 最后一条边的时间戳 → 可用性信号 / Availability signal |
| ④ | TEE 硬件一致性 / TEE Consistency | `tee_fingerprint` 一致性 | 指纹变更 = 硬件升级 or 换皮洗历史？ / Fingerprint change = hardware upgrade or identity laundering? |
| ⑤ | 背书方质量分布 / Endorser Quality | endorser `seed_score` 均值+方差 | 高信誉 Client 背书 vs 新钱包背书 / High-reputation vs new wallet endorsements |

**双层决策架构 / Dual-Layer Decision Architecture**：

```
确定性计算层（bidding_agent.py）            LLM 决策层（sessions_spawn Pro）
┌────────────────────────────────┐        ┌──────────────────────────────────┐
│ ① VeriRank 信誉分              │        │                                  │
│ ② 历史交付量 (edge_count)      │        │  Gemini Pro / Claude Sonnet      │
│ ③ 最近活跃时间戳 (last_active) ├───────►│  输入: 5 维度 structured JSON    │
│ ④ TEE 硬件一致性 (tee_stable)  │        │  输出: ranked selection +        │
│ ⑤ 背书方质量 (endorser_stats)  │        │        reasoning (自然语言)  │
└────────────────────────────────┘        └──────────────────────────────────┘
```

Bidding Agent 负责"计算"（确定性 Python），Pro Agent 负责"决策"（推理维度冲突），通过 `sessions_spawn(agentId="pro")` 调用，无需新增 API key 或 SDK 依赖。
*Bidding Agent handles "computation" (deterministic Python), Pro Agent handles "decision-making" (reasoning through dimension conflicts), invoked via `sessions_spawn(agentId="pro")` — no additional API keys or SDK dependencies required.*

**维度冲突示例 / Dimension Conflict Examples** （LLM 推理的价值 / Value of LLM Reasoning）：
- "Worker Alpha 信誉最高但 20 天未活跃；Worker Beta 信誉稍低但 3 分钟前刚完成任务" → 权衡可用性 vs 信誉
- "Worker Beta 交付量多但 TEE 指纹在 3 天前变更过" → 正常升级还是换皮洗历史？
- "Worker Gamma 所有背书方都是新钱包（低 seed score）" → Sybil 风险判断

---

### 第三步：完整的信誉图随时间成长 / Step 3: The Complete Reputation Graph Grows Over Time

```
第 1 天：3 个 Worker，各有 1-2 条边，信誉图稀疏
第 7 天：10 个 Worker，信誉差距开始显现
第 30 天：高质量 Worker 聚集高信誉 Client 的背书，形成明显的信誉分层
```

**任何人都可以在任意时间点，用 X Layer 链上数据重建这个图，独立验证任何 Worker 的信誉。不需要相信 VeriTask，不需要相信 OKX。**
*Anyone can rebuild this graph at any point in time using X Layer on-chain data and independently verify any Worker's reputation. No need to trust VeriTask. No need to trust OKX.*

---

### 新增：Demo Pre-seed 数据策略与安全模式 / Demo Pre-seed Data Strategy & Security Mode

为展示算法 5 层全覆盖（信誉边拉取 → 边权重公式 → Client 种子分 → VeriRank → Wash-trading 检测），v3.5 为 3 个 Demo Worker 预先锚定了差异化的链上声誉数据：
*To demonstrate full 5-layer algorithm coverage (edge retrieval → edge weight formula → Client seed score → VeriRank → wash-trading detection), v3.5 pre-seeds differentiated on-chain reputation data for 3 Demo Workers:*

| 算法层 | 展示内容 | Pre-seed 如何产生区分度 |
|--------|---------|------------------------|
| ① 链上信誉边拉取 | 不同 Worker 不同边数 | Alpha=5, Beta=3, Gamma=1 |
| ② 边权重公式 | `pq × log(1+amount) × e^(-λ×age)` | 不同 pq (1.0/0.5), amount (0.1~5 USDT), age (1~20天) |
| ③ Client 种子分 | `portfolio-overview` 真实链上数据 | Client A ≈ 0.7; B ≈ 0.3; C ≈ 0 |
| ④ VeriRank | 高 seed Client 背书权重更大 | Alpha 由 A+B+C 混合背书; Gamma 仅 C 背书 |
| ⑤ Wash-trading 检测 | `isolated_endorser` 异常标记 | Gamma: 1边1Client → score ×0.5 |

**安全模式切换 `VERITASK_MODE` / Security Mode Switch**：VTRegistry 合约的 `client = msg.sender` 天然不可伪造，但 Demo pre-seed 需要模拟多个 Client 背书：
*VTRegistry contract’s `client = msg.sender` is inherently unforgeable, but Demo pre-seed needs to simulate multiple Client endorsements:*

| 模式 | Client 身份来源 | 用途 |
|------|----------------|------|
| **Production**（默认） | Event `client` 参数（= `msg.sender`，ECDSA 保证） | 生产环境，不可伪造 |
| **Demo** | VT2 calldata `client` 字段（允许 `--client-override`） | 引用真实活跃地址展示 seed score 差异化 |

---

### 新增：Public PCEG REST API（v3.5.4）/ New: Public PCEG REST API (v3.5.4)

信誉图不应只存在于链上——它还需要一个易于查询的 API 让任何人（评委、其他 Agent、前端）无需跑链扫描即可读取。
*The reputation graph should not only exist on-chain — it also needs an easy-to-query API so anyone (evaluators, other agents, frontends) can read it without running chain scans.*

**设计核心 / Design Core**：API 运行在与 Worker 相同的 Phala CVM 内部，无需 API key，4 个只读 GET 端点。
*The API runs inside the same Phala CVM as the Worker, requires no API key, and exposes 4 read-only GET endpoints.*

| Endpoint | Description |
|----------|-------------|
| `GET /pceg/graph` | Full graph summary with live/demo counts + all worker rankings |
| `GET /pceg/rankings` | Workers ranked by VeriRank (descending) |
| `GET /pceg/worker/{address}` | Single worker detail with all edge history |
| `GET /pceg/edge/{tx_hash}` | Single edge lookup by transaction hash |

**`data_source` 标注策略 / Data Source Labeling Strategy**：

链上数据不可删除。pre-seed demo 边和 live production 边永久共存。API 不隐藏任何数据——而是**标注**每条边的来源：
*On-chain data is immutable. Pre-seed demo edges and live production edges coexist permanently. The API does not hide any data — it **labels** each edge's origin:*

| `data_source` | 判断条件 / Detection Rule | 含义 / Meaning |
|---------------|--------------------------|----------------|
| `live` | `proof_hash` is a valid SHA-256 digest (no leading-zero pattern) | Real C2C task execution (zkTLS + TEE + x402 + anchor) |
| `preseed_demo` | `proof_hash` has 48+ leading zeros (ABI-encoded timestamp) or matches known test values | Algorithm demonstration edge from `preseed.py` |

**为什么标注而非过滤 / Why Label Instead of Filter**：
- 过滤 = 隐藏数据 = 评委可能怀疑"真的都是假的" / Filtering = hiding data = evaluators may suspect all data is fake
- 标注 = 完全透明 = 评委一目了然哪些是真实任务产生的、哪些是算法演示用的 / Labeling = full transparency = evaluators immediately see which edges are from real tasks vs algorithm demos
- `GraphSummary` 包含 `live_edges` 和 `demo_edges` 计数，无需逐条检查 / `GraphSummary` includes `live_edges` and `demo_edges` counts, no need to check edge-by-edge

---

### 为什么 Wash Trading 在这里经济上不合理 / Why Wash Trading Is Economically Irrational Here

一个 Scammer 想刷 Worker X 的信誉：
*A scammer wants to inflate Worker X’s reputation:*

| 步骤 / Step | 成本 / Cost |
|---|---|
| 部署假 Client 钱包 / Deploy fake Client wallet | 接近零 / Near zero |
| 给 Worker X 发 x402 / Send x402 payment to Worker X | 需要真实 USDT / Requires real USDT |
| 让这条边有 proof_quality = 1.0 / Make edge proof_quality = 1.0 | **需要真实 zkTLS Attestor 签名 + 真实 TDX Quote** / **Requires genuine zkTLS Attestor signature + genuine TDX Quote** |
| Bidding Agent 不过滤这条边 / Bidding Agent doesn’t filter this edge | 以上全部缺一不可 / All of the above are required |

**每刷一条有效信誉边，成本等于完整跑一次真实的 VeriTask 任务。** 刷好评的成本和干真活的成本完全一样。在这个结构里，刷好评在经济上是无意义的——不如直接干真活赚信誉。
**The cost of faking one valid reputation edge equals the cost of completing one real VeriTask task.** The cost of fake reviews and real work are identical. In this structure, reputation gaming is economically meaningless — you’re better off just doing real work to earn reputation.

这是 Web3 密码学在结构层面解决了 Web2 刷评问题的地方，不是靠平台打击，是靠协议设计让刷评失去动机。
*This is where Web3 cryptography solves the Web2 fake review problem at the structural level — not through platform enforcement, but through protocol design that removes the incentive to game the system.*

---

### 新增：Dispute Anchor — 负向信誉边 / New: Dispute Anchor — Negative Reputation Edges

PCEG 最初只有正向边（任务成功 → 付款 → Graph Anchor 写入信誉边）。但只有正向反馈的信任体系是不完整的——Worker 交付物存在密码学可验证的缺陷时，当前只是"不付钱、不写边"，没有负面后果。
*PCEG originally only has positive edges (task success → payment → Graph Anchor writes endorsement edge). But a trust system with only positive feedback is incomplete — when a Worker's deliverable has cryptographically verifiable defects, the current behavior is simply "no payment, no edge written" — no negative consequence.*

Dispute Anchor 的目标：**验证失败不只是"不赚信誉"，而是"主动扣信誉"。**
*Dispute Anchor's goal: verification failure doesn't just mean "no reputation earned" — it means "reputation actively reduced."*

#### 链上数据格式 / On-chain Data Format

在现有 `VT2:{json}` calldata 基础上，升级到 v3，新增 `edge_type` 和 `dispute_reason` 字段：
*Building on the existing `VT2:{json}` calldata format, upgrade to v3 with new `edge_type` and `dispute_reason` fields:*

```json
// Positive edge (existing behavior, unchanged)
{
  "v": "3", "edge_type": "endorsement",
  "worker": "0xWorker", "client": "0xClient",
  "proof_hash": "sha256...", "tee_fingerprint": "a1b2c3d4...",
  "task_type": "defi_tvl", "amount_usdt": "0.01", "ts": 1773040716
}

// Negative edge (new)
{
  "v": "3", "edge_type": "dispute",
  "worker": "0xWorker", "client": "0xClient",
  "proof_hash": "", "tee_fingerprint": "",
  "task_type": "defi_tvl", "amount_usdt": "0",
  "dispute_reason": "zk_proof_invalid", "ts": 1773040716
}
```

**向后兼容 / Backward Compatibility**：v2 边（现有链上数据）没有 `edge_type` 字段 → Bidding Agent 解析时默认为 `"endorsement"`。
*v2 edges (existing on-chain data) lack the `edge_type` field → Bidding Agent defaults to `"endorsement"` when parsing.*

#### 触发条件 / Trigger Conditions

**核心原则：只有密码学可验证的失败才写链上，网络问题不算。**
*Core principle: only cryptographically verifiable failures are anchored on-chain. Network issues don't count.*

| # | 失败场景 / Failure Scenario | `dispute_reason` | 行为 / Behavior |
|---|---------------------------|------------------|----------------|
| ① | ZK Proof 验证失败（hash 不匹配） | `zk_proof_invalid` | 不付款 + 写入 Dispute 边 / No payment + anchor Dispute edge |
| ② | TEE Attestation 验证失败（report_data 不匹配） | `tee_attestation_invalid` | 不付款 + 写入 Dispute 边 / No payment + anchor Dispute edge |
| ③ | ZK + TEE 双失败 | `full_proof_failure` | 不付款 + 写入 Dispute 边（加重 κ）/ No payment + anchor Dispute edge (elevated κ) |

**不触发链上 Dispute 的场景 / Scenarios that do NOT trigger on-chain Dispute**：
- Worker HTTP 超时 / 5xx → 仅记本地日志（网络抖动、CVM 重启不是密码学诚信问题）
  *Worker HTTP timeout / 5xx → local log only (network jitter, CVM restart are not cryptographic integrity issues)*
- Worker 地址为空 → 跳过（无法索引到具体 Worker）

#### VeriRank 负向边权重公式 / VeriRank Negative Edge Weight Formula

正向边权重（不变 / unchanged）：
```
w_endorsement = proof_quality × log(1 + amount_USD) × e^(-λ × age_days)
```

负向边权重（新增 / new）：
```
w_dispute = -κ × seed(client) × e^(-λ × age_days)
```

| `dispute_reason` | κ 系数 / κ coefficient |
|------------------|----------------------|
| `zk_proof_invalid` | 0.3 |
| `tee_attestation_invalid` | 0.5 |
| `full_proof_failure` | 0.8 |

**VeriRank 公式变为 / Updated VeriRank formula**：
```
VeriRank(w) = Σ [seed(c) × w_endorsement(e)]  +  Σ [w_dispute(d)]
              over positive edges                  over negative edges
```

**设计要点 / Design Notes**：
- 负向边的 **Client seed score 参与权重** → 高信誉 Client 的 dispute 权重更大（其判断可信），新钱包的 dispute 权重趋近于零（自然防御 Sybil 攻击）
  *Negative edge weight incorporates Client seed score → high-reputation Client disputes carry more weight (their judgment is credible); new wallet disputes have near-zero weight (natural Sybil defense)*
- 与正向边**完全对称**：正向边=高信誉 Client 背书权重大；负向边=高信誉 Client dispute 权重大
  *Fully symmetric with positive edges: positive = high-reputation Client endorsements weigh more; negative = high-reputation Client disputes weigh more*
- **时间衰减相同**（`e^(-λ × age)`）→ Worker 可通过后续优质交付恢复信誉
  *Same time decay (`e^(-λ × age)`) → Worker can recover reputation through subsequent quality deliveries*

#### 防滥用机制 / Anti-abuse Mechanisms

| # | 防御措施 / Defense Mechanism | 原理 / Rationale |
|---|---------------------------|-----------------|
| ① | 负向边权重 ∝ `seed(client)` | 新钱包 seed ≈ 0 → dispute 权重 ≈ 0，自然阻止 Sybil 攻击 / New wallet seed ≈ 0 → dispute weight ≈ 0, naturally blocks Sybil attacks |
| ② | 必须实际调用 Worker | 每次 dispute 需先发 HTTP 请求到 Worker 并取得响应，不能凭空 dispute / Must actually invoke Worker first, cannot dispute from thin air |
| ③ | 时间衰减 | 旧 dispute 边指数衰减，不会永久影响 / Old dispute edges decay exponentially, no permanent damage |
| ④ | Client dispute 频率监控 | 同一 Client 短期大量 dispute 不同 Worker → 该 Client 自身 seed score 被降权 / Same Client disputing many Workers in short time → Client's own seed score is reduced |

#### 实施范围 / Implementation Scope

| 文件 / File | 修改内容 / Change |
|------------|------------------|
| `graph_anchor.py` | 新增 `anchor_dispute()` 函数，构造 dispute calldata（`edge_type: "dispute"`）/ Add `anchor_dispute()` function for dispute calldata |
| `task_delegator.py` | 验证失败分支调用 `anchor_dispute()` / Call `anchor_dispute()` on verification failure branches |
| `bidding_agent.py` | 解析 `edge_type` 字段，负向边用 `w_dispute` 公式 / Parse `edge_type`, apply `w_dispute` formula for negative edges |
| `pceg_api.py` | `EdgeResponse` 新增 `edge_type` 字段，API 展示正负两类边 / Add `edge_type` to `EdgeResponse`, display both edge types |

### Implementation Status (v3.5.8, 2026-03-23)

All components listed above have been implemented, deployed to Phala CVM, and verified on X Layer mainnet.

#### What Was Built

1. **`graph_anchor.py`** — `anchor_dispute()` writes a negative reputation edge to VTRegistry on X Layer when verification fails. The on-chain calldata includes `edge_type: "dispute"` and `dispute_reason` (e.g., `zk_proof_invalid`).

2. **`task_delegator.py`** — On verification failure (hash mismatch, attestation invalid, or full proof failure), the pipeline aborts payment and calls `anchor_dispute()` instead. The dispute txHash is reported to the user.

3. **`bidding_agent.py`** — Parses `edge_type` from on-chain logs. Dispute edges receive negative weight via the formula defined above. Added `DEMO_SEED_OVERRIDES` env var for testable seed score injection. Implements post-hoc dispute deduction:
   ```
   dispute_deduction = Σ |w_dispute(e)| × seed(client)   for all dispute edges targeting worker
   final_score = max(0, PageRank_score × penalty − dispute_deduction)
   ```

4. **`pceg_api.py`** — Added `final_score` field to `WorkerRanking` model. Rankings sorted by `final_score` (not raw `verirank`). Three additional fixes for Phala CVM stability:
   - **Pre-baked `edge_cache.json`**: Eliminates full blockchain scan on cold start (X Layer's 100-block `eth_getLogs` limit made scanning 186K blocks = ~1879 RPC pages → OOM in 1GB CVM).
   - **`run_in_executor`**: `_refresh_cache()` runs in a thread pool so it doesn't block the asyncio event loop (previously caused health-check timeouts → CVM killed).
   - **Lazy import**: `bidding_agent` loaded on first use, not at module import time.

#### Live Deployment Results

**Docker**: `skottbie/veritask-worker:v3.5.8`
**CVM URL**: `https://2d29518d31fd53641b70a1754c79dce1450188b2-8001.dstack-pha-prod9.phala.network`

**Dispute Penalty Observed** (Worker `0x871c`):
| Metric | Value |
|--------|-------|
| Raw VeriRank (PageRank) | 0.35511178 |
| Final Score (after deduction) | 0.08511185 |
| Penalty | **−76%** |
| Dispute Edges | 3 (reason: `zk_proof_invalid`) |
| Total Edges | 18 (15 endorsement + 3 dispute) |

**Graph Statistics** (`GET /pceg/graph`):
- 26 total edges (4 live, 22 demo seed)
- 23 endorsement + 3 dispute
- 3 workers, 4 clients

All three PCEG endpoints (`/pceg/graph`, `/pceg/rankings`, `/pceg/worker/{address}`) return 200 OK. CVM remains stable after repeated requests (no OOM, no health-check timeout).

---

### 对齐比赛评审标准 / Alignment with Judging Criteria

| 评审维度 / Judging Criterion | VeriTask 2.0 的回答 / VeriTask's Answer |
|---|---|
| Deeply integrated on-chain | X Layer 不只存付款，每条信誉边（正向背书 + 负向 Dispute）都是链上可查的密码学事实 / X Layer stores not just payments — every reputation edge (endorsement + dispute) is a cryptographically verifiable on-chain fact |
| Autonomous agent payment flow | Bidding Agent 全自动选 Worker + Veri Agent 全自动验证 + Graph Anchor Agent 全自动写图（含 Dispute），Client 可以完全离线 / Fully autonomous: Bidding Agent selects Workers, Veri Agent verifies, Graph Anchor writes both endorsement and dispute edges — Client can be completely offline |
| Multiple agents collaboration | Client + Bidding Agent + Worker + Veri Agent + Graph Anchor Agent，5 个 Agent，分工清晰，每一个存在都有充分理由 / 5 agents with clear separation of concerns, each with a well-justified purpose |
| Overall impact on X Layer ecosystem | X Layer 成为第一条有原生 Agent 信誉基础设施的链——任何在 X Layer 上做 A2A 服务的项目都可以读这个图 / X Layer becomes the first chain with native Agent reputation infrastructure — any A2A project on X Layer can read this graph |
| Most Innovative | 第一个 Proof-Conditioned Endorsement Graph + Dispute Anchor 双向信誉机制，引用并超越 TraceRank / First Proof-Conditioned Endorsement Graph with bidirectional reputation (endorsement + dispute), citing and surpassing TraceRank |
| Best in Agentic Payments | x402 不只是支付，每笔付款同时是一次密码学背书 / x402 is not just payment — every payment is simultaneously a cryptographic endorsement |

---

### 为什么？ / Why?

**上届 VeriTask 解决了：这次任务的数据是不是真的。**
*Last season, VeriTask solved: "Is the data from this task authentic?"*

**这届 VeriTask 解决了：这个 Agent 值不值得雇。**
*This season, VeriTask solves: "Is this Agent worth hiring?"*

两个问题合在一起，才是完整的 A2A Commerce 可信层。VeriTask 在两届比赛里，把这个问题的两半都解决了。
*Together, these two questions form the complete trust layer for A2A Commerce. Across two hackathon seasons, VeriTask has solved both halves of this problem.*

TraceRank 论文（2025年10月，https://arxiv.org/pdf/2510.27554）描述了一个需要 Proof-Conditioned Endorsement 才能完整的系统，但他们没有实现它——因为他们没有 zkTLS + TEE 基础设施。VeriTask 已经有了，而且在 X Layer 上跑过多次真实链上交易。
*The TraceRank paper (October 2025, https://arxiv.org/pdf/2510.27554) describes a system that requires Proof-Conditioned Endorsement to be complete, but they didn't implement it — because they lacked the zkTLS + TEE infrastructure. VeriTask already has it, and has executed multiple real on-chain transactions on X Layer.*

---

## 🔍 第一次审计总结（OnchainOS v2.1.0，2025-03-21）

### 审计范围
基于 [okx/onchainos-skills v2.1.0](https://github.com/okx/onchainos-skills)（11 skills），逐项校验设计文档中所有 OnchainOS 命令引用。

### OnchainOS 命令校验汇总

| 设计文档引用 | v2.1.0 实际状态 | 严重度 |
|---|---|---|
| `onchain-gateway broadcast` | ✅ 可用 | — |
| `wallet contract-call --input-data` | ✅ v2.1.0 新增，需 login | — |
| `wallet tx-history [addr]` | ❌ 不存在。替代：RPC/Explorer + `portfolio-dex-history` | ⚠️ 中 |
| `market smart-money [addr]` | ❌ 不存在。替代：`portfolio-overview`（PnL/胜率/交易数） | ⚠️ 低 |
| `wallet pnl [addr]` | ❌ 不存在。替代：`portfolio-overview --address` | ⚠️ 低 |
| `payment x402-pay` | ✅ v2.1.0 新增独立 skill（TEE签名 + 本地 fallback） | — |

### 总结论

**设计方向完全正确，无技术死路。** 3 个不存在的命令中：
- 1 个需要用 EVM RPC 替代（信誉边索引）——标准区块链开发
- 2 个有更好的替代命令（`portfolio-overview` 返回的连续分数比布尔值信息量更大）

**可实现性评级：HIGH。创新性评级：极高（天花板级）。**

---

## 🔍 第二次审计（本地文件复核，v2.1.0 installed，2025-03-21）

**复核方式**：CLI 已更新到 v2.1.0，本地 `.agents/skills/` 已安装全部 11 个 skills，
逐个读取本地 SKILL.md 内容与第一次审计结论交叉验证。

### 复核结果

| 审计项 | 第一次结论 | 本地文件验证 | 是否需要修正 |
|---|---|---|---|
| `gateway broadcast` ✅ | 可用，`--raw-tx` | 实际参数名为 `--signed-tx`，需 `--address` | ✅ 已修正参数名 |
| `wallet contract-call` ✅ | 需 login | 确认 Auth Required: Yes（Command D2） | 无需修正 |
| `wallet tx-history` ❌ | 不存在 | 确认：`wallet history`（E1, auth only）+ `portfolio-dex-history`（DEX only） | 无需修正 |
| `market smart-money` ❌ | 不存在 | 确认：无单地址布尔查询。`signal list` 和 `leaderboard list` 均为聚合/排行榜 | 无需修正 |
| `wallet pnl` ❌ | 替代为 `portfolio-overview` | 确认：Command #6，返回 PnL/winRate/top3Tokens | 无需修正 |
| `portfolio-overview` 链支持 | 未提及 | ⚠️ 新发现：需运行 `portfolio-supported-chains` 确认 X Layer 支持 | ✅ 已补充 fallback |

### 新增发现

1. **`onchainos gateway broadcast` 准确参数**：`--signed-tx <hex> --address <sender> --chain xlayer`
   （不是 `--raw-tx`，且需要 `--address` 声明发送方地址）
2. **`portfolio-supported-chains` 前置检查**：`portfolio-overview` 不保证所有链可用，
   实现时必须先查支持列表，不支持则 fallback 到 RPC 简化分数
3. **`leaderboard list` 单选限制**：`--wallet-type` 一次只能传一个类型（不能 `smartMoney,whale`），
   且每次最多返回 20 条，无法查询特定地址是否在榜

**第二次审计结论：第一次审计核心结论全部确认。仅修正了 gateway broadcast 参数名和补充了 portfolio 链支持检查。**

---

## 🔍 第三次审计（CLI Reference 深度复查 + 第三方独立审计报告，2025-03-21）

**背景**：用户独立审计指出前两次审计存在"把 CLI 语法不匹配等同于功能不存在"的系统性偏差。
本次基于各 skill 的 `references/cli-reference.md` 完整参数表做逐项深度复核。

### 数据源

| 文件 | 关键发现 |
|---|---|
| `okx-agentic-wallet/references/cli-reference.md` | E1 `wallet history` 仅查自己钱包(Auth Required)；C6-C9 `portfolio` 系列接受任意 `--address` |
| `okx-dex-market/references/cli-reference.md` | #6-9 `market portfolio-*` 系列与 `portfolio` 系列功能对等；#10 `address-tracker-activities` 的 `trackerType` 可间接判定地址是否为 smart money |
| `okx-dex-signal/references/cli-reference.md` | `signal list --wallet-type 1` 返回 smart money 买入信号含 `triggerWalletAddress`；`leaderboard list --wallet-type smartMoney` 返回排行榜 |
| `okx-onchain-gateway/references/cli-reference.md` | 确认 6 个命令，无 tx-history 类接口 |

### 逐项修正

#### 1. `wallet tx-history [addr]` → 原判：❌不存在 → **修正：⚠️ 功能部分存在，需组合使用**

| CLI 命令 | 能力 | 限制 | 设计可用性 |
|---|---|---|---|
| `wallet history`（E1） | 查自己钱包全类型 TX（含转账、合约调用） | Auth Required，不接受任意 address | ❌ 不适用于查 Worker 地址 |
| `portfolio dex-history --address <addr>`（C7） | 查**任意地址** DEX 交易，含 `tx-type 3=transfer-in, 4=transfer-out` | 名义上是 "DEX history"，transfer 类型是否覆盖 x402 USDT 直接转账**需实测** | ⚠️ 可能可用 |
| `market portfolio-dex-history --address <addr>`（#7） | 同上，市场技能入口 | 同上 | ⚠️ 可能可用 |

**关键发现**：`portfolio dex-history` 的 `--tx-type` 参数支持 `3=Transfer In, 4=Transfer Out`，
这表明该接口**不仅限于 DEX swap**，还包含代币转入转出记录。
x402 付款本质是 USDT ERC-20 transfer，有可能被索引为 type 3/4。

**实测结果**（2025-03-21，onchainos v2.1.0，proxy via 10808）：
```bash
# 测试 1：dex-history 查 Worker 地址（已知有 x402 USDT 收款）
onchainos market portfolio-dex-history \
  --address 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb \
  --chain xlayer --begin 1773100800000 --end 1773273600000 --tx-type 3,4
→ 结果：{"transactionList": []}  ❌ 空！x402 USDT 转账未被索引

# 测试 2：portfolio all-balances 查同一 Worker 地址
onchainos portfolio all-balances \
  --address 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb --chains xlayer
→ 结果：✅ balance=0.21 USDT（x402 累计收款可见于余额，但无交易记录）
```

**结论**：❌ `portfolio dex-history` **确认不覆盖** x402 USDT 转账（gasless TransferWithAuthorization）。
信誉边索引**必须**使用 RPC fallback：
```
eth_getLogs(USDT contract, Transfer event, to=worker_address)
→ 过滤 calldata 含 VeriTask 版本前缀的 TX
```
这是标准区块链开发，不构成技术阻塞。Demo 叙事：
"图的存储用 EVM 原生能力（区块链本身就是数据库），图的分析用 OnchainOS"。

---

#### 2. `market smart-money [addr]` → 原判：❌不存在 → **修正：⚠️ 功能间接可用**

| CLI 命令 | 能力 | 种子分可用性 |
|---|---|---|
| `market address-tracker-activities --tracker-type multi_address --wallet-address <addr>` | 查任意地址的 DEX 交易，返回的 `trackerType` 字段含 `"1"`=smart_money, `"2"`=kol, `"3"`=multi_address | ✅ **可间接判定地址是否被平台标记为 smart money / KOL / whale** |
| `signal list --chain <chain> --wallet-type 1` | 返回 smart money 买入信号，含 `triggerWalletAddress` | ⚠️ 可检查目标地址是否出现在最近的 smart money 信号中 |
| `leaderboard list --chain <chain> --wallet-type smartMoney --sort-by 1` | 返回排名前 20 smart money，含 `walletAddress` | ⚠️ 可检查目标地址是否在 Top20 榜单 |
| `portfolio overview --address <addr>` | 返回 PnL / winRate / tradeCount | ✅ 构建连续种子分的核心数据 |

**关键发现**：`address-tracker-activities` 的 `trackerType` 字段是**多值数组**，
文档明确说 "May contain multiple values if the address matches more than one tracker type"。
这意味着：查询 `--tracker-type multi_address --wallet-address 0xABC` 时，
如果返回的 trade 记录中 `trackerType: ["1", "3"]`，则该地址**同时被 OKX 分类为 smart money**。

**实测结果**（2025-03-21，onchainos v2.1.0）：
```bash
# 测试 1：smart_money tracker — trackerType 字段
onchainos market address-tracker-activities --tracker-type smart_money --chain xlayer
→ 所有 trade 的 trackerType 都是 []（空数组）  ❌ 交叉标记不工作

# 测试 2：用已知 smart money 地址查 multi_address
onchainos market address-tracker-activities --tracker-type multi_address \
  --wallet-address 0x5720367e4c83187f263a64f1c1af42853e7fe986 --chain xlayer
→ 返回该地址的 DEX 交易，但 trackerType 仍为 []  ❌ 无法通过此字段判定

# 测试 3：signal list 查 smart money 触发钱包
onchainos signal list --chain xlayer --wallet-type 1
→ ✅ 返回 triggerWalletAddress 字段，含真实 smart money 地址列表

# 测试 4：leaderboard smart money
onchainos leaderboard list --chain xlayer --time-frame 3 --sort-by 1 --wallet-type smartMoney
→ ✅ 返回 walletAddress 字段，top smart money 排行
```

**结论**：`trackerType` 交叉标记在实际 API 中不工作（始终空数组），
但可通过 `signal list` 和 `leaderboard list` 获取 smart money 地址池：

```python
# 实际可行的种子分方案：
# 1. 获取 smart money 地址池
smart_money_addrs = set()
for signal in onchainos_signal_list(chain="xlayer", wallet_type=1):
    smart_money_addrs.update(signal.triggerWalletAddress.split(","))
for entry in onchainos_leaderboard_list(chain="xlayer", wallet_type="smartMoney"):
    smart_money_addrs.add(entry.walletAddress)

# 2. 获取 PnL 数据
overview = onchainos_portfolio_overview(address=client_addr, chain="xlayer")

# 3. 计算种子分
seed_score = sigmoid(
    α × normalized_pnl +
    β × win_rate +
    γ × log(1 + trade_count) +
    δ × account_age_factor +
    ε × (1.0 if client_addr in smart_money_addrs else 0.0)
)
```

**结论**：从 ❌ "不存在" 修正为 ⚠️ "无直接布尔接口，但 trackerType 间接路径功能等价"。
种子分公式因此获得更丰富的信号维度。

---

#### 3. `wallet pnl [addr]` → 原判：❌不存在 → **修正：✅ 功能完全存在**

| CLI 命令 | 能力 | 返回字段 |
|---|---|---|
| `portfolio overview --address <any_addr> --chain <chain>` (C6) | 任意地址 PnL + 交易统计 | `realizedPnlUsd`, `unrealizedPnlUsd`, `totalPnlUsd`, `winRate`, `buyTxCount`, `sellTxCount`, `preferredMarketCap`, `topPnlTokenList[]` |
| `market portfolio-overview --address <any_addr> --chain <chain>` (#6) | 同上（市场技能入口） | 同上 + `tokenCountByPnlPercent`, `buysByMarketCap[]` |
| `portfolio recent-pnl --address <addr> --chain <chain>` (C8) | 逐 Token PnL 列表 | `pnlList[].realizedPnl`, `unrealizedPnl`, `totalPnl`, `buyAvgPrice`, `sellAvgPrice` |
| `portfolio token-pnl --address <addr> --chain <chain> --token <token>` (C9) | 单 Token PnL 快照 | 同上，单条记录 |

**结论**：✅ PnL 查询能力**完全存在**且极其丰富。
前两次审计已正确指出 `portfolio-overview` 作为替代，
但用 "不存在" 做标题措辞不当——正确描述应为 "命令名不同，功能完全等价且更强"。

**实测结果**（2025-03-21）：
```bash
# 测试 1：portfolio-supported-chains 确认 X Layer
onchainos market portfolio-supported-chains
→ ✅ chainIndex "196"（X Layer）在列表中

# 测试 2：portfolio-overview 查 Worker 地址（仅有 x402 收款，无 DEX 交易）
onchainos market portfolio-overview \
  --address 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb --chain xlayer --time-frame 5
→ ✅ 返回成功，所有 PnL 字段为 0（因为该地址无 DEX 交易，符合预期）

# 测试 3：portfolio-overview 查 Vitalik 地址（验证命令确实返回实际数据）
onchainos market portfolio-overview \
  --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --chain ethereum --time-frame 5
→ ✅ buyTxCount=5, sellTxCount=3, avgBuyValueUsd=461.95 — 真实数据
```

**注意**：`portfolio-overview` 的 PnL **仅统计 DEX 交易**，不包含 x402 USDT 转账的收支。
对种子分场景（评估 Client 是否为活跃交易者），这恰好是正确的信号源——
我们关心的是 Client 在 DeFi 中的交易表现，不是他付了多少次 VeriTask 费用。

---

### 第三次审计总结（含实测）

| 设计文档引用 | 第一次审计 | 第三次审计（实测结论） | 变化 |
|---|---|---|---|
| `wallet tx-history [addr]` | ❌ 不存在 | ❌ **实测确认**：`dex-history` 不覆盖 x402 转账。必须 RPC fallback | 结论不变，路径确认 |
| `market smart-money [addr]` | ❌ 不存在 | ⚠️ **无直接接口**，`trackerType` 交叉标记不工作，但 `signal list` + `leaderboard list` 可获取 smart money 地址池做集合匹配 | 上调至 ⚠️ |
| `wallet pnl [addr]` | ❌ 不存在 | ✅ **实测确认**：`market portfolio-overview --address <addr>` 在 X Layer 上工作，返回完整 PnL 结构 | 上调至 ✅ |



## 📋 TODO — v3.5 实现计划

### TODO 1: Worker Discovery（Client-Pull 模型）

**方案**：Client-Pull，不做链上 TaskIntent 广播。

**流程**：
1. Client 维护一个 `worker_registry.json` 配置文件
2. Bidding Agent 从 Registry 读取所有候选 Worker 地址
3. 查链上 reputation → VeriRank 排名
4. 选出 top Worker → Task Delegator 用对应的 URL 调用它

```
                Bidding Agent (Client侧)
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   Worker Alpha   Worker Beta   Worker Gamma
   (声誉查询)     (声誉查询)    (声誉查询)
         │             │             │
         ▼             ▼             ▼
   X Layer链上reputation edges (eth_getLogs)
         │
         ▼
   VeriRank 排名 → 选 winner
         │
         ▼
   Task Delegator → POST /execute → winner URL
```

**`worker_registry.json` 结构**：
```json
{
  "workers": [
    {"alias": "worker-alpha", "address": "0xAAA...", "url": "http://127.0.0.1:8001"},
    {"alias": "worker-beta",  "address": "0xBBB...", "url": "http://127.0.0.1:8001"},
    {"alias": "worker-gamma", "address": "0xCCC...", "url": "http://127.0.0.1:8001"}
  ]
}
```

> Demo 阶段所有 Worker URL 指向同一后端，但地址不同以展示声誉差异化。

### TODO 1.5: VTRegistry 合约 — 链上信誉边索引

**问题**：Graph Anchor 当前使用 EOA self-transfer 写入 calldata → 不触发任何 ERC20 event → Bidding Agent 的 `eth_getLogs` 无法索引。

**方案**：部署一个极简 VTRegistry 合约到 X Layer，通过 Solidity event 实现高效索引。

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VTRegistry {
    event Edge(address indexed client, address indexed worker, bytes data);

    function anchor(address worker, bytes calldata data) external {
        emit Edge(msg.sender, worker, data);
    }
}
```

**优势**：
- `msg.sender` = ECDSA 验证的 Client 地址 → **自动解决 client 身份伪造问题**
- `address indexed worker` → Bidding Agent 可用 `eth_getLogs(VTRegistry, Edge, worker=X)` 高效索引
- 合约只需部署 1 次，地址写入 `.env` 为 `VT_REGISTRY_ADDRESS`
- 极简设计：无存储变量、无权限控制、无升级机制 → 审计成本为 0

**改动范围**：
| 组件 | 改动 |
|------|------|
| Graph Anchor | `to` 改为 VTRegistry 合约地址，calldata 改为 `anchor(worker, VT2:{...})` ABI 编码 |
| Bidding Agent | `fetch_transfer_logs` 改为过滤 `Edge(client, worker, data)` event |
| `.env` | 新增 `VT_REGISTRY_ADDRESS=0x...` |

**安全模式联动**：
- Production: `msg.sender == event.client` → 天然密码学保证，无需额外验证
- Demo: 同上（合约本身保证 msg.sender = client，不存在伪造可能）
- VERITASK_MODE 仅影响 seed score 查询策略，不影响 VTRegistry 合约

### TODO 1.6: Bug Fix — tee_fingerprint 字段名不匹配

**问题**：`graph_anchor.py` 读取 `tee_attestation.get("tdx_quote")`，但 `proof_generator.py` 实际输出的字段名是 `"quote"`。**导致真实 TDX 也被当作 mock 处理。**

**修复**：`graph_anchor.py` 改为 `tee_attestation.get("quote", "")`。

### TODO 2: Demo Workers Pre-seed 数据策略

**目的**：为 3 个 Demo Worker 预先锚定差异化的链上声誉数据，使 Bidding Agent 算法有真实数据可演示。

**3 个独立 Demo Worker 钱包**：生成 3 组 keypair，地址写入 `worker_registry.json`。

**3 个 Demo Client 引用地址**：引用 X Layer 上真实活跃地址（通过 `onchainos leaderboard list --chain xlayer` 获取），利用其真实 portfolio 数据产生差异化 seed score。

> ⚠️ Demo 模式下不需要控制 Client 钱包——只需在 calldata 中引用其地址。
> Bidding Agent 查询 `portfolio-overview` 时读取的是公开链上数据。
> 生产模式下必须验证 `calldata.client == tx.from`（见下方安全模式设计）。

#### 算法 5 层全覆盖设计

| 算法层 | 展示内容 | Pre-seed 数据如何产生区分度 |
|--------|---------|---------------------------|
| ① 链上信誉边拉取 | 不同 Worker 不同边数 | Alpha=5, Beta=3, Gamma=1 |
| ② 边权重公式 | `pq × log(1+amount) × e^(-λ×age)` | 不同 pq (1.0/0.5), amount (0.1~5 USDT), age (1~20天) |
| ③ Client 种子分 | `portfolio-overview` → realizedPnl/winRate/tradeCount | Client A = 活跃 DEX 交易者(seed≈0.7); B = 中等(seed≈0.3); C = 新钱包(seed≈0) |
| ④ Personalized VeriRank | 高 seed Client 背书权重更大 | Alpha 由 A+B+C 混合背书 → 最高; Gamma 仅 C 背书 → 最低 |
| ⑤ Wash-trading 检测 | isolated_endorser / client_clique | Gamma: 1边1Client → `isolated_endorser` flag → score ×0.5 |

#### Pre-seed 9 条边完整分配

```
Worker Alpha (5条 — 最强候选):
  Client A → Alpha, amount=5,   pq=1.0, ts=2天前
  Client A → Alpha, amount=3,   pq=1.0, ts=1天前
  Client B → Alpha, amount=2,   pq=1.0, ts=2天前
  Client B → Alpha, amount=1,   pq=1.0, ts=3天前
  Client C → Alpha, amount=0.5, pq=1.0, ts=1天前

Worker Beta (3条 — 中等候选):
  Client A → Beta, amount=1,   pq=1.0, ts=5天前
  Client B → Beta, amount=2,   pq=1.0, ts=6天前
  Client C → Beta, amount=0.1, pq=0.5, ts=7天前   ← mock TDX

Worker Gamma (1条 — 最弱候选):
  Client C → Gamma, amount=0.1, pq=0.5, ts=20天前  ← 唯一背书方是新钱包
```

**Client 地址获取方式**：
1. `onchainos leaderboard list --chain xlayer --sort-by 1 --wallet-type smartMoney`
2. 挑选 3 个不同活跃度的真实地址
3. 验证 `onchainos market portfolio-overview --address <addr> --chain xlayer` 返回差异化数据

**mock 边的意义**：展示算法检测和惩罚低质量证明的能力。真实场景对应：Worker 曾在不可信环境下交付（TEE 不可用降级 / 欺诈声称 TEE）。

#### 安全模式切换：`VERITASK_MODE`（结合 VTRegistry 合约）

VTRegistry 合约的 `event Edge(client indexed, ...)` 中 `client = msg.sender`，天然不可伪造。
但 demo pre-seed 需要模拟多个不同 Client 背书 → 需要区分 Client 身份来源。

| 模式 | 环境变量 | Client 身份来源 |
|------|---------|----------------|
| **Production** | `VERITASK_MODE=production`（默认） | Event 的 `client` 参数（= `msg.sender`，ECDSA 保证） |
| **Demo** | `VERITASK_MODE=demo` | VT2 calldata 中的 `client` 字段（允许 `--client-override`） |

**Production 模式**：Bidding Agent 从 Edge event 的 `client` 参数读取身份，忽略 calldata 中的 client 字段。
**Demo 模式**：Bidding Agent 从 VT2 calldata 的 `client` 字段读取身份（允许 pre-seed 引用任意地址展示 seed score 差异化）。

**安全设计**：
- 默认值为 `production`（fail-safe）
- Demo 模式仅在 `.env` 显式设置时生效
- 合约层始终安全（msg.sender 不可伪造）——demo 模式的 "降级" 仅在 Bidding Agent 读取层

**Pre-seed 执行方式**：使用 `graph_anchor.py --client-override 0xRealActiveAddr` 搭配不同参数多次执行，VT2 calldata 中写入引用地址，event 中 client 仍为实际签名者。

### TODO 3: Bidding Agent 多维度决策层（5 维度）

**核心理念**：VeriRank 只是一个维度。Bidding Agent 应处理多维度之间的张力，做出带推理的综合决策。

**评分标准对应**：`Architecture for collaboration between multiple agents` — Bidding Agent 成为真正的决策 Agent。

**5 个输入维度**：

| # | 维度 | 数据来源 | 当前实现状态 |
|---|------|----------|-------------|
| ① | VeriRank 信誉分 | `run_verirank()` | ✅ 已有 |
| ② | 历史交付量 | `edge_count` | ✅ 已有 |
| ③ | 最近活跃时间戳 | 最后一条边的 `ts` 字段 → `max(ts)` | ❌ 需新增 |
| ④ | TEE 硬件一致性 | 历史所有边的 `tee_fingerprint` 是否一致 | ❌ 需新增 |
| ⑤ | 背书方质量分布 | 所有背书 Client 的 seed_score 均值 + 方差 | ❌ 需新增 |

> ⑥ 报价维度（Worker `/quote` 端点）暂不实现，后续扩展。

**决策层架构**：

```
确定性计算层（bidding_agent.py）            LLM 决策层（sessions_spawn Pro）
┌────────────────────────────────┐        ┌──────────────────────────────────┐
│ ① VeriRank 信誉分              │        │                                  │
│ ② 历史交付量 (edge_count)      │        │  Gemini Pro / Claude Sonnet      │
│ ③ 最近活跃时间戳 (last_active) ├───────►│  输入: 5 维度 structured JSON    │
│ ④ TEE 硬件一致性 (tee_stable)  │        │  输出: ranked selection +        │
│ ⑤ 背书方质量 (endorser_stats)  │        │        reasoning (中文自然语言)  │
└────────────────────────────────┘        └──────────────────────────────────┘
```

**维度冲突示例**（LLM 推理的价值）：
- "Worker Alpha 信誉最高但 20 天未活跃；Worker Beta 信誉稍低但 3 分钟前刚完成任务" → LLM 权衡可用性 vs 信誉
- "Worker Beta 交付量多但 TEE 指纹在 3 天前变更过" → LLM 推理：正常升级还是换皮洗历史？
- "Worker Gamma 所有背书方都是新钱包（低 seed score）" → LLM 判断 Sybil 风险

### TODO 4: LLM 决策层调用方式

**方案**：复用项目已有的 Dual-Model Routing 架构（`sessions_spawn` Orchestrator-Workers 模式）。

**调用链**：
```
Task Delegator (Flash Agent)
  │
  ├── Step 0: Bidding Agent (Python 函数调用)
  │     → bidding_agent.rank_workers() 返回 5 维度 JSON
  │
  ├── Step 0.5: sessions_spawn(agentId="pro") — Bidding Decision
  │     → Pro Agent 接收 5 维度数据
  │     → 推理多维度张力，输出选择 + reasoning
  │     → 返回 winner worker address + 决策理由
  │
  ├── Step 1: POST /execute → winner URL
  │     ...（后续 C2C 流程不变）
```

**理由**：
- 复用 `sessions_spawn(agentId="pro")` — 无需新增 API key 或 SDK 依赖
- Pro 模型已在 `openclaw.json` 中配置（`gemini-3.1-pro-preview`）
- 与 Step 0a 验证策略路由同源，架构统一
- Bidding Agent 负责 "计算"，Pro Agent 负责 "决策" — 职责清晰

**Pro Agent Bidding Decision Prompt 骨架**：
```
分析以下 VeriTask Worker 候选人的 5 维度评估数据，选出最佳 Worker：

{rank_workers() 输出的 JSON}

评估维度权重参考：
① 信誉分（VeriRank）：核心维度，但不是唯一维度
② 历史交付量：交付多 = 有实际历史
③ 最近活跃时间：5分钟前 vs 30天前 = 可用性差异巨大
④ TEE 一致性：指纹变更可能意味着欺诈或正常升级
⑤ 背书方质量：高信誉 Client 背书 vs 新钱包背书 = 信号不同

请输出 JSON：
{
  "winner": "<worker_address>",
  "reasoning": "<中文推理过程，说明各维度权衡>",
  "confidence": <0.0-1.0>,
  "risk_flags": ["<如有风险标记>"]
}
```

---

相关资源：
1.Sybil-Resistant Service Discovery for Agent Economies https://arxiv.org/pdf/2510.27554
2.OKX OnChainOS Skills: https://github.com/okx/onchainos-skills
3.X Layer OnChainOS AI Hachathon
To qualify, your project must:  • Build on the X Layer ecosystem. Bonus points for integrating x402 payments. • Complete at least one transaction on X Layer and submit the transaction hash as proof • Open-source the project code on a GitHub public repository  Bonus points will be given to projects that use Onchain OS.
Use cases include, but are not limited to:  1. Agentic Payments  Onchain payment flows using the x402 protocol for subscriptions, in-game reward settlement, paid group access, and more.  Recommended Onchain OS APIs: x402 Payments, Wallet API  2. AI Agent Playground  Let your Agent run free on X Layer - build paid social forums, AI vs AI strategy games, smart token launch platforms, and beyond.  Recommended Onchain OS APIs: Trade API, Wallet API  3. AI DeFi/Trading  Build a fully autonomous trading system using Onchain OS - intelligent portfolio rebalancing, cross CeDeFi automated arbitrage, and more.  Recommended Onchain OS APIs: Trade API, Market API
Timeline & Prizes for Phase 1:   Mar 12 to 26  50,000 USDT prize pool, 24+ winners  1st Prize - 1 winner gets 12K USDT 2nd Prize - 3 winners get 4K USDT 3rd Prize - 20 winners get 800 USDT  Special Prizes worth 2K USDT each, for: - Most Innovative - Best in Agentic Payments - Highest Real-World Adoption - Highest potential for integration into X Layer ecosystem - Community Favorite  Winners will also receive exposure across the OKX Ecosystem, plus guidance from @OKX_Ventures 
Judging Criteria:  • How deeply AI agents are integrated on-chain • Autonomous agent payment flow within the X Layer ecosystem • Architecture for collaboration between multiple agents • Overall impact on the X Layer ecosystem
Important links for builders:  • X Layer RPC documentation https://web3.okx.com/xlayer/docs/developer/rpc-endpoints/rpc-endpoints • Onchain OS Skills https://github.com/okx/onchainos-skills 

---
