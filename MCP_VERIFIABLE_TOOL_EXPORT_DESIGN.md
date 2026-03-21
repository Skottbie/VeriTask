# VeriTask MCP Verifiable Tool Export

## Public Interface Iteration Design

Document status: Public iteration draft
Intended audience: repository readers, MCP ecosystem integrators, agent infrastructure developers

## 1. Purpose / 文档目的

### 中文

本文档定义 VeriTask 面向 MCP 生态的公开接口迭代方案。该方案的目标，是将 VeriTask 现有的任务委托、可信交付、结果验证与链上结算能力，整理为一组具备接入规模商业化能力的接口模型展示，使 MCP 兼容 Agent 能够在统一契约下发起任务、获取结果、验证交付并完成支付结算。

本文档当前描述的是概念展示阶段的公共接口设计方向，但其结构目标并非停留在演示层，而是作为后续演进为稳定公共接口设计的第一轮公开迭代说明。

本文档不讨论具体代码实现细节，而是用于明确以下问题：

1. 公开导出的系统边界
2. 公共接口层的职责范围
3. 与 OKX OnchainOS MCP 的分工关系
4. 后续迭代的结构性约束

### English

This document defines the public MCP interface iteration for VeriTask. The objective is to consolidate VeriTask's existing task delegation, trusted delivery, result verification, and on-chain settlement capabilities into an interface model showcase with commercial-scale integration potential so that MCP-compatible agents can submit tasks, retrieve results, verify delivery, and complete settlement under a unified contract.

The current document is positioned as a concept-stage public showcase, but its structural intent is not limited to demo narration. It is written as the first public iteration toward a stable public interface design.

This document does not cover implementation-level details. Its purpose is to define:

1. The public system boundary
2. The scope of the public interface layer
3. The division of responsibility between VeriTask and OKX OnchainOS MCP
4. The structural constraints for subsequent iterations

## 2. Background / 背景

### 中文

VeriTask 当前已经具备可信任务交易的基本闭环能力：

1. 接收任务意图并发起执行委托
2. 获取包含证明材料的结果交付物
3. 对交付结果执行密码学验证
4. 在验证通过后执行链上支付与结算

因此，VeriTask 的对外价值不应被理解为单次数据抓取或单个 Worker 调用，而应被理解为可信任务交易中间层。面向 MCP 的公开导出，也不应停留在“概念演示接口”层面，而应按可商用接口设计的标准来组织其边界、对象模型与职责划分，只是在当前阶段以公开概念展示的形式对外说明。

### English

VeriTask already provides the basic closed-loop capabilities required for trusted task transactions:

1. Accept task intent and dispatch execution
2. Receive result deliveries packaged with proof artifacts
3. Perform cryptographic verification on delivered results
4. Execute on-chain payment and settlement after verification succeeds

Accordingly, VeriTask's external value should not be framed as a one-off data fetch or a direct Worker call. It should be framed as a trusted task transaction middleware layer. The public MCP export should be organized with the discipline of a commercial interface design, while still being presented in the current phase as a public concept showcase.

## 3. External Baseline / 外部基线

### 中文

本设计基于对 OKX 官方 onchainos-skills 机制的实际调研。关键结论如下：

1. OKX OnchainOS 已提供原生 MCP Server 机制
2. OnchainOS 的 MCP 入口由统一 CLI 提供
3. 官方 `onchainos mcp` 通过原生 MCP 协议暴露工具，并由源码与测试明确覆盖 `tools/list`、`initialize` 等 MCP 基础交互
4. 其公共工具面已经真实覆盖市场、代币、钱包、网关、信号、交易与组合分析等基础能力，例如 `token_search`、`market_price`、`token_price_info`、`swap_quote`、`portfolio_total_value`、`gateway_gas`

因此，VeriTask 的公开导出不应复制这类基础工具面，而应建立在其之上的高层可信任务交易接口。

换言之，VeriTask 的 MCP 导出前提不是重写一套新的市场、代币、钱包、网关或交易基础设施，而是以官方 `onchainos mcp` 的现有工具面作为能力底座，在其之上组织可信任务交易中间层。

### English

This design is grounded in direct examination of the official OKX onchainos-skills mechanism. The key conclusions are:

1. OKX OnchainOS already provides a native MCP server mechanism
2. The MCP service entry point is exposed through a unified CLI
3. The official `onchainos mcp` implementation exposes real MCP tools and is validated in source and integration tests against core MCP flows such as `initialize` and `tools/list`
4. Its public tool surface already covers foundational capabilities across market, token, wallet, gateway, signal, swap, and portfolio domains, including tools such as `token_search`, `market_price`, `token_price_info`, `swap_quote`, `portfolio_total_value`, and `gateway_gas`

As a result, VeriTask should not duplicate this foundational tool layer. Its public export should provide a higher-level trusted task transaction interface above it.

In other words, VeriTask's MCP export is not based on rebuilding a new market, token, wallet, gateway, or transaction stack. It treats the existing tool surface of the official `onchainos mcp` server as the capability substrate and organizes a trusted task transaction middleware layer above it.

## 4. Design Objective / 设计目标

### 中文

本轮导出的设计目标，是建立一个面向上游 Agent 的公共信任接口层，使调用方能够：

