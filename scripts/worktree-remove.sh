#!/bin/bash
# Remove a git worktree and optionally delete its branch
# Usage: ./scripts/worktree-remove.sh <worktree-name> [--keep-branch]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
WORKTREE_BASE="/home/george_cairns/code/rightplace-worktrees"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if name provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Worktree name required${NC}"
    echo ""
    echo "Usage: $0 <worktree-name> [--keep-branch]"
    echo ""
    echo "Examples:"
    echo "  $0 feature-login-screen          # Remove worktree and branch"
    echo "  $0 feature-login-screen --keep-branch   # Keep the branch"
    echo ""
    echo "Current worktrees:"
    git worktree list | grep -v "$REPO_ROOT " | while read -r line; do
        echo "  $(basename $(echo "$line" | awk '{print $1}'))"
    done
    exit 1
fi

WORKTREE_NAME="$1"
KEEP_BRANCH="$2"
WORKTREE_PATH="$WORKTREE_BASE/$WORKTREE_NAME"

# Derive branch name (same logic as worktree-new.sh)
BRANCH_NAME=$(echo "$WORKTREE_NAME" | sed 's/-/\//' )

cd "$REPO_ROOT"

# Check if worktree exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo -e "${RED}Error: Worktree not found at $WORKTREE_PATH${NC}"
    echo ""
    echo "Available worktrees:"
    git worktree list
    exit 1
fi

# Check for uncommitted changes
cd "$WORKTREE_PATH"
if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
    echo -e "${RED}Warning: Worktree has uncommitted changes!${NC}"
    echo ""
    git status --short
    echo ""
    read -p "Remove anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

cd "$REPO_ROOT"

# Remove the worktree
echo -e "${BLUE}Removing worktree: $WORKTREE_PATH${NC}"
git worktree remove "$WORKTREE_PATH" --force

# Delete the branch unless --keep-branch specified
if [ "$KEEP_BRANCH" != "--keep-branch" ]; then
    echo -e "${BLUE}Deleting branch: $BRANCH_NAME${NC}"
    
    # Check if branch is merged
    if git branch --merged main | grep -q "$BRANCH_NAME"; then
        git branch -d "$BRANCH_NAME" 2>/dev/null || true
    else
        echo -e "${YELLOW}Branch not merged to main. Force delete? (y/N)${NC}"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -D "$BRANCH_NAME" 2>/dev/null || true
        else
            echo -e "${YELLOW}Branch kept: $BRANCH_NAME${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Branch kept: $BRANCH_NAME${NC}"
fi

# Prune stale worktree references
git worktree prune

echo ""
echo -e "${GREEN}✓ Worktree removed successfully!${NC}"
echo ""
echo "Remaining worktrees:"
git worktree list
