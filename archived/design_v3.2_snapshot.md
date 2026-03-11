## 🤖 System Prompt for GitHub Copilot
You are an expert Web3 and AI developer pairing with me to build **VeriTask 3.0**, a flagship project for the **OKX chainOS AI Hackathon (March 2026)**. 
Our goal is to build a "Claw-to-Claw (C2C) verifiable micro-procurement protocol". 
Before generating any code, you MUST understand the architecture and execute specific web searches to retrieve the latest 2026 API documentations.

---

## 🔍 PART 1: Pre-Implementation Research Directives (Verified 2026-03-07)

> ⚠️ All queries below have been **pre-researched and confirmed**. URLs and SDK names are accurate as of March 2026.
> Before implementing each module, fetch the linked documentation to retrieve the latest request/response schemas.

### 1. OKX x402 Payment REST API (Facilitator — Real Endpoints Confirmed)
- **Docs:** `https://web3.okx.com/onchainos/dev-docs/payments/x402-introduction`
- **Base URL:** `https://web3.okx.com`
- **Three endpoints:**
  - `GET  /api/v6/payments/supported/` — 获取支持的网络/代币
  - `POST /api/v6/payments/verify`    — 验证 EIP-712 签名 payload
  - `POST /api/v6/payments/settle`    — 提交链上结算（返回真实 txHash）
- **Auth headers (HMAC-SHA256):** `OK-ACCESS-KEY`, `OK-ACCESS-SIGN`, `OK-ACCESS-PASSPHRASE`, `OK-ACCESS-TIMESTAMP`
- **X Layer:** mainnet `chainIndex=196`, testnet `chainIndex=195`；支持代币：USDG / USDT / USDC
- **底层机制：** EIP-3009 `TransferWithAuthorization`（非 Permit2）— Payer 签名授权，OKX Facilitator 代付 gas

### 2. Coinbase x402 Open Standard (协议规范 + Python SDK)
- **GitHub:** `https://github.com/coinbase/x402` (5.6k stars)
- **Python SDK:** `pip install x402`（官方 SDK，非 OKX 专属）
- **Protocol Flow 参考:** `https://github.com/coinbase/x402/blob/main/README.md`
- OKX 扮演 `facilitator` 角色；x402 是基于 HTTP 的开放支付协议

### 3. OpenClaw Skills System (AgentSkills 格式)
- **Skills 文档:** `https://docs.openclaw.ai/skills`
- **Skill 结构：** 每个 Skill 是一个目录，包含 `SKILL.md`（YAML frontmatter + 指令正文）
- **最小格式：**
  ```yaml
  ---
  name: my-skill
  description: A one-line description shown to the agent
  metadata: {"openclaw": {"requires": {"bins": ["python"], "env": ["OKX_API_KEY"]}}}
  ---
  ```
- **加载位置优先级（高→低）：** `<workspace>/skills` → `~/.openclaw/skills` → bundled skills
- **Python 桥接：** Skills 通过 shell 命令调用 Python 脚本（subprocess 模式），SKILL.md 中直接写 `python skill.py` 调用指令
- **ClawHub 注册表:** `https://clawhub.ai` (可发布 Skill)

### 4. Phala Cloud CVM (TEE 真实集成方案)
- **文档:** `https://docs.phala.com/phala-cloud/attestation/quickstart`
- **dstack Python SDK:** `pip install dstack-sdk`
- **关键 API：** `TappdClient().tdx_quote(report_data: bytes)` → 返回 Intel TDX 硬件签名的 attestation quote
- **Worker 部署方式：** Docker 容器 → 推送到 Phala Cloud CVM（`cloud.phala.network`）→ 免费账户可用
- **本地开发：** 无法生成真实 attestation（需 TDX 硬件）；本地用 mock，CI/Demo 时切 Phala Cloud

### 5. Reclaim Protocol zkFetch (zkTLS — 后端可用)
- **文档:** `https://docs.reclaimprotocol.org/zkfetch`
- **SDK:** `npm install @reclaimprotocol/zk-fetch`
- **用途：** 在 Worker Node 内调用 DefiLlama REST API，生成携带 zkProof 的响应元组 `{redactedRequest, redactedResponse, zkProof}`
- **为何不用 zkPass TransGate：** TransGate 依赖 Chrome 浏览器扩展，不适合 CLI/后端无头场景

### 6. DefiLlama REST API (数据源)
- **无需认证：** `GET https://api.llama.fi/tvl/{protocol}` — 如 `/tvl/aave` 返回 Aave TVL
- **协议列表：** `GET https://api.llama.fi/protocols`

---

## 🏗️ PART 2: Project Architecture (VeriTask 3.0)

**Elevator Pitch:** VeriTask is a "Claw-to-Claw (C2C) verifiable micro-procurement protocol" for autonomous agents. A local OpenClaw agent (Client) outsources a data task to a TEE-isolated OpenClaw agent (Worker running on Phala Cloud CVM). The Worker returns cryptographic proofs of execution integrity, and the Client autonomously pays via OKX's x402 REST API, generating a real on-chain USDC transfer on X Layer with zero gas cost to the payer.

