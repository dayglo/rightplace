# test-ui

Run comprehensive web UI testing workflow with agent-browser.

## Description
Execute a full UI test workflow using agent-browser for the Prison Roll Call web interface. Includes navigation, interaction verification, screenshot capture, and error checking.

## Prerequisites
- Web UI must be running on http://localhost:5173
- agent-browser must be installed

## Steps

1. **Verify web UI is running**
   ```bash
   curl -f http://localhost:5173 || echo "ERROR: Web UI not running. Start with: ./start-project.sh"
   ```

2. **Open the application**
   ```bash
   agent-browser open http://localhost:5173
   ```

3. **Get interactive snapshot**
   ```bash
   agent-browser snapshot -i -c
   ```
   This provides element references (@e1, @e2, etc.) for interaction.

4. **Check for console errors**
   ```bash
   agent-browser console
   agent-browser errors
   ```

5. **Capture initial screenshot**
   ```bash
   agent-browser screenshot screenshots/ui-initial.png
   ```

6. **Test navigation (if applicable)**
   - Use refs from snapshot to click navigation elements
   - Example: `agent-browser click @e1`
   - Verify navigation: `agent-browser get url`

7. **Test interactive elements**
   - Fill forms if present: `agent-browser fill @e2 "test-data"`
   - Click buttons: `agent-browser click @e3`
   - Verify state changes with snapshots

8. **Capture final state**
   ```bash
   agent-browser screenshot screenshots/ui-final.png
   ```

9. **Final error check**
   ```bash
   agent-browser console
   agent-browser errors
   ```

10. **Clean up**
    ```bash
    agent-browser close
    ```

## Success Criteria
- No JavaScript errors in console
- All interactive elements respond correctly
- Screenshots captured successfully
- Navigation works as expected

## Output
Screenshots saved to: `screenshots/` directory
