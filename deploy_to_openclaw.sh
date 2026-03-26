#!/usr/bin/env bash
# deploy_to_openclaw.sh — Deploy VeriTask skills to OpenClaw workspace
# Usage: bash deploy_to_openclaw.sh [--refresh]
#
# This script:
# 1. Copies VeriTask Client + Worker skills to ~/.openclaw/workspace/skills/
# 2. Copies openclaw.json configs
# 3. Installs OKX onchainos-skills (if not already present)
# 4. Optionally refreshes OpenClaw Gateway

set -euo pipefail

# --- Configuration ---
OPENCLAW_WORKSPACE="${HOME}/.openclaw/workspace"
OPENCLAW_SKILLS="${OPENCLAW_WORKSPACE}/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        VeriTask 3.0 — OpenClaw Deployment           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# --- Step 1: Verify OpenClaw installation ---
echo -e "${YELLOW}[Step 1] Checking OpenClaw installation...${NC}"
if command -v openclaw &> /dev/null; then
    OPENCLAW_VERSION=$(openclaw --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}  ✅ OpenClaw found: ${OPENCLAW_VERSION}${NC}"
else
    echo -e "${RED}  ❌ OpenClaw not found. Install with:${NC}"
    echo -e "${RED}     npm install -g openclaw@latest${NC}"
    echo -e "${RED}     openclaw onboard --install-daemon${NC}"
    exit 1
fi

# --- Step 2: Create skill directories ---
echo -e "${YELLOW}[Step 2] Creating skill directories...${NC}"

VERITASK_SKILLS=(
    "task-delegator"
    "verifier"
    "okx-x402-payer"
    "graph-anchor"
    "bidding-agent"
    "defi-scraper"
    "proof-generator"
)

for skill in "${VERITASK_SKILLS[@]}"; do
    mkdir -p "${OPENCLAW_SKILLS}/${skill}"
    echo -e "  📁 ${OPENCLAW_SKILLS}/${skill}"
done

# --- Step 3: Copy Client skills ---
echo -e "${YELLOW}[Step 3] Deploying Client skills...${NC}"

# task-delegator
cp -r "${SCRIPT_DIR}/client_node/skills/task-delegator/"* "${OPENCLAW_SKILLS}/task-delegator/"
echo -e "${GREEN}  ✅ task-delegator deployed${NC}"

# verifier
cp -r "${SCRIPT_DIR}/client_node/skills/verifier/"* "${OPENCLAW_SKILLS}/verifier/"
echo -e "${GREEN}  ✅ verifier deployed${NC}"

# okx-x402-payer
cp -r "${SCRIPT_DIR}/client_node/skills/okx-x402-payer/"* "${OPENCLAW_SKILLS}/okx-x402-payer/"
echo -e "${GREEN}  ✅ okx-x402-payer deployed${NC}"

# graph-anchor
cp -r "${SCRIPT_DIR}/client_node/skills/graph-anchor/"* "${OPENCLAW_SKILLS}/graph-anchor/"
echo -e "${GREEN}  ✅ graph-anchor deployed${NC}"

# bidding-agent
cp -r "${SCRIPT_DIR}/client_node/skills/bidding-agent/"* "${OPENCLAW_SKILLS}/bidding-agent/"
echo -e "${GREEN}  ✅ bidding-agent deployed${NC}"

# --- Step 4: Copy Worker skills ---
echo -e "${YELLOW}[Step 4] Deploying Worker skills...${NC}"

# defi-scraper
cp -r "${SCRIPT_DIR}/worker_node/skills/defi-scraper/"* "${OPENCLAW_SKILLS}/defi-scraper/"
echo -e "${GREEN}  ✅ defi-scraper deployed${NC}"

# proof-generator
cp -r "${SCRIPT_DIR}/worker_node/skills/proof-generator/"* "${OPENCLAW_SKILLS}/proof-generator/"
echo -e "${GREEN}  ✅ proof-generator deployed${NC}"

# --- Step 5: Copy AGENTS.md ---
echo -e "${YELLOW}[Step 5] Deploying AGENTS.md...${NC}"
cp "${SCRIPT_DIR}/AGENTS.md" "${OPENCLAW_WORKSPACE}/AGENTS.md"
echo -e "${GREEN}  ✅ AGENTS.md → ${OPENCLAW_WORKSPACE}/AGENTS.md${NC}"

# --- Step 6: Copy .env (if exists) ---
echo -e "${YELLOW}[Step 6] Checking .env...${NC}"
if [ -f "${SCRIPT_DIR}/.env" ]; then
    cp "${SCRIPT_DIR}/.env" "${OPENCLAW_WORKSPACE}/.env"
    echo -e "${GREEN}  ✅ .env deployed to workspace${NC}"
else
    echo -e "${YELLOW}  ⚠️  No .env found. Copy .env.example and fill in values:${NC}"
    echo -e "${YELLOW}     cp .env.example .env${NC}"
fi

# --- Step 7: Install OKX OnchainOS Skills ---
echo -e "${YELLOW}[Step 7] Installing OKX OnchainOS Skills...${NC}"
if [ -d "${OPENCLAW_SKILLS}/okx-wallet-portfolio" ]; then
    echo -e "${GREEN}  ✅ OKX onchainos-skills already installed${NC}"
else
    echo -e "  📦 Running: npx skills add okx/onchainos-skills"
    cd "${SCRIPT_DIR}"
    npx skills add okx/onchainos-skills 2>/dev/null || {
        echo -e "${YELLOW}  ⚠️  npx skills add failed. You can install manually:${NC}"
        echo -e "${YELLOW}     npx skills add okx/onchainos-skills${NC}"
    }
fi

# --- Step 8: Refresh Gateway (optional) ---
if [[ "${1:-}" == "--refresh" ]]; then
    echo -e "${YELLOW}[Step 8] Refreshing OpenClaw Gateway...${NC}"
    openclaw skills refresh 2>/dev/null && echo -e "${GREEN}  ✅ Skills refreshed${NC}" || true
    openclaw gateway restart 2>/dev/null && echo -e "${GREEN}  ✅ Gateway restarted${NC}" || true
else
    echo -e "${YELLOW}[Step 8] Skipping Gateway refresh (use --refresh flag to auto-refresh)${NC}"
fi

# --- Summary ---
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║               Deployment Complete! 🎉               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Skills deployed to: ${GREEN}${OPENCLAW_SKILLS}/${NC}"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Start Worker:  ${CYAN}cd worker_node && uvicorn server:app --host 127.0.0.1 --port 8001${NC}"
echo -e "  2. Refresh skills: ${CYAN}openclaw skills refresh${NC}"
echo -e "  3. Start Gateway:  ${CYAN}openclaw gateway --port 18789 --verbose${NC}"
echo -e "  4. Test via chat:  ${CYAN}openclaw agent --message \"帮我抓一下 Aave 的 TVL，通过 Worker 验证\"${NC}"
echo ""
echo -e "  ${YELLOW}Verify installation:${NC}"
echo -e "  ${CYAN}openclaw skills list${NC}"
echo -e "  ${CYAN}openclaw doctor${NC}"
