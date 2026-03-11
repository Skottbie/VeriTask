#!/bin/bash
cat /home/skottbie/.openclaw/openclaw.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
agents = d.get('agents', {})
print(json.dumps(agents, indent=2, ensure_ascii=False))
"
