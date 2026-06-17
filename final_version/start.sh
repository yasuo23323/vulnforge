#!/bin/bash

# ========================================
#  VulnForge - One-Click Setup & Launch
# ========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # Go to project root

echo ""
echo "========================================"
echo "  VulnForge - Auto Setup"
echo "========================================"
echo ""

# Step 1: Create .env if missing
if [ ! -f .env ]; then
    echo "[1/4] Creating .env from example..."
    cp final_version/.env.example .env
fi

# Step 2: Check API key
current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "[2/4] Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        # Escape special chars in API key for sed
        api_key_escaped=$(printf '%s\n' "$api_key" | sed 's/[\/&]/\\&/g')
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key_escaped|" .env
        echo "  API Key saved!"
    fi
else
    echo "[2/4] API Key already configured."
fi

# Step 3: Copy .env to final_version/ for Docker
cp .env final_version/.env
echo "[3/4] Environment ready."

# Step 4: Start Docker
echo "[4/4] Starting VulnForge..."
if docker compose -f final_version/docker-compose.yml up -d; then
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://YOUR_SERVER_IP:3000 in your browser"
else
    echo "  Trying with sudo..."
    sudo docker compose -f final_version/docker-compose.yml up -d
    echo ""
    echo "  VulnForge is running!"
fi

echo "========================================"
