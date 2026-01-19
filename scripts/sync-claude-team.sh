#!/bin/bash
# Sync Claude Code team configurations

echo "🔄 Syncing Claude Code team configs..."

# Save personal settings
cp .claude/settings.local.json /tmp/claude-settings-backup.json 2>/dev/null

# Pull latest team changes
echo "📥 Pulling latest team changes..."
git pull origin main

# Show new learnings
if [ -f .claude/learnings.md ]; then
    echo "📚 Recent team learnings:"
    git diff HEAD~1 .claude/learnings.md 2>/dev/null | grep "^+" | grep -v "^+++" | tail -5
fi

# Restore personal settings
if [ -f /tmp/claude-settings-backup.json ]; then
    cp /tmp/claude-settings-backup.json .claude/settings.local.json
    echo "✅ Personal settings preserved"
fi

# Run verification
.claude/verify.sh all

echo "✅ Sync complete!"
