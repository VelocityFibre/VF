# Agent Orchestrator System

**Multi-Agent Task Routing & Coordination**

---

## What This Does

The Agent Orchestrator is the **central coordinator** for a workforce of specialized AI agents. It analyzes incoming user requests, intelligently routes them to the most appropriate agent based on keywords and capabilities, and coordinates multi-agent tasks when needed.

Think of it as a **smart dispatcher** that knows which expert to call for each type of request.

---

## Quick Start

### See the Orchestrator in Action

```bash
# From the project root
./venv/bin/python3 orchestrator/orchestrator.py
```

This will show:
- All registered agents
- Routing examples
- Agent capabilities
- System statistics

### Use in Your Code

```python
from orchestrator.orchestrator import AgentOrchestrator

# Initialize
orchestrator = AgentOrchestrator()

# Route a task
result = orchestrator.route_task("What's the CPU usage on the VPS?")

# Result shows which agent to use
print(f"Route to: {result['agent']['agent_name']}")
```

---

## How It Works (5-Minute Overview)

### The Routing Process

```
1. User Request
   ↓
2. Orchestrator Analyzes Keywords
   ↓
3. Matches Against Agent Registry
   ↓
4. Returns Best Agent(s)
   ↓
5. Task Executed by Specialized Agent
```

### Example: Infrastructure Query

```
User: "Is the server running hot?"
         ↓
Orchestrator: Detects keywords: "server"
         ↓
Registry Lookup: "server" → VPS Monitor Agent
         ↓
Routing Decision: {
  agent: "vps-monitor",
  confidence: HIGH,
  matched_keywords: ["server"]
}
         ↓
VPS Monitor Agent: Executes task
         ↓
Response: "Server healthy. CPU: 12%, Temp: Normal"
```

---

## Project Structure

```
orchestrator/
├── orchestrator.py          # Main routing logic
├── registry.json           # Agent catalog (source of truth)
├── organigram.py           # Visual agent hierarchy generator
└── README.md               # This file

Related:
../agents/                   # All specialized agents
  ├── vps-monitor/          # Infrastructure agent
  ├── neon-database/        # PostgreSQL agent
  ├── convex-database/      # Convex backend agent
  ├── contractor-agent/     # Contractor management
  └── project-agent/        # Project management
```

---

## Key Concepts

### 1. Agent Registry (`registry.json`)

The **source of truth** for all agents. Each agent is registered with:

```json
{
  "id": "vps-monitor",
  "name": "VPS Monitor Agent",
  "type": "infrastructure",
  "triggers": ["vps", "server", "cpu", "memory"],
  "capabilities": {
    "monitoring": ["cpu", "memory", "disk"],
    "analysis": ["health_check", "performance"]
  },
  "path": "agents/vps-monitor",
  "model": "claude-3-5-haiku-20241022"
}
```

**Why this exists:** Centralized registry allows easy discovery, prevents duplication, and enables dynamic agent loading.

### 2. Keyword-Based Routing

**How it works:**
- Each agent defines "trigger" keywords
- Orchestrator scans user request for these keywords
- Matches are scored by number of keyword hits
- Highest-scoring agent is selected

**Example:**
```python
Task: "Check CPU usage on the VPS"
Keywords detected: ["cpu", "vps"]
Matches:
  - vps-monitor: 2 keyword hits → HIGH confidence
  - neon-database: 0 hits
  - convex-database: 0 hits
Winner: vps-monitor
```

**Why keyword-based:** Simple, fast, explainable, and works well for specialized agents with distinct domains.

### 3. Routing Strategies

**Auto-select (default):**
```python
result = orchestrator.route_task("Check server health", auto_select=True)
# Returns single best agent
```

**Multiple matches (user choice):**
```python
result = orchestrator.route_task("Check database", auto_select=False)
# Returns list of matching agents for user to choose
```

**No matches (fallback):**
```python
result = orchestrator.route_task("Unrelated task")
# Returns: {status: "no_match", suggestion: "..."}
```

### 4. Agent Categories

Agents are organized by functional category:

```json
"agent_categories": {
  "infrastructure": ["vps-monitor"],
  "database": ["neon-database", "convex-database"],
  "data_management": ["contractor-agent", "project-agent"]
}
```

**Why categories:** Enables category-based routing, helps organize growing agent workforce, aids in capability discovery.

---

## Architecture

### System Design

