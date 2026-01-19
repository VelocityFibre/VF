# Comparison Test Harness

**Purpose**: Run identical test cases through both skills-based and agent-based implementations to objectively compare them.

## Overview

This directory contains tools to scientifically compare the two architectural approaches:

```
comparison/
├── test_cases.json          # 10 standardized test queries
├── run_comparison.py        # Automated test runner
└── README.md                # This file
```

## Test Cases

10 test cases across 5 categories:

### 1. Simple Queries (2 tests)
- Count contractors (simplest baseline)
- Count active contractors (basic filtering)

### 2. Schema Discovery (2 tests)
- List all tables (metadata operations)
- Describe contractors table (structure introspection)

### 3. Business Intelligence (2 tests)
- List contractors with details (multi-column retrieval)
- Get table statistics (aggregation)

### 4. Multi-Step (2 tests)
- Schema then query (two-step composition)
- List, describe, query (three-step workflow)

### 5. Complex/Edge Cases (2 tests)
- Multi-table analysis (GROUP BY, complex query)
- Error handling (invalid table name)

## Metrics Measured

For each test case, both implementations measured on:

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Context Tokens** | Estimated tokens used | Context efficiency, scalability |
| **Execution Time** | Milliseconds to complete | User experience, performance |
| **Success Rate** | % of tests passing | Reliability, functionality |
| **Error Handling** | Graceful failures | Robustness |

## Running the Comparison

### Prerequisites

```bash
# Ensure both implementations available
ls agents/neon-database/agent.py  # Agent-based
ls .claude/skills/database-operations/skill.md  # Skills-based

# Environment variables set
export ANTHROPIC_API_KEY=sk-ant-...
export NEON_DATABASE_URL=postgresql://...

# Dependencies installed
pip install psycopg2-binary python-dotenv anthropic
```

### Execute Comparison

```bash
cd experiments/skills-vs-agents/comparison

# Make executable
chmod +x run_comparison.py

# Run all tests
./run_comparison.py
```

### Output

**Console Output**:
```
====================================================================
Skills vs Agent Architecture Comparison
====================================================================

Test suite: Skills vs Agent Architecture Comparison
Total tests: 10

Test 1/10: Count contractors
  Category: simple_query
  Complexity: 1/10

  Running skills-based test...
    ✅ PASS
    Time: 156ms
    Context: ~800 tokens

  Running agent-based test...
    ✅ PASS
    Time: 2341ms
    Context: ~4500 tokens

----------------------------------------------------------------------
...

====================================================================
COMPARISON SUMMARY
====================================================================

Total Tests: 10

Skills-Based Approach:
  Success Rate: 10/10 (100%)
  Avg Execution Time: 175ms
  Avg Context Usage: 950 tokens

Agent-Based Approach:
  Success Rate: 10/10 (100%)
  Avg Execution Time: 2200ms
  Avg Context Usage: 4800 tokens

Comparison:
  Context Reduction: 80.2%
  Time Difference: 2025ms (Skills faster)

====================================================================
```

**JSON Results**:
```
results/comparison_20251209_125530.json
```

Contains detailed results for analysis:
```json
{
  "timestamp": "2025-12-09T12:55:30",
  "skills_results": [...],
  "agent_results": [...],
  "summary": {...}
}
```

## Understanding Results

### Context Tokens (Estimated)

**Skills-Based Calculation**:
```
Skill metadata (YAML): 50 tokens
+ Full skill.md content: 600 tokens (when activated)
+ Result data: ~300 tokens
= ~950 tokens average
```

**Agent-Based Calculation**:
```
Agent class scaffolding: 2000 tokens
+ Tool definitions (all 7 tools): 2000 tokens
+ Conversation + result: ~800 tokens
= ~4800 tokens average
```

**Why Agent Uses More**:
- All tools loaded in context (whether used or not)
- Agent scaffolding always present
- No progressive disclosure

**Why Skills Uses Less**:
- Progressive disclosure (load on demand)
- Scripts execute from filesystem (0 context cost)
- Only result data enters context

### Execution Time

**Skills-Based**:
- Script execution: ~100-200ms
- Process spawning overhead: ~20-50ms
- No connection pooling (new connection each time)

