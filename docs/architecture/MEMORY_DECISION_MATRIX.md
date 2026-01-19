# Memory Decision Matrix

**Quick reference for choosing the right memory system**

---

## Three Memory Approaches

| Approach | Use When | Don't Use When | Example |
|----------|----------|----------------|---------|
| **No Memory** | One-off queries, stateless operations | Need to remember across sessions | "What's the current VPS CPU?" |
| **Domain Memory** | Task state, progress tracking, workflow state | Cross-session learning needed | Agent Harness, Operations agent |
| **Superior Agent Brain** | Semantic search, meta-learning, knowledge sharing | Simple task tracking (overkill) | Multi-agent learning system |

---

## Decision Tree

```
Start Here
    ↓
Is this a one-off query?
    ├─ YES → Use NO MEMORY (stateless agent)
    └─ NO → Continue
              ↓
Does this need to persist across sessions?
    ├─ NO → Use CONVERSATION HISTORY only (BaseAgent default)
    └─ YES → Continue
              ↓
Is this tracking a workflow or task state?
    ├─ YES → Use DOMAIN MEMORY (feature_list.json or state.json)
    └─ NO → Continue
              ↓
Does this need semantic search or learning?
    └─ YES → Use SUPERIOR AGENT BRAIN (vector memory)
```

---

## Detailed Breakdown

### 1. No Memory (Stateless)

**Pattern**: Each query is independent

**Implementation**:
```python
class VPSMonitorAgent(BaseAgent):
    # No state_file parameter
    def __init__(self, api_key):
        super().__init__(api_key)
        # NO self.state_file

    def execute_tool(self, tool_name, tool_input):
        # Fetch fresh data every time
        if tool_name == "check_cpu":
            return ssh_get_cpu_usage()  # Always fresh
```

**Use cases**:
- VPS monitoring (always query current state)
- Database queries (data is in database)
- API calls (data is in external system)
- Status checks
- Data retrieval

**Benefits**:
- ✅ Simple
- ✅ No state management complexity
- ✅ No stale data

**Drawbacks**:
- ❌ No memory of past queries
- ❌ Can't track progress
- ❌ Can't learn from history

---

### 2. Domain Memory (Task State)

**Pattern**: Persistent state that survives across sessions

**Implementation**:

#### A. Harness Pattern (Coding Agents)
```json
// feature_list.json
{
  "features": [
    {"id": 1, "description": "...", "passes": false},
    {"id": 2, "description": "...", "passes": true}
  ]
}
```

```markdown
# claude_progress.md
## Session 15
Completed feature #15: OAuth2 implementation
Next: Feature #16
```

**Artifacts**:
- `feature_list.json` - Test status (single source of truth)
- `claude_progress.md` - Session summaries
- Git commits - Atomic state snapshots

#### B. Manual Agent Pattern (Non-Coding)
```python
class OperationsAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(
            api_key,
            state_file="agents/ops/state.json"  # ← Persistent state
        )

    def initialize_state(self):
        return {
            "incidents": [],
            "sla_tracking": {...}
        }

    def execute_tool(self, tool_name, tool_input):
        # Read state
        incidents = self.get_state("incidents", [])

        # Modify
        incidents.append({...})

        # Save
        self.set_state("incidents", incidents)
        self.save_state()  # ← Persist!
```

**Use cases**:
- Agent Harness (feature_list.json)
- Operations agents (incident tracking)
- Project management (milestone tracking)
- Research agents (hypothesis testing)
- Customer support (ticket history)
- Any multi-step workflow

**Benefits**:
- ✅ Survives agent restarts
- ✅ Clear progress tracking
- ✅ Single source of truth
- ✅ Easy to debug (just read JSON)
- ✅ Works with stateless LLMs

**Drawbacks**:
- ❌ Manual state management
- ❌ No semantic search
- ❌ No cross-agent learning

**Templates**:
- `templates/memory_schemas/operations_agent_state.json`
- `templates/memory_schemas/research_agent_state.json`
- `templates/memory_schemas/project_management_agent_state.json`
- `templates/memory_schemas/customer_support_agent_state.json`

---

### 3. Superior Agent Brain (Cross-Session Learning)

**Pattern**: Vector memory + knowledge graphs + meta-learning

