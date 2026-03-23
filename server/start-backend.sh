#!/bin/bash
# Start the Prison Roll Call backend server
# Supports multi-worktree port configuration via .worktree.env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR" || exit 1

# Help
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    cat <<EOF
Usage: $0 [PORT]
Start the backend server. Reads WORKTREE_ENV (or $PROJECT_ROOT/.worktree.env) if present.

Environment variables (optional):
  WORKTREE_ENV         Path to .worktree.env to load (defaults to $PROJECT_ROOT/.worktree.env)
  MAIN_VENV_PYTHON    Path to a python executable to use if no local venv (optional)
  MAIN_VENV_UVICORN   Path to a uvicorn executable to use if no local venv (optional)
EOF
    exit 0
fi

# Load port configuration from .worktree.env if it exists
BACKEND_PORT=8000
WORKTREE_ENV=${WORKTREE_ENV:-$PROJECT_ROOT/.worktree.env}
if [ -f "$WORKTREE_ENV" ]; then
    # shellcheck disable=SC1090
    source "$WORKTREE_ENV"
    echo "Using worktree config: ${WORKTREE_NAME:-(unnamed)}"
fi

# Allow override via command line argument
if [ -n "$1" ]; then
    BACKEND_PORT="$1"
fi

# Kill any existing uvicorn processes on our port and wait until port is free
echo "Checking for existing backend server on port $BACKEND_PORT..."
if fuser $BACKEND_PORT/tcp >/dev/null 2>&1; then
    echo "Killing all processes on port $BACKEND_PORT..."
    fuser -k $BACKEND_PORT/tcp >/dev/null 2>&1
    
    # Wait until port is actually free (max 10 seconds)
    echo "Waiting for port $BACKEND_PORT to be released..."
    for i in {1..20}; do
        if ! fuser $BACKEND_PORT/tcp >/dev/null 2>&1; then
            echo "Port $BACKEND_PORT is now free"
            break
        fi
        # Keep killing any lingering processes
        fuser -k $BACKEND_PORT/tcp >/dev/null 2>&1
        if [ $i -eq 20 ]; then
            echo "Warning: Port $BACKEND_PORT still in use after 10 seconds"
        fi
        sleep 0.5
    done
fi

# Determine which venv to use
# Prefer local venv, fall back to main repo venv for worktrees
# Determine which executable to use to run uvicorn.
# Preference order:
# 1) local uvicorn: $SCRIPT_DIR/.venv/bin/uvicorn
# 2) local python:  $SCRIPT_DIR/.venv/bin/python (used with -m uvicorn)
# 3) MAIN_VENV_UVICORN env var
# 4) MAIN_VENV_PYTHON env var (used with -m uvicorn)
# 5) derived python: $PROJECT_ROOT/server/.venv/bin/python

LOCAL_UVICORN="$SCRIPT_DIR/.venv/bin/uvicorn"
LOCAL_PYTHON="$SCRIPT_DIR/.venv/bin/python"
DERIVED_PYTHON="$PROJECT_ROOT/server/.venv/bin/python"

SELECTED_CMD=""
SELECTED_MODE=""

if [ -x "$LOCAL_UVICORN" ]; then
    SELECTED_CMD="$LOCAL_UVICORN"
    SELECTED_MODE="exec"
elif [ -x "$LOCAL_PYTHON" ]; then
    SELECTED_CMD="$LOCAL_PYTHON"
    SELECTED_MODE="module"
elif [ -n "$MAIN_VENV_UVICORN" ] && [ -x "$MAIN_VENV_UVICORN" ]; then
    SELECTED_CMD="$MAIN_VENV_UVICORN"
    SELECTED_MODE="exec"
elif [ -n "$MAIN_VENV_PYTHON" ] && [ -x "$MAIN_VENV_PYTHON" ]; then
    SELECTED_CMD="$MAIN_VENV_PYTHON"
    SELECTED_MODE="module"
elif [ -x "$DERIVED_PYTHON" ]; then
    SELECTED_CMD="$DERIVED_PYTHON"
    SELECTED_MODE="module"
fi

if [ -z "$SELECTED_CMD" ]; then
    cat <<EOF
ERROR: No usable uvicorn or python executable found.
Suggested fixes:
  - Create a local venv in server/:
      cd "$SCRIPT_DIR" && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
  - Or export MAIN_VENV_PYTHON or MAIN_VENV_UVICORN to a valid executable path.
EOF
    exit 1
fi

echo "Starting backend server on port $BACKEND_PORT using: $SELECTED_CMD (mode: $SELECTED_MODE)"
if [ "$SELECTED_MODE" = "exec" ]; then
    "$SELECTED_CMD" app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > "$LOG_DIR/server.log" 2>&1 &
else
    "$SELECTED_CMD" -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > "$LOG_DIR/server.log" 2>&1 &
fi
BACKEND_PID=$!

echo "Backend server started (PID: $BACKEND_PID)"
echo "API URL: http://localhost:$BACKEND_PORT"
echo "Log file: $LOG_DIR/server.log"
echo "View logs: tail -f $LOG_DIR/server.log"
echo "Stop server: kill $BACKEND_PID"
