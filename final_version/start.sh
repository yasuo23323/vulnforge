#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo ""
echo "========================================"
echo "  VulnForge - Auto Setup"
echo "========================================"
echo ""

# Step 1: Configure Docker (registry mirror for China)
echo "[1/4] Configuring Docker..."
echo '{"ipv6":false,"registry-mirrors":["https://docker.mirrors.daocloud.io"]}' > /etc/docker/daemon.json 2>/dev/null || true
systemctl restart docker 2>/dev/null || true
sleep 5
echo "[2/4] Configuring Docker..."
echo '{"ipv6":false}' > /etc/docker/daemon.json
systemctl restart docker 2>/dev/null || true
sleep 5

# Step 3: Pre-pull images
echo "[3/4] Pre-pulling Docker images..."
docker pull postgres:16-alpine 2>&1 | tail -1
docker pull redis:7-alpine 2>&1 | tail -1

# Step 4: API key
if [ ! -f .env ]; then
    cp final_version/.env.example .env
fi
current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "[4/4] Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
        echo "  API Key saved!"
    fi
else
    echo "[4/4] API Key already configured."
fi

# Step 5: Start
cp .env final_version/.env 2>/dev/null
echo "[5/4] Starting VulnForge..."
docker compose -f final_version/docker-compose.yml down --remove-orphans 2>/dev/null

if docker compose -f final_version/docker-compose.yml up -d --force-recreate 2>/dev/null; then
    ip=$(hostname -I 2>/dev/null | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
    echo "  Open http://${ip:-localhost}:3000 in your browser"
else
    sudo docker compose -f final_version/docker-compose.yml up -d --force-recreate
    ip=$(hostname -I 2>/dev/null | awk "{print $1}")
    echo ""
    echo "  VulnForge is running!"
fi
echo "========================================"
