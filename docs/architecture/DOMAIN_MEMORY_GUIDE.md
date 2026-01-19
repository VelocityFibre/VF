# Domain Memory Guide

**The Foundation of Long-Running Agents**

Based on Anthropic's insights: *"The magic is in the memory. The magic is in the harness. The magic is not in the personality layer."*

---

## The Problem with Generalized Agents

**Generalized agents are amnesiacs with tool belts.** They:
- Start each session with no memory of previous work
- Rederive their own definition of "done" every run
- Guess what happened previously (usually wrong)
- Can't maintain consistent progress across sessions

**This fails because**: LLMs don't have persistent memory. Each API call is stateless.

---

## The Solution: Domain Memory as Primary Interface

**Domain memory** = Persistent, structured representation of work state that survives across agent sessions.

### Core Principle

> The agent is a **policy** that transforms one consistent memory state into another.
>
> Memory is the scaffolding. The agent plays its part on that stage.

---

## FibreFlow's Two Memory Systems

### 1. Harness Domain Memory (Task-Level State)

**Purpose**: Track progress within a single agent-building session or long-running task

**Artifacts**:
- `feature_list.json` - Machine-readable backlog with pass/fail status
- `claude_progress.md` - Human-readable session summaries
- Git commits - Atomic state snapshots
- Test results - Source of truth for "is it working?"

**Use when**: Building agents via harness, implementing multi-step features, ensuring task completion

**Pattern**:
```
Session 1 (Initializer):
  User Prompt → feature_list.json (50-100 test cases, all failing)
                 ↓
                 claude_progress.md (initial plan)
                 ↓
                 Git commit (scaffolding)

Session 2-N (Coding Agents):
  Read feature_list.json → Pick next failing feature
                         ↓
                     Implement + Test
                         ↓
                     Update feature_list.json (pass/fail)
                         ↓
                     Update claude_progress.md
                         ↓
                     Git commit
                         ↓
                     Session ends (agent forgets everything)
                         ↓
  Next session reads memory artifacts and continues
```

**Key Insight**: Each coding agent session is **stateless**. Memory lives in files, not in the agent's context.

---

### 2. Superior Agent Brain (Cross-Session Learning)

**Purpose**: Agents learn patterns, share knowledge, improve over time across different tasks

**Components** (`memory/` directory):
- `vector_memory.py` - Qdrant-based semantic/episodic memory
- `persistent_memory.py` - Neon PostgreSQL for long-term storage
- `meta_learner.py` - Performance tracking and improvement
- `knowledge_graph.py` - Shared learning across agents
- `consolidation.py` - Background memory optimization

**Use when**:
- Need semantic similarity search (find related past solutions)
- Want agents to improve over time (meta-learning)
- Building sophisticated multi-session assistants
- Sharing knowledge across multiple agents

**Pattern**:
```
Agent A completes Task X → Stores experience in vector memory
                        ↓
                   Knowledge graph updated
                        ↓
Agent B encounters similar Task Y → Retrieves Agent A's learnings
                                  ↓
                              Applies patterns, completes faster
```

**Warning**: Don't use Superior Agent Brain for simple task tracking. It's overkill.

---

## When to Use Which Memory System

| Scenario | Use Harness Domain Memory | Use Superior Agent Brain |
|----------|---------------------------|--------------------------|
| Building new agent via harness | ✅ **YES** | ❌ No |
| Multi-step feature implementation | ✅ **YES** | ❌ No |
| Long-running task with clear test cases | ✅ **YES** | ❌ No |
| Agent needs to learn from past interactions | ❌ No | ✅ **YES** |
| Sharing knowledge across agents | ❌ No | ✅ **YES** |
| Semantic search over past solutions | ❌ No | ✅ **YES** |
| Simple one-off query | ❌ No | ❌ No |

---

## Design Principles for Domain Memory

### 1. Externalize the Goal

❌ **Bad**: "Build a SharePoint agent"
✅ **Good**:
```json
{
  "feature_id": 15,
  "description": "Implement upload_file_to_sharepoint tool",
  "validation_steps": [
    "Check tool in define_tools()",
    "Test tool execution",
    "Verify OAuth2 authentication",
    "Run integration test"
  ],
  "passes": false
}
```

Turn vague instructions into **machine-readable backlogs** with pass/fail criteria.

---

### 2. Make Progress Atomic and Observable

Each session should:
1. Pick **one** failing feature
2. Implement it
3. Test it end-to-end
4. Update memory state (pass/fail)
5. Commit to git

**Why atomic?** If a session fails mid-way, you can resume without losing progress.

---

### 3. Enforce Clean State

