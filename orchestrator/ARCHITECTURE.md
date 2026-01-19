# Agent Orchestrator System - Architecture

**Technical Architecture Documentation**

---

## System Overview

The Agent Orchestrator is a lightweight task routing system that coordinates a workforce of specialized AI agents. It uses keyword-based matching to intelligently route user requests to the most appropriate agent.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER / APPLICATION                       │
│         (CLI, API, Web Interface, or Direct Python Import)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ task_description
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT ORCHESTRATOR                           │
│                    (orchestrator.py)                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Routing Engine                                         │    │
│  │  • Analyze task keywords                               │    │
│  │  • Match against agent triggers                        │    │
│  │  • Score confidence                                    │    │
│  │  • Select best agent                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Registry Loader                                        │    │
│  │  • Load registry.json                                  │    │
│  │  • Validate agent metadata                             │    │
│  │  • Cache in memory                                     │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ reads agent catalog
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT REGISTRY                              │
│                     (registry.json)                              │
│                                                                   │
│  {                                                                │
│    "agents": [                                                    │
│      {id, name, triggers, capabilities, path, model},            │
│      ...                                                          │
│    ],                                                             │
│    "categories": {...},                                           │
│    "rules": {...}                                                 │
│  }                                                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ agent definitions
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ INFRASTRUCTURE│    │   DATABASE   │    │ DATA MGMT    │
│   AGENTS      │    │    AGENTS    │    │   AGENTS     │
├──────────────┤    ├──────────────┤    ├──────────────┤
│              │    │              │    │              │
│ VPS Monitor  │    │ Neon DB      │    │ Contractor   │
│              │    │              │    │              │
│              │    │ Convex DB    │    │ Project      │
│              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Component Breakdown

### 1. Orchestrator Core (`orchestrator.py`)

**Responsibilities:**
- Load and validate agent registry
- Parse user task descriptions
- Match tasks to agents using keyword triggers
- Return routing decisions
- Provide agent statistics and capabilities

**Key Classes:**
```python
class AgentOrchestrator:
    - __init__(registry_path)
    - _load_registry()
    - list_agents()
    - get_agent_by_id(agent_id)
    - find_agent_for_task(task_description)
    - route_task(task_description, auto_select)
    - get_agent_stats()
    - explain_capabilities(agent_id)
```

**Dependencies:**
- `json` - Parse registry file
- `pathlib` - File path handling
- `typing` - Type hints

---

### 2. Agent Registry (`registry.json`)

**Responsibilities:**
- Centralized catalog of all agents
- Define agent metadata (triggers, capabilities, paths)
- Track agent categories and relationships
- Maintain orchestration rules

**Schema:**
```json
{
  "registry_version": "1.1.0",
  "last_updated": "YYYY-MM-DD",
  "total_agents": 5,
  "agents": [
    {
      "id": "unique-agent-id",
      "name": "Human-Readable Agent Name",
      "path": "agents/agent-directory",
      "status": "active|inactive",
      "type": "category",
      "description": "What this agent does",
      "triggers": ["keyword1", "keyword2", ...],
      "capabilities": {
        "category": ["capability1", "capability2"]
      },
      "model": "claude-model-id",
      "avg_response_time": "Xs",
      "cost_per_query": "$X"
    }
  ],
  "agent_categories": {
    "category1": ["agent1", "agent2"],
    "category2": ["agent3"]
  },
  "orchestration_rules": {
    "routing_logic": "keyword_match + context_analysis",
    "fallback": "ask_user_for_clarification"
  }
}
```

---

### 3. Specialized Agents (`agents/*/`)

Each agent is independent and has its own:

**Structure:**
```
agents/agent-name/
├── agent.py           # Main agent implementation
├── config.json        # Agent-specific config
├── demo.py            # Demo/test script
└── README.md          # Agent documentation
```

**Agent Interface:**
All agents implement a consistent interface that can be called by:
- Direct Python import
- CLI execution
- API endpoints
- Orchestrator coordination

---

## Data Flow Diagram

### Request Routing Flow

```
Step 1: User Request
┌─────────────────────┐
│ User submits:       │
│ "Check CPU on VPS"  │
└──────────┬──────────┘
           │
           ▼
Step 2: Orchestrator Receives
┌─────────────────────┐
│ route_task()        │
│ task = "Check CPU"  │
└──────────┬──────────┘
           │
           ▼
Step 3: Keyword Analysis
┌─────────────────────────────┐
│ Lowercase: "check cpu vps"  │
│ Extract keywords            │
└──────────┬──────────────────┘
           │
           ▼
Step 4: Registry Matching
┌──────────────────────────────────────┐
│ For each agent in registry:          │
│   For each trigger in agent.triggers:│
│     if trigger in task:               │
│       score += 1                      │
│       matched_keywords.add(trigger)   │
└──────────┬───────────────────────────┘
           │
           ▼
Step 5: Score Results
┌─────────────────────────────────┐
│ vps-monitor: score=2            │
│   keywords: ["cpu", "vps"]      │
│ neon-database: score=0          │
│ convex-database: score=0        │
│                                  │
│ Winner: vps-monitor (highest)   │
└──────────┬──────────────────────┘
           │
           ▼
Step 6: Return Routing Decision
┌─────────────────────────────────┐
│ {                                │
│   status: "routed",              │
│   agent: {                       │
│     agent_id: "vps-monitor",     │
│     agent_name: "VPS Monitor",   │
│     confidence: 2,               │
│     matched_keywords: ["cpu","vps"]│
│   }                              │
│ }                                │
└──────────┬──────────────────────┘
           │
           ▼
Step 7: Agent Execution (by caller)
┌─────────────────────────────────┐
│ Caller invokes vps-monitor      │
│ Agent executes task              │
│ Returns result to user           │
└──────────────────────────────────┘
```

