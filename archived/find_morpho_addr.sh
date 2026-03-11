#!/bin/bash
SDIR="/home/skottbie/.openclaw/agents/main/sessions"
F=$(ls -t "$SDIR"/*.jsonl 2>/dev/null | head -1)
echo "Session file: $F"
echo "Size: $(wc -c < "$F") bytes"
echo ""

echo "=== Token addresses containing 0x58 ==="
grep -oP '0x58[a-fA-F0-9]{38,40}' "$F" 2>/dev/null | sort -u

echo ""
echo "=== All onchainos commands ==="
grep -oP 'onchainos [a-z]+ [a-z-]+ [^\\"]+' "$F" 2>/dev/null | sort -u | head -20

echo ""
echo "=== Morpho references ==="
grep -ioP '[Mm]orpho[^"]{0,100}' "$F" 2>/dev/null | sort -u | head -10
