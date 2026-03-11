#!/bin/bash
/home/skottbie/.local/share/pnpm/openclaw skills 2>&1 | grep -iE "okx-wallet|okx-dex|okx-onchain"