---

## Routing Algorithm Details

### Keyword Matching Logic

```python
def find_agent_for_task(task_description: str) -> List[Match]:
    """
    Keyword-based routing algorithm.

    Time Complexity: O(n * m)
      n = number of agents
      m = average number of triggers per agent

    Space Complexity: O(k)
      k = number of matching agents
    """
    task_lower = task_description.lower()  # O(1)
    matches = []

    for agent in registry['agents']:  # O(n)
        score = 0
        matched_triggers = []

        for trigger in agent['triggers']:  # O(m)
            if trigger.lower() in task_lower:  # O(1) substring check
                score += 1
                matched_triggers.append(trigger)

        if score > 0:
            matches.append({
                "agent_id": agent["id"],
                "confidence": score,
                "matched_keywords": matched_triggers,
                ...
            })

    # Sort by confidence descending
    matches.sort(key=lambda x: x["confidence"], reverse=True)  # O(k log k)

    return matches
```

**Performance Characteristics:**
- **Best case:** O(n) - No matches found
- **Average case:** O(n * m + k log k) - Some matches
- **Worst case:** O(n * m + n log n) - All agents match

**With current scale (5 agents, ~10 triggers each):**
- Routing time: < 1ms
- Highly efficient for current workload

---

## Scalability Considerations

### Current Scale (5 agents)

```
Agents: 5
Triggers per agent: ~10
Total keywords: ~50
Routing time: < 1ms
Memory usage: ~1MB
```

**No optimization needed at this scale.**

---

### Medium Scale (10-20 agents)

**Optimizations to consider:**

1. **Trigger Indexing:**
```python
# Build inverted index: trigger → [agents]
trigger_index = {
    "vps": ["vps-monitor"],
    "cpu": ["vps-monitor"],
    "database": ["neon-database", "convex-database"],
    ...
}

# O(1) lookup instead of O(n*m) scan
matching_agents = set()
for word in task_words:
    matching_agents.update(trigger_index.get(word, []))
```

2. **Compiled Regex:**
```python
# Pre-compile regex patterns for triggers
agent_patterns = {
    "vps-monitor": re.compile(r"\b(vps|server|cpu|memory)\b"),
    ...
}
```

---

### Large Scale (50+ agents)

**Architectural changes to consider:**

1. **ML-Based Routing:**
```
┌─────────────────┐
│ Task Embedding  │
│ (BERT/FastText) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Semantic Search │
│ (Cosine Sim)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Top-K Agents    │
└─────────────────┘
```

2. **Agent Clustering:**
```
┌─────────────────────────────────────┐
│ Infrastructure Cluster              │
│   ├── VPS Monitor                   │
│   ├── Network Monitor               │
│   └── Security Monitor              │
├─────────────────────────────────────┤
│ Database Cluster                    │
│   ├── PostgreSQL                    │
│   ├── MongoDB                       │
│   └── Redis                         │
└─────────────────────────────────────┘
```

3. **Distributed Registry:**
```
┌──────────────┐
│ Agent Cache  │  ← Fast lookup
├──────────────┤
│ Redis/Memcached│
└──────────────┘
       ↑
       │ sync
       │
┌──────────────┐
│ Database     │  ← Persistent storage
├──────────────┤
│ PostgreSQL   │
└──────────────┘
```

---

## Extension Patterns

### Pattern 1: Multi-Agent Coordination

**Use case:** Task requires multiple agents (e.g., compare data across databases)

```
┌─────────────────────────────────────────┐
│ Orchestrator receives complex task      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Identify multiple agents needed:        │
│ - neon-database (source 1)              │
│ - convex-database (source 2)            │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌──────────┐    ┌──────────┐
│ Neon     │    │ Convex   │
│ Agent    │    │ Agent    │
└────┬─────┘    └─────┬────┘
     │                │
     │   results      │
     └────────┬───────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Orchestrator synthesizes results        │
│ Returns unified response                │
└─────────────────────────────────────────┘
```

---

### Pattern 2: Agent Chaining

**Use case:** Output of one agent becomes input to another

```
Task: "Deploy contractor-agent to VPS"
         │
         ▼
┌─────────────────────┐
│ 1. Contractor Agent │  ← Package code
│    (build artifacts)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. VPS Monitor      │  ← Deploy to server
│    (SSH deploy)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Health Check     │  ← Verify deployment
│    (test endpoints) │
└─────────────────────┘
```

---

### Pattern 3: Fallback Chain

**Use case:** Primary agent fails, route to backup

