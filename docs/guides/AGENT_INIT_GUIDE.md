# Agent Architecture Initialization Guide

**Quick Setup for New Repos/Modules/Apps with FibreFlow's Agent Pattern**

## Overview

This guide provides a rapid implementation workflow for adding FibreFlow's proven agent architecture to any new project. Choose between three approaches based on complexity:

- **Skills** (15 mins): Direct operations, no exploration needed
- **Agents** (2 hrs): Complex domain expertise with multiple tools
- **Harness** (overnight): Complete agent systems built autonomously

## Core Principle

> **Direct delegation beats exploration every time**

Instead of Claude exploring and trying different approaches, we give it direct access to specialized tools that know exactly what to do.

## Proven Performance Gains

Based on FibreFlow production metrics:
- **100x faster**: 23ms vs 2.3s per operation
- **79% less tokens**: 930 vs 4,500 tokens per query
- **50x cost reduction**: $0.004 vs $0.20 per session
- **99% fewer errors**: Validated execution vs trial-and-error

## Quick Start Workflow

### Step 1: Initial Project Setup (5 minutes)

```bash
# In your new repo/app root directory
PROJECT_ROOT=$(pwd)

# Create FibreFlow structure
mkdir -p .claude/skills
mkdir -p .claude/commands
mkdir -p agents
mkdir -p orchestrator
mkdir -p shared
mkdir -p tests
mkdir -p harness/specs

# Initialize Python environment
python3 -m venv venv
source venv/bin/activate
pip install anthropic psycopg2-binary pytest

# Create environment template
cat > .env.example << 'EOF'
# Required for all agents
ANTHROPIC_API_KEY=sk-ant-api03-...

# Add your app-specific variables here
YOUR_APP_API_KEY=
YOUR_APP_DATABASE_URL=
EOF

# Copy environment file
cp .env.example .env
echo "Edit .env with your actual values"
```

### Step 2: Copy Base Infrastructure (2 minutes)

```bash
# If you have access to FibreFlow repo
FIBREFLOW_PATH=~/Agents/claude

# Copy essential files
cp $FIBREFLOW_PATH/shared/base_agent.py ./shared/
cp $FIBREFLOW_PATH/orchestrator/orchestrator.py ./orchestrator/
cp $FIBREFLOW_PATH/orchestrator/registry.json ./orchestrator/
cp $FIBREFLOW_PATH/pytest.ini ./

# Create project-specific CLAUDE.md
cat > CLAUDE.md << 'EOF'
# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview
[Your project description here]

## Quick Commands
\`\`\`bash
# Test all agents
./venv/bin/pytest tests/ -v

# Run orchestrator
./venv/bin/python3 orchestrator/orchestrator.py
\`\`\`

## Architecture
- **Skills** in `.claude/skills/` for direct operations
- **Agents** in `agents/` for complex domains
- **Orchestrator** routes requests to appropriate handler

## Adding New Capabilities
1. Simple operation? Create a skill (15 mins)
2. Complex domain? Create an agent (2 hrs)
3. Complete system? Use the harness (overnight)
EOF
```

### Step 3A: Create Skills for Simple Operations (15 mins per skill)

Perfect for: Database queries, API calls, file operations, shell commands

```bash
# Example: Database operations skill
SKILL_NAME="database-operations"
mkdir -p .claude/skills/$SKILL_NAME/scripts

# Create skill metadata
cat > .claude/skills/$SKILL_NAME/skill.md << 'EOF'
---
name: database-operations
description: Direct database access without exploration
version: 1.0.0
requires: python3, psycopg2
---

# Database Operations Skill

Provides direct access to database without Claude exploring SQL syntax.

## Available Scripts
- `query.py` - Execute SELECT queries
- `update.py` - Execute INSERT/UPDATE/DELETE
- `schema.py` - Get table structures
EOF

# Create executable script
cat > .claude/skills/$SKILL_NAME/scripts/query.py << 'EOF'
#!/usr/bin/env python3
import json
import sys
import os
import psycopg2
from urllib.parse import urlparse

def execute_query(query):
    """Direct database query execution"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return {"error": "DATABASE_URL not configured"}

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(query)

        if cur.description:
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
        else:
            results = {"affected_rows": cur.rowcount}
            conn.commit()

        return {"success": True, "data": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "SELECT 1"
    result = execute_query(query)
    print(json.dumps(result, default=str))
EOF

chmod +x .claude/skills/$SKILL_NAME/scripts/query.py

# Test the skill
./venv/bin/python3 .claude/skills/$SKILL_NAME/scripts/query.py "SELECT version()"
```

