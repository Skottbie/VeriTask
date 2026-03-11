#!/bin/bash
find /home/skottbie/.openclaw -name "*.md" -type f 2>/dev/null | head -30
echo "---"
find /home/skottbie/.openclaw -name "*.txt" -type f 2>/dev/null | head -30
echo "---"
# Check if there's any reference to subagent model routing in config files
grep -r "subagent\|routing\|model.*primary\|model.*secondary\|model.*fallback" /home/skottbie/.openclaw/*.json 2>/dev/null | head -20
