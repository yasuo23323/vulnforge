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
if ! command -v node >/dev/null 2>&1; then
    echo "  Node.js not found. Installing Node.js 20..."
    if command -v apt-get >/dev/null 2>&1; then
        # Debian/Ubuntu/Kali - use NodeSource
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>/dev/null || {
            apt-get update -qq
            apt-get install -y -qq nodejs npm
        }
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y nodejs npm
    elif command -v yum >/dev/null 2>&1; then
        yum install -y nodejs npm
    elif command -v pacman >/dev/null 2>&1; then
        pacman -S --noconfirm nodejs npm
    else
        echo "  Please install Node.js 18+ manually: https://nodejs.org"
        exit 1
    fi
    echo "  Node.js installed: $(node --version)"
fi

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y -qq python3 python3-pip python3-venv
    else
        echo "  Please install Python 3.10+ manually"
        exit 1
    fi
fi
echo "  Python: $(python3 --version)"
echo "  Node:   $(node --version)"
if command -v npm >/dev/null 2>&1; then
    echo "  npm:    $(npm --version)"
fi

# 2. Create .env if needed
echo "[2/4] Setting up configuration..."
if [ ! -f .env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example .env
    else
        echo "OPENAI_API_KEY=" > .env
        echo "OPENAI_BASE_URL=https://api.deepseek.com" >> .env
        echo "DATABASE_TYPE=sqlite" >> .env
        echo "DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db" >> .env
    fi
fi

# Check API key
CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "sk-your-api-key-here" ]; then
    if [ -t 0 ]; then
        echo "Enter your DeepSeek/OpenAI API Key (or press Enter to skip):"
        read -r api_key
        if [ -n "$api_key" ]; then
            if grep -q "^OPENAI_API_KEY=" .env 2>/dev/null; then
                sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
            else
                echo "OPENAI_API_KEY=$api_key" >> .env
            fi
            echo "  API Key saved!"
        fi
    else
        echo "  Non-interactive mode. Set OPENAI_API_KEY in .env file."
    fi
fi

# 3. Python setup
echo "[3/4] Setting up Python environment..."
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv 2>/dev/null || pip3 install virtualenv && python3 -m virtualenv venv
source venv/bin/activate
pip install --quiet --upgrade pip 2>/dev/null || true
echo "  Installing Python dependencies..."
pip install --quiet -r backend/requirements.txt 2>/dev/null || pip install --quiet -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || pip install --quiet -r backend/requirements.txt

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
echo ""
echo "  Run: bash start.sh"
echo "  Then open http://localhost:3000"