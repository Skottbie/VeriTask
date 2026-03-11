#!/bin/bash
# Fix: Add allowAgents to subagents config to enable Pro Agent spawning
# Root cause: resolveAgentConfig(cfg, requesterAgentId)?.subagents?.allowAgents ?? []
# When empty, sessions_spawn returns "agentId is not allowed (allowed: none)"

CONFIG="/home/skottbie/.openclaw/openclaw.json"
BACKUP="/home/skottbie/.openclaw/openclaw.json.bak_v332"

echo "=== 1. Backup current config ==="
cp "$CONFIG" "$BACKUP"
echo "Backup saved to: $BACKUP"

echo ""
echo "=== 2. Add allowAgents to subagents config ==="
# Use jq to add allowAgents: ["pro"] to agents.defaults.subagents
jq '.agents.defaults.subagents.allowAgents = ["pro"]' "$CONFIG" > "${CONFIG}.tmp" && mv "${CONFIG}.tmp" "$CONFIG"

echo ""
echo "=== 3. Verify the fix ==="
echo "subagents config now:"
jq '.agents.defaults.subagents' "$CONFIG"

echo ""
echo "=== 4. Full agents section ==="
jq '.agents' "$CONFIG"

echo ""
echo "=== DONE: allowAgents fix applied ==="
echo "Flash (main) can now spawn Pro subagent via sessions_spawn(agentId='pro')"
