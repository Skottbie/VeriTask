#!/usr/bin/env python3
"""VeriTask MCP export adapter.

This server adds a stdio MCP layer on top of the existing VeriTask client-side
workflow without modifying the working delegation, verification, and payment
pipeline.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import uuid
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

CLIENT_NODE_DIR = Path(__file__).resolve().parent
TASK_DELEGATOR_DIR = CLIENT_NODE_DIR / "skills" / "task-delegator"
CLIENT_SKILLS_DIR = CLIENT_NODE_DIR / "skills"
sys.path.insert(0, str(TASK_DELEGATOR_DIR))
sys.path.insert(0, str(CLIENT_SKILLS_DIR / "verifier"))
sys.path.insert(0, str(CLIENT_SKILLS_DIR / "okx-x402-payer"))

from task_delegator import delegate_task  # noqa: E402
from verifier import verify_proof_bundle  # noqa: E402
from okx_x402_payer import execute_payment  # noqa: E402


TaskState = Literal["queued", "running", "completed", "settled", "failed"]
VerificationState = Literal["not_run", "passed", "failed"]
SettlementState = Literal["not_ready", "ready", "completed", "failed", "skipped"]
PAYMENT_CONFIRMATION_TOKEN = "CONFIRM_X402_PAYMENT"


class ResourceLinks(BaseModel):
    task: str = Field(description="Task snapshot resource URI")
    result: str = Field(description="Task result resource URI")
    receipt: str = Field(description="Settlement receipt resource URI")


class TaskHandle(BaseModel):
    handle_id: str = Field(description="Stable MCP-facing task handle")
    protocol: str = Field(description="Requested protocol slug")
    status: TaskState = Field(description="Current execution state")
    created_at: str = Field(description="UTC ISO-8601 timestamp when the handle was created")
    skip_payment: bool = Field(description="Whether on-chain settlement is skipped for this request")
    amount_usdt: float = Field(description="Requested USDT settlement amount")
    resources: ResourceLinks = Field(description="Related MCP resources for the task")


class TaskStatus(BaseModel):
    handle_id: str = Field(description="Stable MCP-facing task handle")
    protocol: str = Field(description="Requested protocol slug")
    status: TaskState = Field(description="Current execution state")
    verification_state: VerificationState = Field(description="Current verification replay state")
    settlement_state: SettlementState = Field(description="Current settlement state")
    created_at: str = Field(description="UTC ISO-8601 timestamp when the handle was created")
    updated_at: str = Field(description="UTC ISO-8601 timestamp of the latest state change")
    worker_task_id: str | None = Field(default=None, description="Underlying VeriTask task_id once available")
    result_available: bool = Field(description="Whether a completed result is available")
    receipt_available: bool = Field(description="Whether a settlement receipt is available")
    error: str | None = Field(default=None, description="Failure reason when status is failed")
    resources: ResourceLinks = Field(description="Related MCP resources for the task")


class SettlementReceipt(BaseModel):
    handle_id: str = Field(description="Stable MCP-facing task handle")
    worker_task_id: str | None = Field(default=None, description="Underlying VeriTask task_id once available")
    settlement_state: SettlementState = Field(description="Settlement state for this task")
    tx_hash: str | None = Field(default=None, description="On-chain settlement transaction hash")
    explorer_url: str | None = Field(default=None, description="Explorer URL for the settlement transaction")
    chain_index: str | None = Field(default=None, description="Target chain index for settlement")
    amount: float | None = Field(default=None, description="Settled amount in payment token units")
    token: str | None = Field(default=None, description="Settled token symbol")
    payer: str | None = Field(default=None, description="Settlement payer address")
    payee: str | None = Field(default=None, description="Settlement payee address")
    error: str | None = Field(default=None, description="Settlement error if settlement failed")
    resources: ResourceLinks = Field(description="Related MCP resources for the task")


class VerificationReplay(BaseModel):
    handle_id: str = Field(description="Stable MCP-facing task handle")
    worker_task_id: str | None = Field(default=None, description="Underlying VeriTask task_id once available")
    verification_state: VerificationState = Field(description="Verification replay state")
    is_valid: bool = Field(description="Whether replay verification passed")
    reason: str = Field(description="Replay verification summary")
    details: list[str] = Field(description="Replay verification detail lines")
    resources: ResourceLinks = Field(description="Related MCP resources for the task")


class TaskResult(BaseModel):
    handle_id: str = Field(description="Stable MCP-facing task handle")
    protocol: str = Field(description="Requested protocol slug")
    status: TaskState = Field(description="Current execution state")
    verification_state: VerificationState = Field(description="Current verification replay state")
    settlement_state: SettlementState = Field(description="Current settlement state")
    worker_task_id: str | None = Field(default=None, description="Underlying VeriTask task_id once available")
    data: dict[str, Any] | None = Field(default=None, description="Worker-delivered business payload")
    proof_details: dict[str, Any] | None = Field(default=None, description="Proof material summary")
    verification: dict[str, Any] | None = Field(default=None, description="Verification summary")
    payment: dict[str, Any] | None = Field(default=None, description="Settlement result when payment is enabled")
    settlement_receipt: SettlementReceipt | None = Field(default=None, description="Normalized settlement receipt when available")
    logs: str = Field(description="Captured stdout and stderr from the existing VeriTask workflow")
    error: str | None = Field(default=None, description="Failure reason when status is failed")
    resources: ResourceLinks = Field(description="Related MCP resources for the task")


class TaskRecord:
    def __init__(self, handle_id: str, protocol: str, amount_usdt: float, skip_payment: bool):
        timestamp = utc_now()
        self.handle_id = handle_id
        self.protocol = protocol
        self.amount_usdt = amount_usdt
        self.skip_payment = skip_payment
        self.status: TaskState = "queued"
        self.created_at = timestamp
        self.updated_at = timestamp
        self.worker_task_id: str | None = None
        self.result: dict[str, Any] | None = None
        self.error: str | None = None
        self.logs = ""
        self.verification_result: dict[str, Any] | None = None
        self.verification_state: VerificationState = "not_run"
        self.settlement_receipt: dict[str, Any] | None = None
        self.settlement_state: SettlementState = "not_ready"


TASKS: dict[str, TaskRecord] = {}
BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()

mcp = FastMCP(
    "VeriTask MCP Export",
    instructions=(
        "Trusted task transaction middleware for verifiable DeFi data procurement. "
        "This first export iteration exposes handle-based task request, status lookup, "
        "result retrieval, and resource replay over stdio without rewriting the existing VeriTask workflow."
    ),
    json_response=True,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_resource_links(handle_id: str) -> ResourceLinks:
    return ResourceLinks(
        task=f"veritask://tasks/{handle_id}",
        result=f"veritask://results/{handle_id}",
        receipt=f"veritask://receipts/{handle_id}",
    )


def get_record(handle_id: str) -> TaskRecord:
    record = TASKS.get(handle_id)
    if record is None:
        raise ValueError(f"Unknown task handle: {handle_id}")
    return record


def build_task_handle(record: TaskRecord) -> TaskHandle:
    return TaskHandle(
        handle_id=record.handle_id,
        protocol=record.protocol,
        status=record.status,
        created_at=record.created_at,
        skip_payment=record.skip_payment,
        amount_usdt=record.amount_usdt,
        resources=build_resource_links(record.handle_id),
    )


def build_task_status(record: TaskRecord) -> TaskStatus:
    return TaskStatus(
        handle_id=record.handle_id,
        protocol=record.protocol,
        status=record.status,
        verification_state=record.verification_state,
        settlement_state=record.settlement_state,
        created_at=record.created_at,
        updated_at=record.updated_at,
        worker_task_id=record.worker_task_id,
        result_available=record.result is not None,
        receipt_available=record.settlement_receipt is not None,
        error=record.error,
        resources=build_resource_links(record.handle_id),
    )


def build_settlement_receipt(record: TaskRecord) -> SettlementReceipt:
    receipt = record.settlement_receipt or {}
    return SettlementReceipt(
        handle_id=record.handle_id,
        worker_task_id=record.worker_task_id,
        settlement_state=record.settlement_state,
        tx_hash=receipt.get("tx_hash"),
        explorer_url=receipt.get("explorer_url"),
        chain_index=receipt.get("chain_index"),
        amount=receipt.get("amount"),
        token=receipt.get("token"),
        payer=receipt.get("from"),
        payee=receipt.get("to"),
        error=receipt.get("error") or record.error,
        resources=build_resource_links(record.handle_id),
    )


def build_task_result(record: TaskRecord) -> TaskResult:
    result = record.result or {}
    return TaskResult(
        handle_id=record.handle_id,
        protocol=record.protocol,
        status=record.status,
        verification_state=record.verification_state,
        settlement_state=record.settlement_state,
        worker_task_id=record.worker_task_id,
        data=result.get("data"),
        proof_details=result.get("proof_details"),
        verification=record.verification_result or result.get("verification"),
        payment=result.get("payment"),
        settlement_receipt=build_settlement_receipt(record) if record.settlement_receipt else None,
        logs=record.logs,
        error=record.error,
        resources=build_resource_links(record.handle_id),
    )


def snapshot_payload(record: TaskRecord) -> dict[str, Any]:
    return {
        "handle": build_task_handle(record).model_dump(mode="json"),
        "status": build_task_status(record).model_dump(mode="json"),
        "result": build_task_result(record).model_dump(mode="json"),
    }


def run_existing_workflow(protocol: str, amount_usdt: float, skip_payment: bool) -> tuple[dict[str, Any], str]:
    worker_url = os.getenv("WORKER_URL", "http://127.0.0.1:8001")
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = delegate_task(
            protocol=protocol,
            worker_url=worker_url,
            amount_usdt=amount_usdt,
            skip_payment=skip_payment,
        )
    logs = stdout_buffer.getvalue()
    stderr_output = stderr_buffer.getvalue()
    if stderr_output:
        logs = f"{logs}\n[stderr]\n{stderr_output}" if logs else f"[stderr]\n{stderr_output}"
    return result, logs


def normalize_payment_result(payment_result: dict[str, Any] | None, record: TaskRecord) -> dict[str, Any] | None:
    if not payment_result:
        return None

    tx_hash = payment_result.get("tx_hash") or payment_result.get("txHash")
    explorer_url = payment_result.get("explorer_url")
    if explorer_url is None and tx_hash:
        explorer_url = f"https://www.oklink.com/xlayer/tx/{tx_hash}"

    return {
        "tx_hash": tx_hash,
        "explorer_url": explorer_url,
        "chain_index": str(payment_result.get("chain_index", os.getenv("CHAIN_INDEX", "196"))),
        "amount": payment_result.get("amount", record.amount_usdt),
        "token": payment_result.get("token", os.getenv("TOKEN_SYMBOL", "USDT")),
        "from": payment_result.get("from"),
        "to": payment_result.get("to") or (record.result or {}).get("proof_details", {}).get("worker_pubkey"),
        "success": payment_result.get("success", False),
        "error": payment_result.get("error"),
    }


def rebuild_bundle_from_record(record: TaskRecord) -> dict[str, Any]:
    if not record.result:
        raise ValueError(f"Task {record.handle_id} has no result to verify")

    proof_details = record.result.get("proof_details") or {}
    return {
        "data": record.result.get("data") or {},
        "zk_proof": {
            "type": (proof_details.get("zk_proof") or {}).get("type"),
            "hash": (proof_details.get("zk_proof") or {}).get("hash"),
        },
        "tee_attestation": {
            "type": (proof_details.get("tee_attestation") or {}).get("type"),
            "report_data": (proof_details.get("tee_attestation") or {}).get("report_data"),
        },
        "worker_pubkey": proof_details.get("worker_pubkey"),
        "timestamp": proof_details.get("timestamp"),
    }


def run_verification_replay(record: TaskRecord) -> tuple[dict[str, Any], str]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    bundle = rebuild_bundle_from_record(record)
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        verification = verify_proof_bundle(bundle)
    logs = stdout_buffer.getvalue()
    stderr_output = stderr_buffer.getvalue()
    if stderr_output:
        logs = f"{logs}\n[stderr]\n{stderr_output}" if logs else f"[stderr]\n{stderr_output}"
    return verification, logs


def run_settlement(record: TaskRecord) -> tuple[dict[str, Any], str]:
    if not record.result:
        raise ValueError(f"Task {record.handle_id} has no result to settle")

    proof_details = record.result.get("proof_details") or {}
    payee = proof_details.get("worker_pubkey")
    if not payee:
        raise ValueError(f"Task {record.handle_id} does not expose a worker payee address")

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        payment_result = execute_payment(payee, record.amount_usdt)
    logs = stdout_buffer.getvalue()
    stderr_output = stderr_buffer.getvalue()
    if stderr_output:
        logs = f"{logs}\n[stderr]\n{stderr_output}" if logs else f"[stderr]\n{stderr_output}"
    return payment_result, logs


async def execute_task(handle_id: str) -> None:
    record = get_record(handle_id)
    record.status = "running"
    record.updated_at = utc_now()
    try:
        result, logs = await asyncio.to_thread(
            run_existing_workflow,
            record.protocol,
            record.amount_usdt,
            record.skip_payment,
        )
        record.logs = logs
        if result.get("success"):
            record.result = result
            record.worker_task_id = result.get("task_id")
            record.verification_result = result.get("verification")
            if (record.verification_result or {}).get("is_valid"):
                record.verification_state = "passed"
                payment_result = result.get("payment")
                if payment_result and payment_result.get("success"):
                    record.settlement_receipt = normalize_payment_result(payment_result, record)
                    record.settlement_state = "completed"
                    record.status = "settled"
                elif payment_result and not payment_result.get("success"):
                    record.settlement_state = "failed"
                    record.status = "completed"
                else:
                    record.settlement_state = "ready"
                    record.status = "completed"
            else:
                record.verification_state = "failed"
                record.settlement_state = "skipped"
                record.status = "failed"
        else:
            record.status = "failed"
            record.error = str(result.get("error", "Unknown execution error"))
            record.result = result
            record.worker_task_id = result.get("task_id")
            record.verification_result = result.get("verification")
            if record.verification_result:
                record.verification_state = "passed" if record.verification_result.get("is_valid") else "failed"
            record.settlement_state = "skipped"
    except Exception as exc:  # pragma: no cover - defensive guard for server runtime
        record.status = "failed"
        record.error = str(exc)
        record.logs = record.logs or ""
        record.settlement_state = "skipped"
    finally:
        record.updated_at = utc_now()


def track_background_task(task: asyncio.Task[Any]) -> None:
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)


@mcp.tool()
async def submit_defi_tvl_task(
    protocol: str,
    amount_usdt: float = 0.01,
    skip_payment: bool = True,
    payment_confirmation: str | None = None,
    ctx: Context | None = None,
) -> TaskHandle:
    """Submit a verifiable DeFi TVL task and receive a stable task handle."""
    normalized_protocol = protocol.strip().lower()
    if not normalized_protocol:
        raise ValueError("protocol must not be empty")
    if amount_usdt <= 0:
        raise ValueError("amount_usdt must be greater than zero")
    if not skip_payment and payment_confirmation != PAYMENT_CONFIRMATION_TOKEN:
        raise ValueError(
            "Payment-enabled requests require payment_confirmation=CONFIRM_X402_PAYMENT"
        )

    handle_id = f"vtmcp-{uuid.uuid4()}"
    record = TaskRecord(
        handle_id=handle_id,
        protocol=normalized_protocol,
        amount_usdt=amount_usdt,
        skip_payment=skip_payment,
    )
    TASKS[handle_id] = record

    if ctx is not None:
        await ctx.info(f"Queued VeriTask request for protocol={normalized_protocol}, handle={handle_id}")
        await ctx.report_progress(progress=0.0, total=1.0, message="Task accepted")

    task = asyncio.create_task(execute_task(handle_id))
    track_background_task(task)
    return build_task_handle(record)


@mcp.tool()
async def vt_request_task(
    protocol: str,
    amount_usdt: float = 0.01,
    ctx: Context | None = None,
) -> TaskHandle:
    """Phase 1 request entrypoint with deferred settlement."""
    return await submit_defi_tvl_task(
        protocol=protocol,
        amount_usdt=amount_usdt,
        skip_payment=True,
        payment_confirmation=None,
        ctx=ctx,
    )


@mcp.tool()
def get_task_status(handle_id: str) -> TaskStatus:
    """Get the latest execution state for a submitted VeriTask handle."""
    return build_task_status(get_record(handle_id))


@mcp.tool()
def vt_get_task_status(handle_id: str) -> TaskStatus:
    """Phase 1 status lookup entrypoint."""
    return get_task_status(handle_id)


@mcp.tool()
def get_task_result(handle_id: str) -> TaskResult:
    """Get the latest task result snapshot, including proofs and captured workflow logs."""
    return build_task_result(get_record(handle_id))


@mcp.tool()
def vt_get_task_result(handle_id: str) -> TaskResult:
    """Phase 1 result retrieval entrypoint."""
    return get_task_result(handle_id)


@mcp.tool()
async def vt_verify_result(handle_id: str, ctx: Context | None = None) -> VerificationReplay:
    """Replay verification for a completed task result."""
    record = get_record(handle_id)
    if record.result is None:
        raise ValueError(f"Task {handle_id} does not have a result to verify")

    verification, logs = await asyncio.to_thread(run_verification_replay, record)
    record.verification_result = verification
    record.verification_state = "passed" if verification.get("is_valid") else "failed"
    if record.verification_state == "failed":
        record.status = "failed"
        record.settlement_state = "skipped"
    elif record.status == "completed" and record.settlement_state == "not_ready":
        record.settlement_state = "ready"
    record.logs = f"{record.logs}\n[verification_replay]\n{logs}".strip()
    record.updated_at = utc_now()

    if ctx is not None:
        await ctx.info(f"Replayed verification for handle={handle_id}")

    return VerificationReplay(
        handle_id=record.handle_id,
        worker_task_id=record.worker_task_id,
        verification_state=record.verification_state,
        is_valid=verification.get("is_valid", False),
        reason=verification.get("reason", "Verification replay completed"),
        details=verification.get("details", []),
        resources=build_resource_links(record.handle_id),
    )


@mcp.tool()
async def vt_settle_payment(
    handle_id: str,
    payment_confirmation: str,
    ctx: Context | None = None,
) -> SettlementReceipt:
    """Settle a verified task on X Layer via x402."""
    if payment_confirmation != PAYMENT_CONFIRMATION_TOKEN:
        raise ValueError("Settlement requires payment_confirmation=CONFIRM_X402_PAYMENT")

    record = get_record(handle_id)
    if record.result is None:
        raise ValueError(f"Task {handle_id} does not have a result to settle")

    if record.settlement_state == "completed" and record.settlement_receipt is not None:
        return build_settlement_receipt(record)

    if record.verification_state != "passed":
        verification, logs = await asyncio.to_thread(run_verification_replay, record)
        record.logs = f"{record.logs}\n[verification_replay]\n{logs}".strip()
        record.verification_result = verification
        record.verification_state = "passed" if verification.get("is_valid") else "failed"
        if record.verification_state != "passed":
            record.status = "failed"
            record.settlement_state = "skipped"
            record.updated_at = utc_now()
            raise ValueError(f"Task {handle_id} failed verification replay and cannot be settled")

    payment_result, logs = await asyncio.to_thread(run_settlement, record)
    record.logs = f"{record.logs}\n[settlement]\n{logs}".strip()

    normalized_receipt = normalize_payment_result(payment_result, record)
    record.settlement_receipt = normalized_receipt
    if payment_result.get("success"):
        record.settlement_state = "completed"
        record.status = "settled"
    else:
        record.settlement_state = "failed"
        record.error = str(payment_result.get("error", "Settlement failed"))
    record.updated_at = utc_now()

    if ctx is not None:
        await ctx.info(f"Settlement attempted for handle={handle_id}")

    return build_settlement_receipt(record)


@mcp.tool()
def vt_get_settlement_receipt(handle_id: str) -> SettlementReceipt:
    """Return the normalized settlement receipt for a task."""
    return build_settlement_receipt(get_record(handle_id))


@mcp.resource("veritask://tasks/{handle_id}")
def read_task_snapshot(handle_id: str) -> str:
    """Read the full task snapshot for a given handle."""
    payload = snapshot_payload(get_record(handle_id))
    return json.dumps(payload, indent=2, ensure_ascii=True)


@mcp.resource("veritask://results/{handle_id}")
def read_task_result_resource(handle_id: str) -> str:
    """Read the result-oriented snapshot for a given handle."""
    payload = build_task_result(get_record(handle_id)).model_dump(mode="json")
    return json.dumps(payload, indent=2, ensure_ascii=True)


@mcp.resource("veritask://receipts/{handle_id}")
def read_settlement_receipt_resource(handle_id: str) -> str:
    """Read the normalized settlement receipt for a given handle."""
    payload = build_settlement_receipt(get_record(handle_id)).model_dump(mode="json")
    return json.dumps(payload, indent=2, ensure_ascii=True)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()