**Implementation**:
```python
from superior_agent_brain import AgentBrain
from memory.vector_memory import VectorMemory
from memory.knowledge_graph import KnowledgeGraph

brain = AgentBrain(
    vector_db=qdrant_client,
    persistent_db=neon_connection,
    agent_id="fiber-ops-001"
)

# Store experience
brain.store_experience(
    context="Fiber cut at Main St",
    action="Dispatched contractor A",
    outcome="Resolved in 2 hours",
    learned="Contractor A is fastest for downtown area"
)

# Retrieve similar experiences
similar = brain.recall_similar("Fiber cut at 5th Ave")
# Returns: Past incidents near downtown with resolution patterns
```

**Components**:
- `memory/vector_memory.py` - Qdrant for semantic search
- `memory/persistent_memory.py` - Neon for long-term storage
- `memory/meta_learner.py` - Performance tracking
- `memory/knowledge_graph.py` - Shared learnings
- `memory/consolidation.py` - Background optimization

**Use cases**:
- Semantic search over past solutions
- Learning from past mistakes
- Sharing knowledge across agents
- Meta-learning (improving over time)
- Complex pattern recognition

**Benefits**:
- ✅ Semantic similarity search
- ✅ Cross-agent learning
- ✅ Improves over time
- ✅ Knowledge graphs
- ✅ Meta-cognition

**Drawbacks**:
- ❌ Complex setup (Qdrant + Neon)
- ❌ Higher cost (vector DB)
- ❌ Overkill for simple state
- ❌ Requires training period

---

## Common Scenarios

### Scenario: VPS Monitoring

**Question**: Agent checks VPS health every 5 minutes. What memory?

**Answer**: **No memory** (stateless)

