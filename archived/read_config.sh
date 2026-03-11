#!/bin/bash
cat /home/skottbie/.openclaw/openclaw.json | python3 -m json.tool 2>/dev/null | head -80
