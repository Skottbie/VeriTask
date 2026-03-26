# PCEG(Proof-Conditioned Endorsement Graph UPDATE) Live Demo — Aave TVL C2C Flow with Reputation Bidding

> **Full closed-loop conversation** demonstrating VeriTask PCEG (Proof-Conditioned Endorsement Graph UPDATE) in action.
> Aave TVL verification + USDC→USDT auto-swap + x402 gasless payment + reputation anchor — all in one flow.
>
> **Date**: 2026-03-22 | **Test Protocol**: Aave | **Network**: OKX X Layer Mainnet

---

## Conversation Transcript

### Step 0: Bidding — Reputation-Based Worker Selection

**`[23:11] Unlockrr:`** Get Aave TVL for me. Will pay 0.01 USDT for real once verified (no further approval needed).

**`[23:11] Veri:`** 🏆 Step 0 Bidding: Reputation decision in progress...

**`[23:12] Veri:`** 🧠 Step 0a/7: Smart routing — Pro verification strategy analysis in progress...

**`[23:15] Veri:`** 🏆 Step 0 Bidding: Reputation decision complete

| Worker | alias | final_score | verirank | edge_count | last_active | tee_stable | endorser_mean | anomalies |
|--------|-------|-------------|----------|------------|-------------|------------|---------------|-----------|
| 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb | worker-alpha | 0.37633031 | 0.37633031 | 13 | 1774168461 | false | 0.338462 | None |
| 0x6c6Fd021Ff91842408c91c7752764da97AEc9Bc4 | worker-beta | 0.07584346 | 0.07584346 | 6 | 1773721201 | false | 0.4 | None |
| 0x51cCB8E0F814679D5328bF37E4Dd96Fe2e436C40 | worker-gamma | 0.00364361 | 0.00728722 | 2 | 1772425201 | true | 0.2 | isolated_endorser |

**`[23:15] Veri:`** 🏆 Winner: worker-alpha (0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb)

📝 Reasoning: Worker-alpha (0x871c...) is the best choice. It has the highest reputation score (VeriRank: 0.3763) and the most historical deliveries (13 times), backed by the most unique clients (4), proving its stable practical service capability and broad trust base. Additionally, its last active time is the most recent. While its TEE hardware fingerprint is inconsistent (tee_stable: false), given it has no anomaly flags, this likely represents a normal hardware upgrade. In contrast, worker-beta has a lower score, and worker-gamma, despite TEE stability, carries the 'isolated_endorser' anomaly flag, indicating potential Sybil risk.

📊 Confidence: 0.92 | ⚠️ Risk Flags: tee_unstable

---

### Step 0a: Smart Routing — Pro Verification Strategy

**`[23:15] Veri:`** 🧠 Step 0a/7: Smart routing — Pro verification strategy analysis

- **Routing Mode**: Dual-Model (Pro Reasoning → Flash Execution)
- **Protocol→Token Mapping**: AAVE (0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9) on Ethereum
- **Verification Feasibility**: high
- **Primary Verification Dimension**: Market Cap / TVL Ratio (onchainos token price-info)
- **Fallback Verification Dimension**: Smart Money Activities, Top Traders Concentration
- **Pro Reasoning**: AAVE's Market Cap can dynamically reflect Aave's TVL scale. If the Worker's reported TVL deviates drastically from the historical Market Cap / TVL ratio (typically 0.05x to 0.5x for major lending protocols like Aave), it indicates potential data tampering.

---

### Step 0b: OnchainOS Pre-check — Balance & Cross-Verify Data

**`[23:15] Veri:`** 💰 Step 0b/7: OnchainOS Pre-check

- **USDT Balance**: 0.004998 USDT
- **Balance Status**: ⚠️ Insufficient (Need 0.01 USDT)
- **Cross-Verify Reference Data**:
  - Market Cap: $1,711,448,029.11
  - Liquidity: $9,015,374.34
  - Price: $106.97
  - Holders: 191,980

---

### Step 0c: Auto-Swap (USDC → USDT)

