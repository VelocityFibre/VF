# Database Operations Skill

**Type**: Skills-based implementation (Anthropic's paradigm)
**Purpose**: Natural language interface to Neon PostgreSQL database
**Status**: Proof of Concept

## Overview

This skill provides database querying capabilities using executable Python scripts rather than a full Agent SDK implementation. It demonstrates Anthropic's "skills-based" architecture where:

1. **Progressive Disclosure**: Only `skill.md` metadata loaded initially (~50 tokens)
2. **Scripts as Tools**: Executable files, not in-memory tool definitions
3. **File System Execution**: Scripts run from file system, not loaded into context
4. **Self-Documenting**: Code IS the documentation

## Structure

```
database-operations/
├── skill.md                  # Progressive disclosure format
├── scripts/
│   ├── db_utils.py          # Shared database utilities
│   ├── list_tables.py       # List all tables
│   ├── describe_table.py    # Table schema
│   ├── table_stats.py       # Row counts, sizes
│   ├── execute_query.py     # SELECT queries
│   ├── execute_insert.py    # INSERT data
│   ├── execute_update.py    # UPDATE data
│   ├── execute_delete.py    # DELETE data
│   ├── test_skill.sh        # Test harness
│   └── requirements.txt     # Python dependencies
└── README.md                 # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd scripts/
pip install -r requirements.txt
```

### 2. Set Environment

```bash
export NEON_DATABASE_URL="postgresql://user:pass@host/database"
```

### 3. Test Skill

```bash
cd scripts/
chmod +x test_skill.sh
./test_skill.sh
```

## Usage Examples

### List Tables
```bash
./scripts/list_tables.py
```

**Output**:
```json
{
  "success": true,
  "data": [
    {"table_name": "contractors", "table_type": "BASE TABLE"},
    {"table_name": "projects", "table_type": "BASE TABLE"}
  ],
  "message": "Found 104 tables"
}
```

### Query Data
```bash
./scripts/execute_query.py --query "SELECT * FROM contractors WHERE status = 'active'" --limit 10
```

**Output**:
```json
{
  "success": true,
  "data": {
    "query": "SELECT * FROM contractors WHERE status = 'active' LIMIT 10;",
    "rows": [ ... ],
    "row_count": 9
  },
  "message": "Query returned 9 rows"
}
```

### Table Statistics
```bash
./scripts/table_stats.py --table contractors
```

**Output**:
```json
{
  "success": true,
  "data": {
    "table_name": "contractors",
    "row_count": 20,
    "total_size": "128 kB",
    "table_size": "64 kB",
    "indexes_size": "64 kB"
  },
  "message": "Statistics for 'contractors'"
}
```

## How It Works

### Traditional Agent (BaseAgent)

```python
class NeonAgent(BaseAgent):
    def define_tools(self):
        return [
            {
                "name": "list_tables",
                "description": "...",
                "input_schema": {...}
            }
        ]  # Lives in context window!

    def execute_tool(self, tool_name, tool_input):
        if tool_name == "list_tables":
            return self.db.list_tables()
```

**Context cost**: ~5000 tokens (agent class + tools + conversation)

### Skills-Based (This Implementation)

```bash
# Agent sees only skill.md metadata (50 tokens)
# When needed, executes:
./scripts/list_tables.py
```

**Context cost**: ~1000 tokens (skill.md + results)
**Savings**: 80% reduction in context usage

## Progressive Disclosure

**Initial Load** (what Claude Code sees):
```yaml
---
id: database-operations
description: Natural language interface to Neon PostgreSQL database
triggers: [database, sql, query, table]
estimated_tokens: 600
---
```

**Full Load** (when skill activated):
- Complete `skill.md` content (~600 tokens)
- Tool descriptions
- Usage examples
- Error handling guides

**Scripts**: NEVER loaded into context (file system execution)

## Context Efficiency

| Item | Tokens | When Loaded |
|------|--------|-------------|
| Skill metadata | ~50 | Always (initial) |
| Full skill.md | ~600 | On activation |
| Script source | 0 | Never (executed from filesystem) |
| Script results | ~500 | After execution |
| **Total** | **~1150** | **Per query** |

**Compare to**:
- Full NeonAgent: ~5000 tokens per query

## Comparison to Agent Approach

### Skills-Based (This)

✅ Context efficient (1K vs 5K tokens)
✅ Scripts easily modifiable
✅ No agent scaffolding needed
✅ Self-documenting (code = docs)
✅ Progressive disclosure built-in

❌ Each script spawns Python interpreter
❌ No connection pooling across calls
❌ No in-memory state
❌ Slightly slower (process spawning)

### Agent-Based (agents/neon-database/)

✅ Connection pooling
✅ In-memory state
✅ Faster (no process spawning)
✅ Rich conversation context

❌ High context usage (5K tokens)
❌ Tools always in context
❌ Agent scaffolding required
❌ Harder to modify on-the-fly

## Testing

Run the test harness:
```bash
cd scripts/
./test_skill.sh
```

Tests:
1. List tables
2. Describe contractors table
3. Get table statistics
4. Execute simple query

All tests output JSON for easy verification.

## Integration with Claude Code

Claude Code natively supports skills via `.claude/skills/` directory. To use:

1. **Symlink this skill**:
   ```bash
   ln -s $(pwd)/experiments/skills-vs-agents/skills-based/database-operations \
         .claude/skills/database-operations
   ```

2. **Claude Code auto-discovers it**

3. **Progressive disclosure happens automatically**:
   - Metadata shown in tool list
   - Full skill.md loaded when activated
   - Scripts executed from filesystem

## Notes

- This is a **proof of concept** for architectural comparison
- Production use would need error handling improvements
- Consider adding retry logic for database connections
- Scripts use simple connection (no pooling) for simplicity

## Next Steps

See `experiments/skills-vs-agents/README.md` for:
- Comparison test harness
- Measurement criteria
- Decision framework
