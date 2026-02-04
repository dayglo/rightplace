# Worktree Awareness

## Detecting Worktree Context

When working in this project, you may be in:
1. **Main worktree** (`/home/george_cairns/code/rightplace`) - the primary development directory
2. **Feature worktree** (`/home/george_cairns/code/rightplace-worktrees/<name>`) - an isolated feature branch

## How to Identify Current Context

Check the current working directory path:
- Main repo: `/home/george_cairns/code/rightplace`
- Worktree: `/home/george_cairns/code/rightplace-worktrees/<feature-name>`

Or check git:
```bash
git worktree list
git branch --show-current
```

## Working in a Worktree

When in a worktree:

### 1. You're on a Feature Branch
Your changes are isolated to this branch. Commit freely without affecting main.

### 2. Use the Shared Python Venv
```bash
source /home/george_cairns/code/rightplace/server/.venv/bin/activate
```

### 3. Install Node Modules if Needed
```bash
cd web-ui && pnpm install
```

### 4. Database is Shared by Default
Unless explicitly copied, you're using the same database as main.

### 5. Push to Create Remote Branch
```bash
git push -u origin $(git branch --show-current)
```

## When to Create a Worktree

Create a new worktree when:
- Starting a new feature that may take multiple sessions
- Working on a task that could conflict with other ongoing work
- Testing experimental changes without affecting main
- Running multiple Claude Code instances in parallel

## Worktree Lifecycle

1. **Create**: `./scripts/worktree-new.sh feature-name`
2. **Develop**: Make changes, commit regularly
3. **Push**: `git push -u origin feature/name`
4. **PR/Merge**: Create PR and merge to main
5. **Cleanup**: `./scripts/worktree-remove.sh feature-name`

## Parallel Agent Work

When multiple Claude Code instances work simultaneously:
- Each instance works in its own worktree
- No conflicts between instances
- Each has its own branch
- Merge to main when complete

## Best Practices

- Keep worktrees short-lived (days, not weeks)
- Sync with main regularly: `git fetch origin && git rebase origin/main`
- Commit frequently with clear messages
- Remove worktrees after merging
- One task per worktree