**Why**: Always query current state. No need to remember past CPU usage (that's in monitoring DB if needed).

```python
class VPSMonitorAgent(BaseAgent):
    # No state_file
    def check_health(self):
        return ssh_get_current_metrics()  # Always fresh
```

---

### Scenario: Building New Agent via Harness

**Question**: Using `/agents/build sharepoint` to create SharePoint agent. What memory?

**Answer**: **Domain memory (Harness pattern)**

**Why**: Harness automatically creates feature_list.json and claude_progress.md for task tracking.

**Artifacts**:
- `harness/runs/sharepoint_20251209/feature_list.json` ← Test status
- `harness/runs/sharepoint_20251209/claude_progress.md` ← Session logs
- Git commits ← Atomic state

**No action needed**: Harness handles it automatically.

---

### Scenario: Operations Agent Tracking Incidents

**Question**: Agent needs to track fiber cuts across days/weeks. What memory?

**Answer**: **Domain memory (Manual pattern with state.json)**

**Why**: Need persistent incident log that survives agent restarts.

```bash
# Use template
cp templates/memory_schemas/operations_agent_state.json agents/fiber-ops/state.json
```

```python
class FiberOpsAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(api_key, state_file="agents/fiber-ops/state.json")

    def initialize_state(self):
        with open("templates/memory_schemas/operations_agent_state.json") as f:
            return json.load(f)
```

---

### Scenario: Agent Learning Best Contractors

**Question**: Agent should remember that "Contractor A is fastest for downtown fiber cuts". What memory?

**Answer**: **Superior Agent Brain (Vector memory)**

**Why**: This is cross-session learning that should be semantically searchable.

```python
brain.store_experience(
    context="Fiber cut in downtown area",
    action="Dispatched Contractor A",
    outcome="Resolved in 2 hours (below 4hr SLA)",
    learned="Contractor A excels at downtown repairs"
)

# Later, for similar incident:
learnings = brain.recall_similar("Fiber cut at Main St (downtown)")
# Returns: "Contractor A excels at downtown repairs"
```

---

### Scenario: Research Agent Testing Hypotheses

**Question**: Research agent testing 10 market hypotheses over 2 weeks. What memory?

**Answer**: **Domain memory (Research template)**

**Why**: Clear workflow state (hypotheses → experiments → evidence), doesn't need semantic search.

```bash
cp templates/memory_schemas/research_agent_state.json agents/market-research/state.json
```

```python
class MarketResearchAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(api_key, state_file="agents/market-research/state.json")

    def add_hypothesis(self, statement):
        hypotheses = self.get_state("hypotheses", [])
        hypotheses.append({
            "id": len(hypotheses) + 1,
            "statement": statement,
            "status": "untested",
            "confidence": "low"
        })
        self.set_state("hypotheses", hypotheses)
        self.save_state()
```

---

### Scenario: Database Query Agent

**Question**: Agent answers database queries. What memory?

**Answer**: **No memory** (stateless)

**Why**: Data is in database. Agent is just a natural language interface.

```python
class NeonDatabaseAgent(BaseAgent):
    # No state_file
    def execute_tool(self, tool_name, tool_input):
        if tool_name == "query":
            return execute_sql(tool_input["query"])  # Query DB directly
```

**Exception**: If you want to track query history for analytics, add domain memory:

```python
class NeonDatabaseAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(api_key, state_file="agents/neon/state.json")

    def initialize_state(self):
        return {"query_history": []}

    def execute_tool(self, tool_name, tool_input):
        result = execute_sql(tool_input["query"])

        # Track query
        history = self.get_state("query_history", [])
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": tool_input["query"],
            "result_count": len(result)
        })
        self.set_state("query_history", history)
        self.save_state()

        return result
```

---

## Can You Combine Memory Systems?

**Yes!** Common pattern:

```
Agent uses:
- Domain memory (state.json) for current task state
- Superior Agent Brain for learning from past tasks
```

**Example**:
```python
class FiberOpsAgent(BaseAgent):
    def __init__(self, api_key):
        # Domain memory for current incidents
        super().__init__(api_key, state_file="agents/fiber-ops/state.json")

        # Superior Agent Brain for learning
        self.brain = AgentBrain(...)

    def execute_tool(self, tool_name, tool_input):
        if tool_name == "dispatch_contractor":
            # 1. Check domain memory for current incident
            incident = self.find_incident(tool_input["incident_id"])

            # 2. Query brain for best contractor
            learnings = self.brain.recall_similar(f"Fiber cut at {incident['location']}")

            # 3. Dispatch based on learnings
            contractor = learnings.best_contractor

            # 4. Update domain memory
            incident["assigned_to"] = contractor
            self.save_state()

            # 5. Store experience in brain
            self.brain.store_experience(
                context=f"Fiber cut at {incident['location']}",
                action=f"Dispatched {contractor}",
                outcome="pending"
            )
```

**When to combine**:
- Need task state tracking (domain memory)
- AND want to learn from past tasks (Superior Agent Brain)

---

## Migration Paths

### From No Memory → Domain Memory

**When**: Agent needs to remember state across sessions

**Steps**:
1. Choose template from `templates/memory_schemas/`
2. Add `state_file` parameter to `__init__()`
3. Override `initialize_state()` to load template
4. Update `execute_tool()` to read/write state
5. Test persistence across agent restarts

---

### From Domain Memory → Superior Agent Brain

**When**: Need semantic search or cross-agent learning

**Steps**:
1. Keep domain memory for task state (don't remove!)
2. Set up Qdrant + Neon databases
3. Initialize AgentBrain in agent's `__init__()`
4. Store experiences after successful operations
5. Query brain before making decisions

---

## Testing Your Memory Choice

**Checklist**:

- [ ] Will agent need to remember across restarts?
  - NO → Consider no memory
  - YES → Continue

- [ ] Is memory just for this session (conversation history)?
  - YES → Use BaseAgent default (no state_file)
  - NO → Continue

- [ ] Is this a clear workflow with steps/tasks?
  - YES → Use domain memory (state.json or feature_list.json)
  - NO → Continue

- [ ] Need semantic search or learning?
  - YES → Use Superior Agent Brain
  - NO → Re-evaluate (might not need memory)

---

## Summary Table

| Memory Type | Storage | Persists? | Searchable? | Use For | Cost |
|-------------|---------|-----------|-------------|---------|------|
| None | N/A | ❌ | ❌ | Stateless queries | Free |
| Conversation History | RAM | ❌ | ❌ | Single session context | Free |
| Domain Memory | JSON files | ✅ | ❌ (manual) | Task state, workflows | Free |
| Superior Agent Brain | Qdrant + Neon | ✅ | ✅ (semantic) | Learning, patterns | $10-30/mo |

---

## Quick Reference Commands

```bash
# Check if agent has domain memory
cat agents/my-agent/agent.py | grep "state_file"

# View agent's current state
cat agents/my-agent/state.json | jq .

# List available memory templates
ls templates/memory_schemas/*.json

# Copy template for new agent
cp templates/memory_schemas/operations_agent_state.json agents/new-agent/state.json

# Test memory persistence
./venv/bin/pytest tests/test_agent_memory.py -v -k "my_agent"
```

---

**Remember**: "The magic is in the memory. Choose the right memory system for the job."
