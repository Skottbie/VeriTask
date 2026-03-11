#!/bin/bash
PID=$(pgrep -f 'openclaw.*gateway' | head -1)
echo "Gateway PID: $PID"
if [ -n "$PID" ]; then
    kill "$PID"
    echo "Killed, waiting for auto-restart..."
    sleep 12
    curl -s http://127.0.0.1:18789/health
else
    echo "No Gateway process found"
fi
