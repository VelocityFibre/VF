#!/bin/bash
# Display workflow reminder banner
# Source this in ~/.bashrc or run manually

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║             📋 FIBREFLOW DEVELOPMENT WORKFLOW                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ✅ BEFORE CODING: cat .claude/modules/{module-name}.md       ║
║  ✅ BEFORE DEPLOY: ./sync-to-hostinger --code                 ║
║                                                                ║
║  Optional Tools:                                              ║
║  • /tdd spec <feature>  - Test-driven development             ║
║  • ff-pr "title"        - Create pull request                 ║
║  • ff-sync              - Check PRs/issues                    ║
║                                                                ║
║  📖 Full Guide: docs/NEW_DEVELOPMENT_WORKFLOW.md              ║
╚════════════════════════════════════════════════════════════════╝
EOF
