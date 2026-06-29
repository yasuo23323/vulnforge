#!/bin/bash
set -e

echo "==============================="
echo "  VulnForge - Linux Install"
echo "==============================="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Check Python 3
echo "[1/3] Checking system..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 not found. Install it:"
    echo "  apt-get install python3 python3-pip python3-venv"
    exit 1
fi
echo "  Python: $(python3 --version)"

# 2. Create .env
echo "[2/3] Setting up configuration..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./vulnforge.db
DEBUG=false
EOF
fi

# Check API key
CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "sk-your-api-key-here" ]; then
    if [ -t 0 ]; then
        printf "Enter your DeepSeek API Key (paste and press Enter): "
        read -r api_key
        if [ -n "$api_key" ]; then
            sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
            echo "  API Key saved!"
        fi
    fi
fi

# 3. Python venv + deps (only thing needed)
echo "[3/3] Setting up Python environment..."
if [ -f venv/bin/python3 ]; then
    if ! venv/bin/python3 -c "import pip" 2>/dev/null; then
        echo "  Old venv has corrupt cache, recreating..."
        rm -rf venv
    fi
fi
python3 -m venv venv 2>/dev/null || python3 -m virtualenv venv 2>/dev/null || { pip3 install virtualenv && python3 -m virtualenv venv; }
source venv/bin/activate
python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
echo "  Installing Python dependencies..."
pip install --quiet -r backend/requirements.txt 2>/dev/null \
  || pip install --quiet -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null \
  || pip install -r backend/requirements.txt
echo "  Python deps OK"

echo ""
echo "==============================="
echo "  Install complete!"
echo "==============================="
echo ""
echo "  Run: bash start.sh"
echo "  Then open http://localhost:3000"