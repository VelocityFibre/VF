# Control Center Integration Guide

## 🎯 Overview: Your Centralized Mission Control

`/home/louisdup/Agents/claude/` is your **centralized control center** for managing all applications, services, and infrastructure. Think of it as your "single pane of glass" for everything.

## 🏗️ Architecture Pattern

```
┌────────────────────────────────────────┐
│     CONTROL CENTER (Agents/claude)     │
│        Single Source of Truth           │
└────────────────┬───────────────────────┘
                 │
     ┌───────────┼───────────┬──────────┐
     ↓           ↓           ↓          ↓
  FF_React   QFieldCloud   Future    Databases
  (Skill)     (Skill)      Apps     (Skills)
     │           │           │          │
     ↓           ↓           ↓          ↓
[Local/VPS]  [VPS Docker]  [Any]   [Neon/PG]
```

## 📦 How to Add New Applications

### Step 1: Create a Skill Directory

```bash
mkdir -p .claude/skills/[app-name]/scripts
```

### Step 2: Create skill.md Metadata

Create `.claude/skills/[app-name]/skill.md`:

```markdown
---
name: app-name
version: 1.0.0
description: Brief description of the application
author: Your Team
category: application
tags: [relevant, tags, here]
created: YYYY-MM-DD
---

# App Name Management Skill

Description of what this skill manages...

## Features
- List key features

## Quick Usage
```bash
./scripts/status.py
./scripts/deploy.py
```
```

### Step 3: Create Core Management Scripts

Essential scripts every app skill should have:

#### 1. Status Monitor (`scripts/status.py`)
```python
#!/home/louisdup/Agents/claude/venv/bin/python3
"""Check application health and status"""
# - Check if app is running
# - Monitor resources
# - Verify API endpoints
# - Database connectivity
```

#### 2. Deployment Script (`scripts/deploy.py`)
```python
#!/home/louisdup/Agents/claude/venv/bin/python3
"""Deploy updates to application"""
# - Pull from git
# - Build/compile
# - Run migrations
# - Restart services
```

#### 3. Log Viewer (`scripts/logs.py`)
```python
#!/home/louisdup/Agents/claude/venv/bin/python3
"""View and analyze application logs"""
# - View recent logs
# - Search for patterns
# - Analyze errors
# - Export logs
```

#### 4. Database Operations (`scripts/database.py`)
```python
#!/home/louisdup/Agents/claude/venv/bin/python3
"""Database-specific operations"""
# - Query tables
# - Backup/restore
# - Migrations
# - Health checks
```

### Step 4: Make Scripts Executable

```bash
chmod +x .claude/skills/[app-name]/scripts/*.py
```

### Step 5: Test the Skill

```bash
.claude/skills/[app-name]/scripts/status.py --help
```

## 🔄 Daily Workflow from Control Center

### Morning Routine
```bash
cd ~/Agents/claude

# Check all systems
"Show me the status of all my applications"

# Claude will:
- Run ff-react/scripts/status.py
- Run qfieldcloud/scripts/status.py
- Run [other-app]/scripts/status.py
- Provide consolidated report
```

### Deployment Workflow
```bash
# Deploy a specific app
"Deploy the latest QFieldCloud updates"

# Claude will:
1. Check git status
2. Create backup
3. Pull updates
4. Build/migrate
5. Restart services
6. Verify deployment
```

### Troubleshooting Workflow
```bash
# Investigate issues
"Why is FF_React slow?"

# Claude will:
1. Check logs: ff-react/scripts/logs.py --analyze
2. Check resources: ff-react/scripts/status.py
3. Check database: ff-react/scripts/query.py
4. Correlate findings
5. Suggest solutions
```

## 📊 How Claude Maintains Context

### 1. Within a Session
- Reads skill.md files for capabilities
- Checks git history for changes
- Queries real-time status
- Maintains todo lists

### 2. Across Sessions
```yaml
Persistent Context Sources:
- Skills: Auto-discovered capabilities
- Git: Complete history of changes
- Logs: What happened when you were away
- CLAUDE.md: Project-specific instructions
- .env: Configuration state
```

### 3. Memory Systems
- **Domain Memory**: Task-specific state (feature_list.json)
- **Superior Agent Brain**: Cross-session learning
- **Git Commits**: Audit trail of all changes

## 🎯 Best Practices

