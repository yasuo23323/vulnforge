#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "Starting VulnForge..."

# Kill old processes
pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true
sleep 1

# Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend dev server (or use dist/)
if [ -d frontend/dist ]; then
    python3 -m http.server 3000 --directory frontend/dist &
    FRONTEND_PID=$!
    echo "  Frontend: http://localhost:3000 (static)"
else
    cd frontend && npx vite --port 3000 --host &
    FRONTEND_PID=$!
    cd "$SCRIPT_DIR"
    echo "  Frontend: http://localhost:3000 (dev mode)"
fi

sleep 2
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait