---
description: Generate or update agent documentation
argument-hint: [agent-name]
---

# Agent Documentation Generator

Generate comprehensive documentation for the **$ARGUMENTS** agent.

## Step 1: Analyze Agent Implementation

Read and analyze:
- `agents/$ARGUMENTS/agent.py` - Agent implementation
- `orchestrator/registry.json` - Agent registration details
- `tests/test_$ARGUMENTS.py` - Test cases (if exists)
- `.env.example` - Environment variable requirements

## Step 2: Generate/Update README.md

Create or update `agents/$ARGUMENTS/README.md` with the following structure:

### Template Structure

```markdown
# {AgentName} Agent

**Purpose**: [One-line description of what this agent does]

**Status**: ✅ Production / 🚧 Development / 🧪 Experimental

## Overview

[2-3 paragraphs explaining:
- What this agent does
- Why it exists in the FibreFlow system
- Key problems it solves
- How it fits into the multi-agent architecture]

## Architecture

```
User Request → Orchestrator → {AgentName} Agent → [External System/Database]
                                    ↓
                              Tool Execution
                                    ↓
                               Response
```

**Position in FibreFlow**:
[Explain how this agent relates to other agents and the overall system]

## Capabilities

### Tool 1: [Tool Name]
**Purpose**: [What this tool does]
**Input**: [Expected parameters]
**Output**: [What it returns]
**Example**:
```python
# Usage example
```

### Tool 2: [Tool Name]
[Same structure as Tool 1]

[Continue for all tools...]

## Configuration

### Environment Variables

Required:
- `ENV_VAR_NAME`: Description of what this is used for
- `ANOTHER_VAR`: Description

Optional:
- `OPTIONAL_VAR`: Description (default: value)

### Dependencies

Python packages required:
```bash
anthropic>=0.XX.X
psycopg2-binary>=2.X.X
[other dependencies]
```

## Installation

```bash
# Install dependencies
./venv/bin/pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set required variables
```

## Usage

### Interactive Mode

```bash
./venv/bin/python3 demo_$ARGUMENTS.py
```

Example session:
```
You: [Example query]
Agent: [Expected response]
```

### Programmatic Usage

```python
from agents.$ARGUMENTS.agent import {AgentName}Agent

# Initialize agent
agent = {AgentName}Agent()

# Execute query
response = agent.chat("Your query here")
print(response)
```

### Via Orchestrator

The orchestrator automatically routes queries containing these keywords:
- [keyword1]
- [keyword2]
- [keyword3]

Example:
```python
from orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()
response = orchestrator.route("Query with trigger keyword")
```

## Testing

### Run All Tests

```bash
./venv/bin/pytest tests/test_$ARGUMENTS.py -v
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
./venv/bin/pytest tests/test_$ARGUMENTS.py -m unit -v

# Integration tests only
./venv/bin/pytest tests/test_$ARGUMENTS.py -m integration -v
```

### Test Coverage

```bash
./venv/bin/pytest tests/test_$ARGUMENTS.py --cov=agents.$ARGUMENTS --cov-report=html
```

## Integration

### With Orchestrator

Registered in `orchestrator/registry.json`:
- **Name**: $ARGUMENTS
- **Triggers**: [List trigger keywords]
- **Priority**: [If applicable]

### With Other Agents

[Describe any interactions with other agents:
- Data sharing
- Workflow dependencies
- Complementary capabilities]

### With Databases

[If applicable:
- Which databases this agent connects to
- What operations it performs
- Data flow patterns]

## Performance

**Model**: Claude [Haiku/Sonnet] (configurable)
**Average Response Time**: [X seconds]
**Cost per Query**: ~$[X] (using [model])

**Optimization Tips**:
- [Tip 1 for improving performance]
- [Tip 2 for reducing costs]

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| [Error message] | [Root cause] | [Step-by-step fix] |
| [Another issue] | [Cause] | [Fix] |

## Troubleshooting

### Agent Not Responding
1. Check environment variables are set
2. Verify [external service] is accessible
3. Check logs: `tail -f [log_file]`

### [Other Common Problem]
[Diagnostic steps and solutions]

## API Reference

### Class: {AgentName}Agent

#### `__init__()`
Initialize the agent.

**Parameters**: None (uses environment variables)

#### `define_tools()`
Define agent-specific tools.

**Returns**: List[dict] - Tool definitions for Claude

#### `execute_tool(tool_name: str, tool_input: dict)`
Execute a specific tool.

**Parameters**:
- `tool_name`: Name of the tool to execute
- `tool_input`: Dictionary of tool parameters

**Returns**: str - Tool execution result

#### `chat(query: str)`
Process a user query.

**Parameters**:
- `query`: Natural language query string

**Returns**: str - Agent response

## Development

### Adding New Tools

1. Define tool in `define_tools()`:
```python
{
    "name": "new_tool_name",
    "description": "What this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
}
```

2. Implement in `execute_tool()`:
```python
elif tool_name == "new_tool_name":
    param = tool_input.get("param")
    # Implementation
    return result