### Tech Stack (verified 2026-03-07)
|层 | 技术 | 状态 |
|---|------|------|
| Agent Framework | OpenClaw (Skills = SKILL.md + Python scripts) | ✅ 已验证可用 |
| **OnchainOS Skills** | **OKX OnchainOS CLI × 5 Skills（wallet/swap/market/token/gateway）** | **✅ CLI 全部可用** |
| Worker 运行环境 | Phala Cloud CVM (Intel TDX TEE, Docker 容器) | ✅ 免费账户可用 |
| TEE Attestation | `dstack-sdk` Python — `TappdClient().tdx_quote()` | ✅ 真实硬件签名 |
| zkTLS 数据来源证明 | Reclaim Protocol `@reclaimprotocol/zk-fetch` v0.8.0 | ✅ 真实 zkTLS attestor 签名已验证 |
| 支付协议 | OKX x402 REST API (Facilitator) — 真实端点 | ✅ 已确认 3 个端点 |
| 链 | OKX X Layer (EVM, chainIndex=196 mainnet / 195 testnet) | ✅ 有 Faucet |
| 签名方案 | EIP-712 + EIP-3009 `TransferWithAuthorization` | ✅ Python eth_account |
| 数据源 | DefiLlama REST API (无需认证) | ✅ 公开可用 |

### System Flow (Corrected):
```
User
  │  "Fetch Aave TVL and pay Worker"
  ▼
[Client Agent — Local OpenClaw]
  │  1. 用户输入触发 task_delegator Skill
  │  2. Client 构造 TaskIntent JSON，通过 HTTP 直发 Worker 的 REST endpoint
  ▼
[Worker Agent — Phala Cloud CVM (Intel TDX TEE)]
  │  3. 接收 TaskIntent
  │  4. 调用 DefiLlama API（通过 Reclaim zkFetch，生成 zkProof）
  │  5. 调用 dstack-sdk TappdClient.tdx_quote()（生成真实 TEE attestation）
  │  6. 返回 ProofBundle: {data, zk_proof, tee_attestation}
  ▼
[Client Verifier Skill]
  │  7. 验证 zk_proof 哈希（数据来源可信）
  │  8. 验证 tee_attestation quote（执行环境可信）
  ▼
[OKX x402 Payer Skill]
  │  9. Client 钱包用 eth_account 对 EIP-712 结构体签名
  │     (TransferWithAuthorization: from, to, value, validAfter, validBefore, nonce)
  │  10. POST /api/v6/payments/verify  → isValid = true
  │  11. POST /api/v6/payments/settle  → txHash (X Layer 真实链上交易)
  ▼
[终端输出] txHash + 区块浏览器链接 + 三层证明摘要
```

### OnchainOS-Enhanced System Flow (v3.2 — 全技能集成)

> **设计理念：** OpenClaw Agent 是 AI，不是死板的 Python 脚本。将全部 5 个 OnchainOS Skills 开放给 Agent，让 AI 根据上下文自主决策何时调用哪个 Skill。强制步骤确保核心流程完整，Agent 智能决策步骤体现 AI+Web3 的协同能力。

```
User
  │  "帮我抓一下 Aave 的 TVL，通过 Worker 验证，然后付款"
  ▼
┌─────────────── Step 0: OnchainOS 前置检查 ───────────────┐
│                                                           │
│  [强制] okx-wallet-portfolio                              │
│    onchainos portfolio token-balances                     │
│      --address <CLIENT_WALLET>                            │
│      --tokens "196:<USDT_CONTRACT>"                       │
│    → 检查 X Layer 上 USDT 余额是否 ≥ 支付金额            │
│                                                           │
│  [条件] 余额不足 → okx-dex-swap                          │
│    onchainos swap quote --from <OKB> --to <USDT>          │
│      --amount <needed> --chain xlayer                     │
│    → 询问用户确认 → onchainos swap swap 执行兑换          │
│                                                           │
│  [Agent智能决策：根据实际任务灵活调用] okx-dex-market / okx-dex-token │
│    onchainos market price <TOKEN_ADDR> --chain xlayer     │
│    onchainos token price-info <TOKEN_ADDR> --chain xlayer │
│    onchainos market signal-list xlayer                    │
│    → 获取参考市场数据（价格/信号/流动性），                │
│      为后续 cross-verify workers交付物 做准备               │
│                                                           │
└───────────────────────────────────────────────────────────┘
  │
  ▼
Step 1: 构造 TaskIntent（携带 OnchainOS 参考数据）
  │  task_delegator.py 构造 TaskIntent JSON
  │  附加 OnchainOS 参考数据（市场价格、智能资金信号等）
  ▼
Step 2: 委托 Worker（Phala Cloud CVM 执行）
  │  HTTP POST → Worker /execute
  │  Worker 在 TEE 内：DefiLlama zkFetch + TDX attestation
  │  返回 ProofBundle: {data, zk_proof, tee_attestation}
  ▼
Step 3: 验证密码学证明 + Agent 智能 Cross-Verify
  │  verifier.py 验证 zk_proof + tee_attestation
  │  [Agent智能决策] 若 Step 0 获取了 market/token 参考数据：
  │    → 对比 Worker 返回的 TVL 与 OnchainOS 市场数据
  │    → 多源交叉验证增强数据可信度
  ▼
Step 3.5: OnchainOS Gas 估算
  │  onchainos gateway gas --chain xlayer
  │  → 展示当前 X Layer gas 费（base fee + priority fee）
  │  → 说明 OKX x402 facilitator 代付 gas（Payer 零成本）
  │  → 用户直观理解 x402 gasless 支付的经济优势
  ▼
Step 4: x402 支付（真实 mainnet txHash）
  │  EIP-712 签名 → POST /verify → POST /settle
  │  → 返回 txHash（X Layer mainnet 链上交易）
  ▼
Step 5: OnchainOS 交易追踪
  │  onchainos gateway orders --address <CLIENT_WALLET> --chain xlayer
  │  → 跟踪交易状态（Pending→Success）
  │  → 若 x402 facilitator tx 不在 gateway orders 中，
  │    直接用 txHash + 区块浏览器链接展示
  ▼
[终端输出]
  ✅ 完整 ProofBundle（zkTLS + TDX attestation）
  ✅ txHash + 区块浏览器链接
  ✅ OnchainOS 参考报告（余额/市场/gas 概览）
```

