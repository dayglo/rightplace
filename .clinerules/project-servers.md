# Project Server Management

## Starting the Project

### Start Everything (Recommended)
Use the uber script to start both backend and web UI:
```bash
cd /home/george_cairns/code/rightplace
./start-project.sh
```

This will:
- Kill any existing server instances
- Start the backend server (FastAPI) on port 8000
- Start the web UI (SvelteKit) on port 5173
- Log everything to `rightplace/log/` directory

### Start Backend Only
```bash
cd /home/george_cairns/code/rightplace/server
./start-backend.sh
```

### Start Frontend Only
```bash
cd /home/george_cairns/code/rightplace/web-ui
./start-frontend.sh
```

## Accessing Services

- **Web UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger)
- **API Docs**: http://localhost:8000/redoc (ReDoc)

## Log Files

All logs are written to `rightplace/log/`:
- **Backend**: `rightplace/log/server.log`
- **Web UI**: `rightplace/log/web-ui.log`

### View Logs
```bash
# Backend logs
tail -f /home/george_cairns/code/rightplace/log/server.log

# Web UI logs
tail -f /home/george_cairns/code/rightplace/log/web-ui.log

# Both logs simultaneously
tail -f /home/george_cairns/code/rightplace/log/*.log
```

## Stopping Services

### Stop Backend
```bash
# Find and kill by port
fuser -k 8000/tcp

# Or by process name
pkill -f 'uvicorn app.main:app'
```

### Stop Web UI
```bash
# Find and kill by port
fuser -k 5173/tcp

# Or by process name
pkill -f 'vite.*rightplace/web-ui'
```

### Stop Everything
```bash
fuser -k 8000/tcp 5173/tcp
# or
pkill -f 'uvicorn app.main:app'
pkill -f 'vite.*rightplace/web-ui'
```

## Troubleshooting

### Port Already in Use
The start scripts automatically kill old instances, but if you encounter issues:
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :5173

# Kill specific PIDs
kill -9 <PID>
```

### Check Server Status
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if web UI is running
curl http://localhost:5173
```

### Clear Logs
```bash
# Clear all logs
rm /home/george_cairns/code/rightplace/log/*.log

# Or truncate
> /home/george_cairns/code/rightplace/log/server.log
> /home/george_cairns/code/rightplace/log/web-ui.log
```

## Development Workflow

1. Start the project: `./start-project.sh`
2. Make code changes
3. Backend auto-reloads (uvicorn --reload)
4. Web UI auto-reloads (Vite HMR)
5. View logs to debug issues
6. Stop services when done

## Important Notes

- **Backend requires virtualenv**: The server script uses `.venv/bin/uvicorn` directly
- **Auto-reload enabled**: Both servers watch for file changes
- **Logs rotate**: Consider implementing log rotation for production
- **Background processes**: All servers run as background processes
- **Kill old instances**: Scripts automatically kill processes on the same ports
