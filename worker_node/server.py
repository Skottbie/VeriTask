#!/usr/bin/env python3
"""
VeriTask 3.0 — Worker Node FastAPI Server
Deployed to Phala Cloud CVM for TEE-isolated execution.

Endpoints:
    POST /execute  — Accept TaskIntent, return ProofBundle
    GET  /health   — Health check with TEE status
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# Load .env from monorepo root
load_dotenv(Path(__file__).parent.parent / ".env")

# Add skill directories to path
WORKER_DIR = Path(__file__).parent
sys.path.insert(0, str(WORKER_DIR / "skills" / "defi-scraper"))
sys.path.insert(0, str(WORKER_DIR / "skills" / "proof-generator"))

# Add bidding-agent to path for PCEG API (copied into Docker image)
# In Docker: /app/client_node/skills/bidding-agent/
# On dev machine: ../client_node/skills/bidding-agent/
_bidding_agent_dir = WORKER_DIR.parent / "client_node" / "skills" / "bidding-agent"
if _bidding_agent_dir.exists():
    sys.path.insert(0, str(_bidding_agent_dir))

# Add worker_node dir itself so pceg_api can be imported
sys.path.insert(0, str(WORKER_DIR))

from proof_generator import generate_proof_bundle  # noqa: E402

# Determine worker address for receiving payments
# Priority: WORKER_WALLET_ADDRESS env var > derived from WORKER_PRIVATE_KEY
WORKER_ADDRESS = "0x0000000000000000000000000000000000000000"
_wallet_addr = os.getenv("WORKER_WALLET_ADDRESS", "").strip()
if _wallet_addr:
    WORKER_ADDRESS = _wallet_addr
else:
    worker_key = os.getenv("WORKER_PRIVATE_KEY")
    if worker_key:
        try:
            from eth_account import Account

            # Strip 0x prefix, zero-pad to 64 hex chars, re-add prefix
            raw = worker_key.replace("0x", "").replace("0X", "")
            raw = raw.zfill(64)  # Handle keys shorter than 32 bytes
            acct = Account.from_key(f"0x{raw}")
            WORKER_ADDRESS = acct.address
        except Exception:
            pass

# Check if running in real TEE (dstack OS 0.5.x uses /var/run/dstack.sock)
TEE_AVAILABLE = False
try:
    dstack_sock = "/var/run/dstack.sock"
    if os.path.exists(dstack_sock):
        TEE_AVAILABLE = True
except Exception:
    pass

EXECUTE_TIMEOUT = 120  # seconds (zkFetch proof generation may take 60-90s)

# ─── Tamper Mode (persistent toggle for dispute demo) ─────────────────
# Valid values: "off", "zk", "tee", "both"
_TAMPER_MODE = "off"

app = FastAPI(
    title="VeriTask Worker Node",
    description="TEE-isolated worker that fetches DeFi data with cryptographic proofs",
    version="3.5.8",
)

# Mount PCEG API router (public read-only reputation graph endpoints)
try:
    from pceg_api import router as pceg_router  # noqa: E402
    app.include_router(pceg_router)
except ImportError as _pceg_err:
    print(f"\033[33m[Worker Server] PCEG API unavailable (missing deps): {_pceg_err}\033[0m")


# ─── Request / Response Models ───────────────────────────────────────

class TaskParams(BaseModel):
    protocol: str = Field(default="aave", description="DefiLlama protocol slug")


class TaskIntent(BaseModel):
    task_id: str = Field(default="", description="Unique task ID (auto-generated if empty)")
    type: str = Field(default="defi_tvl", description="Task type")
    params: TaskParams = Field(default_factory=TaskParams)
    client_wallet: str = Field(
        default="0x0000000000000000000000000000000000000000",
        description="Client's Ethereum address",
    )


class HealthResponse(BaseModel):
    status: str
    tee: bool
    worker_address: str


# ─── Endpoints ────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — reports TEE availability."""
    return HealthResponse(
        status="ok",
        tee=TEE_AVAILABLE,
        worker_address=WORKER_ADDRESS,
    )


@app.post("/execute")
async def execute(task: TaskIntent):
    """
    Execute a task: fetch data, generate proofs, return ProofBundle.
    If _TAMPER_MODE is active, automatically tampers the proof before returning.
    """
    global _TAMPER_MODE

    # Auto-generate task_id if not provided
    if not task.task_id:
        task.task_id = str(uuid.uuid4())

    if task.type != "defi_tvl":
        raise HTTPException(status_code=400, detail=f"Unsupported task type: {task.type}")

    try:
        bundle = await asyncio.wait_for(
            generate_proof_bundle(
                protocol=task.params.protocol,
                worker_address=WORKER_ADDRESS,
            ),
            timeout=EXECUTE_TIMEOUT,
        )
        bundle["task_id"] = task.task_id

        # Apply tamper if mode is active
        if _TAMPER_MODE in ("zk", "both"):
            bundle["zk_proof"]["hash"] = "deadbeef" * 8
        if _TAMPER_MODE in ("tee", "both"):
            bundle["tee_attestation"]["report_data"] = "cafebabe" * 8

        return bundle

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"Task execution timed out ({EXECUTE_TIMEOUT}s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {e}")


_VALID_TAMPER_MODES = {"off", "zk", "tee", "both"}


@app.post("/set_tamper_mode")
async def set_tamper_mode(mode: str = Query("off", description="off|zk|tee|both")):
    """Set persistent tamper mode. 'off' restores normal operation."""
    global _TAMPER_MODE
    if mode not in _VALID_TAMPER_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}. Must be one of {_VALID_TAMPER_MODES}")
    _TAMPER_MODE = mode
    return {"tamper_mode": _TAMPER_MODE}


@app.get("/get_tamper_mode")
async def get_tamper_mode():
    """Check current tamper mode."""
    return {"tamper_mode": _TAMPER_MODE}


# ─── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("WORKER_PORT", "8001"))
    print(f"\033[36m[Worker Server] Starting on port {port}...\033[0m")
    print(f"    TEE available: {TEE_AVAILABLE}")
    print(f"    Worker address: {WORKER_ADDRESS}")
    uvicorn.run(app, host="0.0.0.0", port=port)
