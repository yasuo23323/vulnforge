#!/bin/bash
echo "========================================"
echo " VulnForge - Starting..."
echo "========================================"
echo ""
if [ ! -f .env ]; then
    echo "WARNING: .env not found!"
    echo "Copy .env.example to .env and set your API key."
fi
echo "Starting services..."
docker compose up -d
echo "Opening browser..."
xdg-open http://localhost:3000 2>/dev/null || open http://localhost:3000 2>/dev/null
echo ""
echo "VulnForge running at http://localhost:3000"
echo "Run 'docker compose down' to stop."
