#!/bin/bash
# Start the Prison Roll Call backend server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"

# Kill any existing uvicorn processes on port 8000
echo "Checking for existing backend server..."
EXISTING_PID=$(fuser 8000/tcp 2>/dev/null | awk '{print $1}')
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing server (PID: $EXISTING_PID)"
    kill -9 $EXISTING_PID
    sleep 1
fi

# Start uvicorn with logging to log directory
echo "Starting backend server..."
"$SCRIPT_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/server.log" 2>&1 &
BACKEND_PID=$!

echo "Backend server started (PID: $BACKEND_PID)"
echo "Log file: $LOG_DIR/server.log"
echo "View logs: tail -f $LOG_DIR/server.log"
echo "Stop server: kill $BACKEND_PID"
