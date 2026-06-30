#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Add local tools to PATH
if [ -d tools ]; then
    export PATH="${SCRIPT_DIR}/tools:${PATH}"
fi

# Activate venv
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "Starting VulnForge..."

# Kill old processes
pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true
pkill -f "proxy_server.py" 2>/dev/null || true
pkill -f "python3 -m http.server" 2>/dev/null || true
sleep 1

# Check uvicorn
if ! command -v uvicorn >/dev/null 2>&1; then
    if [ -f venv/bin/uvicorn ]; then
        UVICORN="venv/bin/uvicorn"
    else
        echo "ERROR: uvicorn not found. Run 'bash install.sh' first."
        exit 1
    fi
else
    UVICORN="uvicorn"
fi

# Start backend
$UVICORN backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend proxy (serves static files + proxies API calls)
if [ -f frontend/dist/index.html ]; then
    python3 proxy_server.py &
    PROXY_PID=$!
    echo "  Frontend: http://localhost:3000 (proxied)"
else
    echo "  WARNING: frontend/dist/index.html not found"
    PROXY_PID=""
fi

sleep 3
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $PROXY_PID 2>/dev/null; exit" INT TERM
wait