#!/bin/bash
# Start the Prison Roll Call web UI server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"

# Kill any existing SvelteKit dev server processes on port 5173
echo "Checking for existing web UI server..."
EXISTING_PID=$(fuser 5173/tcp 2>/dev/null | awk '{print $1}')
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing web UI server (PID: $EXISTING_PID)"
    kill -9 $EXISTING_PID
    sleep 1
fi

# Also kill any orphaned vite/node processes for this project
pkill -f "vite.*rightplace/web-ui" 2>/dev/null

# Start SvelteKit dev server with logging to log directory
echo "Starting web UI server..."
npm run dev > "$LOG_DIR/web-ui.log" 2>&1 &
WEB_UI_PID=$!

echo "Web UI server started (PID: $WEB_UI_PID)"
echo "Log file: $LOG_DIR/web-ui.log"
echo "View logs: tail -f $LOG_DIR/web-ui.log"
echo "Stop server: kill $WEB_UI_PID"
echo "Access at: http://localhost:5173"