1. 提交标准化任务请求
2. 获取标准化结果对象
3. 查询或重放验证结论
4. 发起支付并获取结算回执

该接口层必须同时满足两个条件：

1. 不向外暴露底层执行实现的复杂性
2. 不限制 VeriTask 后续演进为多 Worker、多策略、多供应方体系

这意味着本文档不是对最终产品形态的冻结描述，而是对接口演进方向的阶段性公开说明。它需要既能支撑当前展示，又不能阻断后续版本继续扩展、替换与收敛。

### English

The design objective for this iteration is to establish a public trust interface for upstream agents so that callers can:

1. Submit normalized task requests
2. Retrieve normalized result objects
3. Query or replay verification outcomes
4. Initiate settlement and obtain payment receipts

This interface layer must satisfy two conditions simultaneously:

1. It must not expose the complexity of the underlying execution implementations
2. It must not constrain VeriTask's future evolution into a multi-Worker, multi-policy, multi-supplier system

In other words, this document is not a frozen product specification. It is a staged public statement of interface direction that must support today's showcase while preserving room for subsequent versions to expand, refine, and stabilize the contract.

## 5. Export Boundary / 导出边界

### 中文

本轮方案采用如下公开边界：

User or Upstream Agent
-> VeriTask MCP Export
-> VeriTask Orchestration and Verification Layer
-> Open Worker Supply Layer

其中，Open Worker Supply Layer 可以是可开放接入、可扩展、可市场化的供给侧，但在本轮中不直接作为上游调用方交互的公共 MCP 契约暴露。

这一定义意味着：

1. 上游调用方只与 VeriTask 的公共契约交互
2. Worker 可以作为 VeriTask 下游的开放供给层持续接入，但其发现、选路、编排、替换与实现差异统一收敛在 VeriTask 中间层之后
3. 公共接口稳定性与内部执行演进相互解耦

### English

The public boundary for this iteration is defined as follows:

User or Upstream Agent
-> VeriTask MCP Export
-> VeriTask Orchestration and Verification Layer
-> Open Worker Supply Layer

Under this model, the Open Worker Supply Layer may remain attachable, expandable, and eventually marketized, but it is not directly exposed as the public MCP contract for upstream callers in this iteration.

This definition means that:

1. Upstream callers interact only with VeriTask's public contract
2. Workers may continue to join as an open downstream supply layer, while discovery, routing, orchestration, substitution, and implementation variance are normalized behind VeriTask's middleware boundary
3. Public interface stability is decoupled from internal execution evolution

## 6. Boundary Rationale / 边界依据

### 中文

将 Worker 定义为可开放接入的供给层、但不在首阶段直接作为上游公共契约暴露，原因如下：

1. VeriTask 对外提供的是可信任务交易与信任编排能力，而非某个执行节点的直连能力
2. Worker 供给侧天然具有异构性、可替换性与市场化潜力，不适合在首阶段被固化为面向上游调用方的稳定接口
3. 如果上游直接面向 Worker 交互，验证绑定、审计链路、支付结算与策略治理将被迫外移至调用方侧，削弱 VeriTask 作为中间层的核心价值
4. 将统一入口保持在 VeriTask，同时允许 Worker 作为开放供给层演进，既能控制公共攻击面与契约复杂度，也为后续接入 Worker 市场、信誉系统与策略路由保留空间

### English

The Worker layer is treated as an open supply layer, but not exposed as the first-stage public contract for upstream callers, for the following reasons:

1. VeriTask exposes trusted task transaction and trust-orchestration capability rather than direct connectivity to a single execution node
2. The Worker supply side is inherently heterogeneous, replaceable, and potentially market-driven, which makes it unsuitable to freeze immediately as the stable upstream-facing contract
3. If upstream callers were bound directly to Workers, verification binding, audit trails, settlement, and policy governance would be pushed outward, weakening VeriTask's middleware role
4. Keeping the unified entry point at VeriTask while allowing Workers to evolve as an open supply layer reduces public interface complexity and preserves room for later Worker-market, reputation, and policy-routing designs

## 7. Public Capability Domains / 公共能力域

### 中文

首阶段公共导出建议围绕以下能力域组织：

1. Capability Discovery
说明当前实例支持的任务类型、验证能力、链支持范围与结算能力

2. Task Submission
接收标准化任务请求并返回任务句柄

3. Task Status and Retrieval
提供执行状态查询与标准化结果获取

4. Verification
提供验证摘要查询与结果复验入口

5. Settlement
提供支付触发、结算状态查询与回执获取能力

### English

The first public export iteration should be organized around the following capability domains:

1. Capability Discovery
Describe supported task types, verification capabilities, supported chains, and settlement capabilities

2. Task Submission
Accept normalized task requests and return task handles

3. Task Status and Retrieval
Provide execution status lookup and normalized result retrieval

4. Verification
Provide verification summaries and replayable verification entry points

5. Settlement
Provide payment initiation, settlement status lookup, and receipt retrieval

## 8. Recommended Tool Surface / 建议工具面

### 中文

建议的首阶段公共工具集合如下。

这些工具名称和职责划分用于展示 VeriTask 的公共接口组织方式，已经具备明确的可商用接口设计方向，但在当前阶段仍属于迭代中的公开模型，不代表后续版本在命名与拆分上不会继续优化。