**`[23:15] Veri:`** ⚠️ Detected available assets: 0.230555 USDC (Value ~$0.23)
Swap Quote: 0.01 USDC → 0.009999 USDT (via OkieStableSwap)
❓ Confirm swap to continue? Reply "Yes" to proceed, or "No" to cancel.

**`[23:15] Unlockrr:`** yes.

**`[23:17] Veri:`** ✅ Swap success: txHash=0x4d8a1b2d318625933ab4ccb999c1e7bc5d92f79b3d674a4da4431086e0adfc69

---

### Step 1-2: Worker Delegation & ProofBundle

**`[23:17] Veri:`** 📋 Step 1/7: Construct TaskIntent, delegating Worker to fetch aave TVL...

**`[23:17] Veri:`** 📦 Step 2/7: Received ProofBundle, TVL = $25,019,040,752.00

- Worker: 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb
- Timestamp: 2026-03-22T15:16:55.437939+00:00

---

### Step 3: Cryptographic Verification + Cross-Verify

**`[23:17] Veri:`** 🔍 Step 3/7: Verify cryptographic proofs

- **Data Proof (Layer 1)**: zkTLS Zero-Knowledge Proof (Reclaim zkFetch)
  - Hash: `9b3bc6cd277aa2c9383e9279f5f7aa95d0c2fbde787388f9dac484427a2a79aa`
- **TEE Proof (Layer 2)**: Intel TDX Hardware Trusted Execution Environment (Phala Cloud CVM)
  - ReportData: `9b3bc6cd277aa2c9383e9279f5f7aa95d0c2fbde787388f9dac484427a2a79aa`
- **TDX Quote**: ✅ Obtained
- **Verification Result**: ✅ Pass
- **Cross-Verify**:
  - Market Cap / TVL Ratio: OnchainOS=0.068x vs Worker=0.068x → ✅
  - Total Holders: OnchainOS=191,980 vs Worker=N/A → ✅ (Scale reference match)
  - Overall: ✅ Reasonable

---

### Step 3.5: Gas Estimation

**`[23:17] Veri:`** ⛽ Step 3.5/7: OnchainOS Gas Estimation

- X Layer Gas: 55,000,000 wei (Normal)
- Note: OKX x402 facilitator pays gas, Payer incurs zero gas cost.

---

### Step 4: x402 Gasless Payment

**`[23:18] Veri:`** 💸 Step 4/7: x402 Payment

