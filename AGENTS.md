# AGENTS.md — VeriTask 3.2 Multi-Agent Routing (OnchainOS Enhanced)

> This file defines routing rules for the VeriTask skill collection.
> OpenClaw Gateway reads this file to understand how to dispatch user requests
> across the available skills — including 5 OKX OnchainOS Skills and 5 VeriTask Skills.

---

## Project Overview

**VeriTask 3.0** is a Claw-to-Claw (C2C) verifiable micro-procurement protocol
built on OKX OnchainOS. It enables AI agents to trade real-time DeFi data with
cryptographic trust guarantees (zkTLS + Intel TDX TEE) and settle payments
via OKX x402 on X Layer.

**Architecture**: Two-agent system (Client Agent + Worker Agent) communicating
via REST API, with each agent composed of specialized skills.

---

## Agent Definitions

### Client Agent (`veritask-client`)

**Role**: Orchestrates C2C transactions — delegates tasks, verifies proofs, executes payments, and leverages all 5 OKX OnchainOS Skills for wallet management, market intelligence, and on-chain observability.

**VeriTask Skills** (in `client_node/skills/`):
| Skill | Priority | Description |
|-------|----------|-------------|
| `task-delegator` | **PRIMARY** | Entry point for all C2C flows. Orchestrates OnchainOS checks + Worker delegation + verification + payment + tx tracking. |
| `verifier` | INTERNAL | Validates ProofBundle cryptographic integrity. Called by task-delegator. |
| `okx-x402-payer` | INTERNAL | Executes on-chain USDT payment via OKX x402 (gasless). Called after verification. |

**OKX OnchainOS Skills** (in `.agents/skills/`, installed via `npx skills add okx/onchainos-skills`):
| Skill | C2C Flow Step | Description |
|-------|--------------|-------------|
| `okx-wallet-portfolio` | Step 0 (强制) | Check USDT balance before payment |
| `okx-dex-swap` | Step 0 (条件) | Auto-swap to USDT if balance insufficient |
| `okx-dex-market` | Step 0/3 (Agent决策) | Real-time prices + smart money signals for cross-verify |
| `okx-dex-token` | Step 0/3 (Agent决策) | Token metadata, market cap, liquidity analysis |
| `okx-onchain-gateway` | Step 3.5 + 5 (强制) | Gas estimation + tx status tracking |

**Routing Rule**: If user mentions a DeFi protocol and expects verified data + payment,
always route to `task-delegator` first. It handles the full pipeline internally.

### Worker Agent (`veritask-worker`)

**Role**: Executes data tasks inside TEE, returns cryptographically attested ProofBundles.

**Skills** (in `worker_node/skills/`):
| Skill | Priority | Description |
|-------|----------|-------------|
| `defi-scraper` | DATA | Fetches TVL from DefiLlama public API. |
| `proof-generator` | PROOF | Generates ProofBundle with zkTLS + TDX attestation. |

**Routing Rule**: Worker skills are invoked via FastAPI `POST /execute` endpoint,
not directly by user. The Worker server (`server.py`) internally chains
`defi-scraper` → `proof-generator`.

---

## OKX OnchainOS Skills Integration (v3.2)

All 5 OKX OnchainOS Skills are organically integrated into the C2C pipeline.
Installed via `npx skills add okx/onchainos-skills`, they use the `onchainos` CLI
binary which reads OKX API credentials from `.env`.

| OKX Skill | C2C Step | Invocation Mode | Use Case in VeriTask |
|-----------|---------|-----------------|---------------------|
| `okx-wallet-portfolio` | Step 0 | **Mandatory** | Check Client wallet USDT balance on X Layer before payment |
| `okx-dex-swap` | Step 0 | Conditional | Auto-swap tokens to USDT if balance insufficient (user confirms) |
| `okx-dex-market` | Step 0/3 | Agent Decision | Real-time token prices + smart money signals for cross-verification |
| `okx-dex-token` | Step 0/3 | Agent Decision | Token market cap, liquidity, holder distribution for analysis |
| `okx-onchain-gateway` | Step 3.5 + 5 | **Mandatory** | Gas estimation (show gasless advantage) + tx status tracking |

**Sandbox API Keys** (for development):
- API_KEY: `<YOUR_OKX_API_KEY>`
- SECRET: `<YOUR_OKX_SECRET_KEY>`
- PASSPHRASE: `<YOUR_OKX_PASSPHRASE>`

> See `.env.example` for configuration template. Obtain sandbox keys from [OKX OnchainOS docs](https://onchainos.com).

---

## Routing Decision Tree

```
User Request
    │
    ├── Contains "TVL" / "DeFi data" / protocol name + "验证" / "委托"
    │   └── → task-delegator (full C2C flow)
    │
    ├── Contains "TVL" / "DeFi data" ONLY (no verification needed)
    │   └── → defi-scraper (Worker direct, via POST /execute)
    │
    ├── Contains "verify proof" / "检查证明"
    │   └── → verifier
    │
    ├── Contains "pay" / "支付" / "x402" / "settle"
    │   └── → okx-x402-payer
    │
    ├── Contains "wallet balance" / "查余额"
    │   └── → okx-wallet-portfolio (OKX OnchainOS)
    │
    ├── Contains "swap" / "exchange" / "换币"
    │   └── → okx-dex-swap (OKX OnchainOS)
    │
    ├── Contains "market" / "price" / "行情"
    │   └── → okx-dex-market (OKX OnchainOS)
    │
    ├── Contains "token info" / "持仓" / "流动性" / "市值"
    │   └── → okx-dex-token (OKX OnchainOS)
    │
    └── Contains "gas" / "交易状态" / "tx status"
        └── → okx-onchain-gateway (OKX OnchainOS)
```

**Routing Rule**: If user mentions a DeFi protocol and expects verified data + payment,
always route to `task-delegator` first. It handles the full pipeline internally,
including all OnchainOS pre-checks and post-payment tracking.

---

## Environment Requirements

```bash
# Python 3.10+, Node.js 20+
# onchainos CLI: curl -sSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh
# .env file at project root with:
OKX_API_KEY=...
OKX_SECRET_KEY=...
OKX_PASSPHRASE=...
CLIENT_PRIVATE_KEY=...
WORKER_PRIVATE_KEY=...
WORKER_WALLET_ADDRESS=...
TOKEN_CONTRACT_ADDRESS=...
TOKEN_SYMBOL=USDT
CHAIN_INDEX=196
WORKER_URL=http://127.0.0.1:8001
```

---

## Demo Prompt Examples

These prompts demonstrate VeriTask's C2C flow via natural language:

1. **Complete C2C Flow**:
   > "帮我抓一下 Aave 的 TVL，通过 Worker 验证，然后付款 0.01 USDT"

2. **Verification Only**:
   > "验证这个 ProofBundle 的数据完整性"

3. **Combined with OKX Skills**:
   > "先查一下我钱包里有多少 USDT，然后委托 Worker 抓取 Lido TVL 并验证"

4. **Multi-Protocol**:
   > "分别抓 Aave 和 Uniswap 的 TVL，各自生成证明"
