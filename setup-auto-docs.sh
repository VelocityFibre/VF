#!/bin/bash
# Setup automatic documentation syncing (not code) to both servers

echo "🔧 Setting up automatic documentation sync..."

# Create git hook for auto-sync docs
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-sync documentation to both servers after commit
# Code deployments remain manual for safety

BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Only sync on main/develop branches
if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "develop" ]]; then
    echo "📚 Auto-syncing documentation to servers..."

    # Sync docs to VF Server (staging)
    echo "  → VF Server (staging)..."
    scp -q CLAUDE.md docs/*.md louis@100.96.203.105:/srv/data/apps/fibreflow/docs/ 2>/dev/null &

    # Sync docs to Hostinger (production) - docs only!
    echo "  → Hostinger (production docs only)..."
    python3 .claude/skills/hostinger-vps/scripts/sync_docs.py >/dev/null 2>&1 &

    echo "✅ Documentation sync initiated (code remains manual)"
fi
EOF

chmod +x .git/hooks/post-commit

echo "✅ Auto-sync hook installed!"
echo ""
echo "📋 Workflow now configured:"
echo "  1. You commit changes locally"
echo "  2. Docs auto-sync to BOTH servers"
echo "  3. Code deployment remains manual:"
echo "     - VF Server: Test new features first"
echo "     - Hostinger: Deploy after VF testing"
echo ""
echo "🎯 Deploy commands:"
echo "  VF Staging:  ssh louis@100.96.203.105 'cd /srv/data/apps/fibreflow && git pull && npm run build && sudo systemctl restart fibreflow'"
echo "  Hostinger:   ./sync-to-hostinger --code --restart"