### Step 3B: Create Agents for Complex Domains (2 hrs per agent)

Perfect for: Multi-step workflows, stateful operations, complex business logic

#### Option 1: Manual Creation

```bash
AGENT_NAME="your-module"
mkdir -p agents/$AGENT_NAME

# Create agent implementation
cat > agents/$AGENT_NAME/agent.py << 'EOF'
from shared.base_agent import BaseAgent
import json

class YourModuleAgent(BaseAgent):
    """Specialized agent for your module operations"""

    def __init__(self, anthropic_api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(anthropic_api_key, model)
        # Initialize any connections or state
        self.connection = None

    def get_system_prompt(self) -> str:
        return """You are a specialized agent for [your module] operations.
        You have direct access to tools that execute without exploration.
        Always use tools rather than trying to figure things out."""

    def define_tools(self):
        """Define available tools"""
        return [
            {
                "name": "execute_operation",
                "description": "Execute a specific operation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Operation parameters"
                        }
                    },
                    "required": ["operation"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: dict):
        """Execute tools directly without exploration"""
        try:
            if tool_name == "execute_operation":
                # Direct execution - no searching or trying
                operation = tool_input.get("operation")
                params = tool_input.get("parameters", {})

                # Your actual implementation here
                result = self._perform_operation(operation, params)
                return {"success": True, "result": result}

        except Exception as e:
            return {"error": str(e)}

    def _perform_operation(self, operation: str, params: dict):
        """Internal method for actual execution"""
        # Your domain-specific logic here
        return f"Executed {operation} with {params}"
EOF

# Register with orchestrator
python3 -c "
import json

# Load registry
with open('orchestrator/registry.json', 'r') as f:
    registry = json.load(f)

# Add new agent
registry['agents']['$AGENT_NAME'] = {
    'description': 'Handles your module operations',
    'triggers': ['your_keyword', 'module_name', 'specific_terms'],
    'capabilities': ['query', 'update', 'process'],
    'path': 'agents/$AGENT_NAME/agent.py',
    'class_name': 'YourModuleAgent'
}

# Save registry
with open('orchestrator/registry.json', 'w') as f:
    json.dump(registry, f, indent=2)
"

# Create test file
cat > tests/test_$AGENT_NAME.py << 'EOF'
import pytest
from agents.your_module.agent import YourModuleAgent

@pytest.fixture
def agent():
    return YourModuleAgent("test-key")

@pytest.mark.unit
def test_agent_initialization(agent):
    assert agent is not None
    assert len(agent.define_tools()) > 0

@pytest.mark.unit
def test_execute_operation(agent):
    result = agent.execute_tool("execute_operation", {
        "operation": "test",
        "parameters": {"key": "value"}
    })
    assert "success" in result or "error" in result
EOF

# Test the agent
./venv/bin/pytest tests/test_$AGENT_NAME.py -v
```

#### Option 2: Automated via Harness (Overnight)

```bash
# Create specification
cat > harness/specs/${AGENT_NAME}_spec.md << 'EOF'
# Your Agent Specification

## Purpose
What problem does this agent solve?

## Capabilities
1. First major capability
2. Second major capability
3. Third major capability

## Required Tools
- tool_one: Description and parameters
- tool_two: Description and parameters

## Integration Requirements
- Environment variables needed
- External dependencies
- API connections

## Success Criteria
- [ ] All tools implemented and tested
- [ ] Error handling complete
- [ ] Documentation generated
- [ ] Demo script works
EOF

# Run harness overnight
# Note: Requires harness setup from FibreFlow
./harness/runner.py --agent $AGENT_NAME --model haiku

# Or use slash command if available
# /agents/build your-agent-name
```

### Step 4: Create Project-Specific Commands (Optional)

```bash
mkdir -p .claude/commands/project

# Create initialization command
cat > .claude/commands/project/init.md << 'EOF'
---
name: project-init
description: Initialize project with agent architecture
---

# Project Initialization

Sets up FibreFlow agent architecture for the current project.

## Usage
/project-init [module-name]

## What it does
1. Creates directory structure
2. Sets up base agent class
3. Initializes orchestrator
4. Creates first skill or agent
5. Sets up testing framework
EOF
```

## Decision Matrix

| Scenario | Approach | Time | Example |
|----------|----------|------|---------|
| Single API endpoint | Skill | 15 mins | REST API query |
| Database queries | Skill | 15 mins | SQL operations |
| File operations | Skill | 15 mins | Read/write/parse |
| Multi-step workflow | Agent | 2 hrs | Data pipeline |
| Complex domain | Agent | 2 hrs | Business logic |
| Full subsystem | Harness | Overnight | Complete module |
| Multiple integrated features | Harness | Overnight | SharePoint integration |

