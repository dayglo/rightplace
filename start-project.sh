#!/bin/bash
# Start the entire Prison Roll Call project (backend + web UI)
# Supports multi-worktree port configuration via .worktree.env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Load port configuration from .worktree.env if it exists
BACKEND_PORT=8000
FRONTEND_PORT=5173
WORKTREE_NAME="MAIN"
if [ -f "$SCRIPT_DIR/.worktree.env" ]; then
    source "$SCRIPT_DIR/.worktree.env"
fi

echo "========================================="
echo "Starting Prison Roll Call Project"
echo "Worktree: $WORKTREE_NAME"
echo "========================================="
echo ""

# Start backend server
echo "1. Starting backend server on port $BACKEND_PORT..."
cd "$SCRIPT_DIR/server"
./start-backend.sh
echo ""

# Wait a moment for backend to initialize
sleep 2

# Start web UI
echo "2. Starting web UI on port $FRONTEND_PORT..."
cd "$SCRIPT_DIR/web-ui"
./start-frontend.sh
echo ""

echo "========================================="
echo "Project Started Successfully"
echo "========================================="
echo ""
echo "Worktree: $WORKTREE_NAME"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:$BACKEND_PORT"
echo "  - Web UI:      http://localhost:$FRONTEND_PORT"
echo "  - API Docs:    http://localhost:$BACKEND_PORT/docs"
echo ""
echo "Logs:"
echo "  - Backend: $LOG_DIR/server.log"
echo "  - Web UI:  $LOG_DIR/web-ui.log"
echo ""
echo "View logs:"
echo "  tail -f $LOG_DIR/server.log"
echo "  tail -f $LOG_DIR/web-ui.log"
echo ""
echo "Stop this worktree's services:"
echo "  fuser -k $BACKEND_PORT/tcp $FRONTEND_PORT/tcp"
echo ""
