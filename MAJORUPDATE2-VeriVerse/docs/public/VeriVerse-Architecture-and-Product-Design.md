# VeriVerse Public Design

Version: 2026-04-15
Scope: Public-facing architecture and product design for hackathon review

Mock boundary statement:

1. `contracts/mocks/*` and `test/*` are test-only artifacts.
2. Production launch-invest-challenge-graduate runtime path is implemented with non-mock contracts and real on-chain interaction.
3. Runtime/deployment path is 0-mock.

## 1. Product Thesis

VeriVerse is an X Layer-native Agent launch and graduation protocol:

1. Launch any Agent with an on-chain economic identity.
2. Fund it through escrow-backed capital.
3. Stress-test it through adversarial challenges.
4. Graduate it only after verifiable proof and authorization.

Core claim:

- Local demo success is not enough.
- VeriVerse converts local capability into publicly verifiable service credibility.

## 2. Problem Statement

Current agent marketplaces have three structural gaps:

1. No standardized trust progression from "new" to "production-ready".
2. No cryptographic proof gate between claimed ability and delivered output.
3. No transparent economic loop that aligns creator, backer, and reviewer incentives.

VeriVerse solves these gaps with a full on-chain lifecycle and proof-gated graduation.

## 3. Product Closure

Lifecycle:

1. Launch
2. Invest
3. Challenge
4. Graduate

This is not four disconnected demos. It is one economic and trust closure.

### 3.1 Launch

1. Creator launches an Agent.
2. Agent receives wallet identity and on-chain registration.
3. Trust curve starts at zero.

### 3.2 Invest

1. Backers invest USDT to agent escrow.
2. Capital can enter strategy path for efficiency.
3. Every critical action is auditable.

### 3.3 Challenge

1. Agent receives tier-aware challenge.
2. Agent executes task and returns verifiable bundle.
3. Trusted layer validates proof path.
4. DAO reviewers decide PASS/FAIL.
5. Trust score updates on-chain.

### 3.4 Graduate

1. Graduation requires trust threshold.
2. Creator must pass authorization proof.
3. Escrow settles and graduation credential mints on-chain.

## 4. Trust and Security Architecture

VeriVerse uses layered verification instead of single-point trust.

### 4.1 Trusted Execution and Data Provenance

1. zkTLS evidence validates source-level integrity.
2. Runtime attestation verifies execution environment integrity.
3. DAO review enforces independent judgment over output quality.

### 4.2 Authorization and Anti-Replay

1. Graduation authorization follows Semaphore proof path.
2. externalNullifier binds proof to action scope.
3. nullifier consumption blocks replay.

### 4.3 Incentive Gate

1. Reviewer payout is gated by validity conditions.
2. Invalid zk-enhanced provenance skips reward distribution.
3. This prevents “pay-first, verify-later” failure mode.

## 5. Economic Design

Three roles, three aligned incentives:

1. Creator:
- earns operating unlock and downstream service upside after graduation.

2. Backer:
- supplies training-stage capital and receives economic participation rights.

3. Reviewer:
- earns fees for independent, verifiable review contributions.

Economic principle:

- Capital follows proof, not narrative.

## 6. System Architecture

Interaction layer:

1. Telegram natural-language control flow.
2. Dashboard for on-chain visibility.

Execution layer:

1. Orchestrated skill flows for launch, invest, challenge, graduate.
2. Deterministic command chain for reproducibility.

Settlement layer:

1. X Layer contracts for registry, escrow, trust update, and graduation state.
2. USDT-based settlement path and on-chain receipts.

## 7. Judging Alignment (4 x 25%)

### 7.1 OnchainOS and Uniswap integration

1. Multi-skill operational path integrated in end-to-end flows.
2. Route evidence and execution gates are part of challenge/invest closure.

### 7.2 X Layer ecosystem integration

1. Registry, trust update, settlement, and graduation all anchor on X Layer.
2. Real transaction receipts are included for verification.

### 7.3 AI interaction experience

1. Natural-language workflow from launch to graduation.
2. Tier-aware challenge orchestration with reviewer loop.

### 7.4 Product completeness

1. Full closure: launch -> invest -> challenge -> graduate.
2. Public trust progression and graduation gate in one pipeline.

## 8. What Is Already Demonstrated

Public evidence in this package covers:

1. P3 challenge closure and on-chain trust updates.
2. Graduation authorization design and anti-replay model.
3. End-to-end closure diagrams for product-level understanding.

## 9. Public Scope Boundary

This public design intentionally excludes:

1. Internal drafting notes and temporary audit workfiles.
2. Raw chat/key extraction artifacts.
3. Non-public planning variants not required for review.

## 10. Positioning

VeriVerse is positioned as:

1. a practical trust factory for AI agents on X Layer,
2. a reproducible evaluation-to-settlement closure,
3. and a protocol-level bridge from "it runs locally" to "it can be trusted publicly".

## 11. Review Clarification on Mock Usage

1. Mock contracts exist to make local/CI contract behavior deterministic under test.
2. They do not replace deployed contracts in production runtime.
3. Dashboard demo controls do not write trust or settlement results on-chain.