### 1. Skill Naming Convention
```
.claude/skills/
├── [app-name]/          # Lowercase, hyphenated
│   ├── skill.md         # Metadata and docs
│   └── scripts/         # Executable tools
│       ├── status.py    # Health monitoring
│       ├── deploy.py    # Deployment
│       ├── logs.py      # Log analysis
│       └── [custom].py  # App-specific tools
```

### 2. Script Standards
- Use venv Python: `#!/home/louisdup/Agents/claude/venv/bin/python3`
- Load from .env: `from dotenv import load_dotenv`
- Return exit codes: `sys.exit(0 if success else 1)`
- Provide --help: Use argparse

### 3. Environment Variables
Store in `.env`:
```bash
# App-specific prefixes
FF_REACT_DB_URL=...
QFIELDCLOUD_VPS_HOST=...
[APP_NAME]_CONFIG=...
```

### 4. Error Handling
- Always provide fallbacks
- Log errors clearly
- Return actionable messages
- Maintain idempotency

## 🚀 Advanced Patterns

### Parallel Operations
```python
# Check all apps simultaneously
"Check status of all systems in parallel"

# Claude uses multiple tool calls:
- status checks run concurrently
- Results aggregated
- Faster than sequential
```

### Cross-Skill Coordination
```yaml
Example: Deploy with database backup
1. database-operations skill: Create backup
2. git-operations skill: Pull latest
3. ff-react skill: Deploy application
4. All coordinated from control center
```

### Intelligent Routing
```python
# Orchestrator pattern
"Fix the slow database queries"

# Orchestrator routes to:
- database-operations for query analysis
- ff-react for application logs
- vf-server for server metrics
```

## 📝 Adding QFieldCloud Example

You asked about QFieldCloud - here's what we did:

1. **Created Skill Structure**
   ```
   .claude/skills/qfieldcloud/
   ├── skill.md           # Metadata
   └── scripts/
       ├── status.py      # Docker service monitoring
       ├── deploy.py      # Git pull + docker-compose
       └── logs.py        # Docker logs viewer
   ```

2. **Key Differences from FF_React**
   - QFieldCloud uses Docker Compose (multiple services)
   - Deployed on different VPS (72.61.166.168)
   - Requires docker-specific commands
   - Database is containerized

3. **Integration Points**
   - Both skills use same SSH approach
   - Share environment variable patterns
   - Consistent script interfaces
   - Can be managed together

## 🎬 Your Control Center Commands

### Status Checks
```bash
# Individual apps
.claude/skills/ff-react/scripts/status.py
.claude/skills/qfieldcloud/scripts/status.py

# All apps (via Claude)
"What's the status of all my applications?"
```

### Deployments
```bash
# Deploy specific app
.claude/skills/ff-react/scripts/deploy.py --env production
.claude/skills/qfieldcloud/scripts/deploy.py --branch master

# Deploy everything (via Claude)
"Deploy all pending updates to production"
```

### Troubleshooting
```bash
# View logs
.claude/skills/ff-react/scripts/logs.py --follow
.claude/skills/qfieldcloud/scripts/logs.py --analyze

# Search across all (via Claude)
"Search all logs for timeout errors"
```

## 🔮 Future Growth

As you add more applications:

1. **Each gets a skill** in `.claude/skills/`
2. **Consistent interface** across all skills
3. **Claude learns** the patterns
4. **Automation increases** over time
5. **Context accumulates** making operations smarter

### Next Applications to Add
- VF Velocity Server monitoring
- Database backup automation
- CI/CD pipeline management
- Cost tracking across services
- Security scanning automation

## ✅ Summary

Your control center (`~/Agents/claude/`) is:
- **Centralized**: One place for everything
- **Scalable**: Easy to add new apps
- **Intelligent**: Claude understands it all
- **Automated**: Scripts handle complexity
- **Documented**: Self-describing skills
- **Versioned**: Git tracks everything

This is your **mission control**. Every new service gets a skill here. Claude can see and operate everything. The system gets smarter with use.

## Quick Reference Card

```bash
# Add new app
mkdir -p .claude/skills/new-app/scripts
nano .claude/skills/new-app/skill.md
# Create status.py, deploy.py, logs.py
chmod +x .claude/skills/new-app/scripts/*.py

# Daily operations
cd ~/Agents/claude
"Status of everything"
"Deploy FF_React to production"
"Why is QFieldCloud throwing errors?"
"Backup all databases"

# Claude handles the orchestration
```