## Testing Your Setup

```bash
# 1. Test skills directly
./venv/bin/python3 .claude/skills/database-operations/scripts/query.py "SELECT 1"

# 2. Test agents individually
python3 -c "
from agents.your_module.agent import YourModuleAgent
agent = YourModuleAgent('your-api-key')
result = agent.chat('test the agent')
print(result)
"

# 3. Test orchestrator routing
./venv/bin/python3 orchestrator/orchestrator.py
# Type: "your trigger keyword test"

# 4. Run full test suite
./venv/bin/pytest tests/ -v
```

## Best Practices

### 1. Start Simple, Enhance Progressively
```
Day 1: Basic skill for immediate need
Day 2: Add more scripts as patterns emerge
Week 2: Build full agent if complexity warrants
```

### 2. Monitor Claude's Exploration
If Claude keeps trying to figure something out, that's your next skill candidate:
- Repeated SQL syntax attempts → Create database skill
- Multiple file searching → Create file operations skill
- API exploration → Create API skill

### 3. Reuse Patterns
```bash
# Copy existing skill as template
cp -r .claude/skills/database-operations .claude/skills/new-skill
# Modify for your needs
```

### 4. Batch Operations
Create skills that handle multiple operations in one call:
```python
# scripts/batch.py
operations = json.loads(sys.argv[1])
results = [execute(op) for op in operations]
print(json.dumps(results))
```

### 5. Connection Pooling
For database/API operations, maintain persistent connections:
```python
# Global connection pool
_connection_pool = None

def get_connection():
    global _connection_pool
    if not _connection_pool:
        _connection_pool = create_pool()
    return _connection_pool.get()
```

## Common Patterns

### Pattern 1: API Integration Skill
```bash
mkdir -p .claude/skills/api-integration/scripts

cat > .claude/skills/api-integration/scripts/call.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import sys
import os

api_key = os.environ.get('API_KEY')
endpoint = sys.argv[1]
method = sys.argv[2] if len(sys.argv) > 2 else 'GET'
data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

response = requests.request(
    method,
    f"https://api.example.com/{endpoint}",
    headers={"Authorization": f"Bearer {api_key}"},
    json=data
)

print(json.dumps(response.json()))
EOF

chmod +x .claude/skills/api-integration/scripts/call.py
```

### Pattern 2: File Processing Skill
```bash
mkdir -p .claude/skills/file-ops/scripts

cat > .claude/skills/file-ops/scripts/process.py << 'EOF'
#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path

operation = sys.argv[1]  # read, write, list, search
path = sys.argv[2]
data = sys.argv[3] if len(sys.argv) > 3 else None

if operation == "read":
    content = Path(path).read_text()
    print(json.dumps({"content": content}))
elif operation == "write":
    Path(path).write_text(data)
    print(json.dumps({"success": True}))
elif operation == "list":
    files = [str(f) for f in Path(path).glob("**/*") if f.is_file()]
    print(json.dumps({"files": files}))
EOF

chmod +x .claude/skills/file-ops/scripts/process.py
```

## Deployment Checklist

- [ ] All .env variables configured
- [ ] Skills tested individually
- [ ] Agents tested with real data
- [ ] Orchestrator routing verified
- [ ] Test suite passing
- [ ] CLAUDE.md updated with project specifics
- [ ] Team members have access to repo

## Performance Monitoring

Track the effectiveness of your implementation:

```python
# Add to your agents/skills
import time
import json

def log_performance(operation, duration, tokens_used):
    """Log performance metrics"""
    with open('performance.jsonl', 'a') as f:
        f.write(json.dumps({
            'operation': operation,
            'duration_ms': duration * 1000,
            'tokens': tokens_used,
            'timestamp': time.time()
        }) + '\n')
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Claude still exploring | Create more specific skill |
| Skill not discovered | Check skill.md metadata |
| Agent not routing | Verify orchestrator triggers |
| High token usage | Break into smaller skills |
| Slow execution | Add connection pooling |

## Next Steps

1. **Implement basic skills** for immediate needs (15 mins each)
2. **Monitor Claude's behavior** to identify new skill opportunities
3. **Build agents** for complex domains that emerge (2 hrs each)
4. **Use harness** for complete subsystems (overnight)
5. **Share patterns** with team for consistency

---

*This guide is based on FibreFlow's production architecture achieving 100x performance improvements. For support, see the main FibreFlow documentation.*