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
command -v python3 >/dev/null 2>&1 || { echo "Need Python 3.10+"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Need Node.js 18+"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Need npm"; exit 1; }

# 2. Create .env if needed
echo "[2/4] Setting up configuration..."
if [ ! -f .env ]; then
    cp backend/.env .env 2>/dev/null || true
fi
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=" > .env
    echo "OPENAI_BASE_URL=https://api.deepseek.com" >> .env
    echo "DATABASE_TYPE=sqlite" >> .env
    echo "DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db" >> .env
fi

# Check API key
CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$CURRENT_KEY" ]; then
    echo "Enter your DeepSeek/OpenAI API Key (or press Enter to use .env):"
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

# 3. Python setup
echo "[3/4] Setting up Python environment..."
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv 2>/dev/null || { pip3 install virtualenv && python3 -m virtualenv venv; }
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt 2>/dev/null || pip install --quiet -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. Frontend setup
echo "[4/4] Building frontend..."
cd frontend
npm install --silent 2>/dev/null
npm run build 2>/dev/null
cd "$PROJECT_DIR"

echo ""
echo "  Install complete!"
echo "  Run: bash start.sh"
echo "  Then open http://localhost:3000"