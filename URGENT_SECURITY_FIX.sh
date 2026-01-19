#!/bin/bash
# URGENT: Fix exposed credentials in Git
# Run this IMMEDIATELY to secure your systems

set -e

echo "🚨 URGENT SECURITY FIX - Exposed Credentials in Git"
echo "===================================================="
echo ""
echo "⚠️  CRITICAL: Passwords were committed to GitHub!"
echo ""
echo "Exposed credentials:"
echo "- SSH Password: '2025'"
echo "- Database Password: 'npg_aRNLhZc1G2CD'"
echo ""
echo "This script will help you fix the issue."
echo ""
read -p "Have you CHANGED these passwords on your servers? (yes/no): " changed

if [ "$changed" != "yes" ]; then
    echo ""
    echo "❌ STOP! Change these passwords FIRST:"
    echo ""
    echo "1. SSH to VF Server and change password:"
    echo "   ssh velo@100.96.203.105"
    echo "   passwd"
    echo ""
    echo "2. Change Neon database password at:"
    echo "   https://console.neon.tech"
    echo ""
    echo "3. Update your local .env with new passwords"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo ""
echo "Good! Now let's clean Git history..."
echo ""

# Backup current branch
git branch backup-before-security-fix

# Create clean template without secrets
echo "Creating clean settings template..."
cat > .claude/settings.template.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Write(**)",
      "Edit(**)",
      "Bash(pytest:*)",
      "Bash(curl localhost:*/health)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(npm test)",
      "Bash(npm run build)"
    ],
    "deny": [
      "Bash(*rm -rf*)",
      "Bash(*DROP TABLE*)"
    ]
  },
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
      }
    }
  }
}
EOF

# Stage the clean version
git add .claude/settings.template.json
git commit -m "fix(security): Remove exposed credentials from template

- Remove hardcoded passwords
- Create clean template structure
- Credentials should be in environment variables only"

echo ""
echo "✅ Clean template created and committed"
echo ""
echo "Now we need to clean the Git history..."
echo ""
echo "⚠️  WARNING: This will rewrite Git history!"
echo "⚠️  Your teammate will need to re-clone the repo"
echo ""
read -p "Continue with history cleanup? (yes/no): " cleanup

if [ "$cleanup" == "yes" ]; then
    echo "Removing secrets from Git history..."

    # Remove the file from all commits
    git filter-branch --force --index-filter \
        'git rm --cached --ignore-unmatch .claude/settings.template.json 2>/dev/null || true' \
        --prune-empty --tag-name-filter cat -- --all

    # Add back the clean version
    git add .claude/settings.template.json
    git commit -m "fix(security): Add clean template without secrets" || true

    echo ""
    echo "✅ Git history cleaned locally"
    echo ""
    echo "FINAL STEP: Force push to GitHub"
    echo ""
    echo "⚠️  This will overwrite the remote repository!"
    echo "⚠️  Make sure your teammate knows to re-clone!"
    echo ""
    echo "Run these commands manually:"
    echo ""
    echo "  git push origin --force --all"
    echo "  git push origin --force --tags"
    echo ""
    echo "Then notify your teammate to:"
    echo "  rm -rf FF_Claude_SDK_Agent"
    echo "  git clone https://github.com/VelocityFibre/FF_Claude_SDK_Agent.git"
    echo ""
else
    echo ""
    echo "History cleanup skipped."
    echo "Your secrets are still visible in Git history!"
    echo "Run this script again when ready."
fi

echo ""
echo "📝 Security Checklist:"
echo "[ ] Changed VF Server SSH password"
echo "[ ] Changed Neon database password"
echo "[ ] Updated local .env with new passwords"
echo "[ ] Cleaned Git history (if yes above)"
echo "[ ] Force pushed to GitHub"
echo "[ ] Notified teammate to re-clone"
echo ""
echo "Remember: NEVER commit passwords to Git!"
echo "Use environment variables instead."