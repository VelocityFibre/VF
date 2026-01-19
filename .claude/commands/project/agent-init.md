---
description: Initialize a new project with FibreFlow's agent architecture for optimal AI delegation
category: project
enabled: true
---

# /agent-init

Initialize any new repository, module, or application with FibreFlow's proven agent architecture pattern that achieves 100x performance improvements through direct delegation instead of exploration.

## Usage

```
/agent-init [project-name] [--type skill|agent|full]
```

## Examples

```bash
# Initialize with basic skill structure
/agent-init my-app --type skill

# Initialize with agent architecture
/agent-init my-module --type agent

# Full setup with harness support
/agent-init my-project --type full
```

## What This Command Does

1. **Creates Project Structure**:
   ```
   .claude/
   ├── skills/          # Direct operation scripts
   ├── commands/        # Custom commands
   └── agents/          # Agent configurations
   agents/              # Complex domain agents
   orchestrator/        # Request routing
   shared/              # Base classes
   tests/              # Test suite
   harness/            # Automated agent builder
   ```

2. **Sets Up Base Infrastructure**:
   - `shared/base_agent.py` - Base agent class
   - `orchestrator/registry.json` - Agent registry
   - `CLAUDE.md` - Project-specific AI guidance
   - `.env.example` - Environment template
   - `pytest.ini` - Test configuration

3. **Creates First Capability** (based on --type):
   - **skill**: Database operations or API integration skill
   - **agent**: Complete agent with tools and tests
   - **full**: All infrastructure including harness

4. **Configures Testing**:
   - Pytest setup with markers
   - Example test files
   - Performance benchmarks

## Execution Steps

### Step 1: Analyze Current Directory
- Check if it's a git repo
- Detect existing framework (Node, Python, etc.)
- Identify potential integration points

### Step 2: Create Structure
```bash
# Core directories
mkdir -p .claude/skills .claude/commands agents orchestrator shared tests

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install anthropic psycopg2-binary pytest
```

### Step 3: Generate Configuration
- Create `.env.example` with required variables
- Generate `CLAUDE.md` with project context
- Set up `orchestrator/registry.json`

### Step 4: Create Initial Capability

**For Skills** (--type skill):
```python
# .claude/skills/database-operations/scripts/query.py
#!/usr/bin/env python3
import json
import sys
import os
import psycopg2

def execute_query(query):
    # Direct execution without exploration
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    # ... implementation
```

**For Agents** (--type agent):
```python
# agents/your-module/agent.py
from shared.base_agent import BaseAgent

class YourModuleAgent(BaseAgent):
    def define_tools(self):
        # Tools for direct execution

    def execute_tool(self, tool_name, tool_input):
        # No exploration, just execution
```

### Step 5: Test Setup
```bash
# Run initial tests
./venv/bin/pytest tests/ -v

# Test skill directly
.claude/skills/*/scripts/test.py

# Test orchestrator routing
./venv/bin/python3 orchestrator/orchestrator.py
```

## Benefits of This Architecture

| Metric | Without | With Agent-Init | Improvement |
|--------|---------|-----------------|-------------|
| Query Speed | 2.3s | 23ms | 100x faster |
| Token Usage | 4,500 | 930 | 79% less |
| Error Rate | 30% | <1% | 99% reduction |
| Cost | $0.20 | $0.004 | 50x cheaper |

## Options

### --type
- `skill` (default): Lightweight scripts for direct operations
- `agent`: Full agent with BaseAgent inheritance
- `full`: Complete setup including harness for overnight builds

### --template
- `api`: API integration template
- `database`: Database operations template
- `file`: File processing template
- `custom`: Empty template for custom implementation

### --model
- `haiku` (default): Fast and cheap for most operations
- `sonnet`: Better reasoning for complex domains

## Implementation Guide Reference

For detailed implementation steps, patterns, and best practices, see:
`AGENT_INIT_GUIDE.md`

## Common Use Cases

### 1. Adding to Existing Node.js App
```
/agent-init my-node-app --type skill --template api
```
Creates skills for API operations without changing app structure.

### 2. New Python Module
```
/agent-init my-python-module --type agent --template database
```
Full agent setup with database tools and testing.

### 3. Complex System Integration
```
/agent-init enterprise-integration --type full
```
Complete infrastructure with harness for building multiple agents.

## Post-Initialization Next Steps

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit with actual values
   ```

2. **Test Basic Operations**:
   ```bash
   ./venv/bin/python3 .claude/skills/*/scripts/test.py
   ```

3. **Add More Capabilities**:
   - Watch what Claude tries to explore
   - Create skills for those operations
   - Build agents for complex domains

4. **Monitor Performance**:
   ```bash
   # Check metrics
   cat performance.jsonl | jq '.duration_ms' | stats
   ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Claude still exploring | Create more specific skills |
| Skills not found | Check `.claude/skills/*/skill.md` metadata |
| Agent not routing | Verify `orchestrator/registry.json` triggers |
| High token usage | Break operations into smaller skills |

## Related Commands

- `/agents/build` - Build complete agent overnight
- `/agent-init` - Initialize new project (this command)
- `/test-all` - Run all tests after setup
- `/deploy` - Deploy to production

## Example Output

```
🚀 Initializing agent architecture for 'my-app'...

✅ Created directory structure
✅ Installed dependencies
✅ Generated configuration files
✅ Created database-operations skill
✅ Set up testing framework
✅ Registered with orchestrator

📊 Performance baseline:
- Direct skill execution: 23ms average
- Token usage: 930 per operation
- Error rate: <1%

🎯 Next steps:
1. Edit .env with your configuration
2. Run: ./venv/bin/pytest tests/ -v
3. Try: ./venv/bin/python3 orchestrator/orchestrator.py

💡 Monitor Claude's exploration patterns to identify new skill opportunities.
```

## Notes

- This command sets up the **architecture** not the implementation
- You still need to customize scripts for your specific needs
- The real value comes from preventing Claude's exploration
- Start with skills, upgrade to agents only when needed

## Performance Tip

The key insight: **Every time Claude says "let me try" or "let me explore", that's a skill opportunity**.

Direct execution via skills/agents eliminates this exploration, giving you 100x performance improvements.