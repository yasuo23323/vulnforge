#!/bin/bash
set -e

echo "==============================="
echo "  VulnForge - Linux Install"
echo "==============================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

NODE_VERSION="20.19.0"

# --------------------------------------------------
# [1] Check & install Node.js
# --------------------------------------------------
install_nodejs() {
    echo "  Downloading Node.js ${NODE_VERSION} (prebuilt binary)..."
    local node_dir="${PROJECT_DIR}/node"
    mkdir -p "$node_dir"

    # Try primary download, fallback to China mirror
    local tarball="node-v${NODE_VERSION}-linux-x64.tar.xz"
    local primary_url="https://nodejs.org/dist/v${NODE_VERSION}/${tarball}"
    local mirror_url="https://npmmirror.com/mirrors/node/v${NODE_VERSION}/${tarball}"

    if curl -fsSL "$primary_url" -o "/tmp/${tarball}" 2>/dev/null; then
        echo "  Downloaded from nodejs.org"
    elif curl -fsSL "$mirror_url" -o "/tmp/${tarball}" 2>/dev/null; then
        echo "  Downloaded from npmmirror.com"
    else
        echo "ERROR: Could not download Node.js. Check your internet connection."
        echo "  Try manually: curl -fsSL $primary_url -o /tmp/${tarball}"
        exit 1
    fi

    tar -xf "/tmp/${tarball}" -C "$node_dir" --strip-components=1
    rm "/tmp/${tarball}"

    export PATH="${node_dir}/bin:${PATH}"
    echo "  Node.js $(node --version) ready"
    echo "  npm $(npm --version) ready"
}

if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    echo "  Node.js $(node --version) found"
else
    echo "[1/4] Installing Node.js..."
    # Try apt first (works on most Debian/Ubuntu, but not always on Kali)
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq nodejs npm 2>/dev/null && {
            echo "  Node.js $(node --version) via apt"
        } || {
            install_nodejs
        }
    else
        install_nodejs
    fi
fi

# Ensure node is in PATH for subsequent steps
if command -v node >/dev/null 2>&1; then
    # Already in PATH
    :
elif [ -f "${PROJECT_DIR}/node/bin/node" ]; then
    export PATH="${PROJECT_DIR}/node/bin:${PATH}"
fi

# --------------------------------------------------
# [2] Check Python
# --------------------------------------------------
install_python() {
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq python3 python3-pip python3-venv
    else
        echo "ERROR: Python 3 not found. Install it manually."
        exit 1
    fi
}

if ! command -v python3 >/dev/null 2>&1; then
    echo "[1/4] Installing Python 3..."
    install_python
fi
echo "  Python: $(python3 --version)"

# --------------------------------------------------
# [3] Create .env
# --------------------------------------------------
echo "[2/4] Setting up configuration..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db
DEBUG=false
EOF
fi

# Check/ask for API key
CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "sk-your-api-key-here" ]; then
    if [ -t 0 ]; then
        printf "Enter your DeepSeek API Key (paste and press Enter): "
        read -r api_key
        if [ -n "$api_key" ]; then
            if grep -q "^OPENAI_API_KEY=" .env 2>/dev/null; then
                sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
            else
                echo "OPENAI_API_KEY=$api_key" >> .env
            fi
            echo "  API Key saved!"
        fi
    fi
fi

# --------------------------------------------------
# [4] Python venv + deps
# --------------------------------------------------
echo "[3/4] Setting up Python environment..."
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv
source venv/bin/activate
pip install --quiet --upgrade pip 2>/dev/null || true
echo "  Installing Python dependencies..."
pip install --quiet -r backend/requirements.txt 2>/dev/null \
  || pip install --quiet -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null \
  || pip install -r backend/requirements.txt
echo "  Python deps OK"

# --------------------------------------------------
# [5] Frontend build
# --------------------------------------------------
echo "[4/4] Building frontend..."
cd frontend

# Ensure npm is available
if ! command -v npm >/dev/null 2>&1; then
    if [ -f "${PROJECT_DIR}/node/bin/npm" ]; then
        export PATH="${PROJECT_DIR}/node/bin:${PATH}"
    fi
fi

# Use China mirror for npm if available
if npm config get registry 2>/dev/null | grep -q "registry.npmjs.org"; then
    # Test if npmjs.org is reachable
    if ! curl -sI "https://registry.npmjs.org/" --connect-timeout 3 >/dev/null 2>&1; then
        echo "  Using npmmirror.com for npm (China mirror)"
        npm config set registry https://registry.npmmirror.com
    fi
fi

npm install --silent 2>/dev/null || npm install
npm run build 2>/dev/null || npm run build
cd "$PROJECT_DIR"

echo ""
echo "==============================="
echo "  Install complete!"
echo "==============================="
echo "  Run: bash start.sh"
echo "  Then open http://localhost:3000"