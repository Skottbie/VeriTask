#!/usr/bin/env python3
"""Add tools.sessions.visibility = 'all' to openclaw.json (H6-B fix)."""
import json

CONFIG_PATH = "/home/skottbie/.openclaw/openclaw.json"

with open(CONFIG_PATH, "r") as f:
    cfg = json.load(f)

# Add tools.sessions.visibility = "all"
if "tools" not in cfg:
    cfg["tools"] = {}
if "sessions" not in cfg["tools"]:
    cfg["tools"]["sessions"] = {}
cfg["tools"]["sessions"]["visibility"] = "all"

with open(CONFIG_PATH, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("OK: tools.sessions.visibility = 'all' added")
print("Current tools config:", json.dumps(cfg["tools"], indent=2))
