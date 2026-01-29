#!/bin/bash
# Start the Prison Roll Call backend server

cd /home/george_cairns/code/rightplace/server

# Kill any existing uvicorn processes on port 8000
echo "Checking for existing backend server..."
EXISTING_PID=$(fuser 8000/tcp 2>/dev/null | awk '{print $1}')
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing server (PID: $EXISTING_PID)"
    kill -9 $EXISTING_PID
    sleep 1
fi

# Use the venv python directly to ensure correct environment
/home/george_cairns/code/rightplace/server/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend-server.log 2>&1 &
BACKEND_PID=$!

echo "Backend server started (PID: $BACKEND_PID)"
echo "Backend log: tail -f /tmp/backend-server.log"
echo "Stop server: kill $BACKEND_PID"