```
                    User / Application
                           │
                           ▼
                ┌──────────────────────┐
                │  AgentOrchestrator   │
                │  (orchestrator.py)   │
                └──────────┬───────────┘
                           │
                    Reads Registry
                           │
                           ▼
                ┌──────────────────────┐
                │   registry.json      │
                │  (Agent Catalog)     │
                └──────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ VPS      │  │ Database │  │ Data Mgmt│
      │ Monitor  │  │ Agents   │  │ Agents   │
      └──────────┘  └──────────┘  └──────────┘
```

### Data Flow: Request Routing

```
1. User submits request
   ↓
2. AgentOrchestrator.route_task(request)
   ↓
3. find_agent_for_task(request)
   - Lowercase request text
   - For each agent in registry:
     - Check if agent triggers appear in request
     - Score each match
   - Sort by confidence (score)
   ↓
4. Return routing decision:
   {
     status: "routed",
     agent: {best match},
     confidence: score,
     matched_keywords: [list]
   }
   ↓
5. Caller invokes selected agent
```

### Module Dependencies

```
orchestrator.py
  ↓ imports
  - json (standard library)
  - pathlib (file path handling)
  - typing (type hints)

orchestrator.py
  ↓ reads
  registry.json (agent catalog)

orchestrator.py
  ← called by
  - CLI applications
  - API endpoints
  - Agent coordination systems
```

---

## Common Tasks

### Task 1: Register a New Agent

1. **Create agent directory and implementation:**
   ```bash
   mkdir -p agents/new-agent
   # Implement agent.py, config.json, etc.
   ```

2. **Add entry to `registry.json`:**
   ```json
   {
     "id": "new-agent",
     "name": "New Agent Name",
     "type": "category",
     "triggers": ["keyword1", "keyword2"],
     "capabilities": {
       "category": ["capability1", "capability2"]
     },
     "path": "agents/new-agent",
     "model": "claude-3-haiku-20240307",
     "status": "active"
   }
   ```

3. **Update agent count and categories:**
   ```json
   "total_agents": 6,  // Increment
   "agent_categories": {
     "category": ["existing-agent", "new-agent"]
   }
   ```

4. **Test routing:**
   ```bash
   ./venv/bin/python3 orchestrator/orchestrator.py
   ```

### Task 2: Find Which Agent Handles a Task

```python
from orchestrator.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
matches = orchestrator.find_agent_for_task("your task description here")

for match in matches:
    print(f"{match['agent_name']}: {match['confidence']} matches")
    print(f"  Keywords: {match['matched_keywords']}")
```

### Task 3: Get Agent Statistics

```python
from orchestrator.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
stats = orchestrator.get_agent_stats()

print(f"Total agents: {stats['total_agents']}")
print(f"Active agents: {stats['active_agents']}")
print(f"By category: {stats['categories']}")
```

### Task 4: View Agent Capabilities

```python
from orchestrator.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
explanation = orchestrator.explain_capabilities("vps-monitor")
print(explanation)
```

### Task 5: Generate Agent Hierarchy Visualization

```bash
./venv/bin/python3 orchestrator/organigram.py
cat AGENT_ORGANIGRAM.txt
```

---

## Key Design Decisions

### Why Keyword-Based Routing (Not ML)?

**Decision:** Use keyword matching instead of ML-based classification

**Context:** Need to route user requests to specialized agents

**Reasoning:**
- **Simplicity:** Keywords are easy to understand and maintain
- **Explainability:** Can show exactly why an agent was selected
- **No training needed:** Works immediately with new agents
- **Low latency:** Instant matching without ML inference overhead
- **Sufficient for current scale:** 5 agents with distinct domains

**Trade-offs:**
- Less sophisticated than ML classification
- Requires manual keyword curation
- May miss semantic similarities
- **Worth it for:** Simplicity, explainability, maintainability at current scale

**Future consideration:** Could add ML layer if agent count exceeds 20+ agents.

---

### Why Centralized Registry?

**Decision:** Single `registry.json` file instead of distributed agent configs

**Context:** Need to track all available agents and their capabilities

**Reasoning:**
- **Single source of truth:** One place to see all agents
- **Easy discovery:** Can list all agents without filesystem traversal
- **Version control friendly:** JSON file tracks changes in git
- **Fast lookups:** Load once, query many times
- **Enables statistics:** Can analyze agent portfolio at a glance

**Trade-offs:**
- Registry can get large with many agents
- Requires manual updates when adding agents
- **Worth it for:** Simplicity and current agent count (< 10)

**Future consideration:** Could move to database if agent count exceeds 50+.

---

### Why Python (Not TypeScript)?

**Decision:** Implement orchestrator in Python despite agents being mixed languages

**Context:** Some agents are Python (VPS monitor, database agents), backend is TypeScript (Convex)

