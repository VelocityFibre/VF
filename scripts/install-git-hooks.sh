#!/bin/bash
# Install git hooks for documentation automation
# Run this once after cloning the repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Installing FibreFlow Git Hooks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if in git repo
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Install commit-msg hook
echo "Installing commit-msg hook..."
cat > "$HOOKS_DIR/commit-msg" << 'EOF'
#!/bin/bash
# Git hook: commit-msg
# Validates commit messages follow conventional commits format

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Conventional commit pattern
PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,100}"

# Skip merge commits, revert commits, and Claude Code commits
if echo "$COMMIT_MSG" | grep -qE "^Merge|^Revert|Co-Authored-By: Claude"; then
    exit 0
fi

# Check if commit message follows pattern
if ! echo "$COMMIT_MSG" | grep -qE "$PATTERN"; then
    echo "❌ ERROR: Commit message doesn't follow Conventional Commits format"
    echo ""
    echo "Expected format: <type>(<scope>): <description>"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore"
    echo ""
    echo "Example: feat(agents): Add SharePoint integration agent"
    echo ""
    exit 1
fi

# Suggest documentation based on commit type
FIRST_LINE=$(echo "$COMMIT_MSG" | head -1)

if echo "$FIRST_LINE" | grep -qE "^feat|^fix"; then
    echo "💡 TIP: Consider updating CHANGELOG.md"
fi

exit 0
EOF
chmod +x "$HOOKS_DIR/commit-msg"
echo "✓ commit-msg hook installed"

# Install pre-push hook
echo "Installing pre-push hook..."
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Git hook: pre-push
# Reminds about documentation before pushing

# Check what's being pushed
COMMITS=$(git log @{u}.. --oneline 2>/dev/null)

if [ -z "$COMMITS" ]; then
    exit 0
fi

# Analyze commits
NEEDS_CHANGELOG=false
NEEDS_OPS_LOG=false

while IFS= read -r line; do
    if echo "$line" | grep -qE "feat|fix|perf"; then
        NEEDS_CHANGELOG=true
    fi
    if echo "$line" | grep -qiE "deploy|migration|infra|server"; then
        NEEDS_OPS_LOG=true
    fi
done <<< "$COMMITS"

# Check if docs were updated
CHANGELOG_UPDATED=$(git diff --name-only @{u}.. | grep -c "CHANGELOG.md" || true)
OPS_LOG_UPDATED=$(git diff --name-only @{u}.. | grep -c "OPERATIONS_LOG.md" || true)

# Display warnings
WARNINGS=0

if $NEEDS_CHANGELOG && [ "$CHANGELOG_UPDATED" -eq 0 ]; then
    echo "⚠️  CHANGELOG.md not updated (feat/fix commits detected)"
    WARNINGS=$((WARNINGS + 1))
fi

if $NEEDS_OPS_LOG && [ "$OPS_LOG_UPDATED" -eq 0 ]; then
    echo "⚠️  docs/OPERATIONS_LOG.md not updated (deployment commits detected)"
    WARNINGS=$((WARNINGS + 1))
fi

if [ "$WARNINGS" -gt 0 ]; then
    echo ""
    echo "Continue anyway? [y/N]"
    read -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Push cancelled. Update docs and try again."
        exit 1
    fi
fi

exit 0
EOF
chmod +x "$HOOKS_DIR/pre-push"
echo "✓ pre-push hook installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Git Hooks Installed Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Hooks installed:"
echo "  - commit-msg: Validates conventional commit format"
echo "  - pre-push: Reminds about documentation updates"
echo ""
echo "To test:"
echo "  git commit -m \"test message\"  # Should fail (wrong format)"
echo "  git commit -m \"test: message\"  # Should pass"
echo ""
echo "To bypass (when needed):"
echo "  git commit --no-verify"
echo "  git push --no-verify"
echo ""