1. vt_capabilities
返回支持的任务类型、验证模式、结算能力与运行约束

2. vt_request_task
提交任务请求，返回 task_id、生命周期状态与轮询句柄

3. vt_get_task_status
返回任务状态，例如 accepted、running、verifying、completed、failed

4. vt_get_task_result
返回标准化结果对象，包括结果载荷、来源信息、证明摘要与关联元数据

5. vt_verify_result
返回验证结论、验证细项，以及用于复验的摘要信息

6. vt_settle_payment
在验证与策略条件满足时触发结算

7. vt_get_settlement_receipt
返回交易哈希、链信息、结算状态以及与结果记录的关联键

### English

The recommended first-stage public tool set is listed below.

These tool names and responsibilities are intended to demonstrate VeriTask's public interface organization in a form that already points toward commercial-grade integration. At the current stage, however, they should still be treated as an iterative public model rather than a permanently frozen naming surface.

1. vt_capabilities
Returns supported task types, verification modes, settlement capabilities, and operating constraints

2. vt_request_task
Submits a task request and returns task_id, lifecycle state, and polling handle

3. vt_get_task_status
Returns lifecycle states such as accepted, running, verifying, completed, and failed

4. vt_get_task_result
Returns a normalized result object including payload, source information, proof summary, and related metadata

5. vt_verify_result
Returns verification outcome, verification details, and sufficient summary data for replayable verification flows

6. vt_settle_payment
Triggers settlement only when verification and policy conditions are satisfied

7. vt_get_settlement_receipt
Returns transaction hash, chain metadata, settlement status, and linkage to the corresponding result record

## 9. Public Object Model / 公共对象模型

### 中文

公共接口层建议稳定以下对象：

1. TaskRequest
描述任务类型、输入参数、验证要求、预算约束与结算条件

2. TaskHandle
描述 task_id、当前状态、创建时间、更新时间与查询入口

3. VerifiableResult
描述结果数据、来源信息、证明摘要、验证摘要与策略注记

4. SettlementReceipt
描述结算状态、交易哈希、链标识、金额、付款方、收款方与审计关联键

对象设计应尽量继承现有任务意图与证明对象的结构方向，以降低迁移成本并避免概念分裂。

### English

The public export layer should stabilize the following object families:

1. TaskRequest
Describes task type, input parameters, verification requirements, budget constraints, and settlement conditions

2. TaskHandle
Describes task_id, current state, creation time, update time, and lookup entry points

3. VerifiableResult
Describes result payload, source information, proof summary, verification summary, and policy notes

4. SettlementReceipt
Describes settlement state, transaction hash, chain identifier, amount, payer, payee, and audit linkage key

The object design should inherit as much as possible from the existing task intent and proof object direction in order to reduce migration cost and avoid conceptual fragmentation.

## 10. Trust Properties / 信任属性

### 中文

VeriTask 的公共导出需要稳定向调用方交付以下属性：

1. Provenance
结果来源可说明且可验证

2. Integrity
交付结果在传递过程中未被篡改

3. Execution Trust
结果生产过程具有可信执行约束或等价证明

4. Verification Replayability
调用方可以对结果进行复验，而非只能依赖单次响应

5. Settlement Binding
支付结算与验证通过的结果对象建立明确绑定

6. Auditability
结果、证明与结算之间具备可追踪的审计关联

### English

The public VeriTask export must provide the following stable trust properties:

1. Provenance
The result source is explainable and verifiable

2. Integrity
The delivered result has not been altered in transit

3. Execution Trust
The result production process is backed by trusted execution constraints or equivalent evidence

4. Verification Replayability
Callers can re-verify the result rather than relying on a single response

5. Settlement Binding
Payment and settlement are explicitly bound to the verified result object

6. Auditability
Results, proofs, and settlements remain traceably linked for audit purposes

## 11. Relationship with OnchainOS MCP / 与 OnchainOS MCP 的关系

### 中文

VeriTask 与 OKX OnchainOS MCP 的关系，应定义为上层组合关系，而非重复暴露关系。

职责划分如下：

1. OnchainOS MCP 已经提供可直接复用的基础工具能力，包括 token search、market price、token price info、portfolio balances、swap quote、gateway gas 与 broadcast 等
2. VeriTask 提供可信任务交易、证明绑定、验证摘要、结果回放与结算回执等高层能力
3. VeriTask 的公开导出应当调用、编排并约束这些官方 MCP 能力，而不是平行再造一套等价基础工具面
4. 因此，VeriTask 与 OnchainOS MCP 的关系应被理解为“可信交易中间层对官方能力栈的有机组合”，而不是“另一套并列的基础 MCP 服务”

### English

The relationship between VeriTask and OKX OnchainOS MCP should be defined as an upper-layer composition relationship rather than a redundant exposure relationship.

The division of responsibility is:

1. OnchainOS MCP already provides reusable foundational tools such as token search, market price, token price info, portfolio balances, swap quote, gateway gas, and broadcast
2. VeriTask provides higher-level capabilities such as trusted task transactions, proof binding, verification summaries, replayable result verification, and settlement receipts
3. VeriTask's public export should invoke, orchestrate, and constrain those official MCP capabilities rather than rebuilding a parallel equivalent tool surface
4. Therefore, the relationship should be understood as an organic composition of a trusted transaction middleware layer on top of the official capability stack, not as a separate peer MCP foundation

