# Git Worktrees for Agentic Development

## Overview

Git worktrees allow multiple working directories to share the same repository, enabling **parallel agent work** on different features without conflicts. This is ideal for Claude Code when you want multiple instances working on different tasks simultaneously.

## Directory Structure

```
/home/george_cairns/code/
├── rightplace/                    # Main worktree (main branch)
│   ├── .git/                      # Shared git directory
│   ├── server/
│   ├── web-ui/
│   └── ...
└── rightplace-worktrees/          # Container for all worktrees
    ├── feature-auth/              # Worktree for auth feature
    ├── feature-ui-redesign/       # Worktree for UI work
    ├── bugfix-face-detection/     # Worktree for a bug fix
    └── experiment-onnx/           # Worktree for experiments
```

## Why Worktrees for Agentic Work?

1. **Parallel Development**: Multiple Claude instances can work on different features simultaneously
2. **No Conflicts**: Each worktree has its own branch and working state
3. **Efficient Storage**: Git objects are shared, not duplicated
4. **Easy Context Switching**: Open different VSCode windows for each worktree
5. **Clean Separation**: Each agent works in isolation, merging when ready

## Port Allocation

Each worktree gets its own unique port pair to avoid conflicts:

| Worktree | Backend Port | Frontend Port |
|----------|--------------|---------------|
| MAIN | 8000 | 5173 |
| Worktree 1 | 8010 | 5183 |
| Worktree 2 | 8020 | 5193 |
| Worktree 3 | 8030 | 5203 |
| ... | +10 | +10 |

Ports are automatically assigned when creating a worktree and stored in `.worktree.env`.

## Quick Start

### Create a New Worktree

```bash
# From the main repo
cd /home/george_cairns/code/rightplace

# Create worktree with a new branch and unique ports
./scripts/worktree-new.sh feature-my-feature

# Output includes:
# Port Assignment:
#   Backend:  http://localhost:8010
#   Frontend: http://localhost:5183
```

### Database Options

```bash
# Option 1: No database (uses shared database from main)
./scripts/worktree-new.sh feature-my-feature

# Option 2: Fresh seeded database (HMP Oakwood with 864 locations)
./scripts/worktree-new.sh feature-my-feature --seed-db

# Option 3: Copy of main database (preserves existing data)
./scripts/worktree-new.sh feature-my-feature --copy-db
```

**Recommendation:**
- Use `--seed-db` for features that modify location/schema
- Use `--copy-db` for features that need existing data
- Use no flag if you only need read-only access to shared data

### List All Worktrees

```bash
git worktree list
```

### Remove a Worktree (after merging)

```bash
# Remove the worktree
git worktree remove ../rightplace-worktrees/feature-my-feature

# Or if you need to force removal
git worktree remove --force ../rightplace-worktrees/feature-my-feature
```

### Switch to a Worktree in VSCode

```bash
code /home/george_cairns/code/rightplace-worktrees/feature-my-feature
```

## Claude Code Workflow

### Starting a New Agent Task

1. **Create a dedicated worktree** for the task:
   ```bash
   cd /home/george_cairns/code/rightplace
   ./scripts/worktree-new.sh feature-login-screen
   ```

2. **Open VSCode in the new worktree**:
   ```bash
   code /home/george_cairns/code/rightplace-worktrees/feature-login-screen
   ```

3. **Start Claude Code** in that VSCode window - it will work in isolation

4. **When complete**, from the main repo:
   ```bash
   cd /home/george_cairns/code/rightplace
   git checkout main
   git merge feature/login-screen
   git worktree remove ../rightplace-worktrees/feature-login-screen
   git branch -d feature/login-screen
   ```

### Running Multiple Agents

You can have multiple VSCode windows open, each with its own Claude Code instance:

```bash
# Terminal 1: Agent working on backend
./scripts/worktree-new.sh feature-api-pagination
code /home/george_cairns/code/rightplace-worktrees/feature-api-pagination

# Terminal 2: Agent working on frontend  
./scripts/worktree-new.sh feature-dashboard-ui
code /home/george_cairns/code/rightplace-worktrees/feature-dashboard-ui

# Terminal 3: Agent fixing a bug
./scripts/worktree-new.sh bugfix-face-matching
code /home/george_cairns/code/rightplace-worktrees/bugfix-face-matching
```

Each agent sees only its own changes and works on its own branch.

## Naming Conventions

Use these prefixes for worktree names:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature-` | New features | `feature-biometric-login` |
| `bugfix-` | Bug fixes | `bugfix-memory-leak` |
| `refactor-` | Code improvements | `refactor-repository-layer` |
| `experiment-` | Experimental work | `experiment-gpu-acceleration` |
| `docs-` | Documentation | `docs-api-reference` |
| `test-` | Test improvements | `test-integration-coverage` |

## Worktree-Specific Setup

Each worktree may need its own setup:

### Python Virtual Environment

Each worktree can share the same venv or have its own:

```bash
# Option 1: Shared venv (recommended for most cases)
# Just activate the main venv from the worktree
cd /home/george_cairns/code/rightplace-worktrees/feature-X
source /home/george_cairns/code/rightplace/server/.venv/bin/activate

# Option 2: Separate venv (for testing dependency changes)
cd /home/george_cairns/code/rightplace-worktrees/feature-X/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Node Modules

For web-ui work, you'll need to install node_modules in each worktree:

```bash
cd /home/george_cairns/code/rightplace-worktrees/feature-X/web-ui
pnpm install
```

### Database

Each worktree shares the same database by default. If you need isolation:

```bash
# Copy the database for testing
cp /home/george_cairns/code/rightplace/server/data/prison_rollcall.db \
   /home/george_cairns/code/rightplace-worktrees/feature-X/server/data/
```

## Best Practices

### 1. Keep Worktrees Short-Lived

Create worktrees for specific tasks and remove them after merging. Don't let them linger.

### 2. Sync Regularly

Pull changes from main into your worktree branch regularly:

```bash
cd /home/george_cairns/code/rightplace-worktrees/feature-X
git fetch origin
git rebase origin/main
```

### 3. Use Descriptive Names

Name worktrees after the task they're working on:
- ✅ `feature-face-enrollment-api`
- ❌ `work1`, `temp`, `test`

### 4. One Task Per Worktree

Don't mix unrelated changes in the same worktree. Create a new one for each distinct task.

### 5. Clean Up After Merging

```bash
# After PR is merged
cd /home/george_cairns/code/rightplace
git worktree remove ../rightplace-worktrees/feature-X
git branch -d feature/X
```

## Troubleshooting

### "fatal: 'branch-name' is already checked out"

A branch can only be checked out in one worktree at a time. Either:
- Use a different branch name
- Remove the existing worktree first

### Worktree shows as "prunable"

The worktree directory was deleted but not properly removed:

```bash
git worktree prune
```

### Locked worktree

If a worktree is locked (usually after a crash):

```bash
git worktree unlock ../rightplace-worktrees/feature-X
```

## Integration with CI/CD

When pushing from a worktree, the remote branch will be created automatically:

```bash
cd /home/george_cairns/code/rightplace-worktrees/feature-X
git push -u origin feature/X
```

GitHub Actions will run on the feature branch. Create a PR when ready to merge.

## Summary Commands

```bash
# Create new worktree
./scripts/worktree-new.sh <name>

# List worktrees
git worktree list

# Open worktree in VSCode
code /home/george_cairns/code/rightplace-worktrees/<name>

# Sync with main
git fetch origin && git rebase origin/main

# Remove worktree (after merging)
git worktree remove ../rightplace-worktrees/<name>
git branch -d <branch-name>

# Clean up stale worktrees
git worktree prune
```