#### OnchainOS Skills 映射表

| Step | OnchainOS Skill | CLI 命令 | 调用模式 | 说明 |
|------|----------------|---------|---------|------|
| 0 | okx-wallet-portfolio | `onchainos portfolio token-balances --address <WALLET> --tokens "196:<USDT>"` | **强制** | 支付前余额预检 |
| 0 | okx-dex-swap | `onchainos swap quote` → `onchainos swap swap` | **条件** | USDT 余额不足时自动换币 |
| 0 / 3 | okx-dex-market | `onchainos market price` / `signal-list` | Agent 决策 | 实时价格 + 智能资金信号 |
| 0 / 3 | okx-dex-token | `onchainos token price-info` / `trending` | Agent 决策 | 市值/流动性/持仓分布 |
| 3.5 | okx-onchain-gateway | `onchainos gateway gas --chain xlayer` | **强制** | 展示 gas 费 + gasless 优势 |
| 5 | okx-onchain-gateway | `onchainos gateway orders --address <WALLET> --chain xlayer` | **强制** | 交易状态追踪 |

> **关于 OKX OnchainOS（更新 2026-03-09）：** OKX OnchainOS 的 Wallet/Payment **MCP** Skills 处于 "Coming Soon" 状态，但 **CLI-based Skills**（onchainos 命令行工具）5 个全部可用。本项目通过 OpenClaw Agent 集成 onchainos CLI 调用，实现全部 5 个 OnchainOS Skills 的有机融合。x402 支付仍直接调用 REST API（因 Payment MCP 未上线），其余流程通过 onchainos CLI 完成。

---

## 🎯 PART 3: Hackathon MVP Scope (1-Week Constraints)

**核心策略：** 在 1 周内完成"三层可验证"的端到端 Demo。技术深度 > 完成度，但每层都要有真实的可演示产出。

### ✅ REAL（必须真实运行，不可 mock）

| 模块 | 具体要求 |
|------|---------|
| **OKX x402 支付** | 必须调用真实 `/api/v6/payments/verify` + `/settle`，产出真实 X Layer txHash |
| **TEE Attestation** | Worker 部署到 Phala Cloud CVM，用 `dstack-sdk` 生成真实 Intel TDX 硬件签名 quote |
| **DefiLlama 数据** | `GET https://api.llama.fi/tvl/aave` 返回真实 TVL 数字 |
| **EIP-712 签名** | 用 `eth_account.sign_typed_data()` 生成真实 ECDSA 签名（不可用随机 bytes 替代）|

### 🟡 SIMPLIFIED（简化但保留技术标识）

| 模块 | 简化策略 |
|------|---------|
| **Reclaim zkFetch** | 集成 SDK v0.8.0，已在 CVM 生产环境生成真实 zkTLS 证明（attestor 节点 `wss://attestor.reclaimprotocol.org:444/ws` 签名确认）；fallback 到 SHA256 mock 保留作容错 |
| **Worker REST Server** | 用 Python Flask/FastAPI 模拟 Worker 的 HTTP 服务（不需要正式 k8s 部署），重点是 Phala Cloud CVM 上能跑即可 |

### ❌ OUT OF SCOPE（本次不做）

- Web UI（纯 CLI 即可）
- OKX MCP 层对接（尚未上线）
- 自定义 ZK 电路（Reclaim zkFetch 已封装）
- 多 Worker 负载均衡
- 真实 Multi-agent 任务调度