## 12. Best-Practice Findings / 最佳实践调研结论

### 中文

基于对官方 MCP 文档与 OnchainOS 官方仓库的联网调研，本方案在后续实现阶段应吸收以下最佳实践：

1. 工具边界应保持单一职责、Schema 明确
MCP 的 Tool 适合表达“单次动作”，不适合把过多隐式流程塞进一个超大接口。因此 VeriTask 应继续把公共工具面稳定为任务提交、状态查询、结果获取、验证与结算等少量明确动作。

2. 结构化输出应成为默认能力，而不是附属说明
官方 MCP 文档强调 `inputSchema`、`outputSchema` 与 `structuredContent`。因此 VeriTask 后续实现不应只返回说明性文本，而应让 `TaskHandle`、`VerifiableResult`、`SettlementReceipt` 具备稳定的结构化输出契约。

3. 长耗时流程应以句柄化和可重取为核心
MCP 架构与实验性 Tasks 方向都支持长任务、状态跟踪与延迟取回。VeriTask 本身天然是长流程，因此不应把完整交易流水压扁成一次同步响应，而应坚持 `request -> handle -> status/result -> verify -> settle` 的句柄式模型。

4. 结果证明与回执适合同时作为 Resource 暴露
MCP 不只有 Tools，也有 Resources。对于 ProofBundle、验证摘要、结算回执、审计记录这类需要复查、重读、订阅更新的对象，更适合在工具返回之外提供稳定 Resource URI 或 Resource Template。

5. 敏感操作必须保留人类确认与审计链路
官方 MCP 文档对敏感 Tool 调用强调 human-in-the-loop、输入校验、限流、超时与日志。对 VeriTask 而言，这意味着支付结算、预算提升、供应方切换等动作不应默许自动放行，而应保留显式策略门与审计记录。

6. 传输层应采用“本地先行、远程后置”的演进方式
官方 MCP 推荐尽可能支持 stdio；HTTP 远程模式则要求 session、认证、Origin 校验与可恢复流。结合 VeriTask 当前形态，首轮更适合先做本地 stdio 导出适配层，远程 Streamable HTTP 作为后续独立阶段推进。

7. 动态供给层变化不应破坏公共工具契约
MCP 支持 `tools/list_changed` 与 `resources/list_changed`，适合表达供给层变化；但这不意味着频繁改工具名。Worker 接入、下线、策略变化更适合作为能力元数据和资源变化，而不是公共工具面的高频重构。

### English

Based on direct research into the official MCP documentation and the OnchainOS repository, the implementation phase for this design should absorb the following best practices:

1. Tool boundaries should remain single-purpose and schema-explicit
MCP Tools are best used for discrete actions, not oversized interfaces with too much hidden workflow. VeriTask should therefore keep its public tool surface focused on a small number of clear actions such as task request, status lookup, result retrieval, verification, and settlement.

2. Structured output should be a default capability, not an afterthought
The official MCP guidance emphasizes `inputSchema`, `outputSchema`, and `structuredContent`. Accordingly, VeriTask should not rely on descriptive text alone. `TaskHandle`, `VerifiableResult`, and `SettlementReceipt` should become stable structured contracts.

3. Long-running flows should be handle-based and replayable
The MCP architecture and experimental Tasks direction both support long-running operations, status tracking, and deferred retrieval. VeriTask is naturally long-running, so it should avoid flattening the full transaction flow into one synchronous response and instead preserve a `request -> handle -> status/result -> verify -> settle` lifecycle.

4. Proofs and receipts should also be exposed as Resources
MCP is not limited to Tools; it also provides Resources. Objects such as ProofBundles, verification summaries, settlement receipts, and audit records are well-suited for stable Resource URIs or Resource Templates in addition to tool-returned content.

5. Sensitive operations must preserve human confirmation and auditability
The official MCP guidance emphasizes human-in-the-loop control, input validation, rate limiting, timeouts, and usage logs for sensitive tool execution. For VeriTask, this means settlement, budget escalation, and supplier-switching actions should remain policy-gated and auditable.

6. Transport evolution should be local-first, remote-second
Official MCP guidance recommends supporting stdio whenever possible, while remote HTTP mode introduces session management, authentication, origin validation, and resumable streams. Given VeriTask's current shape, the first iteration should favor a local stdio export adapter, with Streamable HTTP as a later independent phase.

7. Dynamic supply-side changes should not break the public tool contract
MCP supports `tools/list_changed` and `resources/list_changed`, which are appropriate for reflecting supply-side changes. That does not imply frequent renaming of tools. Worker onboarding, removal, and policy changes should primarily surface as capability metadata and resource updates rather than public tool churn.

## 13. Implementation Plan / 实现计划

### 中文

结合当前 VeriTask 代码边界与上述最佳实践，建议按以下顺序落地：

首先需要明确：本次 MCP 封装在设计目标上属于增量导出与接口整理，不改变 VeriTask 当前已经跑通的委托、验证、支付与 Worker workflow。本轮工作的目标是增加一层可公开组合的 MCP export adapter，而不是回写、替换或破坏现有业务闭环。

Phase A: Local MCP Export Adapter

