#!/bin/bash
export PATH="$HOME/.local/share/pnpm:$HOME/.local/bin:$PATH"
cd /home/skottbie/.openclaw

echo "=== Main agent session files ==="
find agents/main/sessions/ -name "*.json" -type f 2>/dev/null | while read f; do
    echo "File: $f ($(stat -c%s "$f") bytes, $(stat -c%Y "$f"))"
done

echo ""
echo "=== sessions.json content (last session) ==="
SESS="agents/main/sessions/sessions.json"
if [ -f "$SESS" ]; then
    python3 << 'PYEOF'
import json

with open("/home/skottbie/.openclaw/agents/main/sessions/sessions.json") as f:
    data = json.load(f)

# It might be a dict with sessions key or a raw structure
if isinstance(data, dict):
    # Try to find sessions
    for key in ['sessions', 'list', 'data']:
        if key in data:
            sessions = data[key]
            break
    else:
        # Maybe it IS the session itself
        sessions = [data]
else:
    sessions = data

if isinstance(sessions, dict):
    # It's a map
    for sid, sdata in list(sessions.items())[-2:]:
        print(f"\n=== Session: {sid} ===")
        if isinstance(sdata, dict):
            for k, v in sdata.items():
                sv = str(v)
                if len(sv) > 300:
                    sv = sv[:300] + "..."
                print(f"  {k}: {sv}")
elif isinstance(sessions, list):
    for s in sessions[-2:]:
        print(f"\n=== Session ===")
        if isinstance(s, dict):
            for k, v in s.items():
                sv = str(v)
                if len(sv) > 300:
                    sv = sv[:300] + "..."
                print(f"  {k}: {sv}")
else:
    print(f"Type: {type(sessions)}")
    print(str(sessions)[:1000])
PYEOF
fi

echo ""
echo "=== All session dirs (recursive) ==="
find agents/ -name "sessions" -type d 2>/dev/null | while read d; do
    echo "$d:"
    find "$d" -name "*.json" -type f | while read f; do
        echo "  $f ($(stat -c%s "$f") bytes)"
    done
done

echo ""
echo "=== subagents dir ==="
ls -la subagents/ 2>/dev/null
cat subagents/runs.json 2>/dev/null | head -20

echo ""
echo "=== Search for any session with 'morpho' ==="
grep -rl -i "morpho" agents/ 2>/dev/null | head -10