**Reasoning:**
- **Claude SDK native support:** Anthropic's SDK is Python-first
- **Agent implementation:** Most agents use Python for system/DB access
- **Data science friendly:** Easy to add analytics and monitoring
- **Team familiarity:** Python expertise for infrastructure tools

**Trade-offs:**
- Language mismatch with TypeScript backend
- Requires Python runtime in deployment
- **Worth it for:** Claude SDK integration and agent implementation ease

---

## Extension Points

### Adding New Routing Strategies

Current routing is keyword-based. To add new strategies:

**Location:** `orchestrator.py`, method `find_agent_for_task()`

**Example: Add semantic similarity:**
```python
def find_agent_for_task_semantic(self, task_description: str):
    """
    Route based on semantic similarity instead of keywords.
    Uses embeddings to find closest agent match.
    """
    # 1. Generate embedding for task description
    # 2. Compare with agent description embeddings
    # 3. Return highest similarity match
    pass
```

### Adding Multi-Agent Coordination

Current system routes to single agent. To coordinate multiple agents:

**Location:** New method in `orchestrator.py`

**Example:**
```python
def coordinate_multi_agent_task(self, task: str, agents: List[str]):
    """
    Execute task requiring multiple agents.
    Example: "Compare contractor data between Neon and Convex"
    """
    results = {}
    for agent_id in agents:
        # Execute task with each agent
        # Collect results
        # Synthesize response
        pass
    return synthesize_results(results)
```

### Adding Agent Health Monitoring

Track agent availability and performance:

**Location:** New module `orchestrator/health.py`

**Example:**
```python
class AgentHealthMonitor:
    def check_agent_health(self, agent_id: str):
        """Ping agent, check response time, verify availability"""
        pass

    def get_agent_uptime(self, agent_id: str):
        """Track agent availability over time"""
        pass
```

---

## Troubleshooting

### Problem: "No agent found for task"

**Symptom:**
```python
result = orchestrator.route_task("my task")
# Returns: {status: "no_match"}
```

**Causes:**
1. Task description doesn't contain agent trigger keywords
2. No agent registered for this domain
3. Typo in keywords

**Solutions:**
```bash
# List all agent triggers
./venv/bin/python3 orchestrator/orchestrator.py

# Check which keywords exist:
grep -r "triggers" orchestrator/registry.json

# Add new agent or update triggers in registry.json
```

---

### Problem: "Wrong agent selected"

**Symptom:** Task routed to incorrect agent

**Causes:**
1. Keyword overlap between agents
2. Generic keywords matched by multiple agents
3. Task description ambiguous

**Solutions:**
```python
# See all matches, not just top one
result = orchestrator.route_task("task", auto_select=False)
print(result['options'])  # Shows all matching agents

# Update agent triggers in registry.json to be more specific
# Add negative keywords or confidence thresholds
```

---

### Problem: "Registry not found"

**Symptom:**
```
FileNotFoundError: Agent registry not found at orchestrator/registry.json
```

**Causes:**
1. Running from wrong directory
2. Registry file deleted or moved
3. Incorrect path in orchestrator initialization

**Solutions:**
```bash
# Ensure registry exists
ls orchestrator/registry.json

# Run from project root, not orchestrator directory
cd /home/louisdup/Agents/claude/
./venv/bin/python3 orchestrator/orchestrator.py

# Or specify registry path explicitly:
orchestrator = AgentOrchestrator(registry_path="/full/path/to/registry.json")
```

---

### Problem: "Can't add new agent"

**Symptom:** JSON parsing error when updating registry

**Causes:**
1. Invalid JSON syntax
2. Missing comma
3. Incorrect nesting

**Solutions:**
```bash
# Validate JSON syntax
python3 -m json.tool orchestrator/registry.json

# Use JSON linter
# Check for missing commas, brackets, quotes

# Backup before editing
cp orchestrator/registry.json orchestrator/registry.json.backup
```

---

## Testing

### Manual Testing

```bash
# Run orchestrator demo
./venv/bin/python3 orchestrator/orchestrator.py
```

### Integration Testing Example

```python
import pytest
from orchestrator.orchestrator import AgentOrchestrator

def test_vps_routing():
    """Test that VPS-related queries route to VPS monitor"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.route_task("Check CPU usage")
    assert result['status'] == 'routed'
    assert result['agent']['agent_id'] == 'vps-monitor'

def test_database_routing():
    """Test that database queries route to database agents"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.route_task("Query contractors in database")
    assert result['status'] == 'routed'
    assert result['agent']['agent_id'] in ['neon-database', 'convex-database']

def test_no_match():
    """Test handling of unrelated queries"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.route_task("completely unrelated random text")
    assert result['status'] == 'no_match'
```

