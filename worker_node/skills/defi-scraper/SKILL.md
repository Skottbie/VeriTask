---
name: defi-scraper
description: "This skill should be used when the user asks to 'check TVL', 'fetch DeFi data', 'how much is locked in Aave', mentions '查TVL', 'TVL是多少', 'DeFi数据', 'DefiLlama', '协议锁仓量', 'fetch TVL', or provides a specific DeFi protocol name (Aave, Lido, Uniswap, Compound, etc.) and wants to know its on-chain total value locked. This skill is the Worker-side data collection layer for VeriTask. Do NOT use for on-chain transactions, wallet balances, or token prices (route to OKX onchainos-skills instead)."
license: MIT
metadata:
  author: veritask
  version: "3.0.0"
  homepage: "https://github.com/veritask/veritask"
  openclaw:
    requires:
      bins: ["python"]
---

# SKILL: DeFi TVL Scraper

> **角色**：VeriTask Worker 侧数据采集技能，负责从公共 API 获取 DeFi 协议实时锁仓量。
> **上下游**：本技能输出的 `DataResult` 将传递给 `proof-generator` 生成密码学证明。

---

## Pre-flight Checks

| 检查项 | 要求 |
|--------|------|
| Python 3.10+ | `python --version` |
| requests 库 | `pip install requests` |
| 网络可达 | `curl https://api.llama.fi/tvl/aave` 返回纯数字 |

---

## Skill Routing

当用户消息匹配以下模式之一时，Agent 应调用此技能：
- 包含 "TVL"、"锁仓量"、"DeFi 数据" 关键词
- 提及 DefiLlama 或具体协议名称（aave / lido / uniswap / compound 等）
- 在 C2C 任务流中被 `task-delegator` 调用时，作为第一步数据源

**不应调用**：用户询问链上交易、钱包余额、Token 价格（应路由到 OKX onchainos-skills）。

---

## Command Index

```bash
# 基础调用 — 获取 Aave TVL
python {baseDir}/defi_scraper.py --protocol aave

# JSON 机器可读输出
python {baseDir}/defi_scraper.py --protocol uniswap --json
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--protocol` | 否 | `aave` | DefiLlama 协议 slug |
| `--json` | 否 | — | 输出原始 JSON |

---

## Operation Flow

```
Step 1 → 用户/Agent 指定协议名称 (e.g. "aave")
Step 2 → GET https://api.llama.fi/tvl/{protocol} (无需 Auth)
Step 3 → 解析响应（纯数字），组装 DataResult
Step 4 → 返回 DataResult JSON，供 proof-generator 消费
```

---

## Input / Output Examples

**Input:**
```bash
python defi_scraper.py --protocol aave --json
```

**Output (DataResult):**
```json
{
  "protocol": "aave",
  "tvl_usd": 26260483533.0,
  "fetched_at": "2026-03-07T12:34:56+00:00",
  "source_url": "https://api.llama.fi/tvl/aave"
}
```

---

## Cross-Skill Workflows

| 步骤 | 技能 | 说明 |
|------|------|------|
| 1 | **defi-scraper** (本技能) | 采集 TVL 数据 |
| 2 | proof-generator | 对 DataResult 生成 zkProof + TEE attestation |
| 3 | verifier (Client) | 验证 ProofBundle 密码学完整性 |
| 4 | okx-x402-payer (Client) | 验证通过后向 Worker 支付 USDT |

---

## Edge Cases

- **协议 slug 不存在**：DefiLlama 返回非数字响应 → 抛出 `RuntimeError`
- **网络超时**：requests 默认 10s 超时 → 捕获 `ConnectionError`，建议重试
- **API 限流**：公共 API 无需 Auth，高频调用可能触发限流 → 间隔 ≥ 1s

---

## Data Source

- **API**: `GET https://api.llama.fi/tvl/{protocol}` (无认证)
- **文档**: https://api-docs.defillama.com/
