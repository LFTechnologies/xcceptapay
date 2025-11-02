#!/bin/bash

# XcceptaPay - GitHub Push Helper Script
# This script helps you safely push your monorepo to GitHub

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════╗"
echo "║  XcceptaPay GitHub Push Helper     ║"
echo "╚════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check if git is initialized
echo -e "${BLUE}[1/7]${NC} Checking Git repository..."

if [ ! -d .git ]; then
    echo -e "${YELLOW}→${NC} Git not initialized. Initializing..."
    git init
    echo -e "${GREEN}✓${NC} Git repository initialized"
else
    echo -e "${GREEN}✓${NC} Git repository exists"
fi

# Step 2: Security check
echo ""
echo -e "${BLUE}[2/7]${NC} Security check - looking for secrets..."

SECRETS_FOUND=0

# Check if .env is being tracked
if git ls-files 2>/dev/null | grep -q "^\.env$"; then
    echo -e "${RED}✗${NC} ERROR: .env file is being tracked!"
    echo "  Run: git rm --cached .env"
    SECRETS_FOUND=1
fi

# Check for .env in working directory
if [ -f .env ]; then
    # Verify .env is ignored
    if git check-ignore .env > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} .env file exists and is properly ignored"
    else
        echo -e "${RED}✗${NC} ERROR: .env exists but may not be ignored!"
        SECRETS_FOUND=1
    fi
fi

if [ $SECRETS_FOUND -eq 1 ]; then
    echo -e "${RED}✗${NC} Security issues found. Fix them before pushing!"
    exit 1
else
    echo -e "${GREEN}✓${NC} No secrets detected"
fi

# Step 3: Show what will be committed
echo ""
echo -e "${BLUE}[3/7]${NC} Staging files..."

# Add all files
git add .

# Show staged files
STAGED_COUNT=$(git diff --cached --name-only | wc -l)
echo -e "${GREEN}✓${NC} Staged $STAGED_COUNT files"

echo ""
echo "Files to be committed:"
git diff --cached --name-only | head -20
if [ $STAGED_COUNT -gt 20 ]; then
    echo "... and $((STAGED_COUNT - 20)) more files"
fi

# Step 4: Create commit
echo ""
echo -e "${BLUE}[4/7]${NC} Creating commit..."

read -p "Enter commit message (or press Enter for default): " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="feat: initial monorepo setup with full XRPL offline payments stack

- Complete Docker Compose deployment (API, Frontend, MongoDB, Redis, Nginx)
- React + TypeScript web dashboard with real-time monitoring
- Enhanced ESP32 firmware with BLE and PayChannel support
- Kivy mobile wallet with offline claim verification
- Production-ready deployment scripts and documentation
- Comprehensive architecture and API documentation

Built for XRPL Grants submission - enabling offline payments
with cryptographic verification and online settlement."
fi

git commit -m "$COMMIT_MSG"
echo -e "${GREEN}✓${NC} Commit created"

# Step 5: Check/set remote
echo ""
echo -e "${BLUE}[5/7]${NC} Configuring GitHub remote..."

if git remote | grep -q "^origin$"; then
    CURRENT_REMOTE=$(git remote get-url origin)
    echo -e "${YELLOW}→${NC} Remote 'origin' already exists: $CURRENT_REMOTE"
    read -p "Keep this remote? (y/n): " KEEP_REMOTE
    if [[ ! $KEEP_REMOTE =~ ^[Yy]$ ]]; then
        git remote remove origin
        echo "Remote removed. Please add new remote."
    fi
fi

if ! git remote | grep -q "^origin$"; then
    echo ""
    echo "You need to create a GitHub repository first:"
    echo ""
    echo "Option 1 - Using GitHub CLI (recommended):"
    echo -e "  ${BLUE}gh auth login${NC}"
    echo -e "  ${BLUE}gh repo create xcceptapay --private --source=. --remote=origin${NC}"
    echo ""
    echo "Option 2 - Manual setup:"
    echo "  1. Go to https://github.com/new"
    echo "  2. Name: xcceptapay"
    echo "  3. Visibility: Private"
    echo "  4. DO NOT initialize with README"
    echo "  5. Create repository"
    echo ""
    read -p "Enter your GitHub username: " GH_USERNAME
    read -p "Repository name [xcceptapay]: " REPO_NAME
    REPO_NAME=${REPO_NAME:-xcceptapay}

    git remote add origin "https://github.com/$GH_USERNAME/$REPO_NAME.git"
    echo -e "${GREEN}✓${NC} Remote added: https://github.com/$GH_USERNAME/$REPO_NAME.git"
fi

# Step 6: Set main branch
echo ""
echo -e "${BLUE}[6/7]${NC} Setting main branch..."
git branch -M main
echo -e "${GREEN}✓${NC} Branch set to 'main'"

# Step 7: Push to GitHub
echo ""
echo -e "${BLUE}[7/7]${NC} Pushing to GitHub..."

echo ""
echo -e "${YELLOW}⚠${NC}  Final check before push:"
echo "  Repository: $(git remote get-url origin)"
echo "  Branch: main"
echo "  Commits: $(git log --oneline | wc -l)"
echo ""
read -p "Ready to push? (yes/no): " CONFIRM_PUSH

if [ "$CONFIRM_PUSH" == "yes" ]; then
    echo ""
    echo "Pushing to GitHub..."

    if git push -u origin main; then
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Successfully pushed to GitHub! 🚀 ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
        echo ""
        REPO_URL=$(git remote get-url origin | sed 's/\.git$//')
        echo "View your repository:"
        echo -e "  ${BLUE}$REPO_URL${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Verify on GitHub (check for secrets!)"
        echo "  2. Add repository description and topics"
        echo "  3. Review GITHUB_SETUP.md for release creation"
        echo ""
    else
        echo ""
        echo -e "${RED}✗${NC} Push failed!"
        echo ""
        echo "Common issues:"
        echo "  - Authentication: Set up GitHub CLI or Personal Access Token"
        echo "  - Permissions: Check repository permissions"
        echo "  - Network: Verify internet connection"
        echo ""
        echo "See GITHUB_SETUP.md for detailed troubleshooting"
    fi
else
    echo ""
    echo -e "${YELLOW}✗${NC} Push cancelled"
    echo ""
    echo "To push manually:"
    echo -e "  ${BLUE}git push -u origin main${NC}"
fi

echo ""
echo "For more help, see: GITHUB_SETUP.md"
