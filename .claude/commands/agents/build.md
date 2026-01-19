---
description: Build agent via long-running harness (overnight execution)
argument-hint: [agent-name]
---

# Long-Running Agent Builder

Use the **FibreFlow Agent Harness** to build a complete, production-ready specialized agent via autonomous overnight execution.

**Agent Name**: `$ARGUMENTS`

## What is the Agent Harness?

The harness is a **spec-driven development system** that runs multiple Claude Code sessions over hours/days to build complex agents:

```
App Spec → Initializer Agent → Coding Agent #1 → Coding Agent #2 → ... → Complete Agent
             (1 session)         (Fresh context)   (Fresh context)       (50-100 sessions)
```

**Each session**:
- Fresh context window (no context bloat)
- Implements ONE feature
- Validates via automated tests
- Commits to git
- Passes progress to next session

**Key Benefit**: Can build agents with 50-100 granular features without overwhelming a single context window.

## Prerequisites

### 1. Create App Spec

First, define what agent to build:

```bash
# Create spec file
nano harness/specs/$ARGUMENTS_spec.md
```

**App Spec Template**:

```markdown
# $ARGUMENTS Agent Specification

## Purpose

[One paragraph: What problem does this agent solve?]

## Domain

**Type**: [Infrastructure | Database | Data Management | External Integration]
**Specialization**: [Specific expertise area]

## Capabilities

### 1. [Capability Name]
**What it does**: [Description]
**When to use**: [Use cases]
**Tool**: `tool_name_1`

### 2. [Capability Name]
**What it does**: [Description]
**When to use**: [Use cases]
**Tool**: `tool_name_2`

[Add 3-6 capabilities total]

## Tools

### Tool: `tool_name_1`

**Purpose**: [What it does]

**Parameters**:
- `param1` (string, required): [Description]
- `param2` (integer, optional): [Description]

**Returns**: `{data: ..., status: ...}`

**Example**:
```python
agent.execute_tool("tool_name_1", {"param1": "value"})
# Returns: {"data": [...], "status": "success"}
```

### Tool: `tool_name_2`

[Define each tool]

## Integration Requirements

### Environment Variables

```bash
ANTHROPIC_API_KEY=...        # Required
$ARGUMENTS_SPECIFIC_VAR=...  # Agent-specific config
```

### External Dependencies

- [Dependency 1]: [Why needed]
- [Dependency 2]: [Why needed]

### Orchestrator Triggers

**Keywords that should route to this agent**:
- keyword1
- keyword2
- keyword3
- keyword4
- keyword5
- keyword6
- keyword7
- keyword8

## Success Criteria

Agent is complete when:
- [ ] All tools implemented and working
- [ ] Full test coverage (unit + integration)
- [ ] README.md documentation complete
- [ ] Registered in orchestrator/registry.json
- [ ] Demo script functional
- [ ] Environment variables documented in .env.example
- [ ] Error handling comprehensive
- [ ] Follows BaseAgent pattern

## Architecture

```
User Query → Orchestrator → $ARGUMENTS Agent → Tools → External System/API
                                ↓
                         [Tool 1, Tool 2, Tool 3]
```

**Position in FibreFlow**:
- Inherits from: `shared/base_agent.py`
- Registers in: `orchestrator/registry.json`
- Tests in: `tests/test_$ARGUMENTS.py`

## Example Usage

### Via Orchestrator
```python
# User query with trigger keywords
query = "Use $ARGUMENTS to [do something]"
# Orchestrator routes to $ARGUMENTSAgent
```

### Direct Usage
```python
from agents.$ARGUMENTS.agent import $ARGUMENTSAgent

agent = $ARGUMENTSAgent(os.getenv('ANTHROPIC_API_KEY'))
response = agent.chat("Your query here")
```

## Complexity Estimate

**Simple Agent** (20-40 features, 4-8 hours, $3-5):
- 2-3 simple tools
- Basic CRUD operations
- Minimal external dependencies

**Moderate Agent** (40-75 features, 8-16 hours, $10-15):
- 4-6 tools with moderate complexity
- External API integration
- Error handling and retries
- Comprehensive tests

**Complex Agent** (75-100+ features, 16-24 hours, $20-30):
- 6+ sophisticated tools
- Multiple external system integrations
- Advanced error handling
- State management
- Extensive test coverage
- Complex business logic

## Notes

[Add any agent-specific considerations, limitations, or important details]
```

