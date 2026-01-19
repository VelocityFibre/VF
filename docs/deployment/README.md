# Deployment Documentation

All server setup, deployment, and infrastructure configuration documentation.

## Server Setup

### VF Server (100.96.203.105) - PRIMARY PRODUCTION
- **[VF_SERVER_PRODUCTION_SETUP.md](VF_SERVER_PRODUCTION_SETUP.md)** - Complete production setup guide
- **[HEIN_CLAUDE_PROMPT_UPDATED.md](HEIN_CLAUDE_PROMPT_UPDATED.md)** - Claude Code prompt for Hein
- **[VF_SERVER_DIRECTORY_STRUCTURE.md](VF_SERVER_DIRECTORY_STRUCTURE.md)** - Directory layout

### Hostinger (Backup Server)
- **[HOSTINGER_DECOMMISSION_PROCEDURE.md](HOSTINGER_DECOMMISSION_PROCEDURE.md)** - Old server decommission

## Service-Specific Deployments

### QFieldCloud
- **[QFIELDCLOUD_MIGRATION_PLAN.md](QFIELDCLOUD_MIGRATION_PLAN.md)** - QFieldCloud migration to VF Server
- **[QFIELD_MONITOR_DEPLOYMENT.md](QFIELD_MONITOR_DEPLOYMENT.md)** - Monitoring setup
- **[QFIELD_WORKER_MONITORING.md](QFIELD_WORKER_MONITORING.md)** - Worker monitoring
- **[QFIELD_SYNC_TROUBLESHOOTING.md](QFIELD_SYNC_TROUBLESHOOTING.md)** - Sync troubleshooting
- **[QFIELD_SUPPORT_SETUP.md](QFIELD_SUPPORT_SETUP.md)** - Support portal setup

### WhatsApp Monitor
- **[WA_MONITOR_SETUP.md](WA_MONITOR_SETUP.md)** - Main WhatsApp sender setup (CRITICAL)
- **[WA_MONITOR_MODULE_DOCUMENTATION.md](WA_MONITOR_MODULE_DOCUMENTATION.md)** - Module docs
- **[WA_DR_QUICKSTART.md](WA_DR_QUICKSTART.md)** - DR monitoring quickstart
- **[WA_FEEDBACK_FIX_DEPLOYMENT.md](WA_FEEDBACK_FIX_DEPLOYMENT.md)** - Feedback fix

### Other Services
- **[VOICE_AGENT_SETUP.md](VOICE_AGENT_SETUP.md)** - Voice agent with Grok API
- **[CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)** - Cloudflare tunnel config

## Authentication & Security
- **[HANDOVER_TO_HEIN_AUTH.md](HANDOVER_TO_HEIN_AUTH.md)** - Clerk auth handover to Hein
- **[HEIN_AUTH_INSTRUCTIONS.md](HEIN_AUTH_INSTRUCTIONS.md)** - Auth instructions
- **[SECURE_COLLABORATION_SETUP.md](SECURE_COLLABORATION_SETUP.md)** - Secure collaboration setup
- **[DOPPLER_SETUP_GUIDE.md](DOPPLER_SETUP_GUIDE.md)** - Doppler secrets management

## CI/CD
- **[GITHUB_ACTIONS_SETUP_INSTRUCTIONS.md](GITHUB_ACTIONS_SETUP_INSTRUCTIONS.md)** - GitHub Actions setup

## Architecture Reference
See parent directory: `../INFRASTRUCTURE_RESILIENCE_STRATEGY.md`

---

**Last Updated**: 2026-01-08
**Source of Truth**: This git repository (local)
**Server Copies**: For reference only - edit local first, then deploy