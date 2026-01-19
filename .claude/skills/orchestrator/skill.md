---
id: orchestrator
name: Agent Orchestrator
description: Intelligent routing to specialized AI agents. Routes tasks to VPS monitoring, database queries, contractor management, and project tracking agents.
triggers: [orchestrate, route, agent, vps, monitor, database, contractor, project, task, delegate, which agent, help]
estimated_tokens: 800
complexity: moderate
---

# Agent Orchestrator Skill

## Overview

Intelligent orchestration system that routes tasks to specialized agents in the FibreFlow workforce. Analyzes user queries and delegates to the most appropriate agent based on keyword matching and capability scoring.

## Agent Workforce

### Available Agents

1. **VPS Monitor Agent** (`vps-monitor`)
   - Infrastructure monitoring via SSH
   - CPU, memory, disk, process tracking
   - Health checks and performance analysis
   - Triggers: vps, server, cpu, memory, disk, ssh, hostinger

2. **Neon Database Agent** (`neon-database`)
   - Natural language PostgreSQL queries
   - Schema discovery and business intelligence
   - 104 tables for fiber optic operations
   - Triggers: neon, database, sql, query, table, schema

3. **Convex Database Agent** (`convex-database`)
   - Task management backend
   - Real-time sync operations
   - Statistics and reporting
   - Triggers: convex, tasks, backend, sync

4. **Contractor Agent** (`contractor-agent`)
   - Contractor and vendor management
   - Active/inactive status tracking
   - Company information queries
   - Triggers: contractor, vendor, company, supplier

5. **Project Agent** (`project-agent`)
   - Project status and tracking
   - Budget and location management
   - Deployment monitoring
   - Triggers: project, site, deployment, rollout, installation

## Capabilities

### Task Routing
- Keyword-based intelligent matching
- Multi-agent capability detection
- Confidence scoring for route selection
- Fallback suggestions for unclear queries

### Agent Discovery
- List all available agents
- Check agent status (active/inactive)
- Get agent capabilities and triggers
- Performance metrics (response time, cost)

### Orchestration
- Single-agent routing (direct match)
- Multi-agent suggestions (multiple matches)
- Context-aware routing
- Task delegation with parameters

## Tools

All tools are Python scripts in `scripts/` directory.

### route_task
Routes a task to the appropriate agent.

**Usage**:
```bash
./scripts/route_task.py --task "TASK_DESCRIPTION" [--auto-select]
```

**Parameters**:
- `--task`: Natural language task description
- `--auto-select`: Automatically select best match (optional)

**Returns**: Selected agent, confidence score, alternatives

---

### list_agents
List all registered agents and their status.

**Usage**:
```bash
./scripts/list_agents.py [--category CATEGORY]
```

**Parameters**:
- `--category`: Filter by category (infrastructure, database, data_management)

**Returns**: JSON array of agent information

---

### agent_info
Get detailed information about a specific agent.

**Usage**:
```bash
./scripts/agent_info.py --agent AGENT_ID
```

**Parameters**:
- `--agent`: Agent ID (e.g., vps-monitor)

**Returns**: Agent capabilities, triggers, performance metrics

---

### execute_agent
Execute a task through a specific agent.

**Usage**:
```bash
./scripts/execute_agent.py --agent AGENT_ID --query "QUERY"
```

**Parameters**:
- `--agent`: Agent to execute through
- `--query`: Natural language query for the agent

**Returns**: Agent response with results

---

### workforce_stats
Get statistics about the agent workforce.

**Usage**:
```bash
./scripts/workforce_stats.py
```

**Returns**: Total agents, categories, performance metrics

## Workflow Examples

### Example 1: Route a Database Query
```bash
# Find the right agent for a database task
./scripts/route_task.py --task "How many active contractors do we have?"

# Returns: neon-database agent with high confidence
# Execute through the selected agent
./scripts/execute_agent.py --agent neon-database --query "How many active contractors?"
```

### Example 2: Check VPS Health
```bash
# Route infrastructure monitoring task
./scripts/route_task.py --task "Check CPU usage on the server" --auto-select

# Auto-routes to vps-monitor agent and returns agent info
./scripts/execute_agent.py --agent vps-monitor --query "Show CPU and memory usage"
```

