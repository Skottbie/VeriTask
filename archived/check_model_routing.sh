#!/bin/bash
# Check existing SKILL.md files for any model-related metadata
echo "=== Checking all SKILL.md files for model/routing metadata ==="
for f in /home/skottbie/.openclaw/workspace/skills/*/SKILL.md; do
    skill=$(basename $(dirname "$f"))
    # Extract YAML frontmatter metadata
    echo "--- $skill ---"
    sed -n '/^---$/,/^---$/p' "$f" | grep -i "model\|routing\|agent\|subagent" || echo "  (no model metadata)"
done

echo ""
echo "=== Check openclaw.json for model-override or routing config ==="
python3 -c "
import json
with open('/home/skottbie/.openclaw/openclaw.json') as f:
    config = json.load(f)
# Look for anything model-related
for key in config:
    val = json.dumps(config[key])
    if 'model' in val.lower() or 'routing' in val.lower() or 'subagent' in val.lower():
        print(f'{key}: {val[:500]}')
"
