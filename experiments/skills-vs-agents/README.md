# Skills-Based vs Multi-Agent Architecture: Proof of Concept

## Experiment Overview

This is an isolated proof-of-concept comparing **two competing architectural approaches** for AI agent capabilities:

**Option A: Multi-Agent Specialist** (FibreFlow's current approach)
- Dedicated agent per domain (VPS, Database, etc.)
- Each agent = 200K dedicated context window
- Orchestrator routes tasks to specialist agents
- Location: `agents/neon-database/`

**Option B: Skills-Based General Agent** (Anthropic's new paradigm)
- ONE general agent with progressive skill disclosure
- Skills loaded on-demand into shared context
- Context efficiency through lazy loading
- Location: `experiments/skills-vs-agents/skills-based/`

## Why This Experiment?

FibreFlow is **pre-production** - now is the time to validate architecture before lock-in.

The question: **Does skills-based approach provide better outcomes for Claude Code integration?**

## Directory Structure

```
experiments/skills-vs-agents/
├── README.md                          # This file
├── INSIGHTS.md                        # Key insights from Anthropic Agent Skills talk
│
├── skills-based/                      # OPTION B: Skills implementation
│   ├── database-operations/
│   │   ├── skill.md                  # Progressive disclosure format
│   │   └── scripts/                  # Executable tools
│   │       ├── list_tables.py
│   │       ├── execute_query.py
│   │       ├── describe_table.py
│   │       └── table_stats.py
│   └── general_agent.py              # Claude Code agent using skills
│
├── comparison/                        # Test harness
│   ├── test_cases.json               # Standardized test queries
│   ├── run_comparison.py             # Executes both implementations
│   └── measure_results.py            # Analyzes results
│
└── results/                           # Output (git-ignored)
    ├── comparison_report.md
    ├── option_a_results.json
    └── option_b_results.json
```

## Test Cases

Both implementations tested with identical queries:

### 1. Simple Query (Baseline)
**Query**: "How many active contractors are there?"
**Tests**: Basic capability, context efficiency

### 2. Cross-Domain Query (Skills advantage?)
**Query**: "Show contractors working on projects where VPS CPU > 80%"
**Tests**: Ability to compose multiple domains in one conversation

### 3. Complex Analysis (Specialist advantage?)
**Query**: "Analyze contractor performance trends over 6 months with statistical breakdown"
**Tests**: Deep domain work, context capacity

### 4. Multi-Step Workflow (Composition)
**Query**: "Find duplicate contractor entries, generate cleanup SQL, and estimate impact"
**Tests**: Multi-step reasoning, tool orchestration

## Measurement Criteria

| Metric | How Measured | Why It Matters |
|--------|--------------|----------------|
| **Context Tokens** | Count tokens in conversation | Efficiency, scalability |
| **Response Time** | Seconds from query to answer | User experience |
| **Response Quality** | Accuracy (correct answer?) | Reliability |
| **Implementation Effort** | Lines of code, complexity | Maintainability |
| **Cross-Domain Ease** | Can it answer query #2? | Flexibility |

## Running the Experiment

### Prerequisites
```bash
# Activate environment
source venv/bin/activate

# Ensure environment variables set
export ANTHROPIC_API_KEY=sk-ant-...
export NEON_DATABASE_URL=postgresql://...
```

### Execute Comparison
```bash
cd experiments/skills-vs-agents

# Run both implementations with test cases
./comparison/run_comparison.py

# Analyze results
./comparison/measure_results.py

# View report
cat results/comparison_report.md
```

## Decision Framework

After running experiments, decide based on data:

**Choose Skills-Based IF**:
- ✅ Context usage < 50% of multi-agent approach
- ✅ Cross-domain queries work seamlessly
- ✅ Response quality equal or better
- ✅ Implementation simpler to maintain

**Choose Multi-Agent IF**:
- ✅ Complex queries hit context limits with skills
- ✅ Specialist agents provide better quality
- ✅ Cross-domain queries are rare (<10% of usage)
- ✅ Parallel execution needed

**Hybrid IF**:
- Both approaches have strengths for different query types
- Implement smart routing based on complexity

## Key Insights Reference

See `INSIGHTS.md` for detailed analysis of Anthropic's Agent Skills talk and architectural implications.

## Current Status

- [ ] Skills-based implementation complete
- [ ] Test harness built
- [ ] Comparison executed
- [ ] Results analyzed
- [ ] Architecture decision documented

## Notes

This is an **experiment**, not production code. After decision:
- Winning approach becomes production architecture
- Losing approach archived for reference
- No wasted effort - we gained knowledge

**Principle**: Measure, don't theorize.
