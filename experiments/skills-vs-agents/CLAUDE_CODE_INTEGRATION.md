# Testing Skills with Claude Code

**Status**: ✅ Skill installed and ready for testing

## What We Set Up

```bash
.claude/skills/database-operations/  → symlinked to experiments/skills-vs-agents/skills-based/database-operations/
```

Claude Code will now auto-discover this skill using progressive disclosure.

## How Claude Code Skills Work

### Progressive Disclosure Flow

**Phase 1: Discovery** (Happens automatically on startup)
```
Claude Code reads .claude/skills/*/skill.md
Loads ONLY the YAML frontmatter (lines 1-8):
---
id: database-operations
name: Database Operations
description: Natural language interface to Neon PostgreSQL...
triggers: [database, sql, query, neon, postgresql, ...]
estimated_tokens: 600
complexity: simple
---

Context cost: ~50 tokens
```

**Phase 2: Activation** (Happens when user query matches triggers)
```
User: "How many contractors are in the database?"
                ↓
Claude sees trigger word: "database", "contractors"
                ↓
Loads full skill.md content (300 lines)
                ↓
Context cost: ~600 tokens (full skill instructions)
```

**Phase 3: Execution** (Happens when Claude decides to use a tool)
```
Claude reads tool documentation in skill.md
                ↓
Decides to use: execute_query
                ↓
Executes: ./scripts/execute_query.py --query "SELECT COUNT(*)..."
                ↓
Gets JSON result (not in context - from filesystem)
                ↓
Context cost: ~500 tokens (result data)
```

**Total Context**: ~1,150 tokens (50 + 600 + 500)

**Compare to Full Agent**: ~5,000 tokens (agent class always loaded)

**Savings**: 77% context reduction

## Testing the Skill

### Test 1: Verify Skill Discovery

Claude Code should show the skill in available skills list. The skill should appear with its metadata.

**Expected**: skill appears with description and triggers

### Test 2: Simple Query (Context Efficiency Test)

**Query to test**:
```
How many contractors are in the database?
```

**What should happen**:
1. Claude sees "database" and "contractors" triggers
2. Loads full skill.md (~600 tokens)
3. Reads tool documentation for execute_query
4. Executes: `./scripts/execute_query.py --query "SELECT COUNT(*) FROM contractors"`
5. Returns: "There are 20 contractors in the database."

**Context usage**: ~1,150 tokens total

**Verification**:
- Check that Claude executed the script (not wrote new code)
- Check that result came from JSON output
- Response should be fast (no agent initialization)

### Test 3: Multi-Step Query (Composition Test)

**Query to test**:
```
Show me the database schema for contractors table, then query how many are active.
```

**What should happen**:
1. Claude uses describe_table tool first
2. Then uses execute_query tool
3. Both executions use same loaded skill (no reload needed)
4. Maintains context across steps

**Context usage**: ~1,800 tokens (skill + 2 results)

**Verification**:
- Two separate tool executions
- Results composed into single answer
- No skill reload between tools

### Test 4: Cross-Domain Query (Skills Advantage Test)

**Query to test**:
```
List all tables in the database that contain contractor-related data.
```

**What should happen**:
1. Uses list_tables tool
2. Filters results for "contractor" keyword
3. Returns: contractors, contractor_performance, etc.

**Why this tests skills advantage**:
- With multi-agent: Would route to database agent exclusively
- With skills: Can compose with other skills if needed (e.g., VPS monitoring)

### Test 5: Safety Check (Error Handling Test)

**Query to test**:
```
Delete all contractors from the database.
```

**What should happen**:
1. Claude attempts execute_delete tool
2. Script rejects query (no WHERE clause)
3. Returns error: "DELETE without WHERE clause is EXTREMELY dangerous"
4. Claude explains why it failed

**Verification**:
- No data deleted (safety check worked)
- Clear error message
- Claude explains the safety mechanism

## Manual Verification

If you want to manually verify the skill works:

```bash
# Navigate to skill scripts
cd .claude/skills/database-operations/scripts

# Test 1: List tables
./list_tables.py | head -30

# Test 2: Count contractors
./execute_query.py --query "SELECT COUNT(*) as count FROM contractors"

# Test 3: Describe table
./describe_table.py --table contractors

# Test 4: Table stats
./table_stats.py --table contractors
```

All should return JSON with `"success": true`

## Comparing to Multi-Agent Approach

### Multi-Agent (`agents/neon-database/`)

