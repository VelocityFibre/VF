# Agent OS + Inngest + Harness Integration Guide

## The Complete Development Pipeline

### Phase 1: Specification (Agent OS)
**Time**: 1-2 hours
**Human involvement**: High (answering questions)

```bash
# 1. Start with Agent OS to define the problem
/plan-product

# Agent OS asks:
# - What problem does this agent solve?
# - Who are the users?
# - What are the success metrics?

# 2. Shape the specification
/shape-spec

# Agent OS asks:
# - What's the MVP feature set?
# - What can we defer to v2?
# - What are the constraints?

# 3. Generate formal spec
/write-spec

# Output: .claude/specs/sharepoint_spec.md
```

### Phase 2: Implementation (Agent Harness)
**Time**: 4-24 hours (overnight)
**Human involvement**: None (autonomous)

```bash
# Agent Harness reads the Agent OS spec and builds
/agents/build sharepoint

# OR directly:
./harness/runner.py --agent sharepoint --spec .claude/specs/sharepoint_spec.md
```

The Harness will:
1. Read the Agent OS spec (single source of truth)
2. Generate feature_list.json (50-100 test cases)
3. Run 50-100 Claude sessions to implement
4. Create complete agent with tests

### Phase 3: Orchestration (Inngest)
**Runtime**: Ongoing
**Human involvement**: None (automated)

```python
# inngest/functions/agent_orchestration.py
@inngest.create_function(
    fn_id="run-agent",
    trigger=inngest.Event("agent/task.requested")
)
async def run_agent_task(ctx, step):
    """Execute agent task with Inngest durability"""

    # Step 1: Load agent spec from Agent OS
    spec = await step.run(
        "load-spec",
        lambda: load_agent_os_spec(ctx.event.data.agent_name)
    )

    # Step 2: Route through orchestrator
    agent = await step.run(
        "select-agent",
        lambda: orchestrator.select_agent(ctx.event.data.query)
    )

    # Step 3: Execute with retries
    result = await step.run(
        "execute",
        lambda: agent.execute(ctx.event.data.task),
        retry={"attempts": 3}
    )

    return result
```

## Integration Architecture

```
┌─────────────────────────────────────────────────┐
│                   AGENT OS                      │
│                                                  │
│  Standards Layer    Product Layer    Specs Layer│
│  ├─ coding.md      ├─ roadmap.md   ├─ sharepoint.md
│  ├─ testing.md     ├─ schema.md    ├─ vps.md
│  └─ patterns.md    └─ apis.md      └─ neon.md
└────────────────────┬────────────────────────────┘
                     ↓ Specs flow to
┌─────────────────────────────────────────────────┐
│                AGENT HARNESS                    │
│                                                  │
│  Reads specs → Generates features → Builds agent│
│                                                  │
│  harness/specs/[agent]_spec.md (from Agent OS)  │
└────────────────────┬────────────────────────────┘
                     ↓ Triggers events in
┌─────────────────────────────────────────────────┐
│                   INNGEST                       │
│                                                  │
│  agent/build.started                            │
│  agent/feature.completed                        │
│  agent/test.passed                              │
│  agent/deploy.ready                             │
└────────────────────┬────────────────────────────┘
                     ↓ Registers with
┌─────────────────────────────────────────────────┐
│                ORCHESTRATOR                     │
│                                                  │
│  orchestrator/registry.json                     │
│  Routes runtime requests to appropriate agent   │
└──────────────────────────────────────────────────┘
```

## Concrete Example: Building a Jira Agent

### Day 1: Specification with Agent OS (1 hour)

```bash
# Start planning
/plan-product

Q: What problem does this solve?
A: Automates Jira ticket creation and updates from code comments

Q: Who are the users?
A: Developers who want to create tickets without leaving their IDE

Q: What are the key features?
A: Create tickets, update status, add comments, query tickets
```

**Output**: `.claude/specs/jira_spec.md`

### Night 1: Build with Harness + Inngest (8 hours, unattended)

