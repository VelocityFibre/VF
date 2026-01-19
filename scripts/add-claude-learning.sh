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
