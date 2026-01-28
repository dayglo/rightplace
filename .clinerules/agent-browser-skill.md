# Agent Browser Skill

## Overview
You have access to `agent-browser`, a headless browser automation CLI tool for testing and interacting with web applications during frontend development.

## When to Use
- Testing React Native web builds or web components
- Debugging UI issues in the browser
- Automated testing of frontend features
- Verifying responsive design and interactions
- Taking screenshots for documentation
- Validating accessibility tree structure

## Core Workflow

### 1. Navigate and Snapshot
```bash
agent-browser open http://localhost:3000
agent-browser snapshot -i --json   # Get interactive elements with refs
```

### 2. Interact Using Refs
The snapshot returns refs like `@e1`, `@e2`, etc. Use these for deterministic interactions:
```bash
agent-browser click @e2                   # Click button
agent-browser fill @e3 "test@example.com" # Fill input
agent-browser get text @e1                # Get text content
```

### 3. Verify Results
```bash
agent-browser screenshot page.png         # Visual verification
agent-browser get url                     # Check navigation
agent-browser is visible @e5              # Check element state
```

## Common Commands

### Navigation
```bash
agent-browser open <url>
agent-browser back
agent-browser forward
agent-browser reload
```

### Interaction
```bash
agent-browser click <selector|@ref>
agent-browser fill <selector|@ref> "text"
agent-browser press Enter
agent-browser hover @e1
agent-browser scroll down 100
```

### Information Gathering
```bash
agent-browser snapshot -i              # Interactive elements only
agent-browser snapshot -c              # Compact view
agent-browser snapshot -d 3            # Limit depth
agent-browser get text @e1
agent-browser get value @e2
agent-browser get url
agent-browser get title
```

### Verification
```bash
agent-browser is visible @e1
agent-browser is enabled @e2
agent-browser is checked @e3
```

### Screenshots & Debug
```bash
agent-browser screenshot [path]        # Saves to temp if no path
agent-browser screenshot --full        # Full page screenshot
agent-browser console                  # View console logs
agent-browser errors                   # View JS errors
agent-browser --headed open <url>      # Show browser window
```

### Sessions
```bash
agent-browser --session test1 open site.com
agent-browser --session test2 open other.com
agent-browser session list
```

## Best Practices

### 1. Use Refs for Reliability
Always get a snapshot first, then use refs (`@e1`, `@e2`) instead of CSS selectors:
```bash
# ✅ Good - deterministic
agent-browser snapshot -i
agent-browser click @e2

# ❌ Avoid - may break with DOM changes
agent-browser click "#submit-button"
```

### 2. Filter Snapshots
Use flags to reduce noise:
```bash
agent-browser snapshot -i              # Interactive only
agent-browser snapshot -i -c           # Interactive + compact
agent-browser snapshot -i -c -d 5      # + limit depth
```

### 3. JSON Output for Parsing
```bash
agent-browser snapshot --json          # Machine-readable
agent-browser get text @e1 --json
agent-browser is visible @e2 --json
```

### 4. Wait for Dynamic Content
```bash
agent-browser wait @e1                 # Wait for element
agent-browser wait 1000                # Wait 1 second
agent-browser wait --text "Welcome"    # Wait for text
agent-browser wait --load networkidle  # Wait for network
```

### 5. Debug with Headed Mode
```bash
agent-browser --headed open localhost:3000
# Browser window appears - useful for debugging
```

## Frontend Testing Workflow

### Testing a React Component
```bash
# 1. Start dev server (in background)
cd app && npm start &

# 2. Wait for server to be ready
sleep 3

# 3. Open and test
agent-browser open http://localhost:3000
agent-browser snapshot -i
agent-browser click @e1
agent-browser wait 500
agent-browser screenshot result.png

# 4. Verify
agent-browser get text @e2
agent-browser console  # Check for errors

# 5. Cleanup
agent-browser close
```

### Testing Form Submission
```bash
agent-browser open http://localhost:3000/login
agent-browser snapshot -i

# Fill form using refs
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3  # Submit button

# Wait for navigation
agent-browser wait --url "**/dashboard"
agent-browser screenshot success.png
```

### Responsive Testing
```bash
agent-browser set viewport 375 667     # iPhone SE
agent-browser open http://localhost:3000
agent-browser screenshot mobile.png

agent-browser set viewport 1920 1080   # Desktop
agent-browser screenshot desktop.png
```

## Selectors

### Refs (Recommended)
```bash
@e1, @e2, @e3  # From snapshot output
```

### CSS Selectors
```bash
"#id"
".class"
"div > button"
```

### Semantic Locators
```bash
agent-browser find role button click --name "Submit"
agent-browser find label "Email" fill "test@test.com"
agent-browser find text "Sign In" click
```

## Error Handling

### Check for Errors
```bash
agent-browser console                  # View console logs
agent-browser errors                   # View JS exceptions
```

### Debug Failed Interactions
```bash
agent-browser snapshot -i              # Re-check element refs
agent-browser is visible @e1           # Verify element state
agent-browser screenshot debug.png     # Visual inspection
agent-browser --headed open <url>      # Watch in real browser
```

## Integration with TDD

When implementing frontend features:

1. **Write test expectations** - Define what should be visible/interactive
2. **Use agent-browser to verify** - Automate the manual testing
3. **Take screenshots** - Document expected vs actual
4. **Check console/errors** - Catch JS issues early

Example:
```bash
# After implementing login form
agent-browser open http://localhost:3000/login
agent-browser snapshot -i > snapshot.txt
agent-browser screenshot login-form.png
agent-browser console
agent-browser errors

# Verify form works
agent-browser fill @e1 "test@example.com"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser screenshot logged-in.png
```

## Notes

- Browser state persists between commands (cookies, localStorage)
- Use `--session` for isolated testing
- Use `--profile` for persistent state across restarts
- Always `close` when done to free resources
- Chromium is downloaded automatically on first use
- Works headless by default (use `--headed` to see browser)

## Quick Reference

```bash
# Essential commands for frontend dev
agent-browser open <url>               # Navigate
agent-browser snapshot -i              # Get interactive elements
agent-browser click @e1                # Interact
agent-browser screenshot page.png      # Capture
agent-browser console                  # Check logs
agent-browser errors                   # Check errors
agent-browser close                    # Cleanup
```