```
Primary Agent
     │
     ├─ Success → Return
     │
     └─ Fail → Try Secondary Agent
              │
              ├─ Success → Return
              │
              └─ Fail → Try Tertiary Agent
                       │
                       ├─ Success → Return
                       │
                       └─ Fail → Return Error
```

---

## Security Considerations

### Current Security Model

**Registry Access:**
- ✅ Read-only access for orchestrator
- ✅ File-based, version controlled
- ⚠️ No encryption (not needed for metadata)

**Agent Invocation:**
- ✅ Orchestrator only suggests agent, doesn't execute
- ✅ Caller controls agent execution
- ✅ Each agent handles its own authentication

**Input Validation:**
- ✅ Task description is just text (no code execution)
- ✅ Agent IDs validated against registry
- ⚠️ No input sanitization (orchestrator is routing only)

---

### Production Security Enhancements

**If deploying as API:**

1. **Authentication:**
```python
@require_auth
def route_task_api(request):
    user = authenticate(request.token)
    if not user.has_permission("use_agents"):
        return 403

    orchestrator = AgentOrchestrator()
    result = orchestrator.route_task(request.task)
    log_usage(user, result)
    return result
```

2. **Rate Limiting:**
```python
@rate_limit(max_requests=100, window=3600)
def route_task_api(request):
    ...
```

3. **Audit Logging:**
```python
def route_task(self, task):
    result = self._do_route(task)
    audit_log.write({
        "timestamp": now(),
        "user": get_current_user(),
        "task": task,
        "agent_selected": result['agent']['agent_id'],
        "success": True
    })
    return result
```

---

## Monitoring & Observability

### Metrics to Track

**Routing Metrics:**
- Routing latency (p50, p95, p99)
- Routing accuracy (correct agent selected?)
- No-match rate (% of tasks with no agent)
- Multi-match rate (% of tasks with multiple agents)

**Agent Metrics:**
- Agent usage frequency
- Agent success/failure rates
- Agent response times
- Agent cost per query

**System Metrics:**
- Registry load time
- Memory usage
- Cache hit rate (if caching added)

---

### Implementation Example

```python
class InstrumentedOrchestrator(AgentOrchestrator):
    def route_task(self, task):
        start = time.time()

        result = super().route_task(task)

        metrics.record({
            "routing_latency_ms": (time.time() - start) * 1000,
            "agent_selected": result.get('agent', {}).get('agent_id'),
            "status": result['status'],
            "confidence": result.get('agent', {}).get('confidence', 0)
        })

        return result
```

---

## Testing Strategy

### Unit Tests

**Test: Registry Loading**
```python
def test_registry_load():
    orchestrator = AgentOrchestrator()
    assert len(orchestrator.list_agents()) == 5
    assert orchestrator.get_agent_by_id("vps-monitor") is not None
```

**Test: Keyword Matching**
```python
def test_vps_keyword_match():
    orchestrator = AgentOrchestrator()
    result = orchestrator.find_agent_for_task("check cpu usage")

    assert len(result) > 0
    assert result[0]['agent_id'] == 'vps-monitor'
    assert 'cpu' in result[0]['matched_keywords']
```

**Test: No Match Handling**
```python
def test_no_match():
    orchestrator = AgentOrchestrator()
    result = orchestrator.route_task("completely unrelated task")

    assert result['status'] == 'no_match'
    assert 'suggestion' in result
```

---

### Integration Tests

**Test: End-to-End Routing**
```python
def test_e2e_routing_to_vps():
    orchestrator = AgentOrchestrator()

    # Route task
    routing = orchestrator.route_task("Check VPS health")
    assert routing['status'] == 'routed'

    # Get agent path
    agent_path = routing['agent']['path']

    # Verify agent exists and is executable
    assert Path(agent_path).exists()
```

---

### Performance Tests

**Test: Routing Latency**
```python
def test_routing_performance():
    orchestrator = AgentOrchestrator()

    start = time.time()
    for _ in range(1000):
        orchestrator.route_task("random task description")
    elapsed = time.time() - start

    avg_latency = elapsed / 1000
    assert avg_latency < 0.001  # < 1ms per routing
```

---

## Version History

- **v1.1.0** (2025-11-04): Added contractor-agent and project-agent
- **v1.0.0** (2025-11-03): Initial release with VPS, Neon, Convex agents

---

## Future Roadmap

### Phase 1: Core Improvements (Q1 2026)
- [ ] Add ML-based semantic routing
- [ ] Implement agent health monitoring
- [ ] Add performance metrics dashboard
- [ ] Create integration test suite

### Phase 2: Multi-Agent Coordination (Q2 2026)
- [ ] Multi-agent task execution
- [ ] Agent chaining workflows
- [ ] Result synthesis across agents
- [ ] Conflict resolution strategies

### Phase 3: Production Hardening (Q3 2026)
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Audit logging
- [ ] API deployment

### Phase 4: Advanced Features (Q4 2026)
- [ ] Agent clustering
- [ ] Distributed registry
- [ ] Auto-scaling agents
- [ ] Agent marketplace

---

**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
**Architecture Version:** 1.1