```

3. Add tests in `tests/test_$ARGUMENTS.py`
4. Update this documentation

### Contributing

Guidelines for extending this agent:
- Follow existing code patterns
- Add tests for new functionality
- Update documentation
- Test with orchestrator integration

## Version History

**v1.0.0** (YYYY-MM-DD)
- Initial implementation
- Core tools: [list]

[Future versions...]

## Future Enhancements

Planned improvements:
- [ ] Enhancement 1
- [ ] Enhancement 2
- [ ] Enhancement 3

## References

- FibreFlow Architecture: `AGENT_WORKFORCE_GUIDE.md`
- Base Agent Pattern: `shared/base_agent.py`
- Orchestrator Documentation: `orchestrator/README.md`
- Project Overview: `CLAUDE.md`

## Support

For issues or questions:
1. Check this documentation
2. Review `TROUBLESHOOTING.md`
3. Check logs in [log location]
4. Refer to `orchestrator/registry.json` for configuration

---

**Last Updated**: [Auto-generate date]
**Maintainer**: [If applicable]
**License**: [Project license]
```

## Step 3: Validation

Ensure documentation includes:
- [ ] Clear purpose statement
- [ ] Complete capabilities list
- [ ] All tools documented
- [ ] Configuration requirements
- [ ] Usage examples (interactive and programmatic)
- [ ] Testing instructions
- [ ] Integration details
- [ ] Troubleshooting guide
- [ ] API reference
- [ ] Common issues table

## Step 4: Cross-Reference Check

Verify consistency with:
- [ ] `orchestrator/registry.json` - Triggers and capabilities match
- [ ] `.env.example` - All environment variables documented
- [ ] `CLAUDE.md` - Agent listed in appropriate section
- [ ] `tests/test_$ARGUMENTS.py` - Tests cover documented capabilities

## Step 5: Generate Output

Provide:
```markdown
## Documentation Complete: $ARGUMENTS Agent

📄 **File**: `agents/$ARGUMENTS/README.md`
📏 **Sections**: [Count of major sections]
🔧 **Tools Documented**: [Count]
⚙️ **Environment Variables**: [Count]
📝 **Examples**: [Count]

### Documentation Quality Checklist
✅ Purpose and overview clear
✅ All tools documented with examples
✅ Configuration requirements complete
✅ Usage examples provided
✅ Testing instructions included
✅ Integration details explained
✅ Troubleshooting guide present
✅ API reference complete

### Files Updated
- `agents/$ARGUMENTS/README.md` - Main documentation
- [List any other files updated]

### Next Steps
1. Review generated documentation for accuracy
2. Add any project-specific details
3. Update screenshots or diagrams if needed
4. Commit documentation updates
```

## FibreFlow Documentation Standards

Follow these guidelines:
- **Clarity**: Use simple language, avoid jargon where possible
- **Completeness**: Document all features and configuration
- **Examples**: Provide concrete, runnable examples
- **Maintenance**: Include version history and update dates
- **Troubleshooting**: Document common issues and solutions
- **Consistency**: Match format of other agent READMEs

Use relative paths for cross-references to other documentation files.
