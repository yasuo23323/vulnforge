#!/bin/bash
set -e

echo "==============================="
echo "  VulnForge - Linux Install"
echo "==============================="
echo ""

# 1. Check system
echo "[1/4] Checking system..."
python3 --version 2>/dev/null || { echo "Need Python3"; exit 1; }
node --version 2>/dev/null || { echo "Need Node.js"; exit 1; }

# 2. Python setup
echo "[2/4] Setting up Python..."
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

# 3. Frontend setup
echo "[3/4] Building frontend..."
cd frontend
npm install --silent 2>/dev/null
npm run build 2>/dev/null
cd ..

# 4. API key and start
if [ ! -f .env ]; then
    cp backend/.env.example .env 2>/dev/null || true
fi
current_key=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$current_key" ] || [ "$current_key" = "sk-your-api-key-here" ]; then
    echo "[4/4] Enter your DeepSeek API Key:"
    read -r api_key
    if [ -n "$api_key" ]; then
        echo "OPENAI_API_KEY=$api_key" > .env
        echo "DATABASE_TYPE=sqlite" >> .env
        echo "DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db" >> .env
        echo "  API Key saved!"
    fi
fi

echo ""
echo "  Install complete!"
echo "  Run: bash start.sh"
