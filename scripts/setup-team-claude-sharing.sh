#!/bin/bash
# Setup Team Claude Code Configuration Sharing
# Run this to initialize Git-based team collaboration for Claude Code

set -e  # Exit on error

echo "🚀 Setting up Claude Code team sharing..."

# 1. Create .gitignore for personal files
echo "📝 Creating .claude/.gitignore for personal settings..."
cat > .claude/.gitignore << 'EOF'
# Personal settings (don't share)
settings.local.json
settings.local.json.backup
cache/
logs/
*.tmp
*.log

# Personal commands (optional)
commands/personal/

# MCP personal configs
mcp-config-local.json
EOF

# 2. Create settings template for team
echo "📋 Creating settings template..."
if [ -f .claude/settings.local.json ]; then
    # Strip personal data from settings
    cat .claude/settings.local.json | \
        sed 's/"apiKey": ".*"/"apiKey": "YOUR_API_KEY_HERE"/g' | \
        sed 's/"password": ".*"/"password": "YOUR_PASSWORD_HERE"/g' > \
        .claude/settings.template.json
    echo "✅ Created settings.template.json from your current settings"
else
    echo "⚠️  No settings.local.json found, skipping template creation"
fi

# 3. Create initial learnings file
echo "📚 Creating team learnings file..."
if [ ! -f .claude/learnings.md ]; then
    cat > .claude/learnings.md << 'EOF'
# Claude Code Team Learnings

## Format
- **Date**: YYYY-MM-DD
- **Developer**: Name
- **Issue**: What went wrong
- **Solution**: How it was fixed
- **Verification**: How to check it works
- **Added to CLAUDE.md**: Yes/No

## Learnings

### 2026-01-12 - Team
**Issue**: CLAUDE.md too large (10k tokens)
**Solution**: Split into modules under .claude/modules/
**Verification**: Check token count stays under 2.5k
**Added to CLAUDE.md**: Pending

EOF
    echo "✅ Created learnings.md"
fi

# 4. Create module ownership file
echo "📂 Setting up module ownership..."
cat > .claude/modules/_ownership.yaml << 'EOF'
# Module Ownership Registry
# Each module should have a primary maintainer

modules:
  infrastructure:
    description: "Server configs, ports, deployments"
    maintainer: "team"
    last_updated: "2026-01-12"

  qfieldcloud:
    description: "QFieldCloud service documentation"
    maintainer: "team"
    last_updated: "2026-01-12"

  wa-monitor:
    description: "WhatsApp monitoring service"
    maintainer: "team"
    last_updated: "2026-01-12"

  storage-api:
    description: "Storage API service"
    maintainer: "team"
    last_updated: "2026-01-12"

  ocr-service:
    description: "OCR service documentation"
    maintainer: "team"
    last_updated: "2026-01-12"
EOF

# 5. Create verification script
echo "🔍 Creating team verification script..."
cat > .claude/verify.sh << 'EOF'
#!/bin/bash
# Team verification script
# Run this after pulling team changes

case "$1" in
  qfield)
    echo "🔍 Verifying QFieldCloud..."
    curl -s localhost:8082/health 2>/dev/null || echo "❌ QFieldCloud not running"
    ;;

  wa)
    echo "🔍 Verifying WhatsApp..."
    curl -s localhost:8081/status 2>/dev/null || echo "❌ WhatsApp service not running"
    ;;

  storage)
    echo "🔍 Verifying Storage API..."
    curl -s localhost:8091/health 2>/dev/null || echo "❌ Storage API not running"
    ;;

  tests)
    echo "🔍 Running tests..."
    if [ -d tests/ ]; then
        ./venv/bin/pytest tests/ -v --tb=short
    else
        echo "⚠️  No tests directory found"
    fi
    ;;

  all)
    $0 qfield
    $0 wa
    $0 storage
    $0 tests
    ;;

  *)
    echo "Usage: $0 {qfield|wa|storage|tests|all}"
    exit 1
    ;;
esac
EOF

chmod +x .claude/verify.sh

# 6. Create sync script
echo "🔄 Creating sync script..."
cat > scripts/sync-claude-team.sh << 'EOF'
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
EOF

chmod +x scripts/sync-claude-team.sh

# 7. Create contribution script
echo "💡 Creating learning contribution script..."
cat > scripts/add-claude-learning.sh << 'EOF'
#!/bin/bash
# Add a new learning to team knowledge base

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Your learning here\""
    exit 1
fi

DATE=$(date +%Y-%m-%d)
USER=${USER:-$(whoami)}

cat >> .claude/learnings.md << END

### $DATE - $USER
**Learning**: $1
**Added to CLAUDE.md**: No
END

echo "✅ Added learning to .claude/learnings.md"
echo "📤 Don't forget to commit and push!"
EOF

chmod +x scripts/add-claude-learning.sh

# 8. Add to Git
echo "📦 Adding Claude configurations to Git..."
git add .claude/.gitignore
git add .claude/settings.template.json 2>/dev/null
git add .claude/learnings.md
git add .claude/modules/_ownership.yaml
git add .claude/verify.sh
git add .claude/approved-commands.yaml
git add .claude/commands/
git add .claude/agents/
git add .claude/skills/
git add .claude/hooks/
git add .claude/modules/

# Don't add personal settings
git reset .claude/settings.local.json 2>/dev/null
git reset .claude/cache/ 2>/dev/null
git reset .claude/logs/ 2>/dev/null

echo """
✅ Team Claude Code sharing is ready!

Next steps:
1. Review what will be committed:
   git status .claude/

2. Commit the team configurations:
   git commit -m \"claude: Initialize team configuration sharing\"

3. Push to share with team:
   git push origin main

4. Daily sync (add to crontab):
   0 9 * * * $(pwd)/scripts/sync-claude-team.sh

5. Add a learning:
   ./scripts/add-claude-learning.sh \"Your insight here\"

Team benefits:
✓ Shared commands and skills
✓ Consistent configurations
✓ Team learning capture
✓ Module ownership clarity
✓ Verification scripts

Remember: settings.local.json stays private!
"""