### Example 3: Multi-Agent Suggestion
```bash
# Ambiguous query that could match multiple agents
./scripts/route_task.py --task "Show me the data"

# Returns multiple options:
# - neon-database (for database data)
# - convex-database (for task data)
# - contractor-agent (for contractor data)
# User can select the appropriate one
```

### Example 4: Agent Discovery
```bash
# List all available agents
./scripts/list_agents.py

# Get info about a specific agent
./scripts/agent_info.py --agent contractor-agent

# Check workforce statistics
./scripts/workforce_stats.py
```

## Routing Logic

**Keyword Matching Algorithm**:
1. Parse user query into lowercase tokens
2. Match against agent trigger keywords
3. Score based on matched keyword count
4. Sort by confidence (highest first)
5. Return top match or multiple options

**Confidence Levels**:
- **High (3+ matches)**: Auto-route to agent
- **Medium (2 matches)**: Suggest primary with alternatives
- **Low (1 match)**: Present options to user
- **No match**: Suggest manual agent selection

## Performance Notes

- **Routing**: ~5ms (keyword matching only)
- **Agent execution**: Varies by agent (1-5s typical)
- **Skills-based**: 84% less context than full agent loading
- **Connection pooling**: Reuses database connections

## When to Use This Skill

✅ **Use for**:
- Determining which agent to use for a task
- Discovering available capabilities
- Multi-domain queries requiring coordination
- Getting agent performance metrics

❌ **Don't use for**:
- Direct database queries (use database-operations skill)
- Simple file operations (use native tools)
- Tasks you can handle directly

## Context Efficiency

**Progressive Disclosure**:
- This skill.md: ~800 tokens
- Registry data: Loaded only when needed
- Script execution: File system (0 context)
- Results only: ~200-500 tokens typical

**Total context**: ~1000-1300 tokens for routing query

**Optimization**: Registry cached in memory after first load

## Error Handling

All scripts return errors in JSON format:

```json
{
  "error": "No agent found",
  "task": "unknown task description",
  "suggestions": ["Try rephrasing", "List available agents"]
}
```

**Common errors**:
- **No agent match**: Rephrase with specific keywords
- **Agent not active**: Check agent status first
- **Multiple matches**: Be more specific in query
- **Agent execution failed**: Check agent-specific logs

## Integration Points

### FastAPI Endpoint
The orchestrator can be exposed via API:
```python
POST /orchestrator/route
{
  "task": "Query description",
  "auto_select": true,
  "context": {"page": "dashboard"}
}
```

### Direct Python Import
```python
from orchestrator import AgentOrchestrator
orch = AgentOrchestrator()
result = orch.route_task("Check server health")
```

### UI Integration
- Send natural language queries
- Receive routed agent responses
- Show confidence scores and alternatives
- Allow manual agent selection

## Registry Management

**Registry Location**: `orchestrator/registry.json`

**Registry Structure**:
```json
{
  "agents": [
    {
      "id": "agent-id",
      "name": "Agent Name",
      "triggers": ["keyword1", "keyword2"],
      "status": "active",
      "capabilities": {...}
    }
  ]
}
```

**Adding New Agents**:
1. Create agent in `agents/` directory
2. Update `orchestrator/registry.json`
3. Add trigger keywords
4. Test routing with new keywords

## Security

- **Read-only routing**: No data modifications
- **Agent isolation**: Each agent has separate permissions
- **Parameter validation**: Sanitized before passing to agents
- **Audit logging**: All routing decisions logged

## Dependencies

```bash
# Python packages
pip install psycopg2-binary python-dotenv anthropic

# Required environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export NEON_DATABASE_URL="postgresql://..."
export CONVEX_URL="https://..."
```

See `scripts/requirements.txt` for exact versions.

## Maintenance

**Updating routing logic**:
- Edit `scripts/route_task.py` for algorithm changes
- Update trigger keywords in `registry.json`
- Test with sample queries

**Performance monitoring**:
- Track routing accuracy
- Monitor agent response times
- Optimize keyword matching