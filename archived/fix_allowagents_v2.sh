#!/bin/bash
# Fix v2: Move allowAgents from defaults to per-agent config
# Schema puts allowAgents under agent-specific subagents, not defaults
CONFIG="/home/skottbie/.openclaw/openclaw.json"

python3 -c "
import json

with open('$CONFIG', 'r') as f:
    cfg = json.load(f)

# Remove from defaults (it was unknown there)
if 'allowAgents' in cfg['agents']['defaults']['subagents']:
    del cfg['agents']['defaults']['subagents']['allowAgents']
    print('Removed allowAgents from defaults.subagents')

# Add to main agent's per-agent config
for agent in cfg['agents']['list']:
    if agent['id'] == 'main':
        if 'subagents' not in agent:
            agent['subagents'] = {}
        agent['subagents']['allowAgents'] = ['pro']
        print('Added allowAgents: [\"pro\"] to main agent config')
        break

with open('$CONFIG', 'w') as f:
    json.dump(cfg, f, indent=2)

print()
print('Updated config:')
print('defaults.subagents:', json.dumps(cfg['agents']['defaults']['subagents'], indent=2))
print()
for a in cfg['agents']['list']:
    print(f'Agent {a[\"id\"]}:', json.dumps(a, indent=2))
"
