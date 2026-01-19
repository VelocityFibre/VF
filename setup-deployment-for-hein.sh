#!/bin/bash
# One-Click Deployment Setup for Hein
# Run this after pulling latest from git

echo "🚀 Setting up deployment tools for Hein..."
echo ""

# Check if we're in claude repo
if [ ! -d ".claude" ]; then
    echo "❌ Error: Not in claude repository!"
    echo "Please run from your Agents/claude directory"
    exit 1
fi

# Check if skill exists
if [ -d ".claude/skills/staging-deploy" ]; then
    echo "✅ Deployment skill found"
else
    echo "⚠️  Deployment skill not found. Pull latest from git first!"
    exit 1
fi

# Create local shortcuts (optional)
echo ""
echo "Would you like to add deployment shortcuts to your shell? (y/n)"
read -p "> " response

if [ "$response" = "y" ]; then
    # Detect shell
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi

    # Add aliases
    echo "" >> $SHELL_RC
    echo "# Staging deployment shortcuts (added by setup script)" >> $SHELL_RC
    echo "alias deploy-staging='ssh hein@100.96.203.105 deploy'" >> $SHELL_RC
    echo "alias staging-status='ssh hein@100.96.203.105 deployment-monitor last'" >> $SHELL_RC
    echo "alias staging-logs='ssh hein@100.96.203.105 deployment-monitor monitor'" >> $SHELL_RC
    echo "alias ds='ssh hein@100.96.203.105 deploy'  # Super short!" >> $SHELL_RC

    echo "✅ Shortcuts added to $SHELL_RC"
    echo "   Run: source $SHELL_RC"
    echo "   Then type: ds (to deploy)"
fi

# Test SSH connection
echo ""
echo "Testing SSH connection to VF Server..."
if ssh -o ConnectTimeout=5 hein@100.96.203.105 'echo "Connected!"' 2>/dev/null; then
    echo "✅ SSH connection works!"

    # Show current deployment status
    echo ""
    echo "Current staging status:"
    ssh hein@100.96.203.105 'deployment-monitor last' 2>/dev/null || echo "Unable to fetch status"
else
    echo "⚠️  SSH connection failed. You may need to:"
    echo "   1. Set up SSH key (see HEIN_SSH_SETUP.md)"
    echo "   2. Use password when prompted"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "=== Quick Reference ==="
echo "Deploy from terminal:     ssh hein@100.96.203.105 deploy"
echo "Deploy from Claude:       'deploy to staging'"
echo "Check status:            ssh hein@100.96.203.105 deployment-monitor"
echo ""
echo "With shortcuts (if added): ds"
echo ""
echo "See HEIN_DEPLOYMENT_SETUP.md for full guide"
echo "======================="