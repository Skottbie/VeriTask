# VeriTask 3 — Design Document

> **Version**: 3.5.0 (Active)  
> **Last Updated**: 2026-03-12  
> **Project**: VeriTask — Claw-to-Claw (C2C) Verifiable Micro-Procurement Protocol  
> **Hackathon**: OKX OnchainOS "AI松" (March 2026)  
> **Stack**: Python 3.12 + Node.js + OpenClaw + OKX OnchainOS Skills  
> **Author**: [@eazimonizone](https://x.com/eazimonizone) · [Skottbie](https://github.com/Skottbie/)  
> **Archived Snapshots**: `archived/design_v3.0_snapshot.md`, `archived/design_v3.2_snapshot.md`

---

## 📑 Table of Contents

| #   | Section | Description | Lines |
|-----|---------|-------------|-------|
| 0   | [Context](#-system-prompt-for-github-copilot) | AI Assistant context & project identity | L45 |
| 1   | [PART 1: Research Directives](#-part-1-pre-implementation-research-directives-verified-2026-03-07) | Pre-researched API docs: OKX x402, OpenClaw, Phala CVM, Reclaim zkFetch, DefiLlama | L52 |
| 2   | [PART 2: Architecture](#️-part-2-project-architecture-veritask-30) | Tech stack, base system flow, OnchainOS-enhanced flow (v3.2), skills mapping | L109 |
| 3   | [PART 3: MVP Scope](#-part-3-hackathon-mvp-scope-1-week-constraints) | Real vs Simplified vs Out-of-Scope; dev rhythm; priority cutline | L237 |
| 4   | [PART 4: Project Structure](#-part-4-project-structure-corrected) | Directory layout, module dependency matrix | L289 |
| 5   | [PART 5: Implementation Tasks](#️-part-5-step-by-step-implementation-tasks) | Tasks 0–7: Worker, Client, Payment, Demo | L367 |
| 6   | [PART 6: Roadmap](#-part-6-implementation-roadmap-7-day-plan) | Day-by-day 7-day implementation plan | L485 |
| 7   | [PART 7: Cross-Verification Design](#-part-7-agent-自决策交叉验证设计cross-verification-intelligence-design) | Agent intelligence theory: ReAct, Anthropic best practices, structured reasoning | L558 |
| 8   | [PART 8: Dual-Model Routing](#-part-8-双模型智能路由设计dual-model-verification-routing-design) | Pro/Flash orchestration, RouteLLM theory, implementation details | L693 |
| 9   | [PART 9: Version Corrections](#-part-9-version-correction-log-v33v341) | v3.3.2 Pro Agent binding, Token anti-hallucination, v3.4.0 Anti-Fabrication, v3.4.1 fixes | L855 |
| 10  | [Score Self-Check](#-评分维度自检) | Hackathon scoring dimensions self-assessment | L1080 |

### Quick Reference — Key Technical Facts

| Item | Value |
|------|-------|
| Client Wallet | `0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85` (X Layer) |
| Worker Wallet | `0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb` |
| USDT Contract (X Layer) | `0x779ded0c9e1022225f8e0630b35a9b54be713736` |
| X Layer Chain Index | 196 (mainnet) / 195 (testnet) |
| Worker CVM URL | `https://...dstack-pha-prod9.phala.network` |
| OKX x402 Base URL | `https://web3.okx.com` |
| Payment Protocol | EIP-712 + EIP-3009 `TransferWithAuthorization` |
| Agent Framework | OpenClaw 2026.3 (SKILL.md + Python scripts) |
| Main Agent Model | `gemini-3-flash-preview` (orchestrator) |
| Pro Agent Model | `gemini-3.1-pro-preview` (reasoning) |

---

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
- **Three endpoints（实测确认 2026-03）:**
  - `GET  /api/v6/x402/supported` — 获取支持的网络/代币
  - `POST /api/v6/x402/verify`    — 验证 EIP-712 签名 payload
  - `POST /api/v6/x402/settle`    — 提交链上结算（返回真实 txHash）
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
- **关键 API：** `AsyncDstackClient().get_quote(report_data: bytes)` → 返回 Intel TDX 硬件签名的 attestation quote（dstack-sdk ≥0.1.0 已更名，旧 `TappdClient` 已弃用）
- **Worker 部署方式：** Docker 容器 → 推送到 Phala Cloud CVM（`cloud.phala.network`）→ 免费账户可用
- **本地开发：** 无法生成真实 attestation（需 TDX 硬件）；本地用 mock，CVM 部署时自动使用真实 TDX

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

**Elevator Pitch:** VeriTask is a "Claw-to-Claw (C2C) verifiable micro-procurement protocol" for autonomous agents. A local OpenClaw agent (Client) outsources a data task to a TEE-isolated OpenClaw agent (Worker running on Phala Cloud CVM). The Worker returns cryptographic proofs of execution integrity, and the Client autonomously pays via OKX's x402 REST API, generating a real on-chain stablecoin transfer (USDT/USDC/USDG) on X Layer with zero gas cost to the payer.

### Tech Stack (verified 2026-03-07)
|层 | 技术 | 状态 |
|---|------|------|
| Agent Framework | OpenClaw (Skills = SKILL.md + Python scripts) | ✅ 已验证可用 |
| **OnchainOS Skills** | **OKX OnchainOS CLI × 5 Skills（wallet/swap/market/token/gateway）** | **✅ CLI 全部可用** |
| Worker 运行环境 | Phala Cloud CVM (Intel TDX TEE, Docker 容器) | ✅ 免费账户可用 |
| TEE Attestation | `dstack-sdk` Python — `AsyncDstackClient().get_quote()` | ✅ 真实硬件签名 |
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

## 🎯 PART 3: Hackathon MVP Scope (Constraints)

**核心策略：** 完成"三层可验证"的端到端 Demo。每层都要有真实的可演示产出。


| 模块 | 具体要求 |
|------|---------|
| **OKX x402 支付** | 必须调用真实 `/api/v6/payments/verify` + `/settle`，产出真实 X Layer txHash |
| **TEE Attestation** | Worker 部署到 Phala Cloud CVM，用 `dstack-sdk` 生成真实 Intel TDX 硬件签名 quote |
| **DefiLlama 数据** | `GET https://api.llama.fi/tvl/aave` 返回真实 TVL 数字 |
| **EIP-712 签名** | 用 `eth_account.sign_typed_data()` 生成真实 ECDSA 签名（不可用随机 bytes 替代）|


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
├── AGENTS.md                 # Multi-Agent 路由规则（OpenClaw Gateway 读取）
├── CLAUDE.md                 # AI 助手项目指引
│
├── schemas/                  # 共享数据模型（JSON Schema）
│   ├── task_intent.json      # C2C 任务格式：{task_id, type, params, client_wallet}
│   └── proof_bundle.json     # 证明包格式：{data, zk_proof, tee_attestation, timestamp}
│
├── .agents/skills/           # OKX OnchainOS Skills（npx skills add okx/onchainos-skills 安装）
│   ├── okx-wallet-portfolio/ # 钱包余额查询
│   ├── okx-dex-swap/         # DEX 聚合换币
│   ├── okx-dex-market/       # 实时行情 + 智能资金信号
│   ├── okx-dex-token/        # Token 搜索/市值/流动性
│   └── okx-onchain-gateway/  # Gas 估算 + 交易广播/追踪
│
├── client_node/              # Client Agent（本地 OpenClaw 实例）
│   ├── skills/
│   │   ├── task-delegator/   # Skill 目录（OpenClaw AgentSkills 格式）
│   │   │   ├── SKILL.md      # frontmatter: name/description/metadata + 调用指令（v3.5.0）
│   │   │   ├── task_delegator.py       # 构造 TaskIntent，HTTP POST → Worker
│   │   │   └── swap_and_broadcast.py   # DEX swap 完整流程：approve→swap→sign→broadcast（onchainos CLI）
│   │   ├── verifier/
│   │   │   ├── SKILL.md
│   │   │   └── verifier.py   # 验证 zk_proof hash + tee_attestation quote
│   │   └── okx-x402-payer/
│   │       ├── SKILL.md
│   │       ├── okx_x402_payer.py  # EIP-712 签名 + OKX /verify + /settle（支持 USDT/USDC/USDG）
│   │       └── okx_auth.py   # HMAC-SHA256 header 生成工具
│   └── openclaw.json         # Client 的 OpenClaw 配置（skills.entries + env）
│
├── worker_node/              # Worker Agent（部署到 Phala Cloud CVM）
│   ├── Dockerfile            # Python 3.12 + dstack-sdk + Node.js（供 zkfetch 使用）
│   ├── docker-compose.yml    # 本地测试用
│   ├── docker-compose.phala.yml  # Phala Cloud CVM 部署专用（含加密密钥注入）
│   ├── openclaw.json         # Worker 的 OpenClaw 配置
│   ├── server.py             # FastAPI 服务：POST /execute → 返回 ProofBundle
│   ├── skills/
│   │   ├── defi-scraper/
│   │   │   ├── SKILL.md
│   │   │   └── defi_scraper.py    # GET https://api.llama.fi/tvl/{protocol}
│   │   └── proof-generator/
│   │       ├── SKILL.md
│   │       ├── proof_generator.py # 调用 zkfetch_bridge.js + dstack AsyncDstackClient.get_quote
│   │       └── zkfetch_bridge.js  # Node.js: Reclaim zkFetch 包装（供 Python subprocess 调用）
│   └── requirements.txt      # dstack-sdk, fastapi, eth-account, requests
│
├── package.json              # @reclaimprotocol/zk-fetch（worker_node/zkfetch_bridge.js 依赖）
├── deploy_to_openclaw.sh     # WSL 部署脚本：同步 skills 到 OpenClaw workspace
├── install_onchainos.sh      # OnchainOS CLI 安装脚本
└── run_demo.ps1              # Windows PowerShell: 端到端 Demo 脚本（含彩色输出）
```

**各模块对应关系速查：**
| 模块名 | 类型 | 主要依赖 | 真实/Mock |
|--------|------|---------|----------|
| `task_delegator.py` | Client Skill | requests | 真实 HTTP 调用 |
| `swap_and_broadcast.py` | Client Utility | eth_account, onchainos CLI | **真实 DEX swap + 链上广播** |
| `verifier.py` | Client Skill | hashlib, base64 | 真实哈希验证 |
| `okx_x402_payer.py` | Client Skill | eth_account, requests, hmac | **真实链上支付**（USDT/USDC/USDG） |
| `okx_auth.py` | Client Utility | hmac, hashlib | OKX HMAC-SHA256 认证 |
| `defi_scraper.py` | Worker Skill | requests | 真实 DefiLlama API |
| `zkfetch_bridge.js` | Worker bridge | @reclaimprotocol/zk-fetch | **真实 zkTLS attestor 签名** |
| `proof_generator.py` | Worker Skill | dstack-sdk, subprocess | **真实 TDX quote** |

---

## 🛠️ PART 5: Step-by-Step Implementation Tasks


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
- `from dstack_sdk import AsyncDstackClient`
- `report_data = sha256(json.dumps(data_result)).digest()`
- `quote = await AsyncDstackClient().get_quote(report_data)` （旧 API `TappdClient().tdx_quote()` 已弃用）
- 本地开发 fallback：`{"type": "mock_tdx", "report_data": hex, "note": "deploy to Phala Cloud for real attestation"}`

输出 `ProofBundle`：`{task_id, data, zk_proof, tee_attestation, worker_pubkey, timestamp}`
控制台输出：`[Worker-TEE] 🔐 Intel TDX quote generated` / `[Worker-zkTLS] ✅ zkProof generated`

---

### Task 3: Worker — FastAPI Server（`server.py`）
**文件：** `worker_node/server.py`

要点：
- `POST /execute` → 接收 `TaskIntent`，调用 Task 1 + Task 2，返回 `ProofBundle`
- `GET /health` → 返回 `{"status": "ok", "tee": true/false, "worker_address": "0x..."}`
- 处理超时，最大执行 120 秒（zkFetch 证明生成可能需 60-90s）

验收标准：`uvicorn server:app --port 8001` 启动，curl 能拿到 ProofBundle

---

### Task 4: Client — 验证器 Skill
**文件：** `client_node/skills/verifier/verifier.py` + `SKILL.md`

要点：
- 接收 `ProofBundle`
- 验证 `zk_proof.hash == sha256(data)`（数据完整性）
- 验证 `tee_attestation.type`：若为真实 TDX quote，调用 base64 decode 并打印 quote 摘要
- 返回 `{is_valid: bool, zk_valid: bool, tee_valid: bool, reason: str, details: [str]}`
- 输出：`[Client-Verifier] ✅ ZK-Proof VALID. Data integrity confirmed.` / `[Client-Verifier] ✅ TEE Attestation: Intel TDX CVM verified.`

---

### Task 5: Client — OKX x402 支付 Skill（**核心！**）
**文件：** `client_node/skills/okx-x402-payer/okx_x402_payer.py` + `okx_auth.py` + `SKILL.md`

**okx_auth.py**（独立工具，可复用）：
- 实现 `build_okx_headers(api_key, secret, passphrase, method, path, body)` → 返回 HMAC-SHA256 签名 header dict

**okx_x402_payer.py**：
1. 构造 EIP-712 typed data struct（`TransferWithAuthorization`）：
   - domain: 根据代币动态选择（USDT: `{name: "USD₮0", version: "1", chainId: 196}`；USDC: `{name: "USD Coin", version: "2", chainId: 196}`；USDG: `{name: "USDG", version: "1", chainId: 196}`）
   - message: `{from, to, value, validAfter, validBefore, nonce}`
2. `eth_account.sign_typed_data(private_key, domain_data, types, message)` → 得到 `v, r, s`
3. `POST https://web3.okx.com/api/v6/x402/verify` → 断言 `isValid == true`
4. `POST https://web3.okx.com/api/v6/x402/settle` → 得到 `txHash`
5. 输出：`[Client-x402] 💸 Settling 0.01 USDT → Worker on X Layer...` 和最终 txHash + 浏览器链接

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
Run: `python {baseDir}/okx_x402_payer.py --to <worker_wallet> --amount <amount> [--token USDT|USDC|USDG]`
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
- [ ] 切换 chainIndex 196（mainnet），准备少量 USDT
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

## 🚀 PART 8: 双模型智能路由设计（Dual-Model Verification Routing Design）

> 本节记录 VeriTask 3.3 中双模型智能路由（Dual-Model Routing）的设计决策与理论依据。
> 这是对 PART 7 Agent 自决策交叉验证的 **架构级升级** — 将 "推理" 与 "执行" 分离到不同能力等级的模型。

### 核心问题

在 v3.2 的 Telegram 实测中发现：

- Agent（Gemini Flash）确实读取了 SKILL.md v3.2 的推理三步法
- 执行了 OnchainOS 命令查询 LDO 数据，但获得空结果 `{"ok": true, "data": []}`
- **关键问题**：Flash 在获得空结果后 **直接放弃**，未尝试替代维度（如 ETH 主链价格、智能资金信号等）

**根因分析：推理深度不足。** Flash 模型擅长高速执行，但在面对多步推理（数据不可用 → 分析原因 → 探索替代方案 → 选择最优路径）时表现不如 Pro 模型。

### 解决方案：Orchestrator-Workers 双模型协作

#### 架构一览

```
┌─────────────────────────────────────────────┐
│           User Request (Telegram)           │
│  "帮我抓 Lido TVL，验证后付款 0.01 USDT"   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     Gemini Flash (主 Agent / Orchestrator)  │
│     github-copilot/gemini-3-flash-preview   │
│                                             │
│  职责：流水线执行、工具调用、用户对话       │
│  Step 0a: spawn Pro 子 Agent ──────────┐    │
│                                        │    │
│           ┌────────────────────────────┐│    │
│           │  Gemini Pro (子 Agent)     ││    │
│           │  gemini-3.1-pro-preview    ││    │
│           │                            ││    │
│           │  职责：深度推理、验证策略   ││    │
│           │  输出：结构化验证计划 JSON  ││    │
│           └────────────┬───────────────┘│    │
│                        │                │    │
│  Step 0b: 按 Pro 计划执行 OnchainOS ◄──┘    │
│  Step 1-6: 正常 C2C 流水线                  │
└─────────────────────────────────────────────┘
```

#### 理论依据

**参考 1: RouteLLM — "Routing to the Right Expert" (arXiv:2406.18665)**

RouteLLM 框架提出 **强/弱模型路由** 概念 — 对困难任务使用强模型，简单任务使用弱模型，可在保持 95% 质量的同时降低 85% 成本。VeriTask 借鉴此理念：

- **强模型**（Gemini Pro）：处理需要深度推理的验证策略分析
- **弱模型**（Gemini Flash）：处理高速执行的工具调用和流水线编排

但 VeriTask 的创新在于：**不是路由到不同模型执行同一任务，而是将同一任务的不同阶段分配给不同模型** — Pro 负责 "想"，Flash 负责 "做"。

**参考 2: Anthropic — "Building Effective Agents" (2024.12)**

Anthropic 定义了 5 种 Agentic Pattern，VeriTask v3.3 直接采用 **Orchestrator-Workers** 模式：

> "A central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."

与 Anthropic 描述的典型 Routing 模式不同，VeriTask 的路由不是 "选择一条路径"，而是 "在同一条路径上分工协作"：

| Anthropic 模式 | VeriTask 应用 |
|---------------|--------------|
| **Prompt Chaining** | Steps 0→6 的流水线结构 |
| **Routing** | Flash 根据任务类型决定是否 spawn Pro |
| **Orchestrator-Workers** | Flash(Orchestrator) + Pro(Worker) 双模型协作 |

**参考 3: OpenClaw 原生支持**

OpenClaw 2026.3 提供了 `sessions_spawn` 工具和 `subagents.model` 配置，原生支持子 Agent 使用不同模型：

```bash
# 配置子 Agent 默认使用 Pro 模型
openclaw config set agents.defaults.subagents.model github-copilot/gemini-3.1-pro-preview

# 运行时 spawn 子 Agent（会自动使用配置的 Pro 模型）
sessions_spawn --task "分析验证策略..." --model github-copilot/gemini-3.1-pro-preview
```

### 实现细节

#### Pro 子 Agent 的结构化输出

Flash spawn Pro 时提供精确的任务描述，Pro 返回结构化 JSON 验证计划：

```json
{
  "token_mapping": {"protocol": "Lido", "token": "LDO", "chain": "ethereum"},
  "verification_plan": {
    "primary": [
      {"dimension": "Token 实时价格", "command": "onchainos market price ethereum LDO"},
      {"dimension": "持仓分布", "command": "onchainos token holder-distribution ethereum LDO"}
    ],
    "fallback": [
      {"dimension": "智能资金信号", "command": "onchainos market signal-list ethereum"},
      {"dimension": "ETH 主链价格", "command": "onchainos market price ethereum ETH"}
    ]
  },
  "cross_verify_feasibility": "HIGH",
  "reasoning": "LDO 是 Lido 治理代币，链上数据丰富。Primary 直接查 LDO 数据；Fallback 使用 ETH 生态信号作为间接验证。"
}
```

#### 降级策略

| 场景 | 处理方式 |
|------|---------|
| Pro spawn 成功 | 按 Pro 验证计划逐条执行 primary → 失败则尝试 fallback |
| Pro spawn 超时/失败 | 降级为 v3.2 Flash 自主推理（三步法），输出标注 "⚠️ 验证策略路由降级" |
| Pro 返回格式错误 | 尝试解析关键字段，无法解析则降级为三步法 |

#### 用户可见性

v3.3 中，Pro 的验证策略分析结果 **直接展示在 Step 0a**，用户能清楚看到：
- 协议→Token 映射推理过程
- Primary 和 Fallback 验证维度
- 交叉验证可行性评估
- 完整的推理链（reasoning）

这解决了 v3.2 中 "Agent 为什么选择这些命令" 的黑盒问题。

### 与 v3.2 的对比

| 维度 | v3.2 (Flash 自主推理) | v3.3 (Dual-Model Routing) |
|------|---------------------|--------------------------|
| 推理深度 | Flash 独立三步法 | Pro 深度分析 + Flash 执行 |
| 空结果处理 | 放弃 → "无可用数据" | Pro 预规划 fallback 方案 |
| 用户透明度 | 仅显示最终结果 | 完整验证策略 + 推理过程可见 |
| Token 映射 | Flash 自己猜测 | Pro 精确分析（协议→Token→Chain） |
| 成本 | 1 模型 | 2 模型（同一 Copilot provider，无额外 API 成本） |
| 延迟 | 较低 | Pro 分析增加 ~2-5s |

### 作为黑客松创新点

双模型智能路由是 VeriTask 的 **架构级创新**：

1. **首创 Agent-to-Agent 验证策略分析**：不同于传统单 Agent SKILL prompt，VeriTask 让强模型规划、弱模型执行
2. **零额外成本**：GitHub Copilot 提供 21 个模型，Pro 和 Flash 同属一个 provider
3. **原生集成**：利用 OpenClaw `sessions_spawn` + `subagents.model`，无需外部 API 或自建路由
4. **学术理论支撑**：RouteLLM 强/弱路由 + Anthropic Orchestrator-Workers = 有据可依
5. **降级兼容**：Pro 不可用时自动回退 v3.2 三步法，保证系统鲁棒性

### 技术实现汇总

| 改动项 | 位置 | 理论依据 |
|--------|------|---------|
| 双模型路由 section（60+ 行） | SKILL.md §133-191 | RouteLLM + Anthropic Orchestrator-Workers |
| Step 0a 输出模板 | SKILL.md 输出模板 | 验证策略用户可见性 |
| Step 0b 按 Pro 计划执行 | SKILL.md 输出模板 | Pro 规划 → Flash 执行分离 |
| Pro 子 Agent spawn 模板 | SKILL.md §142-172 | 结构化 JSON 输出约束 |
| sessions_spawn 路由行 | SKILL.md 路由表 | OpenClaw 原生子 Agent 支持 |
| Pro 降级 Edge Case | SKILL.md Edge Cases | 系统鲁棒性 |
| 专用 Pro Agent 创建 | `openclaw agents add pro` | OpenClaw Multi-Agent Model Binding |
| Token 地址动态解析规则 | SKILL.md §107-140 | Anti-Hallucination Token Resolution |
| 子 Agent task 模板改写 | SKILL.md §192-225 | 移除硬编码地址，强制 token search |

---

## 🔧 PART 9: Version Correction Log (v3.3→v3.4.1)

> 本节记录 v3.3.0 至 v3.4.1 期间的实测修正。每个修正包含：问题发现 → 根因分析 → 解决方案 → 验证结果。
> 这些修正基于真实 Telegram 测试反馈，是理论设计（PART 7-8）到生产可用的关键迭代。

### v3.3.2 修正：专用 Pro Agent 架构（Multi-Agent Model Binding）

#### 问题发现（v3.3.0→v3.3.1 实测）

v3.3.0/v3.3.1 的 `subagents.model` + `sessions.patch` 方案存在致命缺陷：

| 版本 | 问题 | 根因 |
|------|------|------|
| v3.3.0 | Flash 幻觉 Step 0a（未调用 `sessions_spawn`） | SKILL.md 约束不足 |
| v3.3.0 | `agentId="gemini-3.1-pro-preview"` 导致 Invalid agentId | 模型名含点号，不合法 |
| v3.3.1 | `agentId="main"` 成功 spawn，`modelApplied: true` | — |
| v3.3.1 | **子 Agent 实际 API 调用仍使用 Flash** | `sessions.patch` 只更新元数据，不改变已建立的 github-copilot API 连接使用的模型 |

**根因深度分析**（基于 OpenClaw 源码 `subagent-spawn.d.ts` + `patchChildSession` 实现）：

1. `resolveSubagentSpawnModelSelection()` 优先级：`params.modelOverride` > `config.subagents.model` > agent default
2. 解析出 `github-copilot/gemini-3.1-pro-preview` → 调用 `patchChildSession({ model: resolvedModel })`
3. `patchChildSession` 调用 `callGateway({ method: "sessions.patch", params: { key, model } })` → **成功（无报错）**
4. 但 GitHub Copilot API 的模型在会话创建时就锁定，`sessions.patch` 只更新了会话配置 JSON，不会改变已建立连接的实际模型

#### 正确方案（来自 OpenClaw 官方多 Agent 文档）

OpenClaw 官方推荐的多模型方案是 **每个 Agent 绑定独立的 model**：

```bash
# 创建专用 Pro Agent，绑定 Pro 模型
openclaw agents add pro \
  --model "github-copilot/gemini-3.1-pro-preview" \
  --workspace ~/.openclaw/workspace

# Agent 列表变为：
# - main (default)  → gemini-3-flash-preview (执行)
# - pro             → gemini-3.1-pro-preview (推理)
```

SKILL.md 中的调用从 `sessions_spawn(agentId="main", ...)` 变为 `sessions_spawn(agentId="pro", ...)`。
Pro Agent 从创建时就绑定 Pro 模型，无需运行时 `sessions.patch`，**根本上解决了模型切换问题**。

#### 架构演进对比

```
v3.3.1 (sessions.patch — 失败):
  Flash Agent (main) → sessions_spawn(agentId="main")
                        → patchChildSession({model: Pro})
                        → 子会话配置标记为 Pro ✅
                        → 实际 API 仍用 Flash ❌

v3.3.2 (专用 Agent — 正确):
  Flash Agent (main) → sessions_spawn(agentId="pro")
                        → Pro Agent 从创建就绑定 Pro 模型
                        → 实际 API 使用 Pro ✅
```

#### v3.3.2 补丁：sessions_spawn agentId 权限修复

**问题**：v3.3.2 首次 Telegram 测试中，Flash 正确调用 `sessions_spawn(agentId="pro")`，但 Gateway 返回：
```json
{"status": "forbidden", "error": "agentId is not allowed for sessions_spawn (allowed: none)"}
```

**根因分析**（OpenClaw 源码 `compact-B247y5Qt.js` Line 38881）：
```javascript
const allowAgents = resolveAgentConfig(cfg, requesterAgentId)?.subagents?.allowAgents ?? [];
const allowAny = allowAgents.some(v => v.trim() === "*");
const allowSet = new Set(allowAgents.filter(v => v.trim() && v !== "*").map(normalizeAgentId));
if (!allowAny && !allowSet.has(normalizedTargetId)) return { status: "forbidden", ... };
```

- `allowAgents` 从 requester agent（main）的 per-agent config `subagents.allowAgents` 读取
- 默认为 `[]`（空），所以 `allowSet` 为空 → "allowed: none"
- **注意**：`allowAgents` 是 per-agent schema 字段，不是 defaults schema 字段

**修复**：在 `openclaw.json` 的 `agents.list[0]`（main agent）中添加：
```json
{
  "id": "main",
  "subagents": {
    "allowAgents": ["pro"]
  }
}
```

**验证**：Gateway restart 后，`openclaw agents list` 不再有 "Unknown config keys" 警告，config 有效。

### v3.3.2 修正：Token 地址动态解析（Anti-Hallucination Token Resolution）

#### 问题发现

v3.3.1 实测中，所有 onchainos 交叉验证命令返回空数据 `{"ok": true, "data": []}`。

**排查过程**：

1. 怀疑 OKX API 限制 → 实测 `onchainos token search MORPHO --chains ethereum` → 成功返回数据
2. 对比地址：
   - Flash 使用的地址：`0x58D5968b0F1d68818817fa2301131938920973A0`（不存在的合约）
   - 正确的 MORPHO 地址：`0x58d97b57bb95320f9a05dc918aef65434969c2b2`
3. 两者共享 `0x58` 前缀但完全不同 — **Flash 模型从训练数据中幻觉了一个似是而非的地址**
4. v3.3.1 的子 Agent task 模板中 `参考映射` 包含硬编码地址，助长了幻觉传播

**OKX OnchainOS 本身完全正常** — 对正确地址返回完整数据（MarketCap $1.08B, Liquidity $7.3M, 24h 交易 1010 笔）。

#### 解决方案：强制 onchainos token search 前置

在 SKILL.md 中新增 **Token 地址动态解析规则**：

1. **Step 0 第一步必须执行** `onchainos token search <Token名> --chains <chain>` 获取真实合约地址
2. 后续所有 onchainos 命令使用 search 返回的 `tokenContractAddress`
3. **禁止从 LLM 记忆中"回忆"合约地址** — 唯一例外是 `.env` 中预配置的地址
4. 子 Agent task 模板中的 `参考映射` 改为只列 Token 名称，不含地址

#### 为什么这是一个关键创新

Token 地址幻觉是 **LLM + 链上数据交互的通用陷阱**：

- 合约地址是 40 位十六进制字符串，LLM 无法可靠记忆
- 同名 Token 在不同链上地址不同（USDT 在 Ethereum vs X Layer vs BSC）
- 合约可能升级、迁移、或已作废
- **解决方案：将 `onchainos token search` 作为"地址解析层"**，类似 DNS 解析域名到 IP

这个设计 pattern 可推广到所有 Agent + 链上数据交互的场景。

### v3.4.0 修正：Anti-Fabrication Protocol（防编造协议）

#### 问题发现（v3.3.2 Telegram 实测）

v3.3.2 的三项修复（专用 Pro Agent、Token 动态解析、allowAgents 权限）均已在生产环境确认生效。但 Telegram 实测暴露了新的致命问题：

**Flash 在成功 spawn Pro 子 Agent 后，不等待 Pro 返回结果，立即编造了完整的 Steps 0a-6 输出**：

- Session Log Event [15]：Flash 输出 1672 字符「完整结果」，包含伪造的 TVL 数字、虚假交易哈希
- 该输出中 **tool_calls = 0**（没有调用任何工具）
- Pro 子 Agent 实际运行了 1 分 14 秒，执行了 9+ 次 onchainos 命令
- Flash 的 `NO_REPLY` 事件 [17] 证明它在 Pro 完成前就已输出所有内容

#### 根因分析（4 层）

| # | 根因 | 表现 | 来源 |
|---|------|------|------|
| 1 | SKILL.md 顶部有「输出模板」含占位符 | Flash 将模板视为填空题，用幻觉数据填充 | Gemini 3 Flash 的 instruction-following 倾向 |
| 2 | `sessions_spawn` 后无显式 STOP 指令 | Flash 继续生成文本而非暂停 | OpenClaw `sessions_spawn` 是非阻塞的 |
| 3 | 步骤描述用声明式而非祈使式 | Flash 描述步骤而非执行步骤 | SKILL.md 行文风格 |
| 4 | 无反幻觉护栏规则 | Flash 自由生成虚假数字和哈希 | 缺少约束性指令 |

#### 解决方案：4 层 Anti-Fabrication 设计

**Layer 1 — Anti-Fabrication Protocol（文档顶部）**：
在 SKILL.md 最前面添加 5 条强制规则：
1. 每个数字必须来自工具调用返回值，不可自行编造
2. 不可描述未执行的步骤
3. `sessions_spawn` 后必须 STOP，等待子 Agent 完成
4. 步骤必须顺序执行，前一步工具返回后才能开始下一步
5. Pro 子 Agent 超时上限 120 秒

**Layer 2 — Action-First 步骤重构**：
将每个 Step 从声明式模板改为祈使式行动指令：
```
### Step X: 标题
**ACTION**: 调用 `tool_name(参数)` → 获取 Y
**WAIT**: 等待工具返回
**OUTPUT**: 用返回的真实数据输出 Z
```

**Layer 3 — STOP 屏障**：
在双模型路由规则中添加 ASCII 视觉屏障：
```
╔══════════════════════════════════════════════════╗
║  MANDATORY STOP — 你 **必须在此停止输出**        ║
║  等待 Pro 结果通过 announce chain 返回           ║
║  在此之前，不可输出 Step 0b ~ Step 6 的任何内容  ║
╚══════════════════════════════════════════════════╝
```

**Layer 4 — Reference-Only 输出模板**：
将原始输出格式模板移至文档末尾，标注为「仅供参考」，并在首行添加警告：
> ⚠️ 警告：此模板仅供参考输出格式。不可直接填充。每个字段必须使用工具调用返回的真实值。

#### 设计依据

| 参考来源 | 关键洞察 | 在 v3.4.0 中的应用 |
|---------|---------|-------------------|
| Anthropic "Building Effective Agents" | Orchestrator-Workers 模式需明确的 gate/barrier | Layer 3 STOP 屏障 |
| Google Gemini 3 Prompting Strategies | Flash 模型对文档前部的模板有强填充倾向 | Layer 4 移除顶部模板 |
| OpenClaw Sub-Agents 文档 | `sessions_spawn` 始终异步，结果通过 announce chain 返回 | Layer 1 Rule 3 + Layer 3 |

### v3.4.1 修正：余额分支 + 重复输出防护 + 智能重试

**触发**：Ondo TVL 测试暴露 3 个问题——余额不足时无分支逻辑、Step 内容被重复输出、Worker 因协议 slug 不匹配返回 500。

#### Fix A — Step 0b 余额分支重写

原 Step 0b 为线性 ACTION-FIRST（执行查余额→继续），**余额不足时无 IF/ELSE 分支**导致 Flash 加了 ⚠️ 但仍继续付款流程。

修正为 3 分支：
| 分支 | 触发条件 | 行为 |
|------|---------|------|
| **A** 余额充足 | USDT ≥ 任务报酬 | 继续 ACTION 2 |
| **B1** 有可兑换资产 | USDT 不足但钱包持有其他代币 | 调 `okx-dex-swap` 获取报价 → MANDATORY STOP 向用户确认 → 确认则执行 swap → 拒绝则终止 |
| **B2** 无可兑换资产 | 所有资产为 0 | 立即终止，告知用户需充值 |

#### Fix B — Anti-Fabrication Rule 6：禁止重复输出

Ondo 测试中 Flash 重复输出了 Step 0a 和 0b 的内容。新增 Rule 6：

> **Rule 6 — 禁止重复输出**：每个 Step 的内容只输出一次。若用户交互导致回到同一 Step，只输出新增信息，不重复已展示的数据和格式。

#### Fix C — 失败处理升级：3 层智能重试策略

原失败处理为「立即终止 + 报告」，无纠错能力。Worker 返回 500（Ondo slug 不匹配）时 Agent 只能放弃。

升级为 3 层：
| Level | 触发条件 | 策略 |
|-------|---------|------|
| **1** 参数可纠正 | 4xx/5xx + 参数相关提示 | AI 分析错误 → 搜索正确参数 → 重试（最多 2 次） |
| **2** 服务暂时不可用 | 超时/503/网络错误 | 等 5 秒 → 重试 1 次 |
| **3** 不可恢复 | 重试耗尽/逻辑错误/验证失败 | 终止 + 确认未支付 + 报告失败原因及尝试过的修复 |

这使 Agent 具备了「出错自修复」能力——面对 Ondo → ondo-finance 这类 slug 不匹配，Agent 可自行尝试常见变体后重试。

---

## 🏆 评分维度自检

> VeriTask 3.5 完整功能对应黑客松评分维度。

| 黑客松评分项 | 本项目对应内容 | 预期得分 |
|------------|--------------|---------|
| **OKX 结合度** | x402 真实支付 + **OnchainOS 5 Skills 全集成** + Agent 自决策交叉验证 + **双模型路由** + **Token 动态解析** | ⭐⭐⭐⭐⭐ |
| **实用性** | Agent 经济的可验证微任务外包，真实 DeFi 数据场景 | ⭐⭐⭐⭐⭐ |
| **创新性** | TEE + zkTLS + x402 三重证明 + **Multi-Agent Pro/Flash 路由** + **Anti-Hallucination Token Resolution** + **Anti-Fabrication Protocol** + **智能重试自修复** | ⭐⭐⭐⭐⭐ |
| **可复制性** | SKILL.md 可上传 ClawHub，其他用户一键安装；双模型路由零额外 API 成本；Token 解析 + Anti-Fabrication + 智能重试 pattern 可推广 | ⭐⭐⭐⭐⭐ |