Save the spec file before proceeding.

### 2. Verify Environment

```bash
# Check virtual environment active
which python3 | grep venv
# Should show: /path/to/venv/bin/python3

# Check BaseAgent accessible
./venv/bin/python3 -c "from shared.base_agent import BaseAgent; print('✅ BaseAgent ready')"

# Check git initialized
git status
# Should not error

# Check Claude token/API key configured
echo $CLAUDE_TOKEN  # For subscription
# OR
echo $ANTHROPIC_API_KEY  # For API key
```

### 3. Review Cost Estimate

Based on your app spec complexity:

| Complexity | Features | Est. Time | Est. Cost (Haiku) | Est. Cost (Sonnet) |
|------------|----------|-----------|-------------------|-------------------|
| Simple     | 20-40    | 4-8 hrs   | $3-5              | $15-25            |
| Moderate   | 40-75    | 8-16 hrs  | $10-15            | $40-70            |
| Complex    | 75-100+  | 16-24 hrs | $20-30            | $90-140           |

**Recommendation**: Use Haiku for harness (fast iterations, cheap) unless you need Sonnet's superior reasoning for very complex agents.

## Running the Harness

### Option 1: Quick Start (Recommended)

```bash
# Run harness runner script
./venv/bin/python3 harness/runner.py --agent $ARGUMENTS --model haiku
```

This will:
1. Validate app spec exists
2. Create run directory
3. Start initializer agent
4. Auto-run coding agents until complete
5. Generate final report

**Flags**:
- `--agent`: Agent name (required)
- `--model`: haiku | sonnet | opus (default: haiku)
- `--max-sessions`: Max coding sessions (default: 50)
- `--session-timeout`: Minutes per session (default: 30)
- `--auto-continue`: Auto-run next session (default: true)
- `--use-subscription`: Use Claude subscription token vs API key (default: true)

### Option 2: Manual Step-by-Step

**For more control over the process**:

#### Step 1: Run Initializer

```bash
# This creates feature list and scaffolding (10-20 min)
./venv/bin/python3 harness/manual_session.py \
  --agent $ARGUMENTS \
  --session-type initializer \
  --model sonnet
```

**Wait for completion**. You'll see:
- Feature list generation (50-100 features)
- Agent directory creation
- Initialization script created
- Git commit

#### Step 2: Review Feature List

```bash
# See what will be built
cat harness/runs/latest/feature_list.json | jq '.features | length'
# Shows: N features

# Review categories
cat harness/runs/latest/feature_list.json | jq '.categories'
```

**Optional**: Edit feature list to:
- Adjust priority (reorder features)
- Remove unnecessary features
- Modify validation steps

#### Step 3: Run First Coding Agent

```bash
./venv/bin/python3 harness/manual_session.py \
  --agent $ARGUMENTS \
  --session-type coding \
  --model haiku
```

This implements ONE feature, validates it, commits it.

#### Step 4: Monitor Progress

```bash
# Check progress
cat harness/runs/latest/claude_progress.md

# Count completed features
cat harness/runs/latest/feature_list.json | jq '[.features[] | select(.passes == true)] | length'

# Run tests
./venv/bin/pytest tests/test_$ARGUMENTS.py -v
```

#### Step 5: Continue Coding Sessions

```bash
# Run next coding agent
./venv/bin/python3 harness/manual_session.py \
  --agent $ARGUMENTS \
  --session-type coding \
  --model haiku

# Repeat until all features complete
```

OR use auto-continue:

```bash
# Run until complete
./venv/bin/python3 harness/runner.py \
  --agent $ARGUMENTS \
  --model haiku \
  --resume \
  --auto-continue
```

## Monitoring Long-Running Execution

### Real-Time Progress

