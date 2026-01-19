# How to Compare Skills vs Agents - Quick Guide

## TL;DR

```bash
# 1. Run the comparison (takes ~30 seconds)
cd experiments/skills-vs-agents/comparison
./run_comparison.py

# 2. View results
cat ../results/comparison_*.json | jq '.summary'

# 3. Make decision based on data
```

## What Gets Compared

The comparison runner executes **10 identical test queries** through both implementations:

**Skills-Based** → Scripts in `.claude/skills/database-operations/`
**Agent-Based** → NeonAgent in `agents/neon-database/`

### Test Queries

1. ✅ "How many contractors are in the database?" (simple count)
2. ✅ "How many active contractors do we have?" (filtered count)
3. ✅ "What tables are in the database?" (schema discovery)
4. ✅ "What columns does the contractors table have?" (table description)
5. ✅ "Show me all contractors with their details" (multi-column query)
6. ✅ "What's the size of the contractors table?" (table stats)
7. ✅ "First show schema, then count contractors" (multi-step)
8. ✅ "List tables, describe projects, count projects" (three-step)
9. ✅ "Analyze contractor distribution by status" (complex GROUP BY)
10. ✅ "Show data from nonexistent_table" (error handling)

## Metrics Measured

For each query:

| Metric | What It Tells You |
|--------|-------------------|
| **Context Tokens** | How much context window is used |
| **Execution Time** | How fast the query executes |
| **Success Rate** | Whether it works correctly |
| **Error Handling** | How gracefully failures are handled |

## Running the Comparison

### Step 1: Prerequisites

```bash
# Verify skills installed
ls .claude/skills/database-operations/skill.md
# Should exist (we installed it earlier)

# Verify agent exists
ls agents/neon-database/agent.py
# Should exist

# Check environment
echo $NEON_DATABASE_URL  # Should show postgresql://...
echo $ANTHROPIC_API_KEY  # Should show sk-ant-...
```

### Step 2: Execute

```bash
cd experiments/skills-vs-agents/comparison
./run_comparison.py
```

**Expected output**:
```
====================================================================
Skills vs Agent Architecture Comparison
====================================================================

Test 1/10: Count contractors
  Running skills-based test...
    ✅ PASS
    Time: 156ms
    Context: ~800 tokens

  Running agent-based test...
    ✅ PASS
    Time: 2341ms
    Context: ~4500 tokens
...
```

**Duration**: ~30 seconds (10 tests × 2 implementations × ~1.5sec each)

### Step 3: Review Results

```bash
# View summary
cat ../results/comparison_*.json | jq '.summary'
```

**Example output**:
```json
{
  "total_tests": 10,
  "skills": {
    "successful": 10,
    "failed": 0,
    "avg_execution_time_ms": 175.23,
    "avg_context_tokens": 950
  },
  "agent": {
    "successful": 10,
    "failed": 0,
    "avg_execution_time_ms": 2200.45,
    "avg_context_tokens": 4800
  },
  "comparison": {
    "context_reduction_pct": 80.2,
    "time_difference_ms": 2025.22,
    "skills_faster": true
  }
}
```

## Interpreting Results

### Context Reduction %

**What it means**: How much less context window the skills approach uses

```
Context Reduction = (1 - skills_tokens / agent_tokens) × 100

Example: (1 - 950 / 4800) × 100 = 80.2%
```

**Decision criteria**:
- ✅ **>70%**: Strong case for skills (significant savings)
- ⚠️ **50-70%**: Moderate savings (consider other factors)
- ❌ **<50%**: Limited benefit (probably stick with agents)

**Why it matters**:
- More queries fit in same context window
- Better scaling for long conversations
- Native Claude Code integration benefit

### Time Difference

**What it means**: Speed difference between approaches

```
Time Difference = skills_time - agent_time

Positive = Agent faster
Negative = Skills faster
```

**Decision criteria**:
- Skills faster for one-off queries (expected)
- Agent faster for repeated queries with connection pooling
- If skills >2x slower: Performance concern

**Why it matters**:
- User experience (response time)
- Cost (longer execution = more API time)

### Success Rate

**What it means**: % of tests that completed successfully

**Decision criteria**:
- Both should be 100% or very close
- If either <90%: Implementation problems

