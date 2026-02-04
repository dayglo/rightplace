#!/bin/bash
# Create a new git worktree for agentic development
# Usage: ./scripts/worktree-new.sh <worktree-name>
# Example: ./scripts/worktree-new.sh feature-login-screen

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
WORKTREE_BASE="/home/george_cairns/code/rightplace-worktrees"

# Source port utilities
source "$SCRIPT_DIR/worktree-ports.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
SEED_DB=false
COPY_DB=false
WORKTREE_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --seed-db)
            SEED_DB=true
            shift
            ;;
        --copy-db)
            COPY_DB=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
        *)
            WORKTREE_NAME="$1"
            shift
            ;;
    esac
done

# Check if name provided
if [ -z "$WORKTREE_NAME" ]; then
    echo -e "${RED}Error: Worktree name required${NC}"
    echo ""
    echo "Usage: $0 <worktree-name> [options]"
    echo ""
    echo "Options:"
    echo "  --seed-db    Create fresh database and seed with HMP Oakwood data"
    echo "  --copy-db    Copy existing database from main worktree"
    echo ""
    echo "Examples:"
    echo "  $0 feature-login-screen              # No database (uses main)"
    echo "  $0 feature-login-screen --seed-db    # Fresh seeded database"
    echo "  $0 feature-login-screen --copy-db    # Copy of main database"
    echo ""
    echo "Naming conventions:"
    echo "  feature-*    New features"
    echo "  bugfix-*     Bug fixes"
    echo "  refactor-*   Code improvements"
    echo "  experiment-* Experimental work"
    echo "  docs-*       Documentation"
    echo "  test-*       Test improvements"
    exit 1
fi
WORKTREE_PATH="$WORKTREE_BASE/$WORKTREE_NAME"

# Derive branch name (convert dashes to slashes for first segment)
# e.g., feature-login-screen -> feature/login-screen
BRANCH_NAME=$(echo "$WORKTREE_NAME" | sed 's/-/\//' )

# Create worktree base directory if it doesn't exist
if [ ! -d "$WORKTREE_BASE" ]; then
    echo -e "${YELLOW}Creating worktree base directory: $WORKTREE_BASE${NC}"
    mkdir -p "$WORKTREE_BASE"
fi

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
    echo -e "${RED}Error: Worktree already exists at $WORKTREE_PATH${NC}"
    echo ""
    echo "To remove it: git worktree remove $WORKTREE_PATH"
    exit 1
fi

# Change to repo root
cd "$REPO_ROOT"

# Fetch latest from origin
echo -e "${BLUE}Fetching latest from origin...${NC}"
git fetch origin

# Create the worktree with a new branch based on main
echo -e "${BLUE}Creating worktree: $WORKTREE_NAME${NC}"
echo -e "${BLUE}Branch: $BRANCH_NAME${NC}"
echo -e "${BLUE}Path: $WORKTREE_PATH${NC}"
echo ""

git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" origin/main

# Copy shared configurations that aren't in git
echo -e "${BLUE}Setting up worktree environment...${NC}"

# Create log directory (gitignored)
mkdir -p "$WORKTREE_PATH/log"

# Create server data directory if needed
mkdir -p "$WORKTREE_PATH/server/data"

# Create .worktree.env with unique port assignments
echo -e "${BLUE}Assigning unique ports...${NC}"
create_worktree_env "$WORKTREE_PATH"

# Source the created env to show the ports
source "$WORKTREE_PATH/.worktree.env"

# Handle database setup
MAIN_VENV="/home/george_cairns/code/rightplace/server/.venv/bin/python"
MAIN_DB="/home/george_cairns/code/rightplace/server/data/prison_rollcall.db"
WT_DB="$WORKTREE_PATH/server/data/prison_rollcall.db"

if [ "$COPY_DB" = true ]; then
    if [ -f "$MAIN_DB" ]; then
        echo -e "${BLUE}Copying database from main worktree...${NC}"
        cp "$MAIN_DB" "$WT_DB"
        echo -e "${GREEN}✓ Database copied${NC}"
    else
        echo -e "${YELLOW}Warning: Main database not found at $MAIN_DB${NC}"
        echo -e "${YELLOW}Run 'python scripts/setup_db.py && python scripts/seed_hmp_oakwood.py' in main first${NC}"
    fi
elif [ "$SEED_DB" = true ]; then
    echo -e "${BLUE}Creating fresh database and seeding with HMP Oakwood data...${NC}"
    cd "$WORKTREE_PATH/server"
    
    # Use the main venv to run the scripts
    if [ -f "$MAIN_VENV" ]; then
        "$MAIN_VENV" scripts/setup_db.py
        "$MAIN_VENV" scripts/seed_hmp_oakwood.py
        echo -e "${GREEN}✓ Database seeded with HMP Oakwood${NC}"
    else
        echo -e "${YELLOW}Warning: Main venv not found. Activate a venv and run manually:${NC}"
        echo "  python scripts/setup_db.py && python scripts/seed_hmp_oakwood.py"
    fi
    cd "$REPO_ROOT"
else
    echo -e "${YELLOW}Note: No database created. Worktree will use shared database from main.${NC}"
    echo -e "${YELLOW}      Use --seed-db or --copy-db for isolated database.${NC}"
fi

echo ""
echo -e "${GREEN}✓ Worktree created successfully!${NC}"
echo ""
echo -e "${YELLOW}Port Assignment:${NC}"
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Open in VSCode:"
echo -e "   ${BLUE}code $WORKTREE_PATH${NC}"
echo ""
echo "2. Set up Python environment (if needed):"
echo "   cd $WORKTREE_PATH/server"
echo "   source /home/george_cairns/code/rightplace/server/.venv/bin/activate"
echo "   # Or create a new venv: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
echo ""
echo "3. Set up Node modules (if working on web-ui):"
echo "   cd $WORKTREE_PATH/web-ui"
echo "   pnpm install"
echo ""
echo "4. Start the project (uses assigned ports):"
echo "   cd $WORKTREE_PATH && ./start-project.sh"
echo ""
echo "5. Start Claude Code in the new VSCode window"
echo ""
echo -e "${YELLOW}When finished:${NC}"
echo "   git worktree remove $WORKTREE_PATH"
echo "   git branch -d $BRANCH_NAME"