### 🚦 开发节奏（testnet → mainnet）

1. **Days 1-5（开发期）：** 所有 x402 调用使用 X Layer **testnet**（chainIndex=195），Faucet 领取测试 USDG
2. **Day 6（Demo 录制前）：** 切换到 X Layer **mainnet**（chainIndex=196），用真实 USDC 执行一笔完整 Demo 交易
3. **提交物：** README 中附上真实 mainnet txHash + 区块浏览器截图

### 🔥 优先级砍线（时间不够时按序砍）

```
必须保留（不可砍）：
⭐1. OKX x402 真实支付 → 这是黑客松核心评分项
⭐2. Phala Cloud TEE 真实 attestation → 差异化竞争力

可以简化（时间不够时）：
3. Reclaim zkFetch → 改为 SHA256 data hash + 说明"未来用 zkFetch 替换"
4. 完整 OpenClaw Skill 集成 → 退化为 Python CLI 脚本，保留 SKILL.md 框架

绝对不做（防止时间黑洞）：
5. 调试 OKX testnet 失败超过 4 小时 → 立即切 mainnet 少量测试
6. Reclaim zkFetch 配置问题超过 8 小时 → 直接 fallback mock
```

---

## 📂 PART 4: Project Structure (Corrected)

**关键约束：**
- OpenClaw Skill = 一个目录 + `SKILL.md` 文件（内含 YAML frontmatter 和调用指令）
- Python 脚本放在 Skill 目录内，由 `SKILL.md` 中的 shell 命令调用
- Worker Node 必须提供 `Dockerfile`（Phala Cloud CVM 部署要求）
- 所有私钥/API Key 存 `.env`，绝不提交 config.json 明文密钥

```text
veritask-monorepo/
├── .env.example              # 模板：OKX_API_KEY, WORKER_PRIVATE_KEY, RECLAIM_APP_ID 等
├── .gitignore                # 包含 .env, __pycache__, node_modules
├── README.md                 # Pitch + 架构图 + mainnet txHash 证明
│
├── schemas/                  # 共享数据模型（JSON Schema）
│   ├── task_intent.json      # C2C 任务格式：{task_id, type, params, client_wallet}
│   └── proof_bundle.json     # 证明包格式：{data, zk_proof, tee_attestation, timestamp}
│
├── client_node/              # Client Agent（本地 OpenClaw 实例）
│   ├── skills/
│   │   ├── task-delegator/   # Skill 目录（OpenClaw AgentSkills 格式）
│   │   │   ├── SKILL.md      # frontmatter: name/description/metadata + 调用指令
│   │   │   └── task_delegator.py  # 构造 TaskIntent，HTTP POST → Worker
│   │   ├── verifier/
│   │   │   ├── SKILL.md
│   │   │   └── verifier.py   # 验证 zk_proof hash + tee_attestation quote
│   │   └── okx-x402-payer/
│   │       ├── SKILL.md
│   │       ├── okx_x402_payer.py  # EIP-712 签名 + OKX /verify + /settle
│   │       └── okx_auth.py   # HMAC-SHA256 header 生成工具
│   └── openclaw.json         # Client 的 OpenClaw 配置（skills.entries + env）
│
├── worker_node/              # Worker Agent（部署到 Phala Cloud CVM）
│   ├── Dockerfile            # Python 3.11 + dstack-sdk + Node.js（供 zkfetch 使用）
│   ├── docker-compose.yml    # 本地测试用
│   ├── server.py             # FastAPI 服务：POST /execute → 返回 ProofBundle
│   ├── skills/
│   │   ├── defi-scraper/
│   │   │   ├── SKILL.md
│   │   │   └── defi_scraper.py    # GET https://api.llama.fi/tvl/{protocol}
│   │   └── proof-generator/
│   │       ├── SKILL.md
│   │       ├── proof_generator.py # 调用 zkfetch_bridge.js + dstack tdx_quote
│   │       └── zkfetch_bridge.js  # Node.js: Reclaim zkFetch 包装（供 Python subprocess 调用）
│   └── requirements.txt      # dstack-sdk, fastapi, eth-account, requests
│
├── package.json              # @reclaimprotocol/zk-fetch（worker_node/zkfetch_bridge.js 依赖）
└── run_demo.ps1              # Windows PowerShell: 端到端 Demo 脚本（含彩色输出）
```

**各模块对应关系速查：**
| 模块名 | 类型 | 主要依赖 | 真实/Mock |
|--------|------|---------|----------|
| `task_delegator.py` | Client Skill | requests | 真实 HTTP 调用 |
| `verifier.py` | Client Skill | eth_account, base64 | 真实哈希验证 |
| `okx_x402_payer.py` | Client Skill | eth_account, requests, hmac | **真实链上支付** |
| `defi_scraper.py` | Worker Skill | requests | 真实 DefiLlama API |
| `zkfetch_bridge.js` | Worker bridge | @reclaimprotocol/zk-fetch | **真实 zkTLS attestor 签名** |
| `proof_generator.py` | Worker Skill | dstack-sdk, subprocess | **真实 TDX quote** |

