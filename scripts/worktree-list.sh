#!/bin/bash
# List all git worktrees with status information
# Usage: ./scripts/worktree-list.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

cd "$REPO_ROOT"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                        Git Worktrees - RightPlace                             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get worktree list
WORKTREES=$(git worktree list --porcelain)

if [ -z "$WORKTREES" ]; then
    echo -e "${YELLOW}No worktrees found.${NC}"
    exit 0
fi

echo -e "${BLUE}Active Worktrees:${NC}"
echo ""

git worktree list | while read -r line; do
    path=$(echo "$line" | awk '{print $1}')
    commit=$(echo "$line" | awk '{print $2}')
    branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
    
    # Check if it's the main worktree
    if [[ "$path" == "$REPO_ROOT" ]]; then
        echo -e "  ${GREEN}● MAIN${NC}"
    else
        echo -e "  ${YELLOW}○ WORKTREE${NC}"
    fi
    
    echo -e "    Path:   ${CYAN}$path${NC}"
    echo -e "    Branch: ${BLUE}$branch${NC}"
    echo -e "    Commit: $commit"
    
    # Show port configuration if .worktree.env exists
    if [ -f "$path/.worktree.env" ]; then
        source "$path/.worktree.env"
        echo -e "    Ports:  Backend=${GREEN}$BACKEND_PORT${NC}, Frontend=${GREEN}$FRONTEND_PORT${NC}"
    else
        echo -e "    Ports:  Backend=${GREEN}8000${NC}, Frontend=${GREEN}5173${NC} (defaults)"
    fi
    
    # Check for uncommitted changes
    if [ -d "$path" ]; then
        cd "$path"
        if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
            echo -e "    Status: ${RED}Has uncommitted changes${NC}"
        else
            echo -e "    Status: ${GREEN}Clean${NC}"
        fi
        cd "$REPO_ROOT"
    fi
    
    echo ""
done

echo -e "${BLUE}Quick Commands:${NC}"
echo ""
echo "  Create new worktree:  ./scripts/worktree-new.sh <name>"
echo "  List port allocations: ./scripts/worktree-ports.sh"
echo "  Remove worktree:      ./scripts/worktree-remove.sh <name>"
echo "  Open in VSCode:       code <path>"
echo "  Clean stale:          git worktree prune"
echo ""
