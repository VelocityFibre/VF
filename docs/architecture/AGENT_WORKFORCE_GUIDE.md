# Agent Workforce System - Complete Guide

**Multi-Agent Architecture for Specialized AI Tasks**

---

## 🎯 Vision

Build a **workforce of specialized AI agents**, each expert in their domain. You (Claude Code) act as the **orchestrator**, intelligently routing tasks to the right agent and coordinating their work.

**Benefits:**
- ✅ **Context isolation** - Each agent has focused, manageable context
- ✅ **Specialization** - Agents become experts in specific domains
- ✅ **Scalability** - Easy to add new agents without affecting existing ones
- ✅ **Cost efficiency** - Use cheaper models for simpler agents
- ✅ **Maintainability** - Each agent can be updated independently
- ✅ **Discoverability** - Registry makes all agents visible and searchable

---

## 📁 Directory Structure

```
/home/louisdup/Agents/claude/
│
├── agents/                         # All specialized agents
│   ├── vps-monitor/               # Infrastructure monitoring
│   │   ├── agent.py               # Agent implementation
│   │   ├── demo.py                # Demo/test script
│   │   ├── config.json            # Agent metadata
│   │   └── README.md              # Agent documentation
│   │
│   ├── neon-database/             # Neon PostgreSQL agent
│   │   ├── agent.py
│   │   └── ...
│   │
│   ├── convex-database/           # Convex backend agent
│   │   ├── agent.py
│   │   └── ...
│   │
│   └── [future agents...]
│
├── orchestrator/                   # Central coordination
│   ├── registry.json              # Agent catalog (central registry)
│   ├── orchestrator.py            # Task routing logic
│   └── organigram.py              # Visualization generator
│
├── shared/                         # Shared utilities
│   ├── base_agent.py              # Base class for agents
│   └── common_tools.py            # Reusable tools
│
└── [project files...]
```

---

## 🧠 How It Works

### 1. User Makes Request

```
You: "What's the CPU usage on the VPS?"
```

### 2. Orchestrator Analyzes Request

```python
orchestrator = AgentOrchestrator()
routing = orchestrator.route_task("What's the CPU usage on the VPS?")

# Orchestrator finds:
# - Keywords: "cpu", "vps"
# - Best match: vps-monitor agent
# - Confidence: High (2 keyword matches)
```

### 3. Task Routed to Specialized Agent

```
Orchestrator → VPS Monitor Agent
```

### 4. Agent Executes Task

```python
# VPS Monitor Agent:
# 1. SSHs into srv1092611.hstgr.cloud
# 2. Runs: top -bn1 | grep "Cpu(s)"
# 3. Claude AI analyzes output
# 4. Returns: "CPU usage is 12.4% (normal)"
```

### 5. Response Returns Through Orchestrator

```
VPS Monitor Agent → Orchestrator → You → User
```

---

## 📊 Current Workforce

### Infrastructure Agents (1)

**VPS Monitor Agent** (`vps-monitor`)
- Monitors Hostinger VPS via SSH
- Tracks CPU, memory, disk, processes, services
- Real-time health checks
- Model: Claude 3.5 Haiku
- Cost: ~$0.001/query

### Database Agents (2)

**Neon PostgreSQL Agent** (`neon-database`)
- Natural language SQL interface
- Schema discovery and querying
- Business intelligence
- Model: Claude 3 Haiku
- Cost: ~$0.001/query

**Convex Database Agent** (`convex-database`)
- Task management
- Sync operations
- Statistics and reporting
- Model: Claude 3 Haiku
- Cost: ~$0.001/query

---

## 🔑 Agent Registry

The **registry.json** file is the **source of truth** for all agents.

### Registry Structure

```json
{
  "agents": [
    {
      "id": "vps-monitor",
      "name": "VPS Monitor Agent",
      "type": "infrastructure",
      "triggers": ["vps", "server", "cpu", "memory", ...],
      "capabilities": {...},
      "path": "agents/vps-monitor"
    }
  ]
}
```

### Key Fields

- **id**: Unique identifier (kebab-case)
- **name**: Human-readable name
- **type**: Category (infrastructure, database, etc.)
- **triggers**: Keywords that route to this agent
- **capabilities**: What the agent can do
- **path**: Location of agent code

---

## 🎮 Using the Orchestrator

### List All Agents

```python
from orchestrator.orchestrator import AgentOrchestrator

orch = AgentOrchestrator()

# Get all agents
agents = orch.list_agents()
print(f"Total agents: {len(agents)}")

# Get stats
stats = orch.get_agent_stats()
print(stats)
```

