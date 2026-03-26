---
name: graph-anchor
author: VeriTask Team
version: 1.0.0
license: MIT
description: >-
  Anchors reputation edges on X Layer. Encodes ProofBundle as calldata,
  signs a self-transfer tx, and broadcasts via onchainos gateway.
capabilities:
  - Build VT2 calldata from ProofBundle
  - Sign EIP-1559 self-transfer on X Layer
  - Broadcast via onchainos gateway broadcast
permissions:
  - env:CLIENT_PRIVATE_KEY
  - network:xlayerrpc.okx.com
examples:
  - "Write this proof to the reputation graph"
  - "Anchor the verified ProofBundle on-chain"
---

# Graph Anchor Agent

Writes a Proof-Conditioned reputation edge to X Layer after a successful C2C task.

## Usage

```bash
python graph_anchor.py --bundle proof_bundle.json
python graph_anchor.py --bundle proof_bundle.json --dry-run
echo '<json>' | python graph_anchor.py --stdin --json
```
