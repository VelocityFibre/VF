# VF Agent Workforce

**Multi-Agent AI System for VF Operations**

---

## 🏢 What is VF Agent Workforce?

The **VF Agent Workforce** is a specialized AI system designed for VF's fiber optic infrastructure business operations. It consists of multiple AI agents, each expert in their domain, coordinated by an intelligent orchestrator.

**Project:** VF Operations Management
**Location:** `/home/louisdup/Agents/claude/`
**Status:** Active Development
**Current Agents:** 3 specialized agents

---

## 📊 Current VF Agents

### Infrastructure Operations

**VPS Monitor Agent** (`vps-monitor/`)
- **Purpose:** Monitor VF's Hostinger VPS infrastructure
- **Server:** srv1092611.hstgr.cloud (Lithuania)
- **Capabilities:** CPU, memory, disk, process tracking via SSH
- **Use Cases:** Server health checks, performance monitoring, service status
- **Status:** ✅ Active

### Data Management

**Neon Database Agent** (`neon-database/`)
- **Purpose:** Access VF's Neon PostgreSQL database
- **Database:** Production database with 104 tables
- **Capabilities:** Schema discovery, SQL querying, business intelligence
- **Use Cases:** Project data, contractor info, BOQ/RFQ queries
- **Status:** ✅ Active

**Convex Database Agent** (`convex-database/`)
- **Purpose:** Manage VF's Convex backend
- **Backend:** quixotic-crow-802.convex.cloud
- **Capabilities:** Task management, sync operations, statistics
- **Use Cases:** Task tracking, project management, sync monitoring
- **Status:** ✅ Active

---

## 🎯 VF Agent Workforce Architecture

```
                        VF Operations Team
                              │
                              ▼
                    🧠 Orchestrator (Claude)
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
         Infrastructure   Database     Backend

    🖥️  VPS Monitor    🗄️  Neon DB    📦 Convex

    srv1092611         PostgreSQL    Task Mgmt
    CPU/RAM/Disk      Schema/Query   Sync Ops
    Service Status    BI Analytics   Statistics
```

---

## 🚀 Quick Start

### Check Agent Status
```bash
# View all VF agents
./venv/bin/python3 orchestrator/orchestrator.py

# See visual organization
./venv/bin/python3 orchestrator/organigram.py
cat AGENT_ORGANIGRAM.txt
```

### Use VPS Monitor
```bash
cd agents/vps-monitor
../../venv/bin/python3 demo.py
```

### Query Neon Database
```bash
cd agents/neon-database
../../venv/bin/python3 ../../demo_neon_agent.py
```

### Manage Convex Tasks
```bash
cd agents/convex-database
../../venv/bin/python3 ../../demo_convex_agent.py
```

---

## 📋 VF Agent Registry

All agents are registered in: `orchestrator/registry.json`

Each agent has:
- **ID**: Unique identifier
- **Triggers**: Keywords that route to this agent
- **Capabilities**: What the agent can do
- **Model**: Which Claude model it uses
- **Cost**: Estimated cost per query

---

## 🔑 Environment Variables

VF agents require these credentials in `.env`:

```bash
# Required for all agents
ANTHROPIC_API_KEY=sk-ant-api03-...

# VPS Monitor
VPS_HOSTNAME=srv1092611.hstgr.cloud

# Neon Database
NEON_DATABASE_URL=postgresql://...

# Convex Backend
CONVEX_URL=https://quixotic-crow-802.convex.cloud
```

---

## 📖 Documentation

**Complete Guides:**
- `AGENT_WORKFORCE_GUIDE.md` - Complete system guide
- `AGENT_ORGANIGRAM.txt` - Visual agent structure
- `agents/vps-monitor/README.md` - VPS monitoring guide
- `NEON_AGENT_GUIDE.md` - Neon database guide
- `CONVEX_AGENT_GUIDE.md` - Convex backend guide

**Quick References:**
- `QUICK_REFERENCE.md` - VF operations quick ref
- `PROJECT_SUMMARY.md` - Overall project summary

---

## 🏗️ Adding VF Agents

### Future VF Agents (Roadmap)

**Phase 2: Business Operations**
- Project Management Agent
- Contractor Tracking Agent
- BOQ/RFQ Processing Agent
- Financial Analysis Agent

**Phase 3: Integration**
- SharePoint Sync Agent
- Email/Calendar Agent
- Report Generation Agent

**Phase 4: Specialized**
- Deployment Agent
- Monitoring Alerts Agent
- Documentation Agent

### How to Add New VF Agent

1. **Create agent directory:**
   ```bash
   mkdir -p agents/new-agent
   ```

2. **Implement agent:** Create `agent.py`, `config.json`, `README.md`

3. **Register in orchestrator:**
   - Add entry to `orchestrator/registry.json`
   - Define triggers relevant to VF operations
   - Specify capabilities

4. **Test:**
   ```bash
   ./venv/bin/python3 orchestrator/orchestrator.py
   ```

---

## 🔍 How VF Orchestrator Works

**Example: Infrastructure Query**
```
VF Team: "Is the server running hot?"
    ↓
Orchestrator: Matches "server" → VPS Monitor Agent
    ↓
VPS Agent: SSH into srv1092611, check CPU/temp
    ↓
Response: "Server healthy. CPU: 12%, Temp: Normal"
```

**Example: Business Query**
```
VF Team: "How many active contractors?"
    ↓
Orchestrator: Matches "contractors" → Neon Database Agent
    ↓
Neon Agent: Query contractors table
    ↓
Response: "20 active contractors"
```

---

## 💰 Cost Management

**VF Agent Costs (Estimated):**
- VPS Monitor: ~$0.001/query (Haiku)
- Neon Database: ~$0.001/query (Haiku)
- Convex Backend: ~$0.001/query (Haiku)

**Monthly estimates for VF:**
- Light usage (500 queries): ~$1-2/month
- Medium usage (2000 queries): ~$4-6/month
- Heavy usage (10000 queries): ~$20-30/month

---

## 🎯 VF-Specific Features

**Infrastructure:**
- Real-time monitoring of srv1092611.hstgr.cloud
- Nginx status tracking
- Neon-agent service monitoring
- Network usage tracking

**Business Data:**
- Contractor performance tracking
- Project status queries
- BOQ/RFQ management
- Financial analytics

**Operations:**
- Task management via Convex
- Sync operations monitoring
- Automated health checks

---

## 📊 VF Agent Statistics

**Current Deployment:**
- Total Agents: 3
- Active Agents: 3
- Categories: Infrastructure (1), Database (2)
- Total Tools: 26 across all agents
- Routing Keywords: 28 triggers

**Server Infrastructure:**
- Primary VPS: srv1092611.hstgr.cloud (Lithuania)
- Database: Neon PostgreSQL (104 tables)
- Backend: Convex (quixotic-crow-802)

---

## 🔐 Security Notes

**VF Agent Security:**
- SSH keys stored in `~/.ssh/` (not in repo)
- API keys in `.env` (gitignored)
- Database credentials encrypted
- No secrets in code or git history

**Access Control:**
- VPS: Root access via SSH key
- Neon: Pooled connection with SSL
- Convex: Auth key required
- Anthropic: API key required

---

## 🐛 Troubleshooting

**Agent not responding:**
```bash
# Check orchestrator
./venv/bin/python3 orchestrator/orchestrator.py

# Verify agent exists
ls -la agents/agent-name/

# Check registry
cat orchestrator/registry.json | grep agent-name
```

**VPS connection failed:**
```bash
# Test SSH manually
ssh root@srv1092611.hstgr.cloud

# Check SSH key
ls -la ~/.ssh/id_ed25519

# Run VPS agent demo
cd agents/vps-monitor && ../../venv/bin/python3 demo.py
```

**Database connection error:**
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Test connection
cd agents/neon-database
../../venv/bin/python3 ../../test_neon.py
```

---

## 📞 Support

**For VF team:**
- Check documentation in this directory
- Run orchestrator demo for agent overview
- Review agent-specific READMEs

**Resources:**
- Agent Workforce Guide: `../AGENT_WORKFORCE_GUIDE.md`
- Organigram: `../AGENT_ORGANIGRAM.txt`
- VF Operations: See PROJECT_SUMMARY.md

---

## 🎯 Success Metrics

**VF Agent Performance:**
- ✅ Average response time: 2-5 seconds
- ✅ Routing accuracy: 100% on tested queries
- ✅ Uptime: srv1092611 running 3+ days
- ✅ Database queries: Sub-second execution
- ✅ Cost efficiency: <$0.01 per complex query

---

**VF Agent Workforce - Empowering VF Operations with AI**

*Built with Claude Agent SDK*
*Version 1.0.0 | November 2025*
