#!/usr/bin/env python3
"""Fix openclaw.json: add tools.agentToAgent.enabled=true"""
import json

CONFIG = "/home/skottbie/.openclaw/openclaw.json"

with open(CONFIG, "r") as f:
    cfg = json.load(f)

if "tools" not in cfg:
    cfg["tools"] = {}

cfg["tools"]["agentToAgent"] = {"enabled": True}

with open(CONFIG, "w") as f:
    json.dump(cfg, f, indent=2)

print("OK: added tools.agentToAgent.enabled=true")
print(f"tools section: {json.dumps(cfg['tools'], indent=2)}")
