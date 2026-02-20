# Claude Code Skills for Prison Roll Call

This directory contains custom skills for Claude Code to streamline development workflows.

## Available Skills

### `/start-servers`
Start both backend and frontend development servers with health checks.

**Usage:**
```
/start-servers
```

**What it does:**
- Kills any existing server instances
- Starts backend (FastAPI on port 8000)
- Starts web UI (SvelteKit on port 5173)
- Verifies both services are healthy
- Shows log locations and service URLs

---

### `/test-ui`
Run comprehensive web UI testing workflow with agent-browser.

**Usage:**
```
/test-ui
```

**What it does:**
- Opens web UI in agent-browser
- Captures interactive element snapshot
- Checks for console errors
- Takes screenshots for visual verification
- Tests navigation and interactions
- Reports any JavaScript errors

**Prerequisites:** Web UI must be running on http://localhost:5173

---

### `/db-inspect`
Quick database inspection and health check.

**Usage:**
```
/db-inspect
```

**What it does:**
- Shows table row counts
- Displays location type distribution
- Lists recent roll call sessions
- Shows verification statistics
- Reports database file metadata

---

## Installation

Skills can be installed in two ways:

### Option 1: Global Installation (Recommended)
Install skills globally to use across all Claude Code sessions:

```bash
# Copy skills to Claude Code config directory
mkdir -p ~/.config/claude/skills
cp skills/*.md ~/.config/claude/skills/
```

### Option 2: Project-Specific Installation
Skills in this directory are automatically available when working in this project (no action needed).

## Using Skills

In Claude Code, invoke skills with a slash command:

```
/start-servers
```

Or ask Claude Code to use them:

```
Can you start the servers?
```

Claude Code will automatically recognize the request and invoke the appropriate skill.

## Creating Custom Skills

Skills are markdown files with this structure:

```markdown
# skill-name

Brief description

## Description
Detailed description of what the skill does

## Prerequisites (optional)
Any requirements

## Steps
1. First step with bash code blocks
2. Second step
3. ...

## Success Criteria
What indicates success

## Output (optional)
What the skill produces
```

**Best Practices:**
- Use absolute paths for reliability
- Include health checks and verification
- Provide clear success/failure indicators
- Add helpful output formatting
- Keep skills focused on one task

## Troubleshooting

**Skill not found:**
- Verify skills are in `~/.config/claude/skills/` for global access
- Or ensure you're in the project directory for project-specific skills
- Restart Claude Code after adding new skills

**Skill fails:**
- Check prerequisites are met (e.g., servers running, venv activated)
- Review error messages in skill output
- Verify file paths are correct

## Contributing

To add a new skill:
1. Create a new `.md` file in this directory
2. Follow the skill structure above
3. Test the skill thoroughly
4. Update this README with the new skill documentation
