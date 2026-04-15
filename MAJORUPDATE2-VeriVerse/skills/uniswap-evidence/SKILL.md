---
name: uniswap-evidence
description: >
  M4 路由证据层。只做 swap quote 的路由来源提取与 Uniswap 命中证据，不执行真实换币。
  触发词：Uniswap 证据、route evidence、路由来源、这条报价是不是走了 Uniswap。
license: MIT
metadata:
  author: VeriVerse
  version: "1.0.0"
  openclaw:
    requires:
      bins: ["python3", "onchainos"]
      env: []
---

# SKILL: uniswap-evidence

角色：评审证据层（M4）。

## Command

```bash
python3 {baseDir}/uniswap_evidence.py \
  --from-token <FROM_TOKEN_ADDRESS> \
  --to-token <TO_TOKEN_ADDRESS> \
  --amount <MINIMAL_UNITS> \
  --chain xlayer \
  --json
```

输出要点：
- routeEvidence.routeSources: 报价里识别到的路由来源列表
- routeEvidence.containsUniswap: 是否命中 Uniswap
- routeEvidence.uniswapMatches: 命中的 Uniswap 来源名称
- routeEvidence.quoteSummary: 报价关键摘要（toTokenAmount/priceImpact/gasFee）

约束：
- 本技能只做 quote 证据提取，不做 approve/swap/broadcast。
- 任何真实换币执行请走既有的 Step 0c 流程。