**Agent-Based**:
- First query: ~2000-3000ms (agent initialization)
- Subsequent queries: ~500-1000ms (connection pooled)
- LLM tool selection overhead: ~100-500ms

**Interpretation**:
- Skills faster for one-off queries
- Agent faster for repeated queries (connection pooling)

## Comparison Report

After running, analyze results in:

```bash
cat results/comparison_YYYYMMDD_HHMMSS.json | jq '.summary'
```

**Key Metrics to Review**:

1. **Context Reduction %**
   - Expected: 70-85% reduction with skills
   - If <70%: Skills may not be worth it
   - If >85%: Strong case for skills

2. **Success Rate**
   - Both should be 100% or close
   - If skills <90%: Implementation issues
   - If agent <90%: Agent setup issues

3. **Execution Time**
   - Skills expected faster for one-off
   - Agent expected faster for repeated (with pooling)
   - If skills >3x slower: Performance concern

## Interpreting Results for Decision

### If Skills Win (Expected)

**Indicators**:
- ✅ 70-85% context reduction
- ✅ Similar or better execution time
- ✅ 100% success rate
- ✅ Better error handling

**Decision**: Choose skills-based for FibreFlow

**Rationale**:
- Context efficiency matters for scaling
- Claude Code native integration
- Simpler maintenance

### If Agent Wins (Unlikely)

**Indicators**:
- Skills context reduction <50%
- Skills significantly slower (>2x)
- Skills lower success rate (<90%)

**Decision**: Stick with agent-based

**Rationale**:
- Already built and working
- Performance matters more than context
- Context efficiency not realized in practice

### If Mixed Results

**Indicators**:
- Context: Skills win (70%+ reduction)
- Performance: Agent wins (connection pooling)
- Quality: Tie (both 100% success)

**Decision**: Hybrid approach

**Rationale**:
- Use skills for simple queries (80% of usage)
- Use agent for complex sessions (20% of usage)
- Get best of both worlds

## Customizing Tests

### Add New Test Case

Edit `test_cases.json`:

```json
{
  "id": "custom_001",
  "category": "custom",
  "name": "My custom test",
  "description": "Tests specific functionality",
  "query": "Natural language query here",
  "expected_tool": "execute_query",
  "complexity": 3,
  "expected_context_tokens": {
    "skills": 1000,
    "agent": 4500
  }
}
```

### Modify Metrics

Edit `run_comparison.py` and add metrics to `result` dict:

```python
result["custom_metric"] = calculate_custom_metric()
```

## Limitations

**Current Implementation**:
- SQL generation simplified (predefined queries)
- Context token estimation (not actual measurement)
- No LLM comparison (both use same model)
- Limited error scenario coverage

**Future Enhancements**:
- Actual token counting via API
- Real LLM natural language to SQL conversion
- More edge cases and error scenarios
- Performance testing under load
- Multi-user concurrent testing

## Troubleshooting

### Agent Not Available

```
Error: Agent not available: No module named 'agents.neon_database'
```

**Fix**:
```bash
# Ensure agent exists
ls agents/neon-database/agent.py

# Check Python path
export PYTHONPATH=/home/louisdup/Agents/claude:$PYTHONPATH
```

### Skills Not Found

```
Error: Script execution failed: No such file or directory
```

**Fix**:
```bash
# Verify skills symlinked
ls -la .claude/skills/database-operations

# Re-create symlink if needed
ln -s $(pwd)/experiments/skills-vs-agents/skills-based/database-operations \
      .claude/skills/database-operations
```

### Database Connection Failed

```
Error: NEON_DATABASE_URL not set
```

**Fix**:
```bash
export NEON_DATABASE_URL="postgresql://..."
```

## Next Steps

1. **Run comparison**: Execute `./run_comparison.py`
2. **Review results**: Check `results/comparison_*.json`
3. **Analyze metrics**: Focus on context reduction and success rate
4. **Make decision**: Use decision framework in `../README.md`
5. **Document choice**: Update `../STATUS.md` with decision

## Files Reference

- `test_cases.json` - Test definitions
- `run_comparison.py` - Automated runner
- `../results/` - Output directory (git-ignored)
- `../README.md` - Experiment overview
- `../STATUS.md` - Current status and decision framework
