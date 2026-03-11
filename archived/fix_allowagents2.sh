#!/bin/bash
# Fix: Add allowAgents to subagents config using Python
CONFIG="/home/skottbie/.openclaw/openclaw.json"

python3 -c "
import json

with open('$CONFIG', 'r') as f:
    cfg = json.load(f)

# Add allowAgents to defaults subagents
cfg['agents']['defaults']['subagents']['allowAgents'] = ['pro']

with open('$CONFIG', 'w') as f:
    json.dump(cfg, f, indent=2)

print('SUCCESS: allowAgents added')
print('subagents config:', json.dumps(cfg['agents']['defaults']['subagents'], indent=2))
"

echo ""
echo "=== Verify file ==="
python3 -c "
import json
with open('$CONFIG', 'r') as f:
    cfg = json.load(f)
print('agents.defaults.subagents:', json.dumps(cfg['agents']['defaults']['subagents'], indent=2))
print()
print('agents.list:')
for a in cfg['agents']['list']:
    print(f'  - {a[\"id\"]}: model={a.get(\"model\",\"(default)\")}')
"
