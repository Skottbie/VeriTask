<#
.SYNOPSIS
    VeriTask 3.0 — End-to-End Demo Script
.DESCRIPTION
    Demonstrates the full C2C (Claw-to-Claw) verifiable micro-procurement flow:
    1. Start Worker server (background)
    2. Client delegates DeFi TVL task to Worker
    3. Worker fetches real data + generates cryptographic proofs
    4. Client verifies proofs (ZK + TEE)
    5. Client pays Worker via OKX x402 (optional)
.NOTES
    Run from the VeriTask monorepo root: .\run_demo.ps1
#>

param(
    [string]$Protocol = "aave",
    [switch]$SkipPayment,
    [switch]$JsonOutput,
    [int]$WorkerPort = 8001
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$WorkerUrl = "http://127.0.0.1:$WorkerPort"

# ─── Helper Functions ────────────────────────────────────────────────

function Write-Banner {
    param([string]$Text, [string]$Color = "Cyan")
    $line = "=" * 60
    Write-Host ""
    Write-Host $line -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host $line -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host "[VeriTask] $Text" -ForegroundColor $Color
}

function Wait-ForWorker {
    param([string]$Url, [int]$MaxRetries = 15)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        try {
            $resp = Invoke-RestMethod -Uri "$Url/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.status -eq "ok") {
                return $true
            }
        } catch {
            # Worker not ready yet
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

# ─── Pre-flight Checks ──────────────────────────────────────────────

Write-Banner "VeriTask 3.0 — C2C Verifiable Micro-Procurement Demo"

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python venv not found at $PythonExe" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv && .venv\Scripts\activate && pip install -r worker_node\requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Step "Python: $PythonExe" "Gray"
Write-Step "Worker: $WorkerUrl" "Gray"
Write-Step "Protocol: $Protocol" "Gray"
Write-Step "Payment: $(if ($SkipPayment) { 'SKIPPED' } else { 'ENABLED (x402)' })" "Gray"
Write-Host ""

# ─── Phase 1: Start Worker ──────────────────────────────────────────

Write-Banner "Phase 1: Starting Worker Server" "Yellow"

$workerLogOut = Join-Path $ScriptDir "worker_stdout.log"
$workerLogErr = Join-Path $ScriptDir "worker_stderr.log"

$workerProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "worker_node.server:app", "--host", "127.0.0.1", "--port", $WorkerPort, "--log-level", "info" `
    -WorkingDirectory $ScriptDir `
    -NoNewWindow `
    -RedirectStandardOutput $workerLogOut `
    -RedirectStandardError $workerLogErr `
    -PassThru

Write-Step "Worker starting in background (PID $($workerProcess.Id))..." "Yellow"
Start-Sleep -Seconds 6

$workerReady = Wait-ForWorker -Url $WorkerUrl -MaxRetries 20
if (-not $workerReady) {
    Write-Host "ERROR: Worker failed to start within timeout" -ForegroundColor Red
    if (Test-Path $workerLogErr) {
        Write-Host "--- Worker stderr ---" -ForegroundColor Red
        Get-Content $workerLogErr | Write-Host -ForegroundColor Red
    }
    if (Test-Path $workerLogOut) {
        Write-Host "--- Worker stdout ---" -ForegroundColor Yellow
        Get-Content $workerLogOut | Write-Host -ForegroundColor Yellow
    }
    if ($workerProcess -and -not $workerProcess.HasExited) {
        Stop-Process -Id $workerProcess.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

$health = Invoke-RestMethod -Uri "$WorkerUrl/health"
Write-Step "Worker is READY" "Green"
Write-Step "  TEE available: $($health.tee)" "Gray"
Write-Step "  Worker address: $($health.worker_address)" "Gray"

Start-Sleep -Seconds 1

# ─── Phase 2: Execute C2C Flow ──────────────────────────────────────

Write-Banner "Phase 2: C2C Task Delegation + Verification" "Cyan"

$delegatorArgs = @(
    (Join-Path $ScriptDir "client_node\skills\task-delegator\task_delegator.py"),
    "--protocol", $Protocol,
    "--worker-url", $WorkerUrl
)

if ($SkipPayment) {
    $delegatorArgs += "--skip-payment"
}

if ($JsonOutput) {
    $delegatorArgs += "--json"
}

# Run the orchestrator
& $PythonExe @delegatorArgs

Start-Sleep -Seconds 1

# ─── Phase 3: Cleanup ───────────────────────────────────────────────

Write-Banner "Phase 3: Cleanup" "Yellow"

Write-Step "Stopping Worker server..." "Yellow"
if ($workerProcess -and -not $workerProcess.HasExited) {
    Stop-Process -Id $workerProcess.Id -Force -ErrorAction SilentlyContinue
}
# Clean up log files
Remove-Item -Path $workerLogOut -ErrorAction SilentlyContinue
Remove-Item -Path $workerLogErr -ErrorAction SilentlyContinue
Write-Step "Worker stopped." "Green"

# ─── Done ────────────────────────────────────────────────────────────

Write-Banner "Demo Complete!" "Green"
Write-Step "Three-Layer Trust Chain:" "Cyan"
Write-Step "  Layer 1: Data Provenance — Reclaim zkFetch (zkTLS)" "White"
Write-Step "  Layer 2: Execution Integrity — Intel TDX TEE (Phala CVM)" "White"
Write-Step "  Layer 3: Payment Settlement — OKX x402 (X Layer, gasless)" "White"
Write-Host ""
Write-Step "Next steps:" "Yellow"
Write-Step "  1. Set OKX credentials in .env for real x402 payment" "Gray"
Write-Step "  2. Deploy Worker to Phala Cloud CVM for real TEE attestation" "Gray"
Write-Step "  3. Configure Reclaim Protocol for real zkFetch proofs" "Gray"
Write-Host ""
