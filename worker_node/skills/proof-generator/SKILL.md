---
name: proof-generator
description: "This skill should be used when the user asks to 'generate proof', 'create ProofBundle', 'add cryptographic attestation', mentions '生成证明', 'proof', 'ProofBundle', 'zkFetch', 'TEE证明', 'TDX attestation', '密码学证明', or when the Worker needs to attach verifiable credentials to collected data in a C2C flow. This skill is the core of VeriTask's trust chain: it ensures data provenance via zkTLS (Reclaim Protocol) and execution environment integrity via Intel TDX TEE attestation (Phala Cloud CVM). Do NOT use when the user only needs raw data (use defi-scraper) or wants to verify an existing proof (use verifier)."
license: MIT
metadata:
  author: veritask
  version: "3.0.0"
  homepage: "https://github.com/veritask/veritask"
  openclaw:
    requires:
      bins: ["python"]
      env: ["WORKER_PRIVATE_KEY"]
---

# SKILL: Proof Generator

> **角色**：VeriTask Worker 侧证明生成技能，为采集的 DeFi 数据提供双层密码学证明。
> **上下游**：接收 `defi-scraper` 的 DataResult → 输出 ProofBundle → 由 Client `verifier` 验证。

---

## Pre-flight Checks

| 检查项 | 要求 |
|--------|------|
| Python 3.10+ | `python --version` |
| Node.js 18+ | `node --version`（zkFetch 依赖） |
| dstack-sdk | `pip install dstack-sdk` |
| @reclaimprotocol/zk-fetch | `npm install`（项目根目录 package.json） |
| (可选) Reclaim 凭据 | `RECLAIM_APP_ID` + `RECLAIM_APP_SECRET` 环境变量 |
| (可选) TEE 环境 | `/var/run/tappd.sock` 存在（Phala Cloud 部署时） |

---

## Skill Routing

当以下条件满足时，Agent 应调用此技能：
- 用户请求为数据生成密码学证明
- 在 C2C 流程中，`defi-scraper` 已返回 DataResult，需要附加 ProofBundle
- Worker FastAPI `POST /execute` 内部自动调用

**不应调用**：用户只需要原始数据（应路由到 `defi-scraper`）；用户需要验证已有证明（应路由到 `verifier`）。

---

## Command Index

```bash
# 基础调用 — 为 Aave 数据生成 ProofBundle
python {baseDir}/proof_generator.py --protocol aave

# JSON 机器可读输出
python {baseDir}/proof_generator.py --protocol lido --json
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--protocol` | 否 | `aave` | DefiLlama 协议 slug |
| `--json` | 否 | — | 输出原始 JSON ProofBundle |

---

## Operation Flow

```
Step 1 → 调用 defi-scraper 获取 DataResult
Step 2 → Layer 1: Reclaim zkFetch (Node.js subprocess)
         → 成功: zkProof with type "reclaim_zkfetch"
         → 失败: fallback SHA256 hash with type "sha256_mock"
Step 3 → Layer 2: Phala dstack TDX quote
         → TEE 可用: TappdClient().tdx_quote(report_data)
         → 非 TEE: mock attestation with type "mock_tdx"
Step 4 → 组装 ProofBundle {task_id, data, zk_proof, tee_attestation, worker_pubkey, timestamp}
```

---

## Input / Output Examples

**Input:**
```bash
python proof_generator.py --protocol aave --json
```

**Output (ProofBundle):**
```json
{
  "task_id": "vt-abc12345",
  "data": {
    "protocol": "aave",
    "tvl_usd": 26260483533.0,
    "fetched_at": "2026-03-07T12:34:56+00:00",
    "source_url": "https://api.llama.fi/tvl/aave"
  },
  "zk_proof": {
    "type": "reclaim_zkfetch",
    "hash": "a1b2c3d4...",
    "proof": { "...reclaim proof object..." }
  },
  "tee_attestation": {
    "type": "intel_tdx",
    "report_data": "e5f6a7b8...",
    "quote": "base64-encoded-tdx-quote..."
  },
  "worker_pubkey": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
  "timestamp": "2026-03-07T12:34:58+00:00"
}
```

---

## Cross-Skill Workflows

| 步骤 | 技能 | 说明 |
|------|------|------|
| 1 | defi-scraper | 采集 TVL 数据 → DataResult |
| 2 | **proof-generator** (本技能) | DataResult → ProofBundle |
| 3 | verifier (Client) | 验证 ProofBundle |
| 4 | okx-x402-payer (Client) | 链上 USDT 支付 |

---

## Edge Cases

- **zkFetch 超时/失败**：自动 fallback 到 SHA256 hash mock → ProofBundle 仍可生成，但 `zk_proof.type` 为 `"sha256_mock"`
- **TEE 不可用**（本地开发）：自动 fallback 到 mock attestation → `tee_attestation.type` 为 `"mock_tdx"`
- **Node.js 不可用**：zkFetch bridge 调用失败 → 直接走 SHA256 fallback
- **协议不存在**：`defi-scraper` 层抛错 → proof-generator 传播异常

---

## Dependencies

- `@reclaimprotocol/zk-fetch` (Node.js, via subprocess `node zkfetch_bridge.js`)
- `dstack-sdk` (Python, `TappdClient().tdx_quote()`)
- `defi_scraper.py` (内部导入)
