# Velocity Fibre Agent Workforce

## 🎯 Repository Goal & Focus

**This repository contains the COMPLETE Velocity Fibre ecosystem:**
- Two production applications (FibreFlow & QFieldCloud)
- Full documentation and knowledge base
- AI agent infrastructure and automation
- All operational tools and scripts

**Primary Focus**: Deliver fiber optic infrastructure management through AI-powered automation while maintaining 99%+ uptime on production systems.

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

## 📂 Complete Repository Structure

```
VF/
├── .claude/
│   ├── rules/           # Auto-loaded modular documentation
│   ├── modules/         # Application-specific profiles
│   ├── skills/          # Executable scripts (99% faster than agents)
│   ├── commands/        # Slash commands
│   └── agents/          # Sub-agents for delegation
├── docs/                # COMPLETE documentation (100+ files)
│   ├── architecture/    # System design and decisions
│   ├── deployment/      # Setup and deployment guides
│   ├── guides/          # How-to guides and tutorials
│   ├── api/             # API references
│   └── fixes/           # Bug fixes and solutions
├── api/                 # API implementations
├── dashboard/           # Dashboard UI code
├── inngest_workflows/   # Background task automation
├── convex/              # Real-time database functions
├── agents/              # AI agent implementations
├── orchestrator/        # Agent coordination system
├── harness/             # Agent building framework
├── tests/               # Test suites
├── scripts/             # Operational scripts
└── data/                # System manifests and evaluations
```

## ⚠️ Context Management

Claude automatically loads relevant rules from `.claude/rules/` based on your current task.
For complete documentation, explore the `docs/` directory which contains 100+ guides and references.

## 🔒 Critical Files - Never Delete
- `~/whatsapp-sender/store/whatsapp.db` - WhatsApp session
- `.env` - Environment variables
- `~/.ssh/vf_server_key` - Server SSH key

## 📋 Where to Find Information

| Topic | Location |
|-------|----------|
| **System Architecture** | `docs/architecture/` |
| **Deployment Guides** | `docs/deployment/` |
| **API Documentation** | `docs/api/` and `api/` |
| **How-To Guides** | `docs/guides/` |
| **Bug Fixes** | `docs/fixes/` |
| **Module Details** | `.claude/modules/` |
| **App-Specific Rules** | `.claude/rules/applications/` |
| **Environment Configs** | `.claude/rules/environments/` |
| **Automation Scripts** | `.claude/skills/` |
| **Agent Code** | `agents/` |
| **Dashboard Code** | `dashboard/` |
| **Background Tasks** | `inngest_workflows/` |

## 🎯 Development Focus Areas

1. **Production Stability**: Maintain 99%+ uptime
2. **Token Efficiency**: Use modular documentation (74% reduction achieved)
3. **Clear Separation**: FibreFlow vs QFieldCloud
4. **Documentation First**: Update docs with changes
5. **Test Coverage**: 80%+ for critical paths

---
*This repository contains the COMPLETE VF ecosystem with all knowledge, code, and documentation.*
*Migration Status: Modular structure implemented for 74% token reduction*