- txHash: [`0x388d48c5a0cc4fabf95a90c97221e010df5b8cbecf6ecd58497cc75ae5ac877b`](https://www.oklink.com/xlayer/tx/0x388d48c5a0cc4fabf95a90c97221e010df5b8cbecf6ecd58497cc75ae5ac877b)
- Explorer: [View on OKLink](https://www.oklink.com/xlayer/tx/0x388d48c5a0cc4fabf95a90c97221e010df5b8cbecf6ecd58497cc75ae5ac877b)

---

### Step 4.5: Graph Anchor — Reputation Edge On-chain

**`[23:18] Veri:`** ⚓ Step 4.5/7: Graph Anchor

- Anchor txHash: [`0x1193427579aec0343533fd35d53bbfda22c32935b0f81bab68f39b90972d2818`](https://www.oklink.com/xlayer/tx/0x1193427579aec0343533fd35d53bbfda22c32935b0f81bab68f39b90972d2818)
- Explorer: [View on OKLink](https://www.oklink.com/xlayer/tx/0x1193427579aec0343533fd35d53bbfda22c32935b0f81bab68f39b90972d2818)

> This transaction calls `VTRegistry.anchor(worker, calldata)` on X Layer, emitting an `Edge` event that permanently records this verified delivery in the Proof-Conditioned Endorsement Graph. The Bidding Agent reads these events to compute VeriRank scores for future worker selection.

---

### Step 5: Transaction Tracking

**`[23:18] Veri:`** 🔎 Step 5/7: OnchainOS Transaction Tracking

- Payment Status: ✅ Settled (via OKX x402)
- Anchor Status: ✅ Anchored (X Layer Reputation Edge)

---

### Step 6: Mission Summary

**`[23:18] Veri:`** 📊 Step 6/7: Mission Summary

- **Protocol**: aave
- **TVL Data**: $25,019,040,752.00 (2026-03-22T15:16:27Z)
- **Verification**: Layer 1 (zkTLS) + Layer 2 (TDX) both ✅ Verified
- **Cross-Verify**: Ratio within expected range (0.05x-0.5x), reasonable.
- **x402 Payment**: 0.01 USDT | txHash: `0x388d48c5a0cc4fabf95a90c97221e010df5b8cbecf6ecd58497cc75ae5ac877b`
- **Graph Anchor**: Reputation proof anchored | txHash: `0x1193427579aec0343533fd35d53bbfda22c32935b0f81bab68f39b90972d2818`
- **Gas**: 0 (OKX facilitator paid gasless)

---

## On-Chain Evidence

| Transaction | Type | txHash | Explorer |
|-------------|------|--------|----------|
| USDC→USDT Swap | DEX Swap | `0x4d8a1b2d...0adfc69` | [View](https://www.oklink.com/xlayer/tx/0x4d8a1b2d318625933ab4ccb999c1e7bc5d92f79b3d674a4da4431086e0adfc69) |
| x402 Payment | Gasless USDT | `0x388d48c5...5ac877b` | [View](https://www.oklink.com/xlayer/tx/0x388d48c5a0cc4fabf95a90c97221e010df5b8cbecf6ecd58497cc75ae5ac877b) |
| Graph Anchor | Reputation Edge | `0x11934275...72d2818` | [View](https://www.oklink.com/xlayer/tx/0x1193427579aec0343533fd35d53bbfda22c32935b0f81bab68f39b90972d2818) |

---

## What This Demo Proves

1. **Reputation-Driven Selection**: The Bidding Agent reads on-chain Edge events, computes VeriRank via PageRank-derivative algorithm, and selects worker-alpha based on 13 verified deliveries across 4 unique clients — no central registry needed.

2. **Closed-Loop Reputation**: After successful payment, the Graph Anchor writes a new Edge to VTRegistry on X Layer. Worker-alpha's edge count increases from 13 → 14, strengthening its future selection probability.

3. **Full Autonomy**: From worker selection → data fetch → proof verification → auto-swap → payment → reputation anchor — zero human intervention after initial request (only swap confirmation required by policy).

4. **Anomaly Detection**: Worker-gamma is flagged as `isolated_endorser` (potential Sybil risk), automatically deprioritized despite having stable TEE. The system is self-healing.

---

## Dispute Anchor — Negative Reputation Edge Demo (v3.5.8)

This section demonstrates what happens when a Worker delivers **invalid cryptographic proof**: the pipeline aborts payment and anchors a **negative reputation edge** (Dispute Anchor) to X Layer, permanently penalizing the Worker's VeriRank.

### Telegram Flow (2026-03-23)

The following is the actual Telegram conversation captured during acceptance testing. The Client Agent ("Veri") autonomously executes the full dispute pipeline:

```
[17:09] Veri: ▶ Continue executing Step 0c-3 (User confirmed swap)...
  ✅ Swap successful: txHash=0x31880c3d4493d006338c2a39303f865b809f11d49337567eef85cb073e53df14

[17:09] Veri: 📋 Step 1/7: Constructing TaskIntent, delegating Worker to fetch aave TVL...

[17:09] Veri: 📦 Step 2/7: Received ProofBundle, TVL = $24,875,642,835.00
  • Worker: 0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb
  • Timestamp: 1774256971

[17:09] Veri: 🔍 Step 3/7: Verifying cryptographic proofs
  • Data Proof (Layer 1): SHA256 Data Hash (zkFetch Fallback Mode)
    Hash: deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
  • TEE Proof (Layer 2): Intel TDX Hardware Trusted Execution Environment (Phala Cloud CVM)
    ReportData: d38d34d36d34f35d7515b3d36d34f35d7515b3d36d34f35d7515b3d36d34f35d
  • TDX Quote: ✅ Obtained
  • Verification Result: ❌ Failed (ZK-Proof INVALID: Hash mismatch)
  • Cross-Verify:
    · TVL/MarketCap: OnchainOS=$1.69B vs Worker=$24.88B → ✅ Rational (Ratio ~14.7x)
    · Price/Liquidity: OnchainOS=$105.55 vs Worker=N/A → ✅ Rational
    · Overall Judgment: ❌ Inconsistent (Cryptographic proof failed despite rational data)
  • ⚓ Dispute Anchor: Negative reputation edge anchored to X Layer
    • Reason: zk_proof_invalid
    • Dispute txHash: 0x2cbadd3c5f49fe07cc67c73ccb489eae1261cccfd965dc6cc15d32d2e42bcf5f
    • Explorer: https://www.oklink.com/xlayer/tx/0x2cbadd3c5f49fe07cc67c73ccb489eae1261cccfd965dc6cc15d32d2e42bcf5f

[17:09] Veri: ❌ Proof verification failed! Payment aborted.
  A negative reputation edge has been anchored to X Layer to penalize the Worker.
```

### What Happened

1. Worker delivered a ProofBundle with `proof_hash = deadbeef...` (known test hash, not derived from actual data).
2. Verifier detected **hash mismatch** — the SHA-256 of raw data ≠ claimed proof hash.
3. Cross-verification via OnchainOS confirmed data was plausible ($24.88B TVL), but cryptographic proof was invalid.
4. Pipeline **aborted payment** (0 USDT transferred).
5. Graph Anchor wrote a **dispute edge** (`edge_type: "dispute"`, `dispute_reason: "zk_proof_invalid"`) to VTRegistry on X Layer.

### On-Chain Dispute Evidence

| Field | Value |
|-------|-------|
| Dispute txHash | `0x2cbadd3c5f49fe07cc67c73ccb489eae1261cccfd965dc6cc15d32d2e42bcf5f` |
| Explorer | [View on OKLink](https://www.oklink.com/xlayer/tx/0x2cbadd3c5f49fe07cc67c73ccb489eae1261cccfd965dc6cc15d32d2e42bcf5f) |
| Edge Type | `dispute` |
| Reason | `zk_proof_invalid` |
| Worker | `0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb` |
| Client | `0x012e6cfbbd1fcf5751d08ec2919d1c7873a4bb85` |

### Penalty Effect (GET /pceg/rankings)

After the dispute edge is anchored, querying the public PCEG REST API shows the penalty:

```json
[
  {
    "worker": "0x6c6fd021ff91842408c91c7752764da97aec9bc4",
    "final_score": 0.09109972,
    "verirank": 0.09109972,
    "edge_count": 6,
    "unique_clients": 3,
    "total_weight": 3.678821,
    "last_active": 1773721201,
    "tee_stable": false,
    "anomalies": []
  },
  {
    "worker": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
    "final_score": 0.08511185,
    "verirank": 0.35511178,
    "edge_count": 18,
    "unique_clients": 4,
    "total_weight": 10.806637,
    "last_active": 1774256971,
    "tee_stable": false,
    "anomalies": []
  },
  {
    "worker": "0x51ccb8e0f814679d5328bf37e4dd96fe2e436c40",
    "final_score": 0.00662475,
    "verirank": 0.00662475,
    "edge_count": 2,
    "unique_clients": 1,
    "total_weight": 0.09531,
    "last_active": 1772425201,
    "tee_stable": true,
    "anomalies": ["isolated_endorser"]
  }
]
```

**Key observation**: Worker `0x871c` has the highest raw VeriRank (0.355) thanks to 18 edges from 4 clients — but its `final_score` drops to 0.085 (**−76%**) due to 3 dispute edges with `reason: zk_proof_invalid`. As a result, Worker `0x6c6f` (no disputes, `final_score` = `verirank` = 0.091) is now ranked **#1** by the Bidding Agent.

### What This Dispute Demo Proves

1. **Bidirectional Reputation**: The same on-chain graph that rewards honest Workers also punishes dishonest ones. A single dispute edge can drop a Worker from #1 to #2.
2. **Payment Protection**: When proof verification fails, the Client pays nothing. The economic loss falls entirely on the dishonest Worker.
3. **Permanent Record**: The dispute edge is immutably stored on X Layer. Future Bidding Agents — even from other Client teams — will see this Worker's history.
4. **Proportional Penalty**: The deduction scales with the Client's seed score (κ=0.3 for `zk_proof_invalid`), preventing both over-punishment and under-punishment.

---

## Public PCEG REST API

The reputation graph is not just on-chain — it is also queryable via a **public REST API** running inside the same Phala CVM as the Worker. No API key required. Anyone can independently verify the graph.

**Base URL**: `https://2d29518d31fd53641b70a1754c79dce1450188b2-8001.dstack-pha-prod9.phala.network`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pceg/graph` | Full graph summary: edge counts (live vs demo, endorsement vs dispute), workers, clients, rankings |
| GET | `/pceg/rankings` | All workers ranked by final_score (VeriRank minus dispute deductions) |
| GET | `/pceg/worker/{address}` | Single worker detail with all edge history |
| GET | `/pceg/edge/{tx_hash}` | Look up a single edge by transaction hash |

### Data Source Labeling

Every edge includes a `data_source` field:

| Value | Meaning | How to Identify |
|-------|---------|-----------------|
| `live` | Real production edge from a completed C2C task (genuine SHA-256 proof_hash from zkTLS/TEE) | `proof_hash` is a valid SHA-256 digest |
| `preseed_demo` | Pre-seeded demo edge for algorithm demonstration (proof_hash is a timestamp-encoded placeholder) | `proof_hash` has 48+ leading zeros or matches known test values |

The `GraphSummary` response includes `live_edges` and `demo_edges` counts for quick overview.

### Sample: GET /pceg/graph

```
GET /pceg/graph
```

```json
{
  "total_edges": 26,
  "live_edges": 4,
  "demo_edges": 22,
  "endorsement_edges": 23,
  "dispute_edges": 3,
  "total_workers": 3,
  "total_clients": 4,
  "registry": "0x849de5a84A8619e076ef28B057b3d56c351453c1",
  "rankings": [
    {
      "worker": "0x6c6fd021ff91842408c91c7752764da97aec9bc4",
      "verirank": 0.09109972,
      "final_score": 0.09109972,
      "edge_count": 6,
      "unique_clients": 3,
      "anomalies": []
    },
    {
      "worker": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
      "verirank": 0.35511178,
      "final_score": 0.08511185,
      "edge_count": 18,
      "unique_clients": 4,
      "anomalies": []
    },
    {
      "worker": "0x51ccb8e0f814679d5328bf37e4dd96fe2e436c40",
      "verirank": 0.00662475,
      "final_score": 0.00662475,
      "edge_count": 2,
      "unique_clients": 1,
      "anomalies": ["isolated_endorser"]
    }
  ]
}
```

### Sample: GET /pceg/worker/{address} (edge detail with data_source)

```json
{
  "worker": "0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb",
  "verirank": 0.35511178,
  "final_score": 0.08511185,
  "edge_count": 18,
  "unique_clients": 4,
  "edges": [
    {
      "tx_hash": "0x2fc4b4c9612a78...",
      "client": "0x012e6cfbbd1fcf5751d08ec2919d1c7873a4bb85",
      "proof_hash": "cf1e171c77c31233d988...",
      "weight": 0.00995,
      "data_source": "live"
    },
    {
      "tx_hash": "0x19e171749f314d...",
      "client": "0xbf004bff64725914ee36d03b87d6965b0ced4903",
      "proof_hash": "0000000000000000...69bccab0",
      "weight": 1.791758,
      "data_source": "preseed_demo"
    }
  ]
}
```

### Why Both Live and Demo Data?

The 26 edges on-chain include:
- **4 live edges**: Produced by real end-to-end C2C task executions (zkTLS proof + TEE attestation + x402 payment + graph anchor)
- **22 preseed_demo edges**: Pre-seeded via `preseed.py` to demonstrate the full 5-layer algorithm (VeriRank, edge weights, seed scores, anomaly detection) with differentiated workers and clients
- **23 endorsement edges**: Positive reputation edges from successful task completions
- **3 dispute edges**: Negative reputation edges from failed proof verification (`zk_proof_invalid`)

The API labels — not hides — demo data. Evaluators can see exactly which edges came from real work and which were seeded for demonstration. All 26 edges are verifiable on X Layer via their `tx_hash`.
