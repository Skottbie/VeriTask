#!/bin/bash
# Sync 4 files from Windows VeriTask to WSL OpenClaw workspace
set -e

SRC="/mnt/d/VeriTask"
DST="/home/skottbie/.openclaw/workspace"

echo "=== Syncing AGENTS.md ==="
cp "$SRC/AGENTS.md" "$DST/AGENTS.md"
echo "DONE"

echo "=== Syncing proof_generator.py ==="
cp "$SRC/worker_node/skills/proof-generator/proof_generator.py" "$DST/skills/proof-generator/proof_generator.py"
echo "DONE"

echo "=== Syncing zkfetch_bridge.js ==="
cp "$SRC/worker_node/skills/proof-generator/zkfetch_bridge.js" "$DST/skills/proof-generator/zkfetch_bridge.js"
echo "DONE"

echo "=== Syncing .env (Reclaim credentials only) ==="
# Only update the two Reclaim lines, preserve rest of WSL .env
sed -i 's|^RECLAIM_APP_ID=.*|RECLAIM_APP_ID=0x95C8c603977827846109784e44E73D79214b0Fd6|' "$DST/.env"
sed -i 's|^RECLAIM_APP_SECRET=.*|RECLAIM_APP_SECRET=0xdd272b1cf0ab01c0591f952e137041cd8b0a47b49a6591d3eb8cfc5b4e5fe94f|' "$DST/.env"
echo "DONE"

echo ""
echo "=== Verification ==="
echo "AGENTS.md:"
diff "$SRC/AGENTS.md" "$DST/AGENTS.md" && echo "  MATCH ✓" || echo "  MISMATCH ✗"

echo "proof_generator.py:"
diff "$SRC/worker_node/skills/proof-generator/proof_generator.py" "$DST/skills/proof-generator/proof_generator.py" && echo "  MATCH ✓" || echo "  MISMATCH ✗"

echo "zkfetch_bridge.js:"
diff "$SRC/worker_node/skills/proof-generator/zkfetch_bridge.js" "$DST/skills/proof-generator/zkfetch_bridge.js" && echo "  MATCH ✓" || echo "  MISMATCH ✗"

echo ".env Reclaim lines:"
grep "RECLAIM_APP_ID" "$DST/.env"
grep "RECLAIM_APP_SECRET" "$DST/.env" | head -c 60
echo "..."
echo ""
echo "=== All synced ==="
