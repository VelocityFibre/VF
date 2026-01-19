---
description: Scaffold a new specialized agent
argument-hint: [agent-name] [capabilities-description]
---

# New Agent Scaffolder

Create a new specialized agent following FibreFlow architecture patterns.

**Agent Name**: `$ARGUMENTS`

## Step 1: Create Agent Directory

```bash
mkdir -p agents/$ARGUMENTS
```

## Step 2: Generate Agent Implementation

Create `agents/$ARGUMENTS/agent.py` based on `shared/base_agent.py` template:

**Required Components**:
1. Import base agent: `from shared.base_agent import BaseAgent`
2. Define agent class: `class {AgentName}Agent(BaseAgent)`
3. Implement `define_tools()` method with agent-specific tools
4. Implement `execute_tool()` method for tool execution
5. Add `chat()` method for conversation loop
6. Include proper error handling and logging

**Pattern Reference**: Use `agents/vps-monitor/agent.py` or `agents/neon-database/agent.py` as examples

## Step 3: Create README.md

Generate `agents/$ARGUMENTS/README.md` with:
- Purpose and overview
- Architecture diagram showing position in FibreFlow system
- Capabilities and tools list
- Configuration requirements (environment variables)
- Usage examples (interactive and programmatic)
- Testing instructions
- Integration notes
- Common issues and solutions

**Template**: Follow format from `agents/vps-monitor/README.md`

## Step 4: Register in Orchestrator

Add entry to `orchestrator/registry.json`:

```json
{
  "name": "$ARGUMENTS",
  "class": "{AgentName}Agent",
  "module": "agents.$ARGUMENTS.agent",
  "description": "[Agent purpose]",
  "triggers": ["keyword1", "keyword2", "keyword3"],
  "capabilities": [
    "[Capability 1]",
    "[Capability 2]"
  ],
  "requires": {
    "env_vars": ["VAR1", "VAR2"],
    "dependencies": ["package1", "package2"]
  }
}
```

## Step 5: Create Test File

Generate `tests/test_$ARGUMENTS.py`:

**Required Tests**:
```python
import pytest
from agents.$ARGUMENTS.agent import {AgentName}Agent

@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return {AgentName}Agent()

@pytest.mark.unit
def test_agent_initialization(agent):
    """Test agent initializes correctly"""
    assert agent is not None
    assert hasattr(agent, 'define_tools')
    assert hasattr(agent, 'execute_tool')

@pytest.mark.integration
def test_agent_tools(agent):
    """Test agent tools are defined correctly"""
    tools = agent.define_tools()
    assert len(tools) > 0
    # Add specific tool tests

# Add tests for each tool
# Add error handling tests
# Add edge case tests
```

Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.{agent_name}`

## Step 6: Create Demo Script

Generate `demo_$ARGUMENTS.py`:

```python
#!/usr/bin/env python3
"""
Interactive demo for {AgentName} Agent
"""
from agents.$ARGUMENTS.agent import {AgentName}Agent

def main():
    print("=" * 60)
    print(f"{AgentName} Agent - Interactive Demo")
    print("=" * 60)

    agent = {AgentName}Agent()

    # Interactive chat loop
    print("\nType 'quit' to exit")
    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ['quit', 'exit']:
            break

        response = agent.chat(query)
        print(f"\n{AgentName}: {response}")

if __name__ == "__main__":
    main()
```

## Step 7: Update Documentation

Update the following files:
- [ ] `CLAUDE.md` - Add agent to "Agent Types" section if it's a new category
- [ ] `orchestrator/registry.json` - Register agent (already done in Step 4)
- [ ] `requirements.txt` - Add any new dependencies
- [ ] `.env.example` - Document new environment variables

## Step 8: Validation Checklist

Before considering the agent complete:
- [ ] Agent implementation follows BaseAgent pattern
- [ ] All tools are defined and implemented
- [ ] Error handling is in place
- [ ] README.md is comprehensive
- [ ] Registered in orchestrator
- [ ] Tests created and passing
- [ ] Demo script works
- [ ] Documentation updated
- [ ] Environment variables documented

## FibreFlow Agent Architecture Principles

**Domain Specialization**: Each agent should be an expert in a single domain
- ✅ Good: "VPS Monitor" (specific domain)
- ❌ Bad: "System Manager" (too broad)

**Task-Based, Not Role-Based**:
- ✅ Good: Specialized tools for specific tasks
- ❌ Bad: Generic "frontend developer" or "product manager" roles

**Independent Operation**:
- Agent should work standalone
- Minimal dependencies on other agents
- Clear tool definitions

**Reusability**:
- Agent should be reusable across use cases
- Well-documented interface
- Configurable via environment variables

## Output

Provide confirmation when each step is complete:
```markdown
## Agent Scaffolding Complete: $ARGUMENTS

✅ Directory created: agents/$ARGUMENTS/
✅ Agent implementation: agents/$ARGUMENTS/agent.py
✅ Documentation: agents/$ARGUMENTS/README.md
✅ Orchestrator registration: orchestrator/registry.json
✅ Tests: tests/test_$ARGUMENTS.py
✅ Demo: demo_$ARGUMENTS.py
✅ Documentation updates complete

### Next Steps
1. Review generated code
2. Customize tools for specific use case
3. Run tests: `./venv/bin/pytest tests/test_$ARGUMENTS.py -v`
4. Test demo: `./venv/bin/python3 demo_$ARGUMENTS.py`
5. Update environment variables in `.env`

### Integration
Agent is ready to be invoked by orchestrator when queries match triggers:
[List triggers from registry]
```
