---
name: verifier
description: "This skill should be used when the user asks to 'verify a proof', 'check ProofBundle', 'validate data integrity', mentions '验证证明', '检查ProofBundle', '数据完整性', 'TEE验证', 'ZK验证', 'proof valid', or when the Client receives a ProofBundle from Worker in a C2C flow and needs to validate cryptographic integrity. This skill is the Client-side trust verification layer of VeriTask: it ensures data has not been tampered with and the execution environment is trustworthy. Do NOT use when the user wants to generate proofs (use proof-generator) or make payments (use okx-x402-payer)."
license: MIT
metadata:
  author: veritask
  version: "3.0.0"
  homepage: "https://github.com/veritask/veritask"
  openclaw:
    requires:
      bins: ["python"]
---

# SKILL: Proof Verifier

> **角色**：VeriTask Client 侧验证技能，校验 Worker 返回的 ProofBundle 密码学完整性。
> **上下游**：接收 Worker 的 ProofBundle → 验证通过后触发 `okx-x402-payer` 进行链上支付。

---

## Pre-flight Checks

| 检查项 | 要求 |
|--------|------|
| Python 3.10+ | `python --version` |
| eth-account 库 | `pip install eth-account`（base64/hashlib 为标准库） |

---

## Skill Routing

当以下条件满足时，Agent 应调用此技能：
- 用户明确要求验证一个 ProofBundle
- 在 C2C 流程中，Worker 返回 ProofBundle 后自动调用
- `task-delegator` 内部编排时作为第三步

**不应调用**：用户要求生成证明（应路由 `proof-generator`）；用户要求付款（应路由 `okx-x402-payer`）。

---

## Command Index

```bash
# 从文件验证
python {baseDir}/verifier.py --bundle <proof_bundle.json>

# 从 stdin 验证（管道模式）
echo '<json>' | python {baseDir}/verifier.py --stdin

# JSON 机器可读输出
python {baseDir}/verifier.py --bundle proof.json --json
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--bundle` | 与 --stdin 二选一 | — | ProofBundle JSON 文件路径 |
| `--stdin` | 与 --bundle 二选一 | — | 从标准输入读取 ProofBundle |
| `--json` | 否 | — | 输出原始 JSON 验证结果 |

---

## Operation Flow

```
Step 1 → 接收 ProofBundle JSON（文件或 stdin）
Step 2 → Layer 1 验证: SHA256(data) == zk_proof.hash → 数据完整性
Step 3 → Layer 2 验证: SHA256(data) == tee_attestation.report_data → TEE 一致性
         → 若 type 为 "intel_tdx"：检查 quote 结构（base64 解码 + 长度校验）
         → 若 type 为 "mock_tdx"：标记为 mock，仍返回 valid
Step 4 → 返回 VerificationResult {is_valid, zk_valid, tee_valid, reason, details}
```

---

## Input / Output Examples

**Input:**
```bash
python verifier.py --bundle proof_bundle.json --json
```

**Output (VerificationResult):**
```json
{
  "is_valid": true,
  "zk_valid": true,
  "tee_valid": true,
  "reason": "All proofs verified",
  "details": [
    "[ZK Proof] ✅ Hash match confirmed (sha256)",
    "[TEE] ✅ Intel TDX attestation structure valid"
  ]
}
```

**验证失败示例：**
```json
{
  "is_valid": false,
  "zk_valid": false,
  "tee_valid": true,
  "reason": "ZK proof hash mismatch",
  "details": [
    "[ZK Proof] ❌ Hash mismatch: expected a1b2..., got x9y8...",
    "[TEE] ✅ Mock TDX attestation (development mode)"
  ]
}
```

---

## Cross-Skill Workflows

| 步骤 | 技能 | 说明 |
|------|------|------|
| 1 | defi-scraper (Worker) | 采集 TVL 数据 |
| 2 | proof-generator (Worker) | 生成 ProofBundle |
| 3 | **verifier** (本技能) | 验证 ProofBundle 密码学完整性 |
| 4 | okx-x402-payer | 验证通过 → 链上 USDT 支付 |

---

## Edge Cases

- **缺失字段**：ProofBundle JSON 缺少 `zk_proof` 或 `tee_attestation` → 返回 `is_valid: false`
- **Mock 证明**：`type` 为 `"sha256_mock"` 或 `"mock_tdx"` 时仍可验证通过（开发模式）
- **数据被篡改**：hash 不匹配 → `zk_valid: false`，详细错误信息写入 `details`
- **无效 JSON**：解析失败 → 抛出错误并退出
