# Semaphore Authorization Design (P4, Public ZH/EN)

Scope / 范围:

- P4 graduation authorization for Creator-triggered settlement.
- P4 毕业结算授权（仅允许创建者触发）。

Status / 状态:

- Decision frozen: Semaphore-first authorization path.
- 决策冻结：以 Semaphore 作为主授权路径。

Related / 关联:

- PRD.md, Phase 4。

---

## 1. Objectives / 设计目标

EN:

1. Only the legitimate Creator can authorize graduation.
2. Authorization must be verifiable on-chain without relying on a private backend.
3. Do not reveal Telegram plaintext identity on-chain.
4. Prevent replay and duplicate authorization.
5. Stay compatible with trustScore >= 100 graduation threshold.

ZH:

1. 仅允许合法 Creator 触发毕业授权。
2. 授权判定不依赖私有后端，必须链上可验证。
3. 不上链 TG 明文身份。
4. 防重放、防重复触发。
5. 与 trustScore >= 100 的毕业门槛兼容。

## 2. Non-goals / 非目标

EN:

1. This design does not directly prove Web2 identity authenticity.
2. This design does not include on-chain revenue splitting in MVP.
3. This design does not implement a multi-layer anonymous proving network.

ZH:

1. 本方案不直接证明 Web2 身份真实性。
2. 本方案不包含 MVP 阶段的收益分账上链。
3. 本方案不实现多级匿名证明网络。

## 3. Core Decision / 核心结论

EN:

Use pure Semaphore as the P4 authorization main path:

1. Write Creator commitment at enrollment.
2. Submit anonymous membership proof at graduation authorization.
3. Verify proof and consume nullifier on-chain to prevent reuse.

ZH:

采用纯 Semaphore 作为 P4 主授权路径：

1. 入组时写入 Creator commitment。
2. 触发毕业时提交匿名成员证明。
3. 合约验真并消耗 nullifier，防止重复授权。

---

## 4. Terminology / 术语

1. identity secret: local secret used to derive anonymous identity / 用户本地保存的匿名身份秘密。
2. commitment: on-chain commitment derived from identity secret / identity secret 对应承诺值，上链存储。
3. group: authorization member set (Merkle structure) / 授权成员集合（Merkle 结构）。
4. proof: zero-knowledge membership proof / 零知识成员证明。
5. externalNullifier: scenario-binding value (e.g., graduate:agentId) / 场景绑定值。
6. nullifierHash: one-time anti-replay marker / 一次性防重放标识。

---

## 5. End-to-End Flow / 全流程

### 5.1 Enrollment / 发卡

EN:

1. Creator generates identity secret and commitment locally during launch.
2. Commitment is submitted in launch transaction.
3. Contract binds commitment to the target agent authorization group.

ZH:

1. Launch 过程中由 Creator 本地生成 identity secret 与 commitment。
2. 在 Launch 交易中提交 commitment。
3. 合约将 commitment 绑定到目标 agentId 的授权组。

### 5.1.1 Existing Agent Migration / 存量 Agent 迁移

EN:

1. Existing agents are not recreated.
2. Creator executes one-time bindCreatorCommitment(agentId, commitment).
3. After binding, migrated agents follow the same proof authorization path.
4. Without binding, authorization remains safely blocked by default.

ZH:

1. 历史 agentId 不重建、不重发射。
2. 由 Creator 一次性执行 bindCreatorCommitment(agentId, commitment)。
3. 补绑后与新 Agent 使用同一 proof 授权路径。
4. 未补绑时保持“不可授权毕业”的安全默认行为。

### 5.2 Authorization / 刷卡授权

EN:

1. Creator generates proof locally from identity secret.
2. Proof binds to externalNullifier = keccak256("graduate", agentId, chainId).
3. Call authorization entry with minimum payload: agentId + proof + signalHash.
4. Contract checks:
   - proof validity,
   - nullifier unused under this agentId,
   - trustScore >= 100.
5. If passed, mark nullifier consumed and allow settlement stage.

ZH:

1. Creator 本地基于 identity secret 生成 proof。
2. proof 绑定 externalNullifier = keccak256("graduate", agentId, chainId)。
3. 提交最小参数：agentId + proof + signalHash。
4. 合约校验：
   - proof 有效；
   - proof.nullifierHash 在该 agentId 下未使用；
   - trustScore >= 100。
5. 通过后记录 nullifier 已消耗，允许进入结算。

### 5.3 Settlement / 结算

EN:

1. After authorization, execute Escrow settle and SBT mint.
2. Failed path preserves refund logic (fixed 3% fee model).

ZH:

1. 授权通过后执行 Escrow settle 与 SBT mint。
2. 失败路径保留退款逻辑（固定扣费 3%）。

---

## 6. Contract Interface Surface / 合约接口口径

Note / 说明:

- Interface contract only, not full code implementation.
- 此处为接口口径，不是完整代码实现。

1. bindCreatorCommitment(agentId, commitment)
2. authorizeGraduateByProof(agentId, proof, signalHash)
3. isNullifierUsed(agentId, nullifierHash)
4. settle(agentId)

Recommended events / 事件建议:

1. CreatorCommitmentBound(agentId, commitmentHash)
2. GraduateAuthorized(agentId, nullifierHash)
3. GraduateRejected(agentId, reason)

---

## 7. Authorization State Machine / 授权状态机

1. Unbound: commitment not bound / 尚未绑定。
2. Bound: commitment bound, proof can be generated / 已绑定，可生成证明。
3. Eligible: trustScore >= 100, waiting authorization / 满足门槛，等待触发。
4. Authorized: proof verified / proof 验证通过。
5. Executed: settle + mint finished / 结算与铸造完成。
6. Consumed: nullifier consumed, cannot replay / nullifier 已消耗，不可重放。

Invariants / 关键约束:

1. Unbound cannot authorize.
2. trustScore < 100 cannot authorize.
3. Reused nullifier under same agentId must fail.
4. Executed state cannot settle again.
5. Strict two-step flow: authorize first, then settle.

---

## 8. Privacy Analysis / 隐私分析

### 8.1 Protected Content / 可保护内容

1. Telegram plaintext identity is not on-chain.
2. identity secret is never revealed.
3. Authorization does not require reversible backend identity storage.

### 8.2 Single-member Group Boundary / 单成员组边界

EN:

If one agent has exactly one authorized member, observers may infer role-level linkage
"the creator role triggered graduation", but not direct real-world identity by default.

ZH:

若某 agentId 授权组仅一人，外部可感知“创建者角色在操作”，
但默认无法仅凭链上数据映射到具体 TG 用户。

### 8.3 Optional Enhancements / 可选增强

1. Use relayer to reduce direct address linkage.
2. Expand to larger anonymity sets with scoped constraints.
3. Add zkTLS enrollment proof layer when Web2 authenticity is required.

---

## 9. Cost and Trade-off / 成本与权衡

1. Pure Semaphore: main cost is proof verification gas + enrollment write.
2. Pure zkTLS: stronger for source authenticity, typically heavier for per-action auth.
3. Combined model: strongest capability, highest complexity.
4. Reusing deployed Semaphore verifier usually avoids protocol-level license costs; primary cost remains gas + RPC operations.

---

## 10. Upgrade Path / 升级路径

1. v1 (current): pure Semaphore authorization.
2. v1.5: add relayer + finer-grained audit events.
3. v2: add zkTLS enrollment authenticity layer for dual-proof architecture.
