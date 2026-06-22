#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo ""
echo "========================================"
echo "  VulnForge - Auto Setup"
echo "========================================"
echo ""

# Step 1: Check and fix system DNS
echo "[1/5] Checking system DNS..."
if ! ping -c 1 github.com > /dev/null 2>&1; then
    echo "  DNS not working - configuring 8.8.8.8..."
    chattr -i /etc/resolv.conf 2>/dev/null || true
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
    chattr +i /etc/resolv.conf 2>/dev/null || true
    echo "  DNS fixed"
else
    echo "  DNS OK"
fi

# Step 2: Configure Docker
echo "[2/5] Configuring Docker..."
echo '{"ipv6":false}' > /etc/docker/daemon.json
systemctl restart docker 2>/dev/null || true
sleep 5

# Step 3: Pre-pull images
echo "[3/5] Pre-pulling Docker images..."
docker pull postgres:16-alpine 2>&1 | tail -1
docker pull redis:7-alpine 2>&1 | tail -1

# Step 4: API key
if [ ! -f .env ]; then
    cp final_version/.env.example .env
fi
current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "[4/5] Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
        echo "  API Key saved!"
    fi
else
    echo "[4/5] API Key already configured."
fi

# Step 5: Start
cp .env final_version/.env 2>/dev/null
echo "[5/5] Starting VulnForge..."
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