1. 在现有 VeriTask 编排层之外增加一个独立 MCP export adapter，而不是重写 task-delegator、verifier、okx-x402-payer 与 worker 流程
2. 首轮优先采用 stdio 导出模式，与官方 `onchainos mcp` 的本地进程型接入方式保持一致
3. 将 `vt_request_task`、`vt_get_task_status`、`vt_get_task_result`、`vt_verify_result`、`vt_settle_payment`、`vt_get_settlement_receipt` 实现为最小公共工具面

Phase B: Structured Contract Hardening

1. 为 `TaskHandle`、`VerifiableResult`、`SettlementReceipt` 补齐稳定的输入输出 Schema
2. 在工具结果中同时返回说明性文本与结构化对象，避免调用方只能依赖自由文本解析
3. 对错误返回建立明确分层：协议级参数错误、业务级执行失败、验证失败、结算失败分别表达

Phase C: Resource Layer for Replay and Audit

1. 为任务结果、ProofBundle、验证摘要、结算回执设计稳定 Resource URI，例如 `veritask://tasks/{id}`、`veritask://results/{id}`、`veritask://proofs/{id}`、`veritask://receipts/{id}`
2. 对高价值对象增加 `resources/read` 与后续可选 `resources/subscribe` 支持，用于结果重取、审计复查与状态更新
3. 将可订阅变化优先放在资源层，而不是频繁改变工具面

Phase D: Policy and Human Control

1. 对结算、预算升级、供应方切换等敏感动作增加显式确认门
2. 为关键操作增加审计日志与幂等键，确保重复调用不会造成重复支付或重复状态推进
3. 对外清晰区分“任务已完成但未结算”与“任务已结算”的状态边界

Phase E: Open Supply Expansion

1. 在不破坏用户侧公共契约的前提下，引入开放 Worker 接入、信誉、策略与风控层
2. 将 Worker 供给变化通过 capability metadata、resource 更新与策略层治理表达，而不是直接暴露底层调度细节
3. 待本地导出层稳定后，再评估远程 Streamable HTTP 版本，用于多客户端、多租户或外部平台集成

### English

Combining the current VeriTask code boundaries with the best practices above, the recommended implementation order is as follows:

One point should be explicit from the outset: this MCP packaging is intended as an additive export and interface-layer consolidation. It does not change VeriTask's already working delegation, verification, payment, and Worker workflow. The goal of this iteration is to add a publicly composable MCP export adapter, not to rewrite, replace, or disrupt the existing business flow.

Phase A: Local MCP Export Adapter

1. Add an independent MCP export adapter outside the existing VeriTask orchestration layer rather than rewriting the task-delegator, verifier, x402 payer, or Worker flow
2. Use stdio first so the initial export model aligns with the same local process pattern used by the official `onchainos mcp`
3. Implement a minimal public tool surface centered on `vt_request_task`, `vt_get_task_status`, `vt_get_task_result`, `vt_verify_result`, `vt_settle_payment`, and `vt_get_settlement_receipt`

Phase B: Structured Contract Hardening

1. Add stable input/output schemas for `TaskHandle`, `VerifiableResult`, and `SettlementReceipt`
2. Return both human-readable text and structured objects from tool results so integrators do not depend on free-form parsing alone
3. Separate protocol-level argument errors, business execution failures, verification failures, and settlement failures into distinct error classes

Phase C: Resource Layer for Replay and Audit

1. Define stable Resource URIs for task state, results, proofs, verification summaries, and receipts, such as `veritask://tasks/{id}`, `veritask://results/{id}`, `veritask://proofs/{id}`, and `veritask://receipts/{id}`
2. Add `resources/read` and later optional `resources/subscribe` support for replay, audit review, and state refresh on high-value objects
3. Prefer resource updates over frequent tool-surface changes when reflecting evolving supply-side state

Phase D: Policy and Human Control

1. Add explicit confirmation gates for settlement, budget escalation, and supplier-switching actions
2. Add audit logging and idempotency keys to critical operations so repeated calls do not cause duplicate payments or duplicated lifecycle transitions
3. Keep a clear outward distinction between “task completed but not settled” and “task settled”

Phase E: Open Supply Expansion

1. Introduce open Worker onboarding, reputation, policy, and risk-control layers without breaking the user-facing public contract
2. Represent Worker-supply evolution through capability metadata, resource updates, and policy governance rather than exposing raw scheduling details
3. Evaluate a remote Streamable HTTP version only after the local export layer is stable, targeting multi-client, multi-tenant, or external platform integrations

### 13.1 X Layer OnChainOS AI Hackathon Phase 1 Scope / 黑客松 Phase 1 实现范围

### 中文

Onchain OS AI Hackathon Phase 1 时间窗口为 2026 年 3 月 12 日至 3 月 26 日 23:59 UTC。针对该阶段的参赛交付，本项目实现范围定义如下：