Every run ends with:
- ✅ All tests passing
- ✅ Memory updated (feature_list.json, progress.md)
- ✅ Git commit with clear message
- ✅ Human-readable summary

**Never leave the campsite dirtier than you found it.**

---

### 4. Standardize Bootup Ritual

Every coding agent session MUST:
```python
def bootup_ritual():
    # 1. Orient - Read memory
    feature_list = read_json("feature_list.json")
    progress = read_file("claude_progress.md")
    recent_commits = git_log(limit=5)

    # 2. Validate - Run basic checks
    run_tests(filter="unit")  # Make sure nothing broke

    # 3. Choose - Pick next task
    next_feature = get_next_failing_feature(feature_list)

    # 4. Act - Implement feature
    implement_feature(next_feature)

    # 5. Validate - Test end-to-end
    validate_feature(next_feature)

    # 6. Update - Mark complete
    update_feature_list(next_feature, passes=True)
    update_progress_md(f"Session N: Completed feature {next_feature.id}")

    # 7. Commit - Snapshot state
    git_commit(f"feat: {next_feature.description}")
```

**Why ritualize?** Because the agent forgets everything after the session. The ritual is embedded in prompts.

---

### 5. Keep Tests Close to Memory

`feature_list.json` should be the **single source of truth** for:
- What features exist
- Which ones pass/fail
- What "passing" means (validation steps)

Don't have separate tracking in:
- Google Sheets
- Notion
- GitHub Issues
- Slack messages

**Memory lives in the codebase, next to the code.**

---

## Domain Memory Schemas for Non-Coding Tasks

The harness pattern works beyond coding. You just need domain-specific memory schemas.

### Research Agent Memory Schema

```json
{
  "research_project": "Market analysis for fiber optics in South Africa",
  "hypotheses": [
    {
      "id": 1,
      "statement": "SMB market is underserved in rural areas",
      "status": "testing",
      "evidence": [],
      "confidence": "low"
    }
  ],
  "experiments": [
    {
      "id": 1,
      "hypothesis_id": 1,
      "description": "Survey 50 SMBs in rural Western Cape",
      "status": "completed",
      "results": {...}
    }
  ],
  "decision_journal": [
    {
      "date": "2025-12-09",
      "decision": "Focus on Western Cape first",
      "reasoning": "Highest concentration of underserved SMBs",
      "outcome": "pending"
    }
  ]
}
```

### Operations Agent Memory Schema

```json
{
  "runbook": "VPS incident response",
  "incidents": [
    {
      "id": "INC-001",
      "timestamp": "2025-12-09T14:30:00Z",
      "severity": "high",
      "description": "CPU at 98% on srv1092611",
      "status": "resolved",
      "timeline": [
        {"time": "14:30", "action": "Detected high CPU", "actor": "vps-monitor-agent"},
        {"time": "14:32", "action": "Killed runaway process", "actor": "vps-monitor-agent"},
        {"time": "14:35", "action": "CPU normalized", "actor": "vps-monitor-agent"}
      ]
    }
  ],
  "sla_tracking": {
    "response_time_target": "5 minutes",
    "resolution_time_target": "30 minutes",
    "met_this_month": 15,
    "missed_this_month": 2
  }
}
```

### Project Management Agent Memory Schema

```json
{
  "project": "Fiber deployment - Stellenbosch",
  "milestones": [
    {
      "id": 1,
      "name": "Site survey complete",
      "status": "done",
      "completion_date": "2025-11-15"
    },
    {
      "id": 2,
      "name": "Trenching complete",
      "status": "in_progress",
      "progress_pct": 45,
      "blockers": ["Weather delays", "Permit issues"]
    }
  ],
  "risks": [
    {
      "id": 1,
      "description": "Permit approval delayed",
      "impact": "high",
      "probability": "medium",
      "mitigation": "Escalate to municipality contact"
    }
  ]
}
```

---

## Implementing Domain Memory in Your Agents

### For Harness-Built Agents

Domain memory is **automatically** implemented via:
- `harness/prompts/initializer.md` - Generates feature_list.json
- `harness/prompts/coding_agent.md` - Enforces bootup ritual
- `harness/config.json` - Configures memory artifacts

**You just need to**:
1. Write a good app spec (`harness/specs/[agent]_spec.md`)
2. Run `/agents/build [agent-name]`
3. Let harness generate memory scaffolding

### For Manual Agent Development

If you're NOT using the harness:

1. **Create domain memory files manually**:
```bash
# For a research agent
cat > agents/research-agent/research_state.json <<EOF
{
  "hypotheses": [],
  "experiments": [],
  "decision_journal": []
}
EOF
```

