---
name: okx-x402-payer
description: "This skill should be used when the user asks to 'pay the Worker', 'send USDT', 'settle payment via x402', 'execute on-chain payment', mentions '付款', '支付USDT', 'x402', 'pay worker', '链上支付', 'settle payment', 'OKX支付', 'X Layer转账', or when the verifier has confirmed proof validity and the C2C flow needs to execute on-chain settlement. This skill is the final step in the VeriTask trust chain: it uses OKX as a facilitator to complete gasless USDT payment via EIP-712 signature and EIP-3009 TransferWithAuthorization on X Layer. Do NOT use when the user only wants to check wallet balance (use okx-wallet-portfolio) or swap tokens (use okx-dex-swap)."
license: MIT
metadata:
  author: veritask
  version: "3.0.0"
  homepage: "https://github.com/veritask/veritask"
  openclaw:
    requires:
      bins: ["python"]
      env: ["OKX_API_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE", "CLIENT_PRIVATE_KEY"]
---

# SKILL: OKX x402 Payer

> **角色**：VeriTask Client 侧链上支付技能，通过 OKX x402 REST API 在 X Layer 上完成 USDT 无 Gas 支付。
> **上下游**：`verifier` 验证通过 → 本技能执行支付 → 输出 txHash + 区块浏览器链接。
> **核心优势**：OKX 作为 facilitator 代付 Gas（OKB），Client 只需签名 EIP-712 即可完成链上转账。

---

## Pre-flight Checks

| 检查项 | 要求 |
|--------|------|
| Python 3.10+ | `python --version` |
| eth-account | `pip install eth-account` |
| requests | `pip install requests` |
| OKX API 凭据 | `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE` 环境变量 |
| Client 钱包 | `CLIENT_PRIVATE_KEY` 环境变量（EIP-712 签名用） |
| Token 合约地址 | `TOKEN_CONTRACT_ADDRESS` 环境变量（默认 USDT） |
| (可选) 测试网 | OKX X Layer Faucet：`https://web3.okx.com/xlayer/faucet` |

---

## Skill Routing

当以下条件满足时，Agent 应调用此技能：
- 用户明确要求向 Worker 付款
- 在 C2C 流程中，`verifier` 返回 `is_valid: true` 后自动触发
- `task-delegator` 内部编排的最后一步

**不应调用**：用户只需查询余额（应路由 OKX `okx-wallet-portfolio`）；用户需要 swap（应路由 `okx-dex-swap`）。

---

## Command Index

```bash
# 基础调用 — 向 Worker 支付 0.01 USDT (mainnet)
python {baseDir}/okx_x402_payer.py --to <worker_wallet> --amount 0.01

# 指定链
python {baseDir}/okx_x402_payer.py --to <worker_wallet> --amount 0.5 --chain mainnet

# JSON 机器可读输出
python {baseDir}/okx_x402_payer.py --to <worker_wallet> --amount 1.0 --json
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--to` | 是 | — | Worker 钱包地址（payee） |
| `--amount` | 否 | `1.0` | USDT 支付金额 |
| `--chain` | 否 | `testnet` | `testnet` (chainIndex=195) 或 `mainnet` (196) |
| `--json` | 否 | — | 输出原始 JSON |

---

## Operation Flow

```
Step 1 → 构造 EIP-712 TypedData (TransferWithAuthorization / EIP-3009)
         domain: {name: "USD₮0", version: "1", chainId: 196, verifyingContract: 0x779ded...}
         message: {from, to, value, validAfter, validBefore, nonce}
Step 2 → eth_account.sign_typed_data(private_key, ...) → 得到 v, r, s
Step 3 → POST https://web3.okx.com/api/v6/x402/verify → 断言 isValid == true
Step 4 → POST https://web3.okx.com/api/v6/x402/settle → 得到 txHash
         OKX facilitator (0x590ac99e...) 代付 Gas (OKB)，链上 USDT 直接转入 Worker 钱包
```

---

## Input / Output Examples

**Input:**
```bash
python okx_x402_payer.py --to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18 --amount 1.0 --json
```

**Output (PaymentResult):**
```json
{
  "success": true,
  "txHash": "0xabc123def456...",
  "amount_usdt": 0.01,
  "chain": "xlayer-mainnet",
  "chainIndex": 196,
  "explorer_url": "https://www.okx.com/web3/explorer/xlayer/tx/0x7de15cca..."
}
```

---

## Required Environment Variables

| 变量 | 说明 | 示例 (Sandbox) |
|------|------|----------------|
| `OKX_API_KEY` | OKX API Key | `<YOUR_OKX_API_KEY>` |
| `OKX_SECRET_KEY` | OKX API Secret | `<YOUR_OKX_SECRET_KEY>` |
| `OKX_PASSPHRASE` | OKX API Passphrase | `<YOUR_OKX_PASSPHRASE>` |
| `CLIENT_PRIVATE_KEY` | Client 钱包私钥 (hex) | `0xabc...` |
| `TOKEN_CONTRACT_ADDRESS` | Token 合约地址（USDT） | `0x779ded0c9e1022225f8e0630b35a9b54be713736` |
| `CHAIN_INDEX` | 链 ID | `196` (mainnet) |

---

## Cross-Skill Workflows

| 步骤 | 技能 | 说明 |
|------|------|------|
| 1 | defi-scraper (Worker) | 采集数据 |
| 2 | proof-generator (Worker) | 生成 ProofBundle |
| 3 | verifier | 验证证明 → `is_valid: true` |
| 4 | **okx-x402-payer** (本技能) | 链上 USDT 支付 |

---

## Cross-Skill Integration: OKX OnchainOS Skills

本技能与 OKX onchainos-skills 深度互补：
- `okx-wallet-portfolio`：支付前查询 Client 钱包 USDT 余额
- `okx-dex-swap`：若 USDT 不足，先 swap 其他 Token → USDT
- `okx-onchain-gateway`：高级场景下直接广播自定义交易

---

## Edge Cases

- **余额不足**：OKX verify 返回 `isValid: false` → 输出错误并建议充值
- **签名失败**：私钥格式错误或环境变量缺失 → 明确错误提示
- **网络错误**：OKX API 不可达 → 建议检查网络或切换 API endpoint
- **Nonce 冲突**：使用 `os.urandom(32)` 生成随机 nonce，避免重放
