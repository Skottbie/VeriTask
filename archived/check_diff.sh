#!/bin/bash
WORKSPACE="/home/skottbie/.openclaw/workspace"
WINDOWS="/mnt/d/VeriTask"

echo "=== 文件差异检查 ==="

check_file() {
  local wsl_f="$1"
  local win_f="$2"
  local label="$3"
  if [ -f "$wsl_f" ] && [ -f "$win_f" ]; then
    if diff -q "$wsl_f" "$win_f" >/dev/null 2>&1; then
      echo "  $label: SAME"
    else
      echo "  $label: DIFFERENT"
    fi
  elif [ -f "$win_f" ]; then
    echo "  $label: MISSING_IN_WSL"
  else
    echo "  $label: MISSING_IN_WIN"
  fi
}

echo "--- task-delegator ---"
check_file "$WORKSPACE/skills/task-delegator/SKILL.md" "$WINDOWS/client_node/skills/task-delegator/SKILL.md" "SKILL.md"
check_file "$WORKSPACE/skills/task-delegator/task_delegator.py" "$WINDOWS/client_node/skills/task-delegator/task_delegator.py" "task_delegator.py"

echo "--- verifier ---"
check_file "$WORKSPACE/skills/verifier/SKILL.md" "$WINDOWS/client_node/skills/verifier/SKILL.md" "SKILL.md"
check_file "$WORKSPACE/skills/verifier/verifier.py" "$WINDOWS/client_node/skills/verifier/verifier.py" "verifier.py"

echo "--- okx-x402-payer ---"
check_file "$WORKSPACE/skills/okx-x402-payer/SKILL.md" "$WINDOWS/client_node/skills/okx-x402-payer/SKILL.md" "SKILL.md"
check_file "$WORKSPACE/skills/okx-x402-payer/okx_x402_payer.py" "$WINDOWS/client_node/skills/okx-x402-payer/okx_x402_payer.py" "okx_x402_payer.py"
check_file "$WORKSPACE/skills/okx-x402-payer/okx_auth.py" "$WINDOWS/client_node/skills/okx-x402-payer/okx_auth.py" "okx_auth.py"

echo "--- defi-scraper ---"
check_file "$WORKSPACE/skills/defi-scraper/SKILL.md" "$WINDOWS/worker_node/skills/defi-scraper/SKILL.md" "SKILL.md"
check_file "$WORKSPACE/skills/defi-scraper/defi_scraper.py" "$WINDOWS/worker_node/skills/defi-scraper/defi_scraper.py" "defi_scraper.py"

echo "--- proof-generator ---"
check_file "$WORKSPACE/skills/proof-generator/SKILL.md" "$WINDOWS/worker_node/skills/proof-generator/SKILL.md" "SKILL.md"
check_file "$WORKSPACE/skills/proof-generator/proof_generator.py" "$WINDOWS/worker_node/skills/proof-generator/proof_generator.py" "proof_generator.py"
check_file "$WORKSPACE/skills/proof-generator/zkfetch_bridge.js" "$WINDOWS/worker_node/skills/proof-generator/zkfetch_bridge.js" "zkfetch_bridge.js"

echo "--- AGENTS.md ---"
check_file "$WORKSPACE/AGENTS.md" "$WINDOWS/AGENTS.md" "AGENTS.md"

echo "--- .env ---"
check_file "$WORKSPACE/.env" "$WINDOWS/.env" ".env"

echo "=== DONE ==="