```bash
# Watch progress file update
watch -n 60 "cat harness/runs/latest/claude_progress.md | tail -50"

# Monitor feature completion
watch -n 60 "cat harness/runs/latest/feature_list.json | jq '{total: .total_features, completed: .completed, percent: (.completed / .total_features * 100)}'"

# Watch git commits
watch -n 60 "git log --oneline -20"
```

### Test Execution Logs

```bash
# View harness logs
tail -f harness/runs/latest/harness.log

# View session-specific logs
tail -f harness/runs/latest/sessions/session_*.log
```

### Cost Tracking

```bash
# Estimated cost so far
cat harness/runs/latest/cost_estimate.json
```

## When Things Go Wrong

### Session Fails

**Symptoms**: Session times out, infinite loop, crashes

**Fix**:
```bash
# Check what session failed
cat harness/runs/latest/claude_progress.md

# Review session log
cat harness/runs/latest/sessions/session_N.log

# Manually fix the issue
nano agents/$ARGUMENTS/agent.py

# Resume from next session
./venv/bin/python3 harness/runner.py --agent $ARGUMENTS --resume
```

### Tests Keep Failing

**Symptoms**: Coding agent fixes same feature repeatedly

**Fix**:
```bash
# Identify failing feature
cat harness/runs/latest/feature_list.json | jq '.features[] | select(.passes == false) | .id' | head -1

# Review validation steps
cat harness/runs/latest/feature_list.json | jq '.features[N].validation_steps'

# Manually implement feature correctly
nano agents/$ARGUMENTS/agent.py

# Manually mark complete
# Edit feature_list.json: change "passes": false → "passes": true

# Resume harness
./venv/bin/python3 harness/runner.py --agent $ARGUMENTS --resume
```

### Harness Stuck in Loop

**Symptoms**: Same feature attempted 5+ times

**Fix**:
```bash
# Stop harness (Ctrl+C)

# Review problem feature
cat harness/runs/latest/claude_progress.md

# Skip problematic feature (mark as complete manually)
# Edit feature_list.json

# OR: Simplify validation steps
# Edit feature_list.json: reduce validation complexity

# Resume
./venv/bin/python3 harness/runner.py --agent $ARGUMENTS --resume
```

## Post-Completion Steps

### 1. Review Generated Agent

```bash
# View complete agent
cat agents/$ARGUMENTS/agent.py

# Check tests
./venv/bin/pytest tests/test_$ARGUMENTS.py -v

# Review README
cat agents/$ARGUMENTS/README.md
```

### 2. Test Agent Functionality

```bash
# Run demo
./venv/bin/python3 demo_$ARGUMENTS.py

# Test via orchestrator
./venv/bin/python3 orchestrator/orchestrator.py
# Ask: "Use $ARGUMENTS to [do something]"
```

### 3. Verify Orchestrator Registration

```bash
# Check registration
cat orchestrator/registry.json | jq '.agents[] | select(.id == "$ARGUMENTS")'

# Test routing
# Query with triggers should route to this agent
```

### 4. Update Documentation

```bash
# Update CLAUDE.md if needed
nano CLAUDE.md

# Update .env.example
nano .env.example

# Commit documentation
git add CLAUDE.md .env.example
git commit -m "docs: Update docs for $ARGUMENTS agent"
```

### 5. Generate Report

```bash
# Create harness summary
./venv/bin/python3 harness/generate_report.py --run-id latest

# This creates: harness/runs/latest/HARNESS_REPORT.md
cat harness/runs/latest/HARNESS_REPORT.md
```

## Best Practices

### App Spec Writing

✅ **DO**:
- Be specific about capabilities
- Define tools with clear parameters
- Provide usage examples
- Estimate complexity realistically
- Include success criteria

❌ **DON'T**:
- Write vague requirements
- Over-scope (keep focused)
- Skip tool definitions
- Forget environment variables
- Omit integration requirements

### During Execution

