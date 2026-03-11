#!/bin/bash
PID=$(pgrep -f 'openclaw-gate' | head -1)
if [ -z "$PID" ]; then
    echo "No gateway process found"
    exit 1
fi
echo "Gateway PID: $PID"
echo "PATH:"
cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep '^PATH=' || echo "Could not read environ"