---

## Performance Considerations

### Current Performance

- **Routing latency:** < 1ms (keyword matching is O(n*m) where n=agents, m=keywords)
- **Memory usage:** ~1MB (registry loaded in memory)
- **Scalability:** Linear with agent count

### Optimization Opportunities

1. **Cache compiled regex patterns** for faster keyword matching
2. **Index triggers** in hash map for O(1) lookup
3. **Lazy load agent details** instead of full registry
4. **Add routing metrics** to identify bottlenecks

### When to Optimize

**Current scale (5 agents):** No optimization needed
**10-20 agents:** Add trigger indexing
**50+ agents:** Consider ML-based routing or agent clustering

---

## API Reference

### AgentOrchestrator Class

#### `__init__(registry_path: str = None)`

Initialize orchestrator with agent registry.

**Parameters:**
- `registry_path` (str, optional): Path to registry.json file. Defaults to `orchestrator/registry.json`

**Raises:**
- `FileNotFoundError`: If registry file doesn't exist
- `ValueError`: If registry JSON is invalid

---

#### `list_agents() → List[Dict[str, Any]]`

Get list of all registered agents.

**Returns:**
- List of agent information dictionaries

**Example:**
```python
agents = orchestrator.list_agents()
for agent in agents:
    print(f"{agent['name']}: {agent['description']}")
```

---

#### `get_agent_by_id(agent_id: str) → Optional[Dict[str, Any]]`

Get agent information by ID.

**Parameters:**
- `agent_id` (str): Agent identifier (e.g., 'vps-monitor')

**Returns:**
- Agent info dictionary or None if not found

**Example:**
```python
agent = orchestrator.get_agent_by_id('vps-monitor')
if agent:
    print(f"Found: {agent['name']}")
```

---

#### `find_agent_for_task(task_description: str) → List[Dict[str, str]]`

Find best agent(s) for a given task based on keywords.

**Parameters:**
- `task_description` (str): User's task/question description

**Returns:**
- List of matching agents with confidence scores, sorted by confidence

**Example:**
```python
matches = orchestrator.find_agent_for_task("Check server CPU")
for match in matches:
    print(f"{match['agent_name']}: {match['confidence']} keyword matches")
```

---

#### `route_task(task_description: str, auto_select: bool = False) → Dict[str, Any]`

Route a task to the appropriate agent.

**Parameters:**
- `task_description` (str): User's task description
- `auto_select` (bool): If True, automatically select best agent. If False, return options.

**Returns:**
- Routing decision with agent info and confidence

**Return Types:**
```python
# Single match or auto_select=True:
{
  "status": "routed",
  "agent": {...},
  "alternatives": [...]
}

# Multiple matches with auto_select=False:
{
  "status": "multiple_matches",
  "message": "...",
  "options": [...]
}

# No matches:
{
  "status": "no_match",
  "message": "...",
  "suggestion": "..."
}
```

---

#### `get_agent_stats() → Dict[str, Any]`

Get statistics about the agent workforce.

**Returns:**
- Dictionary with total agents, active agents, categories, and types

**Example:**
```python
stats = orchestrator.get_agent_stats()
print(f"Total: {stats['total_agents']}")
print(f"Active: {stats['active_agents']}")
```

---

#### `explain_capabilities(agent_id: str) → str`

Generate human-readable explanation of agent capabilities.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
- Formatted explanation string with agent details, capabilities, triggers, and performance info

---

## Related Documentation

- **Agent Workforce Guide:** `../AGENT_WORKFORCE_GUIDE.md` - Complete guide to multi-agent architecture
- **Individual Agents:**
  - VPS Monitor: `../agents/vps-monitor/README.md`
  - Neon Database: `../NEON_AGENT_GUIDE.md`
  - Convex Database: `../CONVEX_AGENT_GUIDE.md`
- **Skills System:** `../AGENT_SKILLS_GUIDE.md` - How to create and use Claude skills

---

## Version History

- **v1.1.0** (2025-11-04): Added contractor-agent and project-agent
- **v1.0.0** (2025-11-03): Initial release with 3 agents (VPS, Neon, Convex)

---

## Contributing

### Adding New Agents

1. Create agent in `agents/your-agent/`
2. Update `registry.json` with agent entry
3. Test routing with `orchestrator.py`
4. Update this README if architecture changes

### Improving Routing

1. Analyze routing accuracy metrics
2. Update trigger keywords in `registry.json`
3. Consider adding new routing strategies
4. Document changes in this README

---

**Built with:** Python 3.13, Claude Agent SDK
**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
