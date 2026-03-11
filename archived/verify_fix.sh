#!/bin/bash
PID=$(pgrep -f 'openclaw-gate' | head -1)
echo "Gateway PID: $PID"
echo "PATH includes .local/bin:"
cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep '^PATH=' | grep -o '.local/bin' && echo "YES" || echo "NO"
echo ""
echo "onchainos accessible:"
which onchainos && onchainos --version || echo "NOT FOUND"
