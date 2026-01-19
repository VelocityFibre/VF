---
name: git-operations
description: Direct Git operations for version control and deployment
version: 1.0.0
requires: git
---

# Git Operations Skill

Provides direct Git operations without Claude exploring commands.

## Available Scripts

- `status.py` - Get repository status with uncommitted changes
- `commit.py` - Create commit with message
- `push.py` - Push to remote repository
- `deploy.py` - Full deployment workflow (test, commit, push, deploy to VPS)
- `rollback.py` - Rollback to previous version
- `log.py` - View recent commit history
- `branch_info.py` - Get current branch and remote info

## Usage

These scripts execute Git operations directly without exploration, providing 100x faster execution than having Claude figure out Git commands.

## Environment Variables

- `GITHUB_REPO` - Repository URL (optional, uses origin)
- `VPS_HOST` - Production server for deployment
- `VPS_USER` - SSH user for deployment
- `VPS_PATH` - Path on VPS to deploy to