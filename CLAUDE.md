# Velocity Fibre Agent Workforce

This repository manages **two production applications** for Velocity Fibre's fiber optic infrastructure operations.

## 🚨 Critical Security Rules

### Server Access
- **DEFAULT**: Use `louis@100.96.203.105` (limited sudo for monitoring)
- **ADMIN**: Use `velo@100.96.203.105` ONLY when explicitly approved
- **SSH Key**: `~/.ssh/vf_server_key`
- **Password (louis)**: VeloBoss@2026 (only for destructive commands)

### Production Safety
- **NEVER** restart services during 08:00-17:00 SAST without approval
- **ALWAYS** test on staging first
- **ALWAYS** ask approval for destructive commands

## 📍 Navigation

### Applications
- **FibreFlow** (Next.js): See `.claude/rules/applications/fibreflow-app.md`
- **QFieldCloud** (Django): See `.claude/rules/applications/qfieldcloud-app.md`

### Environments
- **Production**: See `.claude/rules/environments/production.md`
- **Staging**: See `.claude/rules/environments/staging.md`
- **Development**: See `.claude/rules/environments/development.md`

### Infrastructure
- **Servers**: See `.claude/rules/infrastructure/servers.md`
- **Databases**: See `.claude/rules/infrastructure/databases.md`
- **Services**: See `.claude/rules/infrastructure/services.md`

## 🎯 Quick Reference

### Production URLs
- FibreFlow: https://app.fibreflow.app (port 3000)
- QFieldCloud: https://qfield.fibreflow.app (port 8082)
- Staging: https://vf.fibreflow.app (port 3006)

### Essential Commands
```bash
# Always activate venv first
source venv/bin/activate

# Deploy to production
./sync-to-hostinger --code

# Run tests
./venv/bin/pytest tests/ -v

# Check service status
ssh louis@100.96.203.105 'sudo systemctl status fibreflow'
```

## 📂 Repository Structure

```
VF/
├── .claude/
│   ├── rules/           # Auto-loaded modular documentation
│   ├── modules/         # Application-specific profiles
│   ├── skills/          # Executable scripts (99% faster than agents)
│   ├── commands/        # Slash commands
│   └── agents/          # Sub-agents for delegation
├── documentation/       # Detailed app documentation
├── src/                # Application source code
├── convex/             # Convex real-time database
└── agents/             # AI agents implementation
```

## ⚠️ Context Management

Claude automatically loads relevant rules from `.claude/rules/` based on your current task.
For detailed documentation, see the `documentation/` folder.

## 🔒 Critical Files - Never Delete
- `~/whatsapp-sender/store/whatsapp.db` - WhatsApp session
- `.env` - Environment variables
- `~/.ssh/vf_server_key` - Server SSH key

## 📋 For Detailed Information

This is a minimal CLAUDE.md. All detailed information is modularized:
- Module profiles: `.claude/modules/`
- Application rules: `.claude/rules/applications/`
- Infrastructure: `.claude/rules/infrastructure/`
- Skills documentation: `.claude/skills/*/skill.md`

---
*Migration Status: Using modular documentation structure for 80% token reduction*