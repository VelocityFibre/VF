#!/bin/bash
# GitHub Workflow CLI Helpers
# Source this file: source scripts/gh-workflows.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper: Create PR
ff-pr() {
    local title="$1"
    if [ -z "$title" ]; then
        echo -e "${RED}❌ Usage: ff-pr \"PR title\"${NC}"
        return 1
    fi

    echo -e "${GREEN}📝 Creating Pull Request${NC}"

    # Get current branch
    local branch=$(git branch --show-current)
    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        echo -e "${RED}❌ Cannot create PR from main/master branch${NC}"
        return 1
    fi

    # Push branch
    echo "Pushing branch..."
    git push -u origin "$branch" || return 1

    # Create PR using GitHub CLI
    gh pr create --title "$title" --fill

    echo -e "${GREEN}✅ PR created${NC}"
}

# Helper: Daily sync status
ff-sync() {
    echo -e "${GREEN}🔄 Daily Sync Status${NC}"
    echo ""

    # PRs assigned to me
    echo "📋 Pull Requests:"
    gh pr list --assignee @me --limit 5

    echo ""

    # Recent issues
    echo "🐛 Recent Issues:"
    gh issue list --limit 5

    echo ""

    # My recent PRs
    echo "📝 My Recent PRs:"
    gh pr list --author @me --limit 5

    echo ""
    echo -e "${GREEN}✅ Sync complete${NC}"
}

# Helper: Review PR
ff-review() {
    local pr_number="$1"
    if [ -z "$pr_number" ]; then
        echo -e "${RED}❌ Usage: ff-review <PR-number>${NC}"
        return 1
    fi

    echo -e "${GREEN}👀 Reviewing PR #${pr_number}${NC}"

    # Checkout PR
    gh pr checkout "$pr_number"

    # View diff
    gh pr diff "$pr_number"

    # View details
    gh pr view "$pr_number"

    echo ""
    echo "Commands:"
    echo "  gh pr comment $pr_number -b 'Your comment'"
    echo "  gh pr review $pr_number --approve"
    echo "  gh pr review $pr_number --request-changes -b 'Reason'"
}

# Helper: Merge PR
ff-merge() {
    local pr_number="$1"
    if [ -z "$pr_number" ]; then
        echo -e "${RED}❌ Usage: ff-merge <PR-number>${NC}"
        return 1
    fi

    echo -e "${YELLOW}⚠️  Merging PR #${pr_number}${NC}"

    # Show PR details
    gh pr view "$pr_number"

    echo ""
    read -p "Confirm merge? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        return 0
    fi

    # Merge
    gh pr merge "$pr_number" --merge --delete-branch

    echo -e "${GREEN}✅ PR merged${NC}"

    # Switch back to main
    git checkout main
    git pull
}

# Helper: Show all commands
ff-help() {
    echo -e "${GREEN}FibreFlow GitHub Workflow Helpers${NC}"
    echo ""
    echo "Commands:"
    echo "  ff-sync               - Daily status sync (PRs, issues)"
    echo "  ff-pr \"title\"         - Create pull request"
    echo "  ff-review <number>    - Review PR"
    echo "  ff-merge <number>     - Merge PR"
    echo "  ff-help               - Show this help"
    echo ""
    echo "Examples:"
    echo "  ff-pr \"Add contractor approval workflow\""
    echo "  ff-review 42"
    echo "  ff-merge 42"
    echo ""
    echo "Requirements:"
    echo "  - GitHub CLI (gh) installed: https://cli.github.com/"
    echo "  - Authenticated: gh auth login"
}

# Auto-show help on first source
if [ -z "$FF_WORKFLOWS_LOADED" ]; then
    ff-help
    export FF_WORKFLOWS_LOADED=1
fi