2. **Implement bootup ritual in agent code**:
```python
class ResearchAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = self.load_state()

    def load_state(self):
        """Read domain memory from disk"""
        with open("research_state.json") as f:
            return json.load(f)

    def save_state(self):
        """Write domain memory to disk"""
        with open("research_state.json", "w") as f:
            json.dump(self.state, f, indent=2)

    def chat(self, user_message: str, max_turns: int = 10) -> str:
        # 1. Orient - State already loaded in __init__

        # 2. Process query using parent's chat method
        response = super().chat(user_message, max_turns)

        # 3. Update domain memory after interaction
        self.update_state_from_conversation()
        self.save_state()

        return response
```

3. **Add state update logic**:
```python
def update_state_from_conversation(self):
    """Extract structured updates from conversation history"""
    # Example: If agent added a hypothesis, update state
    last_msg = self.get_last_message()

    # Parse for structured data (this is domain-specific)
    if "new hypothesis:" in last_msg.get("content", "").lower():
        # Extract hypothesis and add to state
        self.state["hypotheses"].append({...})
```

---

## Common Pitfalls

### ❌ Pitfall 1: Memory in Context Window Only

```python
# BAD - This memory disappears after session ends
def chat(self, user_message):
    self.conversation_history.append(user_message)
    # ... process ...
    # Memory is ONLY in conversation_history, which is lost when agent restarts
```

**Fix**: Persist memory to disk after each interaction.

---

### ❌ Pitfall 2: No Single Source of Truth

```
feature_list.json says: Feature #5 passes ✅
Git commit says: "Fix bug in feature #5" (implies it was broken)
Progress.md says: "Feature #5 still has issues"
```

**Fix**: Decide which artifact is authoritative (usually feature_list.json for test status) and enforce it.

---

### ❌ Pitfall 3: Memory Without Validation

```json
{
  "feature_id": 15,
  "description": "Implement OAuth2",
  "passes": true  // Who verified this? How?
}
```

**Fix**: Always include validation steps:
```json
{
  "feature_id": 15,
  "description": "Implement OAuth2",
  "validation_steps": [
    "Run pytest tests/test_oauth.py",
    "Manual test with real SharePoint tenant",
    "Check token refresh works"
  ],
  "passes": true,
  "last_validated": "2025-12-09T15:30:00Z",
  "validated_by": "session_15"
}
```

---

### ❌ Pitfall 4: Too Generic

```json
{
  "tasks": [
    {"id": 1, "description": "Do the thing", "done": false}
  ]
}
```

**Fix**: Be domain-specific:
```json
{
  "contractor_imports": [
    {
      "id": 1,
      "source": "SharePoint list 'Contractors'",
      "destination": "Neon table 'contractors'",
      "status": "failed",
      "error": "Duplicate primary key on row 15",
      "retry_count": 2,
      "last_attempt": "2025-12-09T14:00:00Z"
    }
  ]
}
```

---

## Strategic Implications

### The Moat Isn't Smarter AI

> Models will get better and become interchangeable.
>
> What won't be commoditized: **Your domain memory schemas and harnesses**.

**Your competitive advantage**:
1. Well-designed domain memory schemas for your business domains
2. Harnesses that enforce discipline and consistency
3. Testing loops that keep agents honest
4. Accumulated knowledge in Superior Agent Brain

### Example: FibreFlow's Moat

- **Fiber deployment domain memory** - Schemas for projects, BOQs, RFQs, contractor tracking
- **Multi-agent orchestration patterns** - Proven routing logic, agent specialization
- **Dual database architecture** - Neon + Convex sync patterns
- **Production-hardened harness** - 50+ successful agent builds with consistent patterns

Competitors can use the same Claude models. They can't replicate your domain expertise encoded in memory schemas.

---

## Next Steps

1. **Audit existing agents**: Which ones have domain memory? Which are "amnesiacs"?
2. **Document memory schemas**: For each agent, document its domain memory artifacts
3. **Enforce bootup rituals**: Add state loading/saving to BaseAgent
4. **Create non-coding templates**: Research agent, ops agent, PM agent schemas
5. **Test memory consistency**: Write tests that verify memory artifacts stay in sync

---

## Further Reading

- `harness/README.md` - How the harness implements domain memory
- `AGENT_WORKFORCE_GUIDE.md` - Multi-agent orchestration
- `shared/base_agent.py` - BaseAgent implementation (extend with memory methods)
- `memory/` - Superior Agent Brain for cross-session learning
- Anthropic's Blog: ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents)

---

**Remember**:
> Generalized agents are a fantasy.
> Domain memory is the reality that makes agents work.