✅ **DO**:
- Monitor progress periodically
- Review commits in git
- Check test results
- Let it run overnight (don't interrupt)
- Trust the process

❌ **DON'T**:
- Interrupt sessions mid-execution
- Manually edit files during run (use resume)
- Ignore failing tests
- Skip validation of final output
- Rush to production without review

### After Completion

✅ **DO**:
- Review ALL generated code
- Run full test suite
- Test agent manually
- Update documentation
- Deploy via /deployment/deploy

❌ **DON'T**:
- Deploy without code review
- Skip testing edge cases
- Ignore TODOs in code
- Leave broken tests
- Forget orchestrator registration

## Integration with Other Commands

```bash
# After harness completes:

# Test the agent
/agents/test $ARGUMENTS

# Document it (if needed)
/agents/document $ARGUMENTS

# Deploy to production
/deployment/deploy $ARGUMENTS

# Run full test suite
/testing/test-all
```

## Output Structure

After completion, you'll have:

```
agents/$ARGUMENTS/
├── __init__.py
├── agent.py                # Complete BaseAgent implementation
└── README.md               # Comprehensive documentation

tests/
└── test_$ARGUMENTS.py      # Full test coverage

demo_$ARGUMENTS.py          # Interactive demo script

orchestrator/registry.json  # Updated with agent registration

harness/runs/[run-id]/
├── feature_list.json       # All features marked complete
├── claude_progress.md      # Final session summary
├── init_agent.sh           # Initialization script
├── harness.log             # Execution log
├── sessions/               # Per-session logs
│   ├── session_001.log
│   ├── session_002.log
│   └── ...
├── cost_estimate.json      # Token usage and cost
└── HARNESS_REPORT.md       # Final summary report
```

## Success Criteria

Harness is successful when:
- ✅ All features in feature_list.json complete
- ✅ Agent follows BaseAgent pattern
- ✅ All tests passing
- ✅ README.md comprehensive
- ✅ Registered in orchestrator
- ✅ Demo script works
- ✅ Environment variables documented
- ✅ No TODO comments left
- ✅ Git history clean with descriptive commits
- ✅ Cost within estimate

## Troubleshooting

**Q**: Harness keeps timing out
**A**: Increase `--session-timeout` or simplify features

**Q**: Too many features generated (100+)
**A**: Edit feature_list.json to remove low-priority features

**Q**: Agent doesn't follow BaseAgent pattern
**A**: Review initializer prompt, ensure it emphasizes patterns

**Q**: Tests keep failing
**A**: Simplify validation steps in feature_list.json

**Q**: Cost exceeding estimate
**A**: Switch to Haiku, reduce max-sessions, or pause and resume

**Q**: Want to resume after stopping
**A**: `./venv/bin/python3 harness/runner.py --agent $ARGUMENTS --resume`

## Example: Building a SharePoint Agent

```bash
# 1. Create app spec
cat > harness/specs/sharepoint_spec.md << 'EOF'
# SharePoint Agent Specification

## Purpose
Integrate with Microsoft SharePoint to upload, download, and manage files.

## Capabilities

### 1. File Upload
**Tool**: `upload_file`
**Parameters**: file_path, sharepoint_folder
**Returns**: {file_id, url}

### 2. File Download
**Tool**: `download_file`
**Parameters**: file_id, local_path
**Returns**: {status, local_path}

[etc...]
EOF

# 2. Run harness
./venv/bin/python3 harness/runner.py \
  --agent sharepoint \
  --model haiku \
  --max-sessions 40

# 3. Wait 8-12 hours (or overnight)

# 4. Test agent
./venv/bin/pytest tests/test_sharepoint.py -v

# 5. Use agent
./venv/bin/python3 demo_sharepoint.py
```

## Advanced: Custom Features

You can customize the harness by:

1. **Editing feature_list.json** after initialization
2. **Adding custom validation steps** to features
3. **Adjusting session timeout** for complex features
4. **Pausing and resuming** to make manual fixes
5. **Running select sessions** manually for control

See `harness/README.md` for advanced configuration.

---

## Ready to Build?

1. Create app spec: `harness/specs/$ARGUMENTS_spec.md`
2. Review cost estimate
3. Run: `./venv/bin/python3 harness/runner.py --agent $ARGUMENTS`
4. Monitor progress periodically
5. Review output when complete
6. Test and deploy

**Estimated Time**: 4-24 hours depending on complexity
**Estimated Cost**: $3-30 depending on model and features
**Result**: Production-ready FibreFlow agent with full test coverage

Let the harness work overnight and wake up to a complete agent!