---

## 🛠️ PART 5: Step-by-Step Implementation Tasks

**在明确说"进入实现阶段"之前不写代码。每个 Task 完成后等待确认。**

---

### Task 0: 环境准备（前置，Day 1 上午）
1. `python -m venv .venv && .venv\Scripts\activate`
2. `pip install dstack-sdk eth-account fastapi uvicorn requests python-dotenv`
3. `npm install @reclaimprotocol/zk-fetch`
4. 创建 `.env` 文件（参照 `.env.example`），填入 OKX API Key 和两个测试钱包私钥
5. 注册 Phala Cloud 免费账户（`cloud.phala.network`），记录 API token
6. 用 OKX X Layer Faucet（`https://web3.okx.com/xlayer/faucet`）领取测试 USDG

---

### Task 1: Worker — DefiLlama 数据抓取 Skill
**文件：** `worker_node/skills/defi-scraper/defi_scraper.py` + `SKILL.md`

要点：
- 调用 `GET https://api.llama.fi/tvl/aave`（无需 Auth）
- 返回标准化 `DataResult` dict：`{protocol, tvl_usd, fetched_at, source_url}`
- 控制台彩色输出：`[Worker] 🌐 Fetching Aave TVL from DefiLlama...`

验收标准：`python defi_scraper.py` 能打印出真实 TVL 数字

---

### Task 2: Worker — Proof Generator Skill（TEE Attestation + zkFetch）
**文件：** `worker_node/skills/proof-generator/proof_generator.py` + `zkfetch_bridge.js`

要点（严格分两层）：

**Layer 1 — Reclaim zkFetch（数据来源证明）：**
- `zkfetch_bridge.js` 调用 `ReclaimClient.zkFetch()` 请求 DefiLlama，输出 `zkProof` JSON
- `proof_generator.py` 通过 `subprocess` 调用 `node zkfetch_bridge.js`，读取 stdout
- fallback：若 Reclaim 失败，改为 `{"type": "sha256_mock", "hash": sha256(data), "note": "fallback"}`

**Layer 2 — Phala dstack TEE Attestation（执行环境证明）：**
- `from dstack_sdk import TappdClient`
- `report_data = sha256(json.dumps(data_result)).digest()`
- `quote = await TappdClient().tdx_quote(report_data=report_data)`
- 本地开发 fallback：`{"type": "mock_tdx", "report_data": hex, "note": "deploy to Phala Cloud for real attestation"}`

输出 `ProofBundle`：`{task_id, data, zk_proof, tee_attestation, worker_pubkey, timestamp}`
控制台输出：`[Worker-TEE] 🔐 Intel TDX quote generated` / `[Worker-zkTLS] ✅ zkProof generated`

---

### Task 3: Worker — FastAPI Server（`server.py`）
**文件：** `worker_node/server.py`

要点：
- `POST /execute` → 接收 `TaskIntent`，调用 Task 1 + Task 2，返回 `ProofBundle`
- `GET /health` → 返回 `{"status": "ok", "tee": true/false}`
- 处理超时，最大执行 30 秒

验收标准：`uvicorn server:app --port 8001` 启动，curl 能拿到 ProofBundle

---

### Task 4: Client — 验证器 Skill
**文件：** `client_node/skills/verifier/verifier.py` + `SKILL.md`

要点：
- 接收 `ProofBundle`
- 验证 `zk_proof.hash == sha256(data)`（数据完整性）
- 验证 `tee_attestation.type`：若为真实 TDX quote，调用 base64 decode 并打印 quote 摘要
- 返回 `{is_valid: bool, reason: str}`
- 输出：`[Client-Verifier] ✅ ZK-Proof VALID. Data integrity confirmed.` / `[Client-Verifier] ✅ TEE Attestation: Intel TDX CVM verified.`

---

### Task 5: Client — OKX x402 支付 Skill（**核心！**）
**文件：** `client_node/skills/okx-x402-payer/okx_x402_payer.py` + `okx_auth.py` + `SKILL.md`

**okx_auth.py**（独立工具，可复用）：
- 实现 `build_okx_headers(api_key, secret, passphrase, method, path, body)` → 返回 HMAC-SHA256 签名 header dict

**okx_x402_payer.py**：
1. 构造 EIP-712 typed data struct（`TransferWithAuthorization`）：
   - domain: `{name: "USD Coin", version: "2", chainId: 195, verifyingContract: <USDC_testnet>}`
   - message: `{from, to, value, validAfter, validBefore, nonce}`
2. `eth_account.sign_typed_data(private_key, domain_data, types, message)` → 得到 `v, r, s`
3. `POST https://web3.okx.com/api/v6/payments/verify` → 断言 `isValid == true`
4. `POST https://web3.okx.com/api/v6/payments/settle` → 得到 `txHash`
5. 输出：`[Client-x402] 💸 Settling 1 USDC → Worker on X Layer...` 和最终 txHash + 浏览器链接

---

### Task 6: OpenClaw Skill 配置文件（SKILL.md）
**为 4 个 Skill 各写 SKILL.md（frontmatter + 调用指令）**

示例格式（`okx-x402-payer/SKILL.md`）：
```markdown
---
name: okx-x402-payer
description: Pay Worker via OKX x402 protocol on X Layer after proof verification
metadata: {"openclaw": {"requires": {"env": ["OKX_API_KEY", "CLIENT_PRIVATE_KEY"]}, "emoji": "💸"}}
---

## Usage
Run: `python {baseDir}/okx_x402_payer.py --to <worker_wallet> --amount <usdc_amount>`
```

---

### Task 7: Demo 脚本 `run_demo.ps1`（Windows PowerShell）

要点：
- 启动 Worker（后台进程），等待 `/health` 就绪
- 以彩色文字显示每个阶段（Write-Host -ForegroundColor Cyan/Green/Yellow）
- 插入 `Start-Sleep -Seconds 2` 模拟网络延迟
- 最终打印 txHash 和区块浏览器链接
- 结束时清理 Worker 进程

---

## 📅 PART 6: Implementation Roadmap (7-Day Plan)

> 所有代码均在明确进入实现阶段后才开始编写。本 Roadmap 是实现启动时的执行顺序。

### Day 1 — 环境 + Worker 数据层（Task 0 + Task 1）
- [ ] 配置 Python venv，安装所有依赖
- [ ] 注册 Phala Cloud 账户，获取 API token
- [ ] 领取 X Layer testnet USDG
- [ ] 实现并测试 `defi_scraper.py`（验收：打印真实 Aave TVL）
- [ ] 搭建 Worker `server.py` 框架（FastAPI `/health` + `/execute` 空实现）

**Day 1 验收门槛：** `GET https://api.llama.fi/tvl/aave` 返回真实数字，Worker server 启动无报错

---

### Day 2 — TEE Attestation 集成（Task 2 Layer 2）
- [ ] 实现 `proof_generator.py`（本地 mock 版 attestation）
- [ ] 编写 `Dockerfile`，构建 Worker Docker 镜像
- [ ] 部署镜像到 Phala Cloud CVM，测试 `/health` 返回 `"tee": true`
- [ ] 验证 `TappdClient().tdx_quote()` 返回真实 quote

**Day 2 验收门槛：** Phala Cloud CVM 上运行，打印带 TDX quote 的 `tee_attestation` JSON

---

### Day 3 — Reclaim zkFetch 集成（Task 2 Layer 1）
- [ ] 实现 `zkfetch_bridge.js`，测试 Reclaim APP_ID 配置
- [ ] 实现 Python `subprocess` 调用 bridge，解析 zkProof JSON
- [ ] 实现 fallback 机制（Reclaim 失败 → SHA256 mock）
- [ ] Worker `/execute` 完整实现返回 `ProofBundle`

**Day 3 验收门槛：** 单独 `curl POST /execute` 返回包含 `zk_proof` + `tee_attestation` 的完整 JSON

---

### Day 4 — Client 验证器 + x402 支付核心（Task 3 + Task 4 + Task 5）
- [ ] 实现 `okx_auth.py` HMAC-SHA256 签名
- [ ] 实现 EIP-712 `TransferWithAuthorization` 签名（testnet）
- [ ] 调用 `/api/v6/payments/verify`，断言 `isValid == true`
- [ ] 调用 `/api/v6/payments/settle`，获取真实 testnet txHash
- [ ] 实现 `verifier.py`，验证 `ProofBundle`

**Day 4 验收门槛：** 获得 X Layer testnet txHash，OKX 区块浏览器可查到交易

---

### Day 5 — OpenClaw Skill 集成（Task 6）
- [ ] 为 4 个 Skill 各编写 `SKILL.md`（frontmatter + 调用指令）
- [ ] 在本地 OpenClaw 实例加载 Skills，用自然语言触发端到端流程
- [ ] 调试 SKILL 环境变量注入（`.env` → `openclaw.json`）

**Day 5 验收门槛：** 在 OpenClaw CLI 中输入 "Fetch Aave TVL and pay Worker" 能完整跑通流程

---

### Day 6 — Mainnet 验证 + Demo 录制（Task 7）
- [ ] 切换 chainIndex 196（mainnet），准备少量 USDC
- [ ] 执行一笔 mainnet 真实付款，记录 txHash
- [ ] 完成 `run_demo.ps1`，调整彩色输出节奏
- [ ] 录制 Demo 视频（CLI 全程终端录屏）

**Day 6 验收门槛：** mainnet txHash 可在 `https://www.oklink.com/xlayer` 查询，0 gas fee 确认

---

