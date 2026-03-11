#!/bin/bash
/home/skottbie/.local/share/pnpm/openclaw skills 2>&1 | grep -iE "onchain-gateway|proof-gen"
