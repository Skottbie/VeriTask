#!/bin/bash
export PATH="/home/skottbie/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

openclaw models list --all 2>&1 | grep -iE "copilot|pro.*preview|flash|gemini"
