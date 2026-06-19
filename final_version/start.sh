#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo ""
echo "========================================"
echo "  VulnForge - Auto Setup"
echo "========================================"
echo ""

if [ ! -f .env ]; then
    echo "[1/4] Creating .env from example..."
    cp final_version/.env.example .env
fi

current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "[2/4] Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
        echo "  API Key saved!"
    fi
else
    echo "[2/4] API Key already configured."
fi

cp .env final_version/.env 2>/dev/null
echo "[3/4] Environment ready."

echo "[4/4] Starting VulnForge..."
docker compose -f final_version/docker-compose.yml down --remove-orphans 2>/dev/null

if docker compose -f final_version/docker-compose.yml up -d --force-recreate 2>/dev/null; then
    my_ip=$(hostname -I | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://${my_ip}:3000 in your browser"
else
    sudo docker compose -f final_version/docker-compose.yml up -d --force-recreate
    my_ip=$(hostname -I | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://${my_ip}:3000 in your browser"
fi

echo "========================================"