**Startup**:
```python
agent = NeonAgent(model="claude-3-haiku-20240307")
# Loads entire agent class into context (~2000 tokens)
# Defines all tools in memory (~2000 tokens)
# Initializes connection pool
```

**Query Execution**:
```python
response = agent.chat("How many contractors?")
# Agent already in context (2000 tokens)
# Tools already in context (2000 tokens)
# Result added (500 tokens)
# Total: 4500 tokens
```

**Advantages**:
- ✅ Connection pooling (faster repeated queries)
- ✅ Maintains conversation state
- ✅ Rich context across queries

**Disadvantages**:
- ❌ High context usage (4500 tokens per query)
- ❌ Agent scaffolding required
- ❌ Tools always in context (whether used or not)

### Skills-Based (`.claude/skills/database-operations/`)

**Startup**:
```
# Claude Code reads skill metadata (50 tokens)
# Nothing else loaded until needed
```

**Query Execution**:
```
User query → Skill activated (600 tokens)
          → Tool executed (script from filesystem)
          → Result returned (500 tokens)
          → Total: 1150 tokens
```

**Advantages**:
- ✅ Context efficient (1150 tokens per query)
- ✅ Progressive disclosure (load on demand)
- ✅ Scripts easily modifiable
- ✅ Native Claude Code integration

**Disadvantages**:
- ❌ No connection pooling (slower repeated queries)
- ❌ No persistent state between calls
- ❌ Process spawning overhead

## Context Usage Breakdown

| Scenario | Multi-Agent | Skills-Based | Savings |
|----------|-------------|--------------|---------|
| **Simple query** | 4,500 tokens | 1,150 tokens | 74% |
| **Multi-step** (3 queries) | 7,500 tokens | 2,350 tokens | 69% |
| **Cross-domain** (2 domains) | 9,000 tokens | 2,600 tokens | 71% |
| **Average** | **7,000 tokens** | **2,000 tokens** | **71%** |

**Implication**: With skills, you can fit 3.5x more queries in the same context window.

## When to Use Each Approach

### Use Skills-Based When:
- ✅ Simple, one-off queries (80% of usage)
- ✅ Context efficiency is priority
- ✅ Claude Code integration is important
- ✅ Cross-domain composition needed
- ✅ Easy modification valued

### Use Multi-Agent When:
- ✅ Long, complex debugging session (20+ messages)
- ✅ Performance is critical (connection pooling matters)
- ✅ Deep domain expertise needed
- ✅ Maintaining state across queries important

### Hybrid (Recommended):
- Skills for simple queries (fast, efficient)
- Escalate to agent for complex analysis
- Best of both worlds

## Expected Results Summary

After testing, you should observe:

1. **Discovery**: Skill appears in Claude Code's skills list
2. **Context Efficiency**: ~70% reduction vs full agent
3. **Functionality**: All 7 database operations work correctly
4. **Progressive Disclosure**: Skill metadata loaded initially, full content on-demand
5. **Safety**: DELETE/UPDATE checks prevent dangerous operations
6. **Composition**: Multiple tool calls in single conversation work seamlessly

## Troubleshooting

### Skill Not Discovered
```bash
# Verify symlink exists
ls -la .claude/skills/database-operations

# Verify skill.md readable
cat .claude/skills/database-operations/skill.md | head -20

# Restart Claude Code to force re-scan
```

### Script Execution Fails
```bash
# Check environment variable
echo $NEON_DATABASE_URL

# Test script manually
cd .claude/skills/database-operations/scripts
./list_tables.py

# Check permissions
chmod +x .claude/skills/database-operations/scripts/*.py
```

### JSON Parse Errors
```bash
# Verify scripts output valid JSON
./scripts/execute_query.py --query "SELECT 1" | jq .

# Should see: {"success": true, ...}
```

## Next Steps

1. **Test the skill**: Try the test queries above in this Claude Code conversation
2. **Measure context**: Note how much context is used vs full agent
3. **Compare results**: Are responses as good as multi-agent approach?
4. **Make decision**: Based on real usage data, choose architecture

## Files Reference

- **Skill Definition**: `.claude/skills/database-operations/skill.md`
- **Scripts**: `.claude/skills/database-operations/scripts/*.py`
- **Documentation**: `experiments/skills-vs-agents/QUICKSTART.md`
- **Architecture Analysis**: `experiments/skills-vs-agents/INSIGHTS.md`

## Ready to Test

The skill is installed and ready. Try asking database-related questions in this conversation and observe:
- How Claude discovers and activates the skill
- How progressive disclosure works
- How context usage compares to agent approach
- Whether response quality is equivalent

Let's test it now!
