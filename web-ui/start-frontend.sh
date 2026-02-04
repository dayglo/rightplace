#!/bin/bash
# Start the Prison Roll Call web UI server
# Supports multi-worktree port configuration via .worktree.env

# Source nvm if available (for npm/pnpm access in non-interactive shells)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"

# Load port configuration from .worktree.env if it exists
FRONTEND_PORT=5173
BACKEND_PORT=8000
WORKTREE_NAME="MAIN"
if [ -f "$PROJECT_ROOT/.worktree.env" ]; then
    source "$PROJECT_ROOT/.worktree.env"
    echo "Using worktree config: $WORKTREE_NAME"
fi

# Allow override via command line argument
if [ ! -z "$1" ]; then
    FRONTEND_PORT="$1"
fi

# Kill any existing SvelteKit dev server processes on our port
echo "Checking for existing web UI server on port $FRONTEND_PORT..."
if fuser $FRONTEND_PORT/tcp >/dev/null 2>&1; then
    echo "Killing all processes on port $FRONTEND_PORT..."
    fuser -k $FRONTEND_PORT/tcp >/dev/null 2>&1
    
    # Wait until port is actually free (max 10 seconds)
    echo "Waiting for port $FRONTEND_PORT to be released..."
    for i in {1..20}; do
        if ! fuser $FRONTEND_PORT/tcp >/dev/null 2>&1; then
            echo "Port $FRONTEND_PORT is now free"
            break
        fi
        # Keep killing any lingering processes
        fuser -k $FRONTEND_PORT/tcp >/dev/null 2>&1
        if [ $i -eq 20 ]; then
            echo "Warning: Port $FRONTEND_PORT still in use after 10 seconds"
        fi
        sleep 0.5
    done
fi

# Also kill any orphaned vite/node processes for this specific worktree
pkill -f "vite.*$SCRIPT_DIR" 2>/dev/null

# Set API URL environment variable for the frontend
export VITE_API_URL="http://localhost:$BACKEND_PORT/api/v1"

# Start SvelteKit dev server with custom port
echo "Starting web UI server on port $FRONTEND_PORT..."
npm run dev -- --port $FRONTEND_PORT > "$LOG_DIR/web-ui.log" 2>&1 &
WEB_UI_PID=$!

echo "Web UI server started (PID: $WEB_UI_PID)"
echo "Frontend URL: http://localhost:$FRONTEND_PORT"
echo "Backend API: http://localhost:$BACKEND_PORT"
echo "Log file: $LOG_DIR/web-ui.log"
echo "View logs: tail -f $LOG_DIR/web-ui.log"
echo "Stop server: kill $WEB_UI_PID"
