---
name: bidding-agent
author: VeriTask Team
version: 1.0.0
license: MIT
description: >-
  Reads the Proof-Conditioned Endorsement Graph from X Layer and ranks
  Workers by reputation. Uses RPC edge indexing, OnchainOS seed scores,
  networkx VeriRank, and wash-trading anomaly detection.
capabilities:
  - Fetch VeriTask reputation edges via X Layer RPC (eth_getLogs)
  - Compute proof quality per edge (zkTLS + TDX)
  - Query OnchainOS market portfolio-overview for seed scores
  - Query OnchainOS signal/leaderboard for smart money pool
  - Run Proof-Conditioned VeriRank (networkx)
  - Detect wash-trading anomalies (cycles, cliques, isolated endorsers)
permissions:
  - network:xlayerrpc.okx.com
  - env:OKX_API_KEY (for OnchainOS CLI)
examples:
  - "Rank these Workers by reputation"
  - "Which Worker has the best trust score?"
  - "Check worker 0xABC for wash trading"
---

# Bidding Agent

Reads the on-chain Proof-Conditioned Endorsement Graph (PCEG) from VTRegistry
and ranks Workers by 5-dimension reputation scoring.

## Usage

```bash
# Rank all workers from registry
python bidding_agent.py --registry ../../worker_registry.json --json

# Rank specific workers by address
python bidding_agent.py --workers 0xABC,0xDEF --json

# Verbose mode (show per-edge details)
python bidding_agent.py --registry ../../worker_registry.json --verbose
```

## CLI Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--registry` | path | Path to `worker_registry.json` |
| `--workers` | string | Comma-separated Worker addresses (alternative to `--registry`) |
| `--json` | flag | Output structured JSON |
| `--verbose` | flag | Show edge details per worker |

## Output Schema (--json)

```json
[
  {
    "worker": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
    "alias": "alpha",
    "url": "https://alpha.worker.example",
    "final_score": 0.2994,
    "edge_count": 11,
    "unique_clients": 4,
    "last_active": 1774152574,
    "tee_stable": false,
    "endorser_mean": 0.4,
    "endorser_std": 0.459,
    "anomalies": []
  }
]
```

## 5-Dimension Scoring

| # | Dimension | Key | Description |
|---|-----------|-----|-------------|
| 1 | 信誉分 | `final_score` (VeriRank) | 被高信誉 Client 背书的累积信任度 |
| 2 | 历史交付量 | `edge_count` | 链上 Edge 数量 = 实际工作记录 |
| 3 | 最近活跃 | `last_active` | Unix 时间戳，反映 Worker 可用性 |
| 4 | TEE 一致性 | `tee_stable` | 硬件指纹未变更 = 可信 TEE 环境 |
| 5 | 背书方质量 | `endorser_mean` / `endorser_std` | 背书 Client 的信誉均值和标准差 |

## Anomaly Detection

| Anomaly | Meaning | Risk |
|---------|---------|------|
| `isolated_endorser` | 仅被 1 个 Client 背书 | 可能是 Sybil 攻击 |
| `client_clique` | 背书方之间互相关联 | 可能是合谋刷信誉 |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VT_REGISTRY_ADDRESS` | Yes | VTRegistry 合约地址 (X Layer) |
| `VT_REGISTRY_DEPLOY_BLOCK` | Yes | 合约部署区块号（避免扫描空区块） |
| `http_proxy` / `https_proxy` | Conditional | 如防火墙阻断直连，需配置代理 |

## Integration

此 Skill 由 `task-delegator` 在 **Step -1** 自动调用，输出传递给 **Step 0 Bidding**
（Pro Agent LLM 决策层）进行最终 Worker 选择。不需要用户手动触发。