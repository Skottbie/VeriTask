# CLAUDE.md — VeriTask 3.0 Project Instructions

> Instructions for AI coding assistants working on this project.

## Project Identity

**VeriTask 3.0** — Claw-to-Claw (C2C) Verifiable Micro-Procurement Protocol
- **Hackathon**: OKX OnchainOS "AI松" (2026)
- **Stack**: Python 3.12 + Node.js + OpenClaw + OKX OnchainOS Skills
- **Architecture**: Dual-agent (Client + Worker) with cryptographic trust chain

## Repository Structure

```
VeriTask/
├── AGENTS.md              # Multi-agent routing rules (OpenClaw compatible)
├── CLAUDE.md              # This file — project-level AI instructions
├── .env                   # Environment variables (DO NOT commit)
├── .env.example           # Template for .env
├── run_demo.ps1           # Windows PowerShell demo script
├── package.json           # Node.js deps (@reclaimprotocol/zk-fetch)
├── schemas/               # JSON schemas (TaskIntent, ProofBundle)
├── client_node/
│   ├── openclaw.json      # Client Agent OpenClaw config
│   └── skills/
│       ├── task-delegator/ # C2C orchestrator (entry point)
│       ├── verifier/       # ProofBundle validation
│       └── okx-x402-payer/ # On-chain USDT payment
└── worker_node/
    ├── openclaw.json      # Worker Agent OpenClaw config
    ├── server.py          # FastAPI server (POST /execute)
    ├── Dockerfile         # Docker container config
    ├── docker-compose.yml # Docker Compose config
    └── skills/
        ├── defi-scraper/   # DefiLlama TVL data fetcher
        └── proof-generator/# zkTLS + TEE ProofBundle generator
```

## Key Technical Decisions

1. **SKILL.md files** use OpenClaw 2026.3 format with YAML frontmatter:
   `name`, `author`, `version`, `license`, `homepage`, `description` (routing triggers),
   `capabilities`, `permissions`, `examples`

2. **ProofBundle** has two layers:
   - Layer 1: Reclaim zkFetch (zkTLS data provenance) — fallback: SHA256 hash
   - Layer 2: Phala dstack TDX quote (TEE attestation) — fallback: mock

3. **OKX x402 Payment**: EIP-712 signed → OKX verify → OKX settle (gasless USDT transfer)

4. **Worker communicates via FastAPI** on port 8001, not direct skill invocation

## Development Commands

```bash
# Activate venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # WSL/Linux

# Start Worker server
cd worker_node && uvicorn server:app --host 127.0.0.1 --port 8001

# Run full demo
.\run_demo.ps1

# Run demo (skip payment)
.\run_demo.ps1 -SkipPayment

# OpenClaw integration (WSL)
bash deploy_to_openclaw.sh
openclaw skills refresh
openclaw gateway --port 18789 --verbose
```

## Code Conventions

- All Python scripts have `#!/usr/bin/env python3` shebang
- Console output uses color-coded prefixes: `[Worker]`, `[Client-Verifier]`, `[Client-x402]`
- Every skill supports `--json` flag for machine-readable output
- Use `python-dotenv` to load `.env` from project root
- Error handling: explicit try/except with descriptive messages
- No `localhost` — always use `127.0.0.1` (IPv4 compatibility on Windows)

## Important Notes

- **DO NOT** modify files in `MustReadFirst_donotcommit/` — reference-only docs
- **DO NOT** commit `.env`, `node_modules/`, `.venv/`, `__pycache__/`
- When editing code, always check current state before modifying
- Prefer incremental changes over large rewrites
- OKX sandbox API keys are in `.env.example` — safe for testing
