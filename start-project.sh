#!/bin/bash
# Start the entire Prison Roll Call project (backend + web UI)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "========================================="
echo "Starting Prison Roll Call Project"
echo "========================================="
echo ""

# Start backend server
echo "1. Starting backend server..."
cd "$SCRIPT_DIR/server"
./start-backend.sh
echo ""

# Wait a moment for backend to initialize
sleep 2

# Start web UI
echo "2. Starting web UI..."
cd "$SCRIPT_DIR/web-ui"
./start-frontend.sh
echo ""

echo "========================================="
echo "Project Started Successfully"
echo "========================================="
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Web UI:      http://localhost:5173"
echo "  - API Docs:    http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  - Backend: $LOG_DIR/server.log"
echo "  - Web UI:  $LOG_DIR/web-ui.log"
echo ""
echo "View logs:"
echo "  tail -f $LOG_DIR/server.log"
echo "  tail -f $LOG_DIR/web-ui.log"
echo ""
echo "Stop all services:"
echo "  pkill -f 'uvicorn app.main:app'"
echo "  pkill -f 'vite.*rightplace/web-ui'"
echo ""
