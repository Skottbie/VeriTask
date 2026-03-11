#!/bin/bash
/home/skottbie/.local/share/pnpm/openclaw skills 2>&1 | grep -iE "task-delegator|verifier|x402|defi-scraper|proof-gen|okx-"
