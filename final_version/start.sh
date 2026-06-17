#!/bin/bash
if [ ! -f .env ]; then
    cp final_version/.env.example .env
fi

echo "========================================"
echo "  VulnForge - Setup & Launch"
echo "========================================"
echo ""
current_key=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
if [ "$current_key" = "sk-your-api-key-here" ] || [ -z "$current_key" ]; then
    echo "Enter your DeepSeek API Key (paste and press Enter):"
    read -r api_key
    if [ -n "$api_key" ]; then
        # Replace API key safely (handle special chars with | delimiter)
        sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
        echo "API Key saved!"
    else
        echo "No key entered. Edit .env manually later."
    fi
else
    echo "API Key already configured."
fi
echo ""
echo "Starting VulnForge..."
docker compose -f final_version/docker-compose.yml up -d
echo ""
echo "Done! Open http://YOUR_SERVER_IP:3000"