### Day 7 — README + 提交材料
- [ ] 写 README：Elevator Pitch + 架构图 + 三层证明说明 + txHash 截图
- [ ] 写 Future Roadmap（OKX MCP 集成、多 Worker 调度、任意 Skill 扩展）
- [ ] 上传 skills 到 ClawHub（可选）
- [ ] 提交黑客松项目

---

## 🧠 PART 7: Agent 自决策交叉验证设计（Cross-Verification Intelligence Design）

> 本节记录 VeriTask 3.2 中 Agent 自主交叉验证能力的设计决策与理论依据。
> 这不仅是工程实现，更是对 **"AI Agent 如何在工具丰富的环境中自主决策"** 这一核心问题的系统性回答。

### 核心问题

VeriTask C2C 流程中，Agent 拥有 5 个 OKX OnchainOS Skills（30+ CLI 命令），但大多数任务只需其中 2-3 个。

**关键挑战：Agent 如何知道它"应该"调用哪些 OnchainOS 命令来交叉验证 Worker 交付物？**

朴素方案及其缺陷：
- ❌ **硬编码触发条件**（if TVL → call market price）：不可扩展，无法应对新 Skill 或新任务类型
- ❌ **全部标记"可选"**（Agent 决策）：LLM 倾向走最短路径，几乎不会主动调用不被强制要求的工具

### 设计哲学：结构化强制 + 泛化推理

我们的解决方案：**不是告诉 Agent "什么时候该调用"，而是教会 Agent "如何判断该不该调用"。**

这借鉴了三个关键研究成果：

#### 参考 1: Anthropic — "Building Effective Agents" (2024.12)

> Appendix 2 *Prompt Engineering Your Tools* 核心观点：
> - **"Put yourself in the model's shoes"** — 如果你面对一个工具描述，你能否判断什么情况下应该使用它？
> - **Example usage** 是提升工具调用准确率的最有效手段
> - **Poka-yoke design**（防呆设计）— 让工具和提示词在结构上难以被误用
>
> 来源: https://www.anthropic.com/research/building-effective-agents

**VeriTask 应用：**
- 在 SKILL.md 的 OnchainOS 交叉验证策略中，采用 **推理三步法**（Step A 分解交付物 → Step B 关联映射 → Step C 收集对比），这是让 Agent "站在用户角度" 理解交付物与工具关系的结构化方法
- 用 3 个完整推理示例（正例 × 2 + 负例 × 1）教会 Agent pattern，而非规则
- **防呆设计**：Cross-Verify 字段设为必填且有严格格式（逐维度 `OnchainOS=[值] vs Worker=[值] → [判断]`），Agent 无法跳过推理直接输出空结论

#### 参考 2: Anthropic — "Advanced Tool Use" (2025.11)

> 关键发现：
> - **Tool Use Examples 将复杂参数处理的准确率从 72% 提升到 90%**（+18pp）
> - **"Document return formats clearly"** — Agent 需要知道命令返回什么结构、如何提取关键字段
> - System prompt 中应 **显式声明 Agent 可用的全部工具**（Tools Panorama）
>
> 来源: https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview

**VeriTask 应用：**
- 在 SKILL.md CLI 命令参考中为 3 个关键命令添加了 **返回格式注释**（`portfolio token-balances` → tokenAssets[] 字段说明；`token price-info` → 20+ 字段说明；`market price` → 价格值说明）
- 在交叉验证策略段落顶部添加了 **工具全景声明**："你当前有 5 个 OKX OnchainOS Skills 可用 — [列表]。未来若有新 Skills 加入，你同样必须纳入考量。"
- 3 个推理示例直接展示了从 CLI 输出到验证结论的完整推理链，对标 Anthropic 的 Tool Use Examples 最佳实践

#### 参考 3: ReAct — "Synergizing Reasoning and Acting in Language Models" (Yao et al., ICLR 2023)

> 核心模式：**交错的 Thought → Action → Observation** 推理链
> - Thought: Agent 分析当前状态，规划下一步
> - Action: 调用外部工具
> - Observation: 读取工具返回值，修正推理
>
> 来源: https://arxiv.org/abs/2210.03629

**VeriTask 应用：**
推理三步法本质上是 ReAct 模式的领域特化版本：

| ReAct 通用模式 | VeriTask 推理三步法 | 示例 |
|---|---|---|
| Thought（分析） | Step A — 分解交付物 | "Worker 返回了 TVL = $26.2B" |
| Thought → Action Plan | Step B — 关联映射 | "TVL 与市值有关，OnchainOS ✅ token price-info" |
| Action + Observation | Step C — 收集 & 对比 | "执行命令 → market_cap: $4.1B → TVL/MC = 6.4x → 合理" |

### 关键设计决策

#### 决策 1："强制尝试" vs "可选" vs "硬编码"

| 方案 | 问题 |
|------|------|
| "Agent 决策"（可选） | LLM 倾向走最短路径，几乎不会主动调用 |
| 硬编码触发条件 | 无法扩展到新任务类型或新 Skills |
| **"强制（交叉验证尝试）"** ✅ | Agent 必须尝试推理，但允许结论为"无可用数据" — 既防止跳过，又不强制造假 |

