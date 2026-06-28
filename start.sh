#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "Starting VulnForge..."

# Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Simple frontend server
python3 -m http.server 3000 --directory frontend/dist/ 2>/dev/null &
FRONTEND_PID=$!

sleep 2
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
wait