1. 采用 Phase A 的本地 stdio MCP export adapter 路线，形成可运行、可演示、可被 Agent 调用的统一入口
2. 最小公共动作闭环定义为任务请求、结果获取、支付结算与回执获取；状态查询与结果复验以轻量实现提供
3. 必须确保至少一个真实任务类型形成端到端闭环：上游 Agent 发起请求，VeriTask 编排 Worker 交付结果，结果附带证明材料，通过验证后由 x402 在 X Layer 主网完成支付并返回交易哈希
4. 必须将 x402 支付能力放在 Demo 主链路中心，而不是仅作为附属功能，因为这直接对应官方对 Agentic Payments 与 X Layer 主网交易证明的要求
5. 必须保留多 Agent 协作叙事的可见性，即调用方、VeriTask 中间层、Worker 供给层之间的职责分工在交付物、文档与演示中清晰可见
6. 必须明确展示与 OnchainOS 能力栈的结合，至少在支付层使用 x402，并在需要时调用 Wallet API、Market API 或相关能力支撑任务闭环与演示说服力
7. 结构化契约、Resource 暴露与验证摘要的实现范围以支撑 Demo、评审理解与后续复查为界，不在 Phase 1 内扩展为完整平台化审计系统

### English

Onchain OS AI Hackathon Phase 1 runs from March 12 to March 26, 2026 at 23:59 UTC. For the competition delivery in this phase, the implementation scope is defined as follows:

1. Keep the Phase A local stdio MCP export adapter path so that a runnable, demoable, Agent-callable entry point can be shipped quickly
2. Keep only the minimal public action loop, with highest priority on task request, result retrieval, payment settlement, and settlement receipt retrieval; status lookup and replayable verification should remain lightweight
3. Ensure that at least one real task type forms an end-to-end closed loop: an upstream Agent submits a request, VeriTask orchestrates Worker delivery, the result carries proof artifacts, the result is verified, and x402 completes payment on X Layer mainnet with a transaction hash returned
4. Keep x402 payment on the main demo path rather than as an optional side feature, because this directly supports the official Agentic Payments and X Layer mainnet proof expectations
5. Preserve the visibility of the multi-Agent collaboration narrative so that the caller layer, VeriTask middleware layer, and Worker supply layer remain clearly explainable in the deliverable, documentation, and demo
6. Explicitly demonstrate integration with the OnchainOS capability stack, using x402 for payment and, where helpful, Wallet API, Market API, or adjacent capabilities to strengthen the task loop and judge-facing credibility
7. For structured contracts, Resources, and verification summaries, implement only the level needed to support the demo, reviewer comprehension, and limited replayability; do not expand them into a full platform-grade audit product during Phase 1

## 14. Out of Scope / 本轮不纳入范围

### 中文

以下内容不纳入首阶段公开导出：

1. 面向上游调用方直接开放的 Worker 直连接口
2. 首阶段对外公开的 Worker 市场注册、竞价与供应侧治理协议
3. Worker 私有地址、运行拓扑与供应商特定实现细节
4. 所有链上能力的通用代理接口
5. 与 OnchainOS MCP 公共工具完全重叠的镜像接口
6. 面向外部调用方公开的底层执行调度细节

### English

The following items are out of scope for the first public export iteration:

1. Direct Worker connectivity interfaces exposed to upstream callers
2. Public Worker-market registration, bidding, and supply-side governance protocols in the first-stage release
3. Private Worker addresses, runtime topology, and supplier-specific implementation details
4. Generic proxy interfaces for arbitrary on-chain capabilities
5. Mirrored interfaces that fully overlap with the existing OnchainOS MCP public tool surface
6. Low-level execution scheduling details exposed to external callers

## 15. Iteration Roadmap / 迭代路线

### 中文

Phase 1: Public Export Layer

1. 建立最小可用的 MCP 公共导出层
2. 将现有请求、验证与支付流程收敛为统一公共契约
3. 稳定 TaskHandle、VerifiableResult 与 SettlementReceipt 三类公共对象

Phase 2: Verification and Receipt Hardening

1. 强化生命周期状态模型与错误分类
2. 完善复验接口与结果摘要表达
3. 强化结果对象与结算对象之间的绑定关系

Phase 3: Open Supply Expansion

1. 引入多 Worker 路由
2. 引入开放接入的 Worker 注册、信誉、策略与风控层
3. 保持公共导出面稳定，允许供给层向市场化结构持续演进

### English

Phase 1: Public Export Layer

1. Establish a minimal viable MCP public export layer
2. Converge the current request, verification, and payment flows into a unified public contract
3. Stabilize TaskHandle, VerifiableResult, and SettlementReceipt as the primary public object families

Phase 2: Verification and Receipt Hardening

1. Strengthen lifecycle state modeling and error taxonomy
2. Improve replayable verification interfaces and result summaries
3. Tighten the binding between result objects and settlement objects

Phase 3: Open Supply Expansion

1. Introduce multi-Worker routing
2. Introduce open Worker onboarding, reputation, policy, and risk-control layers
3. Keep the public export surface stable while allowing the supply side to evolve toward market-oriented operation

## 16. Acceptance Criteria / 验收标准

### 中文

本轮方案完成后，应至少满足以下标准：

1. 上游 Agent 无需感知 Worker 地址或实现细节即可发起任务
2. 调用方能够获得标准化结果、验证摘要与结算回执
3. 公共接口职责与 OnchainOS MCP 基础能力职责划分清晰
4. 后续增加或替换 Worker 不需要破坏公共 MCP 接口

### English

This iteration should be considered complete only if it satisfies the following criteria:

1. An upstream agent can submit a task without awareness of Worker addresses or implementation details
2. The caller can obtain a normalized result, a verification summary, and a settlement receipt
3. Responsibility boundaries remain clear between VeriTask's public interface and OnchainOS MCP's infrastructure capabilities
4. Future Worker addition or replacement does not require breaking the public MCP interface

## 16.1 Delivery Standard / 交付标准

### 中文

当 VeriTask 的 MCP 封装进入实现阶段后，本次更新迭代只有在满足以下条件时，才可认为任务完成：

1. 已形成可运行的 MCP export adapter，并以增量方式接入现有 VeriTask，而不是重写或替换原有 workflow
2. 现有已成功实现的委托、验证、支付与 Worker workflow 行为保持不变，不因本轮 MCP 封装产生回归或结构性破坏
3. 对上游 Agent 已稳定提供最小公共能力闭环：任务请求、状态查询、结果获取、验证查询与结算回执获取
4. MCP 导出层对官方 OnchainOS MCP 能力栈形成真实调用与编排关系，而不是平行复制 market、token、wallet、gateway、swap 等基础工具面
5. `TaskHandle`、`VerifiableResult`、`SettlementReceipt` 至少在首轮实现中具备稳定、可解析、可复用的结构化契约
6. 关键敏感动作具备明确策略门，例如支付结算、预算提升、供应方切换不能在无约束状态下自动放行
7. 后续新增或替换 Worker 不需要破坏用户侧公共 MCP 接口，从而证明“中间层稳定、供给层可演进”的设计目标成立

### English

Once VeriTask's MCP packaging enters implementation, this update iteration should be considered complete only if all of the following conditions are met:

1. A runnable MCP export adapter exists and is integrated additively with the current VeriTask system rather than rewriting or replacing the existing workflow
2. The already working delegation, verification, payment, and Worker workflow remains behaviorally unchanged, with no regression or structural break introduced by the MCP packaging work
3. The upstream-agent side is stably provided with the minimal public capability loop: task request, status lookup, result retrieval, verification lookup, and settlement-receipt retrieval
4. The export layer forms a real invocation and orchestration relationship with the official OnchainOS MCP capability stack rather than duplicating equivalent market, token, wallet, gateway, or swap tools in parallel
5. `TaskHandle`, `VerifiableResult`, and `SettlementReceipt` provide stable, parseable, and reusable structured contracts at least in the first implementation round
6. Sensitive actions are policy-gated, meaning settlement, budget escalation, and supplier-switching are not allowed to pass automatically without explicit control
7. Future Worker addition or replacement does not require breaking the user-facing public MCP interface, demonstrating that the middleware boundary remains stable while the supply layer remains evolvable

## 16.2 X Layer OnChainOS AI Hackathon Phase 1 Engineering Acceptance / 黑客松 Phase 1 工程验收标准

### 中文

在本设计进入 Onchain OS AI Hackathon Phase 1 实现窗口后，该工程验收标准定义如下：

1. 必须形成可运行的本地 stdio MCP export adapter，且该适配层以增量方式接入现有 VeriTask workflow，而不是重写或替换既有委托、验证、支付与 Worker 流程
2. Phase 1 必须形成最小公共工程闭环：任务请求、结果获取、支付结算与回执获取四项能力可用；状态查询与结果复验可以轻量实现，但不能缺失
3. 至少一个真实任务类型必须跑通完整工程链路：上游 Agent 请求、VeriTask 编排、Worker 交付、验证通过、x402 在 X Layer 主网完成支付、返回可关联的交易回执
4. 工程实现必须保持多 Agent 分层边界清晰，即上游调用方、VeriTask 中间层与 Worker 供给层之间的职责不混叠，且上游调用方无需感知 Worker 细节即可完成调用
5. 工程实现必须体现与 OnchainOS 能力栈的实质性组合关系，至少在支付层接入 x402；若任务闭环需要钱包、市场或相关能力，也应通过组合调用体现，而不是平行复制基础工具面
6. 工程结果必须同时保留可信层与链上层的可验证对象，即结果对象带有验证摘要或证明材料，结算对象带有交易哈希、链信息与结果关联关系

### English

Once this design enters the Onchain OS AI Hackathon Phase 1 implementation window, the engineering acceptance standard is defined as follows:

1. A runnable local stdio MCP export adapter must exist, and it must integrate additively with the current VeriTask workflow rather than rewriting or replacing the existing delegation, verification, payment, or Worker flow
2. Phase 1 must provide the minimal public engineering loop: task request, result retrieval, payment settlement, and settlement receipt retrieval must be available; status lookup and replayable verification may remain lightweight but cannot be absent
3. At least one real task type must complete the full engineering chain: upstream Agent request, VeriTask orchestration, Worker delivery, successful verification, x402 payment on X Layer mainnet, and a transaction-linked settlement receipt
4. The implementation must preserve clear multi-Agent boundary separation so that the upstream caller layer, VeriTask middleware layer, and Worker supply layer remain distinct, and upstream callers do not need Worker-specific knowledge to complete the flow
5. The implementation must demonstrate a substantive composition relationship with the OnchainOS capability stack, using x402 at minimum in the payment layer and using Wallet, Market, or adjacent capabilities through composition where they materially strengthen the task loop, rather than duplicating foundational tools in parallel
6. The engineering result must preserve both the trust layer and the on-chain layer as verifiable objects: the result object carries proof material or a verification summary, and the settlement object carries transaction hash, chain metadata, and linkage to the result

