# 📋 Claude Code Prompt for Hein - UPDATED

## ✅ Documents Already Uploaded to VF Server

All documentation is now on the server at: `/home/velo/production-docs/`

## 🚀 Claude Code Prompt (Copy This)

```
I need to set up production services on VF Server (100.96.203.105). The documentation is already uploaded to the server.

Server access:
- SSH: velo@100.96.203.105 (password: 2025)
- Documentation location: /home/velo/production-docs/

First, SSH to the server and read the README:
ssh velo@100.96.203.105
cat /home/velo/production-docs/README_FOR_HEIN.md

Then help me follow the setup guide to:
1. Create production directories at /opt/
2. Deploy FibreFlow production on port 3000
3. Set up QFieldCloud on port 8080
4. Migrate WhatsApp sender from old server (72.60.17.245, root, password: VeloF@2025@@)
5. Configure nginx and PM2

Keep my dev instance (port 3005) and Louis's staging (port 3006) running as-is.

The main setup guide is at: /home/velo/production-docs/VF_SERVER_PRODUCTION_SETUP.md
```

## 📍 What's on the Server

SSH to VF Server and you'll find in `/home/velo/production-docs/`:
- `README_FOR_HEIN.md` - Quick start guide specifically for you
- `VF_SERVER_PRODUCTION_SETUP.md` - Complete setup instructions
- `INFRASTRUCTURE_RESILIENCE_STRATEGY.md` - Why we're doing this
- `CLAUDE.md` - Master reference

## 🎯 One-Line Summary

Tell Hein:
```
SSH to VF Server. Documentation is in /home/velo/production-docs/
Read README_FOR_HEIN.md first. Use the Claude prompt above.
```