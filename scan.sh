#!/bin/bash

# Print header
echo "+------------------------------------------+"
echo "|                 PACKSCAN                 |"
echo "+------------------------------------------+"
echo "| DevBy     : github.com/enderphan94       |"
echo "| InspiredBy: Wappalyzer                   |"
echo "+------------------------------------------+"

# Ensure the script exits on errors
set -e

# Validate the URL argument
if [ "$#" -ne 1 ]; then
    echo "[ERROR] Usage: $0 <url>"
    exit 1
fi

URL=$1

if [[ ! "$URL" =~ ^https:// ]]; then
    echo "[ERROR] The URL must start with 'https://'"
    exit 1
fi

# Export PATH to include Go binaries
export PATH=$PATH:$(go env GOPATH)/bin

# Quietly check and install nvm if needed
if ! command -v nvm &>/dev/null; then
    curl -s -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash >/dev/null 2>&1
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" >/dev/null 2>&1
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" >/dev/null 2>&1
fi

# Quietly ensure Node.js version 18 is installed and in use
nvm install 18 >/dev/null 2>&1
nvm use 18 >/dev/null 2>&1
npm install >/dev/null 2>&1

export PUPPETEER_EXECUTABLE_PATH=$(which chromium)
export PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox"

# Run the subdomain scanner
DOMAIN=$(echo "$URL" | sed -e 's/^https:\/\///')
python3.10 scripts/subsh.py -u "$DOMAIN"

# Generate JSON output using the Node.js CLI
JSON_FILE="${URL//[:\/]/_}.json"
node src/drivers/npm/cli.js "$URL" > "$JSON_FILE" 2>/dev/null

# Check if Python 3.10 is available
if ! command -v python3.10 &>/dev/null; then
    echo "[ERROR] Python 3.10 is not installed or not in PATH."
    exit 1
fi

# Run vulnerability scan
python3.10 scripts/vulPack.py "$JSON_FILE"
