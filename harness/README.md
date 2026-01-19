# FibreFlow Agent Harness

**Autonomous Long-Running Agent Builder** - Build complete, production-ready FibreFlow specialized agents via overnight autonomous execution.

Based on [Anthropic's Coding Agent Harness](https://github.com/anthropics/anthropic-harness), adapted for FibreFlow Agent Workforce patterns.

---

## Overview

The FibreFlow Agent Harness is a **meta-development system** that uses multiple Claude Code sessions to build sophisticated agents autonomously:

```
App Spec (Requirements)
    ↓
Initializer Agent (Session 1)
    - Generates 50-100 test cases
    - Creates scaffolding
    - Sets up git repository
    ↓
Coding Agent Session 2
    - Fresh context window
    - Implements Feature #1
    - Validates & commits
    ↓
Coding Agent Session 3
    - Fresh context window
    - Implements Feature #2
    - Validates & commits
    ↓
... (50-100 sessions)
    ↓
Complete Agent
    - BaseAgent implementation
    - Full test coverage
    - Documentation
    - Orchestrator integration
    - Demo script
```

**Key Innovation**: Each session gets a fresh context window, avoiding context pollution while maintaining continuity through:
- `feature_list.json` (comprehensive test cases)
- `claude_progress.md` (session summaries)
- Git history (all previous work)
- Core artifacts (configuration, specs)

---

## Why Use the Harness?

### Without Harness ❌
- Single context window gets overwhelmed (200K tokens)
- Agent forgets earlier decisions
- Inconsistent code patterns
- Manual feature tracking
- Hours of human supervision

### With Harness ✅
- Fresh context every feature
- Consistent BaseAgent patterns
- Automated test validation
- Granular git commits
- Run overnight, wake up to complete agent
- Self-documenting progress

---

## Architecture

### Directory Structure

```
harness/
├── config.json                 # Harness configuration
├── runner.py                   # Main execution engine
├── README.md                   # This file
│
├── prompts/                    # Claude Code prompts
│   ├── initializer.md          # Session 1: Setup & feature generation
│   └── coding_agent.md         # Sessions 2+: Feature implementation
│
├── specs/                      # Agent specifications (PRDs)
│   ├── sharepoint_spec.md      # Example: SharePoint agent
│   └── [agent-name]_spec.md    # Your agent specs
│
└── runs/                       # Execution runs
    ├── latest/                 # Symlink to most recent run
    └── [agent]_[timestamp]/    # Individual run directories
        ├── feature_list.json   # All test cases
        ├── claude_progress.md  # Session summaries
        ├── init_agent.sh       # Initialization script
        ├── sessions/           # Per-session logs
        │   ├── session_001.log
        │   ├── session_002.log
        │   └── ...
        └── HARNESS_REPORT.md   # Final summary
```

### Core Artifacts

The harness maintains continuity across fresh context windows using:

#### 1. Feature List (`feature_list.json`)

Comprehensive test-driven roadmap:

```json
{
  "agent_name": "sharepoint",
  "total_features": 75,
  "completed": 15,
  "features": [
    {
      "id": 1,
      "category": "1_scaffolding",
      "description": "Create agents/sharepoint/ directory",
      "validation_steps": [
        "ls agents/sharepoint/",
        "test -f agents/sharepoint/agent.py"
      ],
      "passes": true,
      "files_involved": ["agents/sharepoint/agent.py"],
      "dependencies": []
    },
    // ... 74 more features
  ]
}
```

#### 2. Progress File (`claude_progress.md`)

Session-to-session communication:

```markdown
# Session 15: Coding Agent

## Previous Session
Session 14 implemented feature #14: execute_tool() method

## This Session
Implemented feature #15: upload_file_to_sharepoint tool
- Added tool definition
- Implemented OAuth2 authentication
- Validated with integration test
- All checks passed ✅

## Current Progress
15/75 features complete (20%)

## Next Steps
Session 16 should implement feature #16: download_file_from_sharepoint
```

#### 3. Configuration (`config.json`)

Harness and FibreFlow settings:

```json
{
  "max_features": 100,
  "session_timeout_minutes": 30,
  "model": {
    "initializer": "claude-sonnet-4.5",
    "coding_agent": "claude-3-5-haiku"
  },
  "fibreflow_patterns": {
    "base_agent_class": "shared.base_agent.BaseAgent",
    "orchestrator_registry": "orchestrator/registry.json",
    "required_methods": ["define_tools()", "execute_tool()", ...]
  }
}
```

#### 4. Git History

Every feature gets a commit:

```bash
$ git log --oneline
a3b4c5d feat: Implement upload_file_to_sharepoint tool
b2c3d4e feat: Add OAuth2 token manager
c1d2e3f feat: Implement execute_tool() method
d0e1f2g feat: Add SharePoint client class
e9f0a1b feat: Implement get_system_prompt()
...
```

---

## Quick Start

### 1. Create App Spec

Define what agent to build:

```bash
nano harness/specs/my_agent_spec.md
```

**Template**: See `harness/specs/sharepoint_spec.md` for comprehensive example.

**Required Sections**:
- Purpose
- Capabilities (3-6 major features)
- Tools (detailed parameter specs)
- Integration Requirements (env vars, dependencies)
- Success Criteria

### 2. Run Harness

```bash
# Using slash command (recommended)
/agents/build my_agent

# OR: Direct runner invocation
./harness/runner.py --agent my_agent --model haiku
```

**What happens**:
1. Validates environment (venv, BaseAgent, git)
2. Validates app spec exists
3. Runs initializer agent (10-20 min)
4. Auto-runs coding agents until complete (4-24 hours)
5. Generates final report

### 3. Monitor Progress

```bash
# Watch progress
watch -n 60 'cat harness/runs/latest/claude_progress.md | tail -30'

# Check completion percentage
cat harness/runs/latest/feature_list.json | jq '{total: .total_features, done: .completed}'

# View git commits
git log --oneline -20
```

### 4. Test Complete Agent

```bash
# Run tests
./venv/bin/pytest tests/test_my_agent.py -v

# Try demo
./venv/bin/python3 demo_my_agent.py

# Use in orchestrator
# Query: "Use my_agent to do something"
```

---

## Integration with Anthropic's Harness

This is a **FibreFlow-adapted version** of Anthropic's harness. To use the actual execution engine:

### Option 1: Use Anthropic's Harness with Our Prompts

```bash
# Clone Anthropic's harness
git clone https://github.com/anthropics/anthropic-harness
cd anthropic-harness

# Copy FibreFlow prompts
cp /path/to/fibreflow/harness/prompts/* ./prompts/

# Copy FibreFlow config
cp /path/to/fibreflow/harness/config.json ./

# Run with your app spec
python run_autonomous_agent.py \
  --app-spec /path/to/fibreflow/harness/specs/my_agent_spec.md \
  --project-dir /path/to/fibreflow/agents/my_agent
```

### Option 2: Integrate Claude Agent SDK

Install the SDK:

```bash
pip install anthropic-agent-sdk
```

Update `harness/runner.py`:

```python
from claude_agent_sdk import create_client, run_session

def run_claude_code_session(...):
    # Load prompt
    prompt = load_prompt(session_type)

    # Create client
    client = create_client(
        project_dir=f"agents/{agent_name}",
        model=model,
        system_prompt=prompt,
        mcp_servers=["filesystem"],
        # FibreFlow-specific config
        hooks={
            "tool_use": validate_baseagent_pattern
        }
    )

    # Run session
    result = run_session(
        client=client,
        initial_message=prompt,
        timeout_minutes=timeout_minutes
    )

    return result.success
```

---

## App Spec Guidelines

### Simple Agent (20-40 features, 4-8 hrs, $3-5)

**Characteristics**:
- 2-3 simple tools
- Basic CRUD operations
- Minimal external dependencies
- Direct API calls

**Example**: File Manager Agent
- Tool 1: List files
- Tool 2: Read file content
- Tool 3: Write file content

### Moderate Agent (40-75 features, 8-16 hrs, $10-15)

**Characteristics**:
- 4-6 tools with moderate complexity
- External API integration
- OAuth2 authentication
- Error handling & retries
- Comprehensive tests

**Example**: SharePoint Agent (included in specs/)
- 6 tools (upload, download, list, create, search, metadata)
- OAuth2 with Azure AD
- Chunked uploads for large files
- Full integration test coverage

### Complex Agent (75-100+ features, 16-24 hrs, $20-30)

**Characteristics**:
- 6+ sophisticated tools
- Multiple external systems
- State management
- Advanced error recovery
- Extensive business logic
- Performance optimization

**Example**: Advanced Project Management Agent
- 10+ tools (create, update, track, assign, report, budget, etc.)
- Integration with Neon DB, Convex, SharePoint
- Complex validation logic
- Real-time updates
- Notification system

---

## Prompts Explained

### Initializer Prompt (`prompts/initializer.md`)

**Purpose**: Set up project foundation

**Responsibilities**:
- Read app spec
- Generate 50-100 granular test cases
- Create feature_list.json with validation steps
- Set up agents/[name]/ directory
- Create BaseAgent skeleton
- Initialize git repository
- Write initial claude_progress.md

**Output**:
- feature_list.json with all features marked `"passes": false`
- Agent directory with BaseAgent skeleton
- init_agent.sh script
- Git commit: "feat: Initialize [agent] harness"

**Duration**: 10-20 minutes

### Coding Agent Prompt (`prompts/coding_agent.md`)

**Purpose**: Implement ONE feature

**Process** (10-step cycle):
1. **Prime**: Read claude_progress.md, feature_list.json, git log
2. **Initialize**: Run init_agent.sh to verify environment
3. **Regression Test**: Validate recent features still work
4. **Choose Feature**: Select next incomplete feature from list
5. **Implement**: Write code following BaseAgent patterns
6. **Validate**: Run ALL validation steps from feature_list.json
7. **Update**: Mark feature complete in feature_list.json
8. **Commit**: Git commit with descriptive message
9. **Progress**: Update claude_progress.md with summary
10. **End**: Exit session (harness starts next coding agent)

**Constraints**:
- ONE feature per session (no batching)
- MUST run all validation steps
- MUST follow BaseAgent patterns
- MUST commit after each feature
- MUST update progress file

**Duration**: 5-30 minutes per session

---

## FibreFlow Patterns Enforced

The prompts ensure coding agents follow FibreFlow standards:

### BaseAgent Inheritance

```python
from shared.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, anthropic_api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(anthropic_api_key, model)
```

### Tool Structure

```python
def define_tools(self) -> List[Dict[str, Any]]:
    return [
        {
            "name": "snake_case_name",
            "description": "Clear description",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "What it is"}
                },
                "required": ["param"]
            }
        }
    ]
```

### Test Markers

```python
@pytest.mark.unit
@pytest.mark.agent_name
def test_something(agent):
    # Unit test
```

### Orchestrator Registration

```json
{
  "id": "agent-name",
  "name": "Agent Name",
  "path": "agents/agent-name",
  "status": "active",
  "type": "infrastructure|database|data_management",
  "triggers": ["keyword1", "keyword2", ...],
  "capabilities": {...}
}
```

---

## Cost Optimization

### Model Selection

| Model | Use Case | Speed | Cost/1M Tokens | Recommended For |
|-------|----------|-------|----------------|-----------------|
| Haiku | Simple features, high volume | Fast | $0.25 | Coding agents (default) |
| Sonnet | Complex logic, reasoning | Medium | $3.00 | Initializer, complex tools |
| Opus | Highest quality | Slow | $15.00 | Not recommended for harness |

**Default Configuration**:
- **Initializer**: Sonnet (one-time, needs good planning)
- **Coding Agents**: Haiku (many iterations, speed matters)

### Cost Estimates

**Simple Agent** (40 features, Haiku):
- Initializer: 1 session × $0.50 = $0.50
- Coding: 40 sessions × $0.10 = $4.00
- **Total**: ~$4.50

**Moderate Agent** (75 features, Haiku):
- Initializer: 1 session × $0.50 = $0.50
- Coding: 75 sessions × $0.15 = $11.25
- **Total**: ~$12

**Complex Agent** (100 features, mixed):
- Initializer: 1 session × $1 = $1
- Coding: 100 sessions × $0.20 = $20
- **Total**: ~$21

### Subscription vs API Key

**Claude Subscription** (Recommended):
- Unlimited queries for $20/month
- Use `CLAUDE_TOKEN` instead of API key
- Best for experimentation and multiple agents

**API Key**:
- Pay-per-token
- Better for production with predictable costs
- Use `ANTHROPIC_API_KEY`

---

## Troubleshooting

### Session Failures

**Symptom**: Session times out or crashes

**Diagnosis**:
```bash
# Check session log
cat harness/runs/latest/sessions/session_NNN.log

# Check what feature was being implemented
cat harness/runs/latest/claude_progress.md
```

**Fix**:
```bash
# Resume from next session
./harness/runner.py --agent my_agent --resume
```

### Tests Keep Failing

**Symptom**: Same feature attempted repeatedly

**Diagnosis**:
```bash
# Find failing feature
cat harness/runs/latest/feature_list.json | jq '.features[] | select(.passes == false) | .id' | head -1

# Check validation steps
cat harness/runs/latest/feature_list.json | jq '.features[N].validation_steps'
```

**Fix**:
```bash
# Option 1: Simplify validation
# Edit feature_list.json: reduce validation complexity

# Option 2: Implement manually
nano agents/my_agent/agent.py
# Fix the implementation
# Mark feature as complete in feature_list.json

# Resume
./harness/runner.py --agent my_agent --resume
```

### Harness Loops Infinitely

**Symptom**: Same feature retried 5+ times

**Fix**:
```bash
# Stop harness (Ctrl+C)

# Skip problematic feature (mark complete manually)
nano harness/runs/latest/feature_list.json
# Find feature, change "passes": false → "passes": true

# Resume
./harness/runner.py --agent my_agent --resume
```

### BaseAgent Patterns Not Followed

**Symptom**: Generated code doesn't inherit from BaseAgent

**Diagnosis**:
```bash
# Check agent.py
grep "BaseAgent" agents/my_agent/agent.py
```

**Fix**:
- Ensure initializer prompt emphasizes BaseAgent pattern
- Check config.json has correct `fibreflow_patterns`
- Manually fix agent.py if needed
- Mark related features as incomplete and resume

---

## Advanced Usage

### Manual Session Control

Run specific session types:

```bash
# Run initializer only
./harness/runner.py --agent my_agent --session-type initializer

# Run single coding session
./harness/runner.py --agent my_agent --session-type coding --auto-continue=false

# Run until specific feature count
# (Monitor progress, Ctrl+C when desired)
```

### Custom Feature Lists

Edit after initialization:

```bash
# Run initializer
./harness/runner.py --agent my_agent --session-type initializer

# Customize features
nano harness/runs/latest/feature_list.json
# - Reorder features
# - Remove low-priority features
# - Adjust validation steps
# - Add custom features

# Resume with customized list
./harness/runner.py --agent my_agent --resume
```

### Parallel Agent Development

Build multiple agents simultaneously:

```bash
# Terminal 1
./harness/runner.py --agent sharepoint --model haiku

# Terminal 2
./harness/runner.py --agent github --model haiku

# Terminal 3
./harness/runner.py --agent slack --model haiku
```

Each runs independently in its own directory.

---

## Best Practices

### App Spec Writing

✅ **DO**:
- Be specific about capabilities
- Define tools with detailed parameters
- Include real-world usage examples
- Estimate complexity accurately
- Specify all environment variables
- Include security considerations

❌ **DON'T**:
- Write vague requirements ("agent that handles data")
- Over-scope (keep focused on one domain)
- Skip tool parameter definitions
- Forget external dependencies
- Omit error handling requirements

### During Execution

✅ **DO**:
- Let it run overnight (don't micromanage)
- Check progress periodically (not constantly)
- Review git commits occasionally
- Trust the test-driven process

❌ **DON'T**:
- Interrupt sessions (use --resume instead)
- Manually edit files during active run
- Panic if tests fail (regression testing catches this)
- Rush to production without review

### After Completion

✅ **DO**:
- **Code review ALL generated code**
- Run full test suite
- Test agent manually with edge cases
- Review error handling
- Update project documentation
- Use /deployment/deploy for production

❌ **DON'T**:
- Deploy without human review
- Skip edge case testing
- Ignore TODO comments
- Leave failing tests
- Forget to register in orchestrator

---

## Integration with FibreFlow

### Orchestrator Auto-Registration

Harness automatically:
1. Generates triggers from app spec keywords
2. Infers capabilities from tools
3. Updates `orchestrator/registry.json`
4. Tests routing with sample queries

### Testing Integration

Harness creates:
- Unit tests with `@pytest.mark.unit`
- Integration tests with `@pytest.mark.integration`
- Agent-specific marker: `@pytest.mark.agent_name`

Run with `/testing/test-all` or pytest directly.

### Documentation Generation

Harness produces:
- `agents/[name]/README.md` - Comprehensive guide
- `demo_[name].py` - Interactive demo script
- Inline docstrings for all methods
- `.env.example` updates

---

## Comparison: Harness vs Manual Development

| Aspect | Manual Development | Harness |
|--------|-------------------|---------|
| **Time** | 2-4 days | Overnight (4-24 hrs) |
| **Consistency** | Varies by developer | BaseAgent patterns enforced |
| **Testing** | Often incomplete | 100% coverage with validation |
| **Documentation** | Often outdated | Auto-generated and current |
| **Code Review** | Required | Still required (but complete) |
| **Context Management** | Human memory | Git + artifacts |
| **Incremental Progress** | Depends on commits | Auto-commit per feature |
| **Regression Testing** | Manual | Built-in every session |
| **Cost** | Developer time ($$$) | API costs ($5-30) |

---

## FAQ

**Q: Can I use this for non-agent code?**
A: Yes! Adapt the prompts for any Python project. The harness works for any test-driven development.

**Q: What if I want to use a different model?**
A: Edit `config.json` or use `--model` flag. Haiku (default) is recommended for cost efficiency.

**Q: Can I pause and resume?**
A: Yes! `Ctrl+C` to stop, `--resume` to continue from last session.

**Q: How do I customize feature generation?**
A: Edit feature_list.json after initializer runs, before starting coding agents.

**Q: Does this work with other AI coding assistants?**
A: Yes! The prompts are markdown. Adapt for Cursor, Windsurf, Aider, etc.

**Q: What if the agent makes mistakes?**
A: Regression testing catches issues. Fix manually and resume, or let harness retry.

**Q: How much does it cost to build an agent?**
A: $3-5 (simple), $10-15 (moderate), $20-30 (complex) using Haiku. Or use Claude subscription ($20/month unlimited).

---

## Resources

### Anthropic Resources
- [Official Harness Repository](https://github.com/anthropics/anthropic-harness)
- [Harness Article](https://www.anthropic.com/research/building-autonomous-agents)
- [Claude Agent SDK Docs](https://docs.anthropic.com/en/docs/build-with-claude/agent-sdk)

### FibreFlow Resources
- `CLAUDE.md` - Project overview and patterns
- `shared/base_agent.py` - Base agent implementation
- `orchestrator/registry.json` - Agent registration
- `.claude/commands/agents/new.md` - Manual agent scaffolding

### Example Agents
- `agents/vps-monitor/` - Simple infrastructure agent
- `agents/neon-database/` - Moderate database agent
- `harness/specs/sharepoint_spec.md` - Moderate external integration

---

## Contributing

To improve the harness:

1. **Better prompts**: Edit `prompts/*.md` with clearer instructions
2. **More examples**: Add app specs to `specs/` for reference
3. **Configuration**: Tune `config.json` for optimal results
4. **Integration**: Full Claude Agent SDK integration in `runner.py`

---

## License

Based on Anthropic's open-source harness. Adapted for FibreFlow Agent Workforce.

---

**Ready to build agents autonomously?**

1. Create your app spec: `harness/specs/my_agent_spec.md`
2. Run: `./harness/runner.py --agent my_agent`
3. Let it work overnight
4. Wake up to a complete agent!

*"The best agent is one you didn't have to manually code."*
