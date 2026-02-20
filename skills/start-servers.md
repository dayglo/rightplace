# start-servers

Start both backend and frontend development servers with health checks.

## Description
Starts the Prison Roll Call project servers (FastAPI backend on port 8000, SvelteKit web UI on port 5173) with proper health checks and logging.

## Steps

1. **Check if servers are already running**
   ```bash
   lsof -i :8000 -i :5173
   ```

2. **Kill any existing instances**
   ```bash
   fuser -k 8000/tcp 5173/tcp 2>/dev/null || true
   ```

3. **Start the project using the uber script**
   ```bash
   cd /home/george_cairns/code/rightplace
   ./start-project.sh
   ```

4. **Wait for servers to be ready**
   ```bash
   sleep 5
   ```

5. **Verify backend health**
   ```bash
   curl -f http://localhost:8000/health || echo "Backend failed to start"
   ```

6. **Verify web UI is responding**
   ```bash
   curl -f http://localhost:5173 || echo "Web UI failed to start"
   ```

7. **Show log locations**
   ```
   Backend logs: log/server.log
   Web UI logs: log/web-ui.log

   To follow logs:
   tail -f log/*.log
   ```

8. **Display service URLs**
   ```
   Web UI: http://localhost:5173
   Backend API: http://localhost:8000
   API Docs: http://localhost:8000/docs
   ```

## Success Criteria
- Both ports (8000, 5173) are listening
- Health endpoint returns 200
- No errors in logs
- All services accessible
