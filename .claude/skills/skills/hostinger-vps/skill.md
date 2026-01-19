---
name: hostinger-vps
version: 1.0.0
description: Deploy and manage FibreFlow on Hostinger VPS production server
author: Claude
created: 2024-12-19
dependencies:
  - sshpass
  - openssh-client
---

# Hostinger VPS Management Skill

Provides deployment and management capabilities for FibreFlow on Hostinger VPS.

## Server Details
- **Host**: 72.60.17.245 (srv1092611.hstgr.cloud)
- **User**: root
- **Port**: 22
- **Purpose**: Public production FibreFlow deployment

## Available Scripts

### deploy.py
Deploy FibreFlow updates to production

### check_status.py
Check FibreFlow production status

### sync_docs.py
Sync documentation to production

## Usage Examples

```bash
# Deploy latest code
.claude/skills/hostinger-vps/scripts/deploy.py

# Check production status
.claude/skills/hostinger-vps/scripts/check_status.py

# Sync documentation only
.claude/skills/hostinger-vps/scripts/sync_docs.py
```

## Security Notes
- Uses environment variable for password (HOSTINGER_PASSWORD)
- Requires SSH access to 72.60.17.245
- Production deployment - use with caution