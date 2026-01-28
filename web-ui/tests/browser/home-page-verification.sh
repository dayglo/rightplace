#!/bin/bash
# Browser verification script for Home/Dashboard page
# Uses agent-browser to verify the UI works correctly

set -e

echo "🌐 Starting Home/Dashboard Page Browser Verification"
echo "=================================================="

# Start the dev server in the background
echo "📦 Starting SvelteKit dev server..."
cd /home/george_cairns/code/rightplace/web-ui
npm run dev > /tmp/sveltekit-dev.log 2>&1 &
DEV_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:5173 > /dev/null; then
    echo "❌ Server failed to start"
    kill $DEV_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Server is running"

# Create directories for outputs
mkdir -p /home/george_cairns/code/rightplace/web-ui/tests/browser/screenshots
mkdir -p /home/george_cairns/code/rightplace/web-ui/tests/browser/snapshots
mkdir -p /home/george_cairns/code/rightplace/web-ui/tests/browser/logs

# Run browser tests
echo ""
echo "🔍 Running browser verification tests..."
echo ""

# Test 1: Open the page
echo "Test 1: Opening home page..."
agent-browser open http://localhost:5173 2>&1 | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test1-open.log

# Test 2: Take initial screenshot
echo "Test 2: Capturing initial screenshot..."
agent-browser screenshot /home/george_cairns/code/rightplace/web-ui/tests/browser/screenshots/home-page-initial.png 2>&1 | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test2-screenshot.log

# Test 3: Get page snapshot
echo "Test 3: Getting page snapshot..."
agent-browser snapshot -i > /home/george_cairns/code/rightplace/web-ui/tests/browser/snapshots/home-page-snapshot.txt 2>&1

# Test 4: Check for console errors
echo "Test 4: Checking for console errors..."
agent-browser errors 2>&1 | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test4-errors.log

# Test 5: Verify page title
echo "Test 5: Verifying page title..."
TITLE=$(agent-browser get title 2>&1)
echo "Page title: $TITLE" | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test5-title.log

# Test 6: Check navigation links
echo "Test 6: Checking navigation and quick action links..."
agent-browser snapshot -i | grep -E "(New Prisoner|New Location|Create Roll Call)" | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test6-links.log

# Test 7: Final screenshot
echo "Test 7: Taking final screenshot..."
agent-browser screenshot --full /home/george_cairns/code/rightplace/web-ui/tests/browser/screenshots/home-page-full.png 2>&1 | tee /home/george_cairns/code/rightplace/web-ui/tests/browser/logs/test7-full-screenshot.log

# Close browser
echo ""
echo "🧹 Cleaning up..."
agent-browser close 2>&1

# Stop dev server
kill $DEV_PID 2>/dev/null || true

echo ""
echo "✅ Browser verification complete!"
echo ""
echo "📊 Results:"
echo "  - Screenshots: web-ui/tests/browser/screenshots/"
echo "  - Snapshots: web-ui/tests/browser/snapshots/"
echo "  - Logs: web-ui/tests/browser/logs/"
echo ""