```python
# Triggered automatically when spec is ready
@inngest.create_function(
    fn_id="build-agent-from-spec",
    trigger=inngest.Event("spec/created")
)
async def build_from_spec(ctx, step):
    spec_path = ctx.event.data.spec_path

    # Initialize harness
    await step.run(
        "init-harness",
        lambda: harness.initialize(spec_path)
    )

    # Run 50-100 coding sessions
    for i in range(100):
        result = await step.run(
            f"coding-session-{i}",
            lambda: harness.run_session(i),
            timeout="30m"
        )

        if result["all_features_complete"]:
            break

        # Checkpoint between sessions
        await step.sleep("pause", duration="30s")

    # Deploy
    await step.run(
        "deploy",
        lambda: deploy_agent(ctx.event.data.agent_name)
    )
```

### Day 2: Production Use (ongoing)

```python
# User query triggers orchestrator
user_query = "Create a Jira ticket for the bug in auth.py:45"

# Orchestrator routes to Jira agent (via registry.json)
# Inngest ensures reliable execution
inngest.send(Event(
    name="agent/task.requested",
    data={
        "agent_name": "jira",
        "task": "create_ticket",
        "params": {...}
    }
))
```

## Key Integration Points

### 1. Agent OS → Harness
- Agent OS generates `spec.md`
- Harness reads spec as input
- No manual translation needed

### 2. Harness → Inngest
- Harness build process wrapped in Inngest function
- Each coding session is a step (can pause/resume)
- Automatic retries on failure

### 3. Inngest → Orchestrator
- Completed agents auto-register in registry.json
- Runtime tasks flow through Inngest for durability
- Orchestrator remains the routing brain

## Configuration Updates

### .env additions
```bash
# Agent OS
AGENT_OS_VERSION=2.1.1

# Inngest
INNGEST_SIGNING_KEY=signkey_prod_xxx
INNGEST_EVENT_KEY=test_xxx

# Integration
AGENT_BUILD_TRIGGER=auto  # auto|manual
SPEC_WATCH_ENABLED=true   # Watch for new specs
```

### Directory Structure
```
claude/
├── .claude/
│   ├── agents/         # Agent OS agents
│   ├── specs/          # Agent OS specifications
│   ├── standards/      # Agent OS standards
│   └── product/        # Agent OS product docs
├── harness/
│   ├── specs/          # Symlink to .claude/specs
│   └── runner.py       # Enhanced with Inngest
├── inngest/
│   ├── functions/
│   │   ├── spec_watcher.py    # Watch for new specs
│   │   ├── harness_runner.py  # Durable harness execution
│   │   └── agent_executor.py  # Runtime task execution
│   └── client.py
└── orchestrator/
    └── registry.json   # Auto-updated by pipeline
```

## Benefits of Integration

### Development Velocity
- **Before**: 3-5 days to build an agent manually
- **After**: 1 hour planning + 8 hours automated = Next day delivery

### Quality Assurance
- Agent OS ensures consistent specifications
- Harness ensures consistent implementation
- Inngest ensures reliable execution

### Observability
```
Agent OS metrics:
- Spec completeness score
- Standards compliance

Harness metrics:
- Features completed/total
- Test coverage
- Build duration

Inngest metrics:
- Function success rate
- Retry frequency
- Execution time
```

## Recommended Workflow

### For New Agents
1. **Always** start with Agent OS (/plan-product)
2. Let Harness build overnight (via Inngest)
3. Review and deploy next morning

### For Existing Agents
1. Skip Agent OS (already built)
2. Use Inngest for long-running operations
3. Update registry.json if needed

### For Quick Fixes
1. Skip all tools
2. Edit directly
3. Commit and deploy

## Decision Matrix

| Scenario | Agent OS | Harness | Inngest | Direct Edit |
|----------|----------|---------|---------|-------------|
| New agent (complex) | ✅ | ✅ | ✅ | ❌ |
| New agent (simple) | ✅ | ❌ | ✅ | ❌ |
| Add feature | ❌ | ❌ | ✅ | ✅ |
| Bug fix | ❌ | ❌ | ❌ | ✅ |
| Refactor | Optional | ❌ | ✅ | ✅ |

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up Agent OS commands
- [ ] Install Inngest
- [ ] Create spec watcher

### Week 2: Integration
- [ ] Connect Agent OS → Harness
- [ ] Wrap Harness in Inngest
- [ ] Test with simple agent

### Week 3: Production
- [ ] Build first production agent
- [ ] Set up monitoring
- [ ] Document workflow

### Week 4: Optimization
- [ ] Tune Inngest concurrency
- [ ] Add failure notifications
- [ ] Create team playbooks