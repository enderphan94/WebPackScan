#!/bin/bash

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

# Check if nvm is installed
if ! command -v nvm &>/dev/null; then
    echo "[INFO] nvm is not installed. Installing nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

    # Load nvm into the current shell session
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    echo "[INFO] nvm is already installed."
fi

# Ensure Node.js version 18 is installed and in use
echo "[INFO] Using Node.js version 18..."
nvm install 18
nvm use 18

export PUPPETEER_EXECUTABLE_PATH=$(which chromium)  # Set Chromium path
export PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox"  # Chromium args


# Generate JSON output using the Node.js CLI
JSON_FILE="${URL//[:\/]/_}.json"  # Replace ":" and "/" with "_" for the filename
echo "[INFO] Generating JSON output for URL: $URL"
node src/drivers/npm/cli.js "$URL" > "$JSON_FILE"

# Run Python script to process the JSON
if ! command -v python3.10 &>/dev/null; then
    echo "[ERROR] Python 3.10 is not installed or not in PATH."
    exit 1
fi

echo "[INFO] Running Python script on JSON file: $JSON_FILE"
python3.10 vulPack.py "$JSON_FILE"

echo "[INFO] Scan completed successfully for URL: $URL"