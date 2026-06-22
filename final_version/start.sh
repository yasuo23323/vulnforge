#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo ""
echo "========================================"
echo "  VulnForge - Auto Setup"
echo "========================================"
echo ""

# Step 1: Configure Docker (IPv6 off + public DNS)
echo "[1/4] Configuring Docker..."
echo '{"ipv6":false,"dns":["8.8.8.8","1.1.1.1"]}' > /etc/docker/daemon.json 2>/dev/null || true
systemctl restart docker 2>/dev/null || true
sleep 3

# Step 2: Create .env if missing
if [ ! -f .env ]; then
    echo "[2/4] Creating .env from example..."
    cp final_version/.env.example .env
fi

# Step 3: Check API key
current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "[3/4] Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
        echo "  API Key saved!"
    fi
else
    echo "[3/4] API Key already configured."
fi

# Step 4: Copy .env and start
cp .env final_version/.env 2>/dev/null
echo "[4/4] Starting VulnForge..."
docker compose -f final_version/docker-compose.yml down --remove-orphans 2>/dev/null

if docker compose -f final_version/docker-compose.yml up -d --force-recreate 2>/dev/null; then
    my_ip=$(hostname -I 2>/dev/null | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://${my_ip:-localhost}:3000 in your browser"
else
    sudo docker compose -f final_version/docker-compose.yml up -d --force-recreate
    my_ip=$(hostname -I 2>/dev/null | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://${my_ip:-localhost}:3000 in your browser"
fi

echo "========================================"