### Route a Task

```python
# Automatic routing
result = orch.route_task("Check VPS CPU usage", auto_select=True)

if result['status'] == 'routed':
    agent = result['agent']
    print(f"Task → {agent['agent_name']}")
    print(f"Confidence: {agent['confidence']} matches")
```

### Find Agent by ID

```python
agent = orch.get_agent_by_id("vps-monitor")
print(agent['description'])
```

### Explain Capabilities

```python
explanation = orch.explain_capabilities("vps-monitor")
print(explanation)
```

---

## 🏗️ Adding New Agents

### Step 1: Create Agent Directory

```bash
mkdir -p agents/new-agent
```

### Step 2: Implement Agent

```python
# agents/new-agent/agent.py

class NewAgent:
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"

    def define_tools(self):
        return [...]  # Your tools

    def execute_tool(self, tool_name, tool_input):
        # Tool execution logic
        pass

    def chat(self, user_message: str):
        # Main chat loop
        pass
```

### Step 3: Create Config

```json
// agents/new-agent/config.json
{
  "agent_id": "new-agent",
  "name": "New Agent",
  "description": "What this agent does",
  "type": "category",
  "capabilities": [...],
  "tools": [...]
}
```

### Step 4: Register in Registry

```json
// orchestrator/registry.json
{
  "agents": [
    ...existing agents...,
    {
      "id": "new-agent",
      "name": "New Agent",
      "type": "category",
      "triggers": ["keyword1", "keyword2"],
      "capabilities": {...},
      "path": "agents/new-agent"
    }
  ]
}
```

### Step 5: Update Agent Count

```json
{
  "total_agents": 4,  // Increment
  "agent_categories": {
    "infrastructure": ["vps-monitor"],
    "database": ["neon-database", "convex-database"],
    "category": ["new-agent"]  // Add category
  }
}
```

---

## 🔍 Keyword Routing Logic

The orchestrator uses **keyword matching** to route tasks:

### Example Routing

```
Query: "What's the CPU usage on srv1092611?"

Orchestrator analysis:
- Extracts keywords: "cpu", "srv1092611"
- Checks registry triggers
- Matches:
  - VPS Monitor: 2 matches ("cpu", "srv1092611")
  - No other agents match

Result: Route to VPS Monitor Agent
```

### Adding Good Triggers

**Good triggers** are:
- Specific terms users will say
- Domain-specific jargon
- Common variations
- Tool names
- Resource names

**Example for VPS agent:**
```json
"triggers": [
  "vps", "server", "cpu", "memory", "disk",
  "ssh", "hostinger", "srv1092611",
  "nginx", "process", "monitoring",
  "health check", "performance"
]
```

---

## 🎯 Best Practices

### Agent Design

1. **Single Responsibility** - Each agent does ONE thing well
2. **Clear Boundaries** - Don't overlap with other agents
3. **Good Documentation** - README.md explains use cases
4. **Comprehensive Triggers** - 10-20 keywords minimum
5. **Cost Awareness** - Use appropriate model for task complexity

### Orchestrator Usage

1. **Trust the Routing** - Let orchestrator decide
2. **Handle No Matches** - Have fallback for unmatched queries
3. **Multi-Agent Tasks** - Coordinate when needed
4. **Monitor Performance** - Track which agents are used most

### Registry Management

1. **Keep Updated** - Add agents immediately to registry
2. **Unique IDs** - Use kebab-case, descriptive IDs
3. **Clear Categories** - Group related agents
4. **Version Control** - Git track registry changes

---

## 📈 Scaling Strategy

### Phase 1: Core Agents (✅ Current)
- VPS monitoring
- Database access (Neon, Convex)

### Phase 2: Business Agents
- Project management agent
- Contractor tracking agent
- BOQ/RFQ processing agent
- Financial analysis agent

### Phase 3: Integration Agents
- Email/calendar agent
- Slack/Discord bot agent
- SharePoint sync agent
- Report generation agent

### Phase 4: Specialized Agents
- Code review agent
- Documentation agent
- Testing agent
- Deployment agent

### Target: 20-50 specialized agents

---

## 🔗 Agent Communication

### Current: Sequential
```
User → Orchestrator → Agent A → Orchestrator → User
```

### Future: Multi-Agent Coordination
```
User → Orchestrator
         ├─→ Agent A ─┐
         ├─→ Agent B ─┼─→ Orchestrator → User
         └─→ Agent C ─┘
```

### Example Multi-Agent Task