我们将 `okx-dex-market` 和 `okx-dex-token` 的调用模式从 "推荐（交叉验证）" 改为 **"强制（交叉验证尝试）"**，在路由表、Cross-Skill 表、Operation Flow、CLI 注释 4 处同步更新。"尝试" 一词是关键 — 它保留了以下容错路径：
- OnchainOS 命令超时/失败 → 标注跳过，不阻塞流程
- 交付物类型无对应链上数据源 → 结论为 "⚠️ 无可用数据"，仅依赖密码学验证

#### 决策 2：结构化结论字段替代 Thought Trace

传统 ReAct 输出中会包含完整的 Thought 段。但在 VeriTask 的终端 / Telegram 输出场景中：

| 方案 | 问题 |
|------|------|
| 输出完整 Thought 段 | 冗长，终端用户不关心内部推理过程 |
| 完全不输出推理 | Agent 可能跳过推理步骤（无输出约束 = 无推理动力） |
| **结构化必填结论字段** ✅ | Agent 为了生成正确的 Cross-Verify 格式，必须先内部完成完整推理链 |

我们设计了 **"隐式 ReAct"** 方案：推理过程不可见但必然发生。

Cross-Verify 输出字段的强制格式：
```
· [数据维度]: OnchainOS=[具体数值] vs Worker=[具体数值] → [✅/⚠️/❌](原因)
· 综合判定: [✅交付物合理/⚠️存在偏差但可接受/❌严重矛盾建议暂停付款]
```

Agent 为了正确填写每一维度的 `OnchainOS=[具体数值]`，**必须先执行对应的 onchainos 命令并解析返回值**。结论字段的格式本身就是推理链的"强制检查点"。

#### 决策 3：多样化示例策略（2 正 + 1 负）

| 示例 | 任务类型 | 交叉验证维度 | 教学目的 |
|------|---------|-------------|---------|
| **Example 1** — TVL 正例 | 协议 TVL | 市值、流动性、智能资金 | 基础 pattern：市值/流动性 vs TVL |
| **Example 2** — Token 持仓正例 | 持仓分布 | 持有人数、交易量、链上分布 | 泛化能力：不同数据维度的交叉验证 |
| **Example 3** — 治理投票负例 | 链下治理数据 | ❌ 无可用数据源 | **防幻觉**：不是所有数据都能验证，不要强行关联 |

> Anthropic 研究表明：Tool Use Examples 是提升准确率最有效的手段（72% → 90%）。
> 3 个示例覆盖了 "能验证" + "能验证但维度不同" + "不能验证" 三种情况，
> Agent 由此学到的是 **推理方法** 而非 **固定规则**。

### 可扩展性

本设计具备以下前向兼容性：

1. **新 OnchainOS Skills**：工具全景声明 + 推理三步法 → Agent 自动将新 Skill 纳入交叉验证候选
2. **新任务类型**：推理三步法是通用框架（分解→关联→对比），不绑定特定数据类型
3. **更多示例**：可在 SKILL.md 中持续添加推理示例，覆盖更多 edge case
4. **替换验证引擎**：Cross-Verify 的结构化格式独立于具体 OnchainOS 命令，底层工具可替换

### 技术实现汇总

| 改动项 | 位置 | 理论依据 |
|--------|------|---------|
| 路由表 "推荐" → "**强制**（交叉验证尝试）" | SKILL.md × 4 处 | 防止 LLM 最短路径 |
| 工具全景声明 | SKILL.md 交叉验证策略段顶部 | Anthropic: 显式声明可用工具 |
| CLI 返回格式注释 | SKILL.md 命令参考 × 3 条 | Anthropic: document return formats clearly |
| 推理三步法（Step A/B/C） | SKILL.md 交叉验证策略段 | ReAct pattern 领域特化 |
| 结构化 Cross-Verify 字段 | SKILL.md 输出模板 | 隐式 ReAct — 结论字段强制推理 |
| 3 个推理示例（2正1负） | SKILL.md 交叉验证策略段 | Anthropic: Tool Use Examples (+18pp) |

---

## 🏆 评分维度自检

| 黑客松评分项 | 本项目对应内容 | 预期得分 |
|------------|--------------|---------|
| **OKX 结合度** | x402 真实支付 + **OnchainOS 5 Skills 全集成** + Agent 自决策交叉验证 | ⭐⭐⭐⭐⭐ |
| **实用性** | Agent 经济的可验证微任务外包，真实 DeFi 数据场景 | ⭐⭐⭐⭐ |
| **创新性** | TEE + zkTLS + x402 三重证明 + **OnchainOS 交叉验证智能**（首创 C2C 协议） | ⭐⭐⭐⭐⭐ |
| **可复制性** | SKILL.md 可上传 ClawHub，其他用户一键安装 | ⭐⭐⭐⭐ |