**Why it matters**:
- Reliability
- Functional equivalence

## Making the Decision

### Scenario 1: Skills Dominate

**Results**:
- Context reduction: 80%+
- Time: Similar or faster
- Success rate: 100%

**Decision**: ✅ **Choose skills-based**

**Why**: Significant context savings, native Claude Code support, no performance penalty

### Scenario 2: Mixed Results (Most Likely)

**Results**:
- Context reduction: 75-85%
- Time: Skills faster for one-off, agent faster for repeated
- Success rate: Both 100%

**Decision**: ⚖️ **Choose hybrid**

**Why**: Get benefits of both - skills for simple queries (context efficient), agents for complex sessions (connection pooling)

**Implementation**:
```python
def route_query(query, complexity):
    if complexity <= 3:  # Simple queries
        return use_skill(query)
    else:  # Complex queries
        return use_agent(query)
```

### Scenario 3: Agent Wins (Unlikely)

**Results**:
- Context reduction: <50%
- Time: Agent significantly faster
- Success rate: Agent better

**Decision**: ❌ **Stick with agents**

**Why**: Skills benefits not realized in practice, agent approach working well

## Quick Decision Matrix

```
                Context     Time        Success    Decision
                Reduction   Difference  Rate
────────────────────────────────────────────────────────────
Skills Win      >70%        Similar     100%       → Skills
Mixed Results   70-85%      Mixed       100%       → Hybrid
Agent Win       <50%        Agent       >Skills    → Agent
```

## Viewing Detailed Results

### Full JSON Output

```bash
# Pretty print full results
cat ../results/comparison_*.json | jq .

# View specific test case
cat ../results/comparison_*.json | jq '.skills_results[0]'

# Compare test #3 between approaches
cat ../results/comparison_*.json | jq '{
  skills: .skills_results[2],
  agent: .agent_results[2]
}'
```

### Summary Statistics Only

```bash
cat ../results/comparison_*.json | jq '.summary'
```

### Context Usage by Test

```bash
# Skills context usage per test
cat ../results/comparison_*.json | jq '.skills_results[] | {
  test: .test_name,
  tokens: .context_tokens_estimated
}'

# Agent context usage per test
cat ../results/comparison_*.json | jq '.agent_results[] | {
  test: .test_name,
  tokens: .context_tokens_estimated
}'
```

## Troubleshooting

### "Agent not available"

**Symptom**:
```
Agent execution error: No module named 'agents.neon_database'
```

**Fix**:
```bash
# Add to Python path
export PYTHONPATH=/home/louisdup/Agents/claude:$PYTHONPATH

# Re-run
./run_comparison.py
```

### "Script execution failed"

**Symptom**:
```
Script execution failed: [Errno 2] No such file or directory
```

**Fix**:
```bash
# Verify skills symlink
ls -la .claude/skills/database-operations

# If missing, recreate
ln -s $(pwd)/experiments/skills-vs-agents/skills-based/database-operations \
      .claude/skills/database-operations
```

### "Database connection failed"

**Symptom**:
```
NEON_DATABASE_URL not set
```

**Fix**:
```bash
export NEON_DATABASE_URL="postgresql://..."
```

## Next Steps After Comparison

1. **Review results** in `results/comparison_*.json`
2. **Analyze summary** statistics (context, time, success rate)
3. **Make decision** using decision matrix above
4. **Update STATUS.md** with your choice
5. **Implement** chosen architecture in production

## Files Created

```
comparison/
├── test_cases.json          ✅ 10 standardized test queries
├── run_comparison.py        ✅ Automated comparison runner
└── README.md                ✅ Detailed documentation

../results/
└── comparison_*.json        ✅ Generated after running tests
```

## Bottom Line

**Run this**:
```bash
cd experiments/skills-vs-agents/comparison && ./run_comparison.py
```

**Review this**:
```bash
cat ../results/comparison_*.json | jq '.summary'
```

**Decide based on**:
- Context reduction % (is 70%+ savings worth it?)
- Time difference (is performance acceptable?)
- Your priorities (context efficiency vs performance?)

**Time investment**: 30 seconds to run, 5 minutes to analyze, informed decision for life of project.
