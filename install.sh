#!/bin/bash
set -e

echo "==============================="
echo "  VulnForge - Linux Install"
echo "==============================="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Check requirements
echo "[1/4] Checking system..."

# Check/install Node.js
install_node() {
    echo "  Installing Node.js via apt..."
    apt-get update -qq 2>/dev/null
    apt-get install -y -qq nodejs npm 2>/dev/null && return 0
    return 1
}

if ! command -v node >/dev/null 2>&1; then
    echo "  Node.js not found. Installing..."
    if command -v apt-get >/dev/null 2>&1; then
        install_node || {
            # Try NodeSource as fallback
            echo "  Trying NodeSource..."
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>/dev/null && apt-get install -y nodejs || {
                echo "ERROR: Could not install Node.js. Try manually:"
                echo "  apt-get install -y nodejs npm"
                exit 1
            }
        }
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y nodejs npm
    elif command -v yum >/dev/null 2>&1; then
        yum install -y nodejs npm
    elif command -v pacman >/dev/null 2>&1; then
        pacman -S --noconfirm nodejs npm
    else
        echo "Please install Node.js 18+ manually: https://nodejs.org"
        exit 1
    fi
    echo "  Node.js $(node --version) ready"
fi

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y -qq python3 python3-pip python3-venv
    else
        echo "Please install Python 3.10+ manually"
        exit 1
    fi
fi
echo "  Python: $(python3 --version)"
echo "  Node:   $(node --version)"
echo "  npm:    $(npm --version 2>/dev/null || echo 'not found')"

# 2. Create .env
echo "[2/4] Setting up configuration..."
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=" > .env
    echo "OPENAI_BASE_URL=https://api.deepseek.com" >> .env
    echo "DATABASE_TYPE=sqlite" >> .env
    echo "DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db" >> .env
    echo "DEBUG=false" >> .env
fi

# Check API key
CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "sk-your-api-key-here" ]; then
    if [ -t 0 ]; then
        echo "Enter your DeepSeek API Key (paste and press Enter):"
        read -r api_key
        if [ -n "$api_key" ]; then
            sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
            echo "  API Key saved!"
        fi
    fi
fi

# 3. Python setup
echo "[3/4] Setting up Python environment..."
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv
source venv/bin/activate
pip install --quiet --upgrade pip 2>/dev/null || true
echo "  Installing Python dependencies..."
if pip install --quiet -r backend/requirements.txt 2>/dev/null; then
    echo "  Python deps OK"
elif pip install --quiet -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null; then
    echo "  Python deps OK (Tsinghua mirror)"
else
    pip install -r backend/requirements.txt
fi

# 4. Frontend setup
echo "[4/4] Building frontend..."
cd frontend
npm install --silent 2>/dev/null || npm install
npm run build 2>/dev/null || npm run build
cd "$PROJECT_DIR"

echo ""
echo "==============================="
echo "  Install complete!"
echo "==============================="
echo "  Run: bash start.sh"
echo "  Then open http://localhost:3000"