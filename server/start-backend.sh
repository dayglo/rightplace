#!/bin/bash
# Start the Prison Roll Call backend server
# Supports multi-worktree port configuration via .worktree.env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"

# Load port configuration from .worktree.env if it exists
BACKEND_PORT=8000
if [ -f "$PROJECT_ROOT/.worktree.env" ]; then
    source "$PROJECT_ROOT/.worktree.env"
    echo "Using worktree config: $WORKTREE_NAME"
fi

# Allow override via command line argument
if [ ! -z "$1" ]; then
    BACKEND_PORT="$1"
fi

# Kill any existing uvicorn processes on our port
echo "Checking for existing backend server on port $BACKEND_PORT..."
EXISTING_PID=$(fuser $BACKEND_PORT/tcp 2>/dev/null | awk '{print $1}')
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing server (PID: $EXISTING_PID)"
    kill -9 $EXISTING_PID
    sleep 1
fi

# Determine which venv to use
# Prefer local venv, fall back to main repo venv for worktrees
VENV_PATH="$SCRIPT_DIR/.venv/bin/uvicorn"
if [ ! -f "$VENV_PATH" ]; then
    VENV_PATH="/home/george_cairns/code/rightplace/server/.venv/bin/uvicorn"
fi

# Start uvicorn with logging to log directory
echo "Starting backend server on port $BACKEND_PORT..."
"$VENV_PATH" app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$LOG_DIR/server.log" 2>&1 &
BACKEND_PID=$!

echo "Backend server started (PID: $BACKEND_PID)"
echo "API URL: http://localhost:$BACKEND_PORT"
echo "Log file: $LOG_DIR/server.log"
echo "View logs: tail -f $LOG_DIR/server.log"
echo "Stop server: kill $BACKEND_PID"