## 16.3 Phase 1 Acceptance Record / 黑客松 Phase 1 验收记录

### 中文

截至 2026-03-21，本设计已完成一次真实 Phase 1 验收闭环，记录如下：

1. MCP 入口：本地 stdio MCP export adapter 成功启动，并通过 `tools/list` 与 `resources/list` 发现性验证
2. 真实任务类型：`aave` TVL 查询
3. MCP Handle：`vtmcp-515e754b-719a-40a2-a03c-d32eaa160fbf`
4. Worker Task ID：`4820c376-d617-4d35-af70-35f8c7fcada8`
5. 结果状态：`completed`，验证状态：`passed`，结算状态：`completed`
6. 结果对象包含可验证材料：TVL 业务结果、`sha256_mock` ZK 摘要、`intel_tdx` TEE attestation 摘要，以及验证详情
7. x402 真实结算已在 X Layer 主网完成：
	- `chain_index`: `196`
	- `token`: `USDT`
	- `amount`: `0.01`
	- `payer`: `0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85`
	- `payee`: `0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb`
	- `tx_hash`: `0xf8c700edb574af275f22c77ec769af54847c91c27d4afaa4e477230eff99bad6`
	- `explorer_url`: `https://www.oklink.com/xlayer/tx/0xf8c700edb574af275f22c77ec769af54847c91c27d4afaa4e477230eff99bad6`
8. 该次真实运行证明本设计已满足 16.2 中定义的最小公共工程闭环要求，即请求、结果、验证、结算与回执在同一条真实链路中全部跑通

补充说明：在本次成功结算之前，曾出现一次 `insufficient_funds`。复核后确认，付款地址由 `.env` 中的 `CLIENT_PRIVATE_KEY` 派生，且当时该地址在 X Layer 上的 USDT 余额低于 `0.01`。补足余额后，同一条 MCP 结算路径已成功返回真实交易回执。

### English

As of 2026-03-21, this design has completed one real Phase 1 acceptance loop with the following record:

1. MCP entrypoint: the local stdio MCP export adapter started successfully and passed discovery validation through `tools/list` and `resources/list`
2. Real task type: `aave` TVL retrieval
3. MCP handle: `vtmcp-515e754b-719a-40a2-a03c-d32eaa160fbf`
4. Worker task ID: `4820c376-d617-4d35-af70-35f8c7fcada8`
5. Result state: `completed`, verification state: `passed`, settlement state: `completed`
6. The result object carried verifiable material: TVL business data, a `sha256_mock` ZK summary, an `intel_tdx` TEE attestation summary, and verification details
7. Real x402 settlement completed on X Layer mainnet:
	- `chain_index`: `196`
	- `token`: `USDT`
	- `amount`: `0.01`
	- `payer`: `0x012E6Cfbbd1Fcf5751d08Ec2919d1C7873A4BB85`
	- `payee`: `0x871c98e2b2f22b6a215493a96d9eb76ccc0015cb`
	- `tx_hash`: `0xf8c700edb574af275f22c77ec769af54847c91c27d4afaa4e477230eff99bad6`
	- `explorer_url`: `https://www.oklink.com/xlayer/tx/0xf8c700edb574af275f22c77ec769af54847c91c27d4afaa4e477230eff99bad6`
8. This real run demonstrates that the design now satisfies the minimal public engineering loop defined in section 16.2, with request, result, verification, settlement, and receipt all completed in one live path

Supplemental note: before the successful settlement above, one run returned `insufficient_funds`. Follow-up verification confirmed that the payer address is derived from `CLIENT_PRIVATE_KEY` in `.env`, and that its X Layer USDT balance was below `0.01` at that time. After funding the payer wallet, the same MCP settlement path returned a real transaction-linked receipt successfully.

## 17. Design Statement / 设计结论

### 中文

本轮公开方案将 VeriTask 定义为面向 MCP 生态的可信任务交易中间层。其公共接口围绕任务请求、结果获取、验证与结算组织；其下游连接可开放接入的 Worker 供给层，并由 VeriTask 持续承接执行路由、验证绑定与结算编排。

这一边界用于在保持公共接口具备接入规模商业化能力的同时，为 VeriTask 后续扩展多 Worker、多策略、多供应方以及潜在 Worker 市场结构预留充足空间。

因此，本文档应被理解为一份面向外部读者的迭代更新说明：当前以概念展示形式发布，但设计口径已经按照可商用公共接口的标准组织，并将随 VeriTask 的后续版本持续收敛与增强。

### English

This iteration defines VeriTask as a trusted task transaction middleware layer for the MCP ecosystem. Its public interface is organized around task request, result retrieval, verification, and settlement, while an attachable Worker supply layer remains downstream of VeriTask and VeriTask continues to own execution routing, verification binding, and settlement orchestration.

This boundary preserves a public interface model with commercial-scale integration potential while retaining sufficient room for future expansion into multi-Worker, multi-policy, multi-supplier, and eventually Worker-market operation.

Accordingly, the document should be read as an iterative update note for external readers: released today as a concept-stage showcase, but already structured with the discipline expected of a future stable public interface.