```
Query: "Generate project report with VPS health and database stats"

Orchestrator:
1. Routes to VPS Monitor → Gets server metrics
2. Routes to Neon Agent → Gets project data
3. Routes to Report Agent → Combines data
4. Returns comprehensive report
```

---

## 🛠️ Troubleshooting

### Agent Not Found

```bash
# Check registry
cat orchestrator/registry.json | grep agent-id

# Verify agent exists
ls -la agents/agent-id/
```

### Wrong Agent Selected

**Fix:** Add more specific triggers to registry

```json
{
  "id": "correct-agent",
  "triggers": [
    ...existing...,
    "specific-term",  // Add this
    "another-keyword"
  ]
}
```

### No Agent Matches

**Options:**
1. Handle with general AI (Claude Code)
2. Create new specialized agent
3. Add triggers to existing agent

---

## 📊 Monitoring & Analytics

### Track Agent Usage

```python
# Add to orchestrator
usage_stats = {
    "vps-monitor": 45,  # queries
    "neon-database": 32,
    "convex-database": 12
}
```

### Cost Tracking

```python
# Calculate monthly costs
total_cost = sum(
    agent['cost_per_query'] * usage_stats[agent['id']]
    for agent in agents
)
```

### Performance Metrics

- Average response time per agent
- Success rate
- User satisfaction
- Error rates

---

## 🎓 Example Workflows

### 1. VPS Health Check

```
User: "Is the server healthy?"
↓
Orchestrator: Matches "server" → VPS Monitor Agent
↓
VPS Agent: SSHs, checks CPU/RAM/disk
↓
Response: "✅ Server healthy. CPU: 12%, RAM: 22%, Disk: 9%"
```

### 2. Database Query

```
User: "How many active contractors?"
↓
Orchestrator: Matches "contractors" → Neon Database Agent
↓
Neon Agent: Runs SQL query
↓
Response: "20 active contractors in the system"
```

### 3. Multi-Step Analysis

```
User: "Compare VPS performance with database load"
↓
Orchestrator: Coordinates 2 agents
├─→ VPS Monitor: Gets server metrics
└─→ Neon Agent: Gets query counts
↓
Orchestrator: Combines results
↓
Response: "Server load is low (12% CPU) despite high DB activity
          (150 queries/min). Performance is optimal."
```

---

## 🚀 Quick Reference

### View Organigram
```bash
./venv/bin/python3 orchestrator/organigram.py
cat AGENT_ORGANIGRAM.txt
```

### Test Orchestrator
```bash
./venv/bin/python3 orchestrator/orchestrator.py
```

### Run Specific Agent
```bash
cd agents/vps-monitor
../../venv/bin/python3 demo.py
```

### Add New Agent
```bash
mkdir -p agents/new-agent
# Create agent.py, config.json, README.md
# Update orchestrator/registry.json
```

---

## 📚 Files Created

```
agents/
  vps-monitor/agent.py          # VPS monitoring agent
  vps-monitor/demo.py            # Interactive demo
  vps-monitor/config.json        # Agent metadata
  vps-monitor/README.md          # Documentation
  neon-database/agent.py         # Neon DB agent
  convex-database/agent.py       # Convex agent

orchestrator/
  registry.json                  # Central agent catalog
  orchestrator.py                # Routing logic
  organigram.py                  # Visualization tool

AGENT_WORKFORCE_GUIDE.md         # This guide
AGENT_ORGANIGRAM.txt             # Visual structure
```

---

## 💡 Key Insights

1. **Separation of Concerns**: Each agent is autonomous and focused
2. **Discoverable**: Registry makes all capabilities visible
3. **Intelligent Routing**: Orchestrator picks the right agent
4. **Scalable Architecture**: Add agents without breaking existing ones
5. **Cost Effective**: Use appropriate models per agent
6. **Context Management**: Each agent maintains its own context
7. **Feedback Loop**: Agents report back through orchestrator

---

## 🎯 Next Steps

1. **Test Current Setup**
   ```bash
   ./venv/bin/python3 orchestrator/orchestrator.py
   ```

2. **Try Routing**
   ```python
   orch = AgentOrchestrator()
   result = orch.route_task("Check CPU usage")
   ```

3. **Plan Next Agents**
   - What tasks do you do frequently?
   - What could be automated?
   - What databases/APIs do you use?

4. **Build Agent Workforce**
   - Add 1-2 agents per week
   - Document as you go
   - Monitor usage patterns

---

**You now have a scalable, intelligent agent workforce!**

The orchestrator (Claude Code) will route tasks to specialized agents,
manage context efficiently, and provide better, faster responses.

---

*Version 1.0.0 | Created: 2025-11-04*
