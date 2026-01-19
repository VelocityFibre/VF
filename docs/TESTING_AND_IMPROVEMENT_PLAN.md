# Testing and Improvement Plan

**Date**: 2025-12-22
**Purpose**: Validate and iteratively improve Auto-Claude integration and workflow documentation
**Approach**: Test → Measure → Analyze → Improve → Repeat

---

## Overview

We have two main areas to test and improve:

1. **Auto-Claude Integration** (Phases 1+2+3) - Technical implementation
2. **Workflow Documentation** - Clarity and usability

Each requires different testing approaches.

---

## Part 1: Testing Auto-Claude Integration

### Phase 1: Worktree Safety - Testing

#### ✅ Already Done

- 6 unit tests passing
- Tested creation, isolation, merge, cleanup

#### 🧪 Real-World Testing Needed

**Test 1: Simple Agent Build with Worktrees**

```bash
# Create minimal test agent
cat > harness/specs/test_worktree_spec.md << 'EOF'
# Test Worktree Agent

Simple agent to test Phase 1 worktree isolation.

## Capabilities
1. Store data in memory
2. Retrieve data by key

## Tools
- store_data(key, value)
- get_data(key)

## Success Criteria
- 5 simple features
- All in isolated worktree
- Main branch unchanged during build
EOF

# Run with worktrees
./harness/runner.py --agent test_worktree --use-worktree

# Validation checks:
# 1. During build: git log main should be unchanged
# 2. After build: Changes should be in main
# 3. .worktrees/ should be cleaned up
```

**What to measure**:
- ✅ Main branch commits during build: Should be 0
- ✅ Worktree created: Check `.worktrees/` exists during build
- ✅ Worktree cleaned: Check `.worktrees/` empty after build
- ✅ Changes merged: Agent files exist in `agents/test_worktree/`

**Expected results**:
- Main branch: 0 commits during build ✅
- Merge: All changes applied after build ✅
- Cleanup: No leftover worktrees ✅

---

### Phase 2: Self-Healing Validation - Testing

#### ✅ Already Done

- Manual simulation: 5/5 features self-healed
- Tested syntax, import, logic errors

#### 🧪 Real-World Testing Needed

**Test 2: Intentional Bug Build**

```bash
# Method 1: Modify coding_agent.md to inject bugs
# (Too invasive, skip)

# Method 2: Build simple agent, monitor self-healing

./harness/runner.py --agent test_selfheal --model haiku

# Then analyze the output:
cat harness/runs/latest/claude_progress.md | grep -A 5 "Validation"
cat harness/runs/latest/feature_list.json | jq '.features[] | select(.validation_attempts > 1)'
```

**What to measure**:
- Average validation attempts per feature
- First-attempt success rate
- Self-healing success rate (attempts 2-10)
- Manual intervention rate

**Success criteria** (Phase 2 targets):
- ✅ Completion rate: ≥90%
- ✅ Avg attempts: <3 per feature
- ✅ Manual interventions: <10%
- ✅ First-attempt success: >60%

**How to track**:
```bash
# After build, analyze metrics
cat harness/runs/latest/feature_list.json | jq '
{
  total: .total_features,
  completed: .completed,
  completion_rate: (.completed / .total_features),
  with_healing: [.features[] | select(.validation_attempts > 1)] | length,
  avg_attempts: ([.features[].validation_attempts] | add / length),
  manual_needed: [.features[] | select(.manual_review_needed == true)] | length
}'
```

---

### Phase 3: Parallel Execution - Testing

#### ✅ Already Done

- 14 unit tests passing
- DependencyGraph tested
- RateLimitHandler tested

#### 🧪 Real-World Testing Needed

**Test 3: Parallel Build with Dependency Levels**

```bash
# Create test agent with clear dependency structure
cat > harness/specs/test_parallel_spec.md << 'EOF'
# Test Parallel Agent

Agent designed to test Phase 3 parallel execution.

## Capabilities
1. Data storage (foundation)
2. Data validation (depends on storage)
3. Data transformation (depends on validation)

## Tools
- store(data)
- validate(data)
- transform(data)

## Success Criteria
- 15 features with dependencies
- Should parallelize into ~4-5 levels
- Speedup vs sequential
EOF

# First: Sequential baseline (for comparison)
time ./harness/runner.py --agent test_parallel_seq --no-parallel

# Then: Parallel mode
time ./harness/runner.py --agent test_parallel_par --parallel 6 --resume

# Compare times
```

**What to measure**:
- Sequential build time (baseline)
- Parallel build time (6 workers)
- Actual speedup factor
- Number of dependency levels
- Rate limit errors
- Worker efficiency

**Success criteria** (Phase 3 targets):
- ✅ Speedup: ≥4x (vs sequential)
- ✅ Rate limit errors: <5%
- ✅ Completion rate: ≥90% (same as Phase 2)

**How to track**:
```bash
# Metrics in feature_list.json
cat harness/runs/latest/feature_list.json | jq '.metrics'

# Expected output:
# {
#   "phase3_enabled": true,
#   "parallel_workers": 6,
#   "total_levels": 4,
#   "sequential_time_estimate": 300,
#   "actual_time": 65,
#   "speedup_factor": 4.6,
#   "rate_limit_errors": 3,
#   "rate_limit_rate": 0.02
# }
```

---

### Integrated Testing (All 3 Phases)

**Test 4: Complete Agent Build End-to-End**

```bash
# Build moderate-complexity agent with all phases
./harness/runner.py --agent sharepoint --parallel 6

# Expected behavior:
# - Phase 1: Isolated worktrees (safe)
# - Phase 2: Self-healing (quality)
# - Phase 3: Parallel execution (speed)

# Validation:
# 1. Check worktrees were used
ls -la .worktrees/  # Should have worktrees during build

# 2. Check self-healing happened
cat harness/runs/latest/feature_list.json | jq '.features[] | select(.validation_attempts > 1)'

# 3. Check parallel speedup
cat harness/runs/latest/feature_list.json | jq '.metrics.speedup_factor'

# 4. Verify agent works
./venv/bin/pytest tests/test_sharepoint.py -v
./venv/bin/python3 demo_sharepoint.py
```

**Success criteria**:
- ✅ All 3 phases active
- ✅ Completion rate: ≥90%
- ✅ Speedup: ≥4x
- ✅ Agent fully functional
- ✅ Tests passing

---

## Part 2: Testing Workflow Documentation

### Test 5: New User Comprehension

**Goal**: Verify documentation is clear and actionable

**Method**: User testing with team members

**Test script** (give to team member):

```
Scenario: You need to build a new Slack integration agent.

Questions:
1. Which tool should you use first? (Answer should be: Agent OS)
2. Why? (Answer should be: Requirement needs planning)
3. What's the next step after Agent OS? (Answer: FibreFlow Harness)
4. How long will the harness take? (Answer: Overnight/4-6x faster)

Now find the answer in CLAUDE.md without asking anyone.

Time how long it takes to find answers (should be <5 minutes).
```

**What to measure**:
- Time to find correct answer
- Accuracy of answer
- Confidence level (1-5 scale)
- Confusion points (where did they get stuck?)

**Success criteria**:
- ✅ Correct answers: >80%
- ✅ Time to find: <5 minutes
- ✅ Confidence: ≥4/5
- ✅ No major confusion points

**Improvement actions**:
- If users confused at step X → Add clarification/example
- If users can't find answer → Add to quick reference table
- If terminology unclear → Add glossary

---

### Test 6: Decision Tree Accuracy

**Goal**: Verify decision tree guides users correctly

**Method**: Scenario-based testing

**Test scenarios**:

| Scenario | Expected Tool | User Selected | Correct? |
|----------|---------------|---------------|----------|
| "Want SharePoint agent" (vague) | Agent OS | ? | ? |
| "Have spec, 50 features" | Harness | ? | ? |
| "Fix typo in agent.py" | Direct dev | ? | ? |
| "Add 2 simple tools" | Direct dev | ? | ? |
| "Add 15 complex tools" | Harness | ? | ? |

**How to run**:
1. Give scenarios to 3-5 team members
2. Ask them to use decision tree
3. Record their selections
4. Compare to expected

**Success criteria**:
- ✅ Accuracy: >90%
- ✅ No ambiguous cases
- ✅ Fast decision (<2 min per scenario)

**Improvement actions**:
- If <90% accuracy → Decision tree needs refinement
- If ambiguous cases → Add more criteria
- If slow decisions → Simplify tree

---

### Test 7: Workflow Example Clarity

**Goal**: Verify example is followable

**Method**: Real execution of Teams agent example

**Test process**:

```bash
# Follow CLAUDE.md example exactly as written
# Document any deviations needed

# Step 1: Agent OS planning (example says 30 min)
# - Did it actually take 30 min?
# - Were Q&A questions clear?
# - Was output usable?

# Step 2: Copy spec (example says simple copy)
# - Was the spec in right format?
# - Did it need editing?

# Step 3: Harness build (example says overnight)
# - Did it complete overnight?
# - Were there issues?
# - Was output as described?

# Step 4: Test and deploy (example says 30 min)
# - Was testing straightforward?
# - Did agent work as expected?
```

**What to measure**:
- Actual time vs documented time
- Steps that needed adjustment
- Unexpected issues
- Final result quality

**Success criteria**:
- ✅ Example is followable without changes
- ✅ Time estimates accurate (±20%)
- ✅ No undocumented steps needed
- ✅ Result matches description

**Improvement actions**:
- If times off → Update estimates
- If steps missing → Add to example
- If issues encountered → Add troubleshooting

---

## Metrics Collection System

### Automatic Metrics (Built-in)

**Phase 1 Metrics** (in git history):
```bash
# Count worktree commits vs main commits during build
git log --since="2025-12-22" --oneline --all | grep worktree | wc -l
git log --since="2025-12-22" --oneline main | wc -l
```

**Phase 2 Metrics** (in feature_list.json):
```json
{
  "features": [
    {
      "id": 15,
      "validation_attempts": 3,
      "self_healing_used": true,
      "manual_review_needed": false
    }
  ]
}
```

**Phase 3 Metrics** (in feature_list.json):
```json
{
  "metrics": {
    "phase3_enabled": true,
    "parallel_workers": 6,
    "speedup_factor": 4.5,
    "rate_limit_errors": 3
  }
}
```

### Manual Metrics (Need to Track)

**Create metrics tracking spreadsheet**:

```
Build Date | Agent Name | Features | Sequential Time | Parallel Time | Speedup | Completion Rate | Self-Healing Rate | Issues
2025-12-23 | test_simple | 10 | 200 min | 50 min | 4.0x | 100% | 30% | None
2025-12-24 | sharepoint | 60 | 1200 min | 220 min | 5.5x | 92% | 45% | 5 manual reviews
...
```

**Track over time**:
- Are speedups consistent?
- Are completion rates stable?
- Are there patterns in issues?

---

## Improvement Process

### Step 1: Collect Data

**Weekly**:
- Run test builds (Test 1-4)
- Record metrics in spreadsheet
- Note any issues encountered

**Monthly**:
- User comprehension testing (Test 5)
- Decision tree accuracy (Test 6)
- Workflow example validation (Test 7)

### Step 2: Analyze Results

**Technical Analysis** (Auto-Claude):
```bash
# Generate report
cat > metrics_analysis.py << 'EOF'
import json
from pathlib import Path

# Load all build metrics
runs = Path("harness/runs/").glob("*/feature_list.json")

speedups = []
completion_rates = []
healing_rates = []

for run in runs:
    with open(run) as f:
        data = json.load(f)
        metrics = data.get("metrics", {})

        if metrics.get("phase3_enabled"):
            speedups.append(metrics.get("speedup_factor", 0))

        total = data["total_features"]
        completed = data["completed"]
        completion_rates.append(completed / total)

        healed = len([f for f in data["features"] if f.get("self_healing_used")])
        healing_rates.append(healed / total)

print(f"Average speedup: {sum(speedups) / len(speedups):.1f}x")
print(f"Average completion: {sum(completion_rates) / len(completion_rates) * 100:.1f}%")
print(f"Average healing: {sum(healing_rates) / len(healing_rates) * 100:.1f}%")
EOF

./venv/bin/python3 metrics_analysis.py
```

**Documentation Analysis**:
- User test accuracy: Did they find correct answers?
- Decision tree accuracy: Did they choose right tools?
- Time to comprehension: How long to understand?

### Step 3: Identify Issues

**Technical Issues** (Auto-Claude):

**If speedup < 4x**:
- Check dependency structure (too linear?)
- Check rate limits (too many errors?)
- Check worker efficiency (workers idle?)

**If completion rate < 90%**:
- Check self-healing effectiveness
- Check common failure patterns
- Check prompt clarity

**If healing rate too high (>50%)**:
- Many bugs in generated code
- May need better initializer prompt
- May need better spec quality

**Documentation Issues**:

**If user accuracy < 90%**:
- Decision tree needs refinement
- Add more examples
- Clarify terminology

**If time to comprehension > 5 min**:
- Reorganize content
- Add quick reference section
- Improve navigation

### Step 4: Make Improvements

**Technical Improvements**:

**Example: Low Speedup**
```bash
# Issue: Speedup only 2x (expected 4-6x)
# Analysis: Dependency graph is linear

# Improvement: Enhance initializer prompt
nano harness/prompts/initializer.md
# Add: "Create independent features when possible to maximize parallelism"
```

**Example: Low Completion Rate**
```bash
# Issue: Completion rate 75% (expected 90%)
# Analysis: Complex errors not self-healing

# Improvement: Enhance self-healing guidance
nano harness/prompts/coding_agent.md
# Add more specific fix strategies for common error types
```

**Documentation Improvements**:

**Example: Users Confused About Tool Selection**
```bash
# Issue: Users picking wrong tool 20% of time
# Analysis: Decision tree not specific enough

# Improvement: Add feature count thresholds
nano CLAUDE.md
# Change "many features" to "10+ features"
# Add concrete examples for 1-2, 3-9, 10+ features
```

### Step 5: Validate Improvements

**Re-test after changes**:
```bash
# Run same test scenarios
# Compare new metrics vs old

# Example:
# Before: Speedup 2x, Completion 75%
# After improvement: Speedup 4.5x, Completion 92%
# Result: ✅ Improvement validated
```

---

## Continuous Improvement Checklist

### Monthly Tasks

- [ ] Run technical tests (Test 1-4)
- [ ] Collect metrics from all builds
- [ ] Analyze trends (improving? declining?)
- [ ] User comprehension testing (Test 5-7)
- [ ] Document common issues
- [ ] Prioritize improvements

### Quarterly Tasks

- [ ] Full review of Auto-Claude phases
- [ ] Documentation audit (is it current?)
- [ ] User satisfaction survey
- [ ] Benchmark against baselines
- [ ] Plan major improvements
- [ ] Update success criteria if needed

### Metrics Dashboard (Recommended)

**Create simple dashboard**:

```bash
# scripts/metrics-dashboard
#!/bin/bash

echo "=== Auto-Claude Integration Metrics ==="
echo ""

echo "Phase 1 (Worktrees):"
echo "  Main branch safety: $(check_main_commits_during_builds)"
echo "  Cleanup rate: $(check_worktree_cleanup_rate)"

echo ""
echo "Phase 2 (Self-Healing):"
echo "  Completion rate: $(calculate_completion_rate)"
echo "  Avg attempts: $(calculate_avg_attempts)"
echo "  Manual rate: $(calculate_manual_rate)"

echo ""
echo "Phase 3 (Parallel):"
echo "  Avg speedup: $(calculate_avg_speedup)"
echo "  Rate limit rate: $(calculate_rate_limit_rate)"

echo ""
echo "Last 10 builds:"
show_recent_builds

echo ""
echo "Issues to address:"
identify_issues
```

---

## Quick Start Testing Guide

### Today: Immediate Testing

```bash
# 1. Test Phase 1 (Worktrees) - 30 minutes
./harness/runner.py --agent test_worktree
# Verify: Main branch unchanged, worktree cleaned

# 2. Test Phase 2 (Self-Healing) - Monitor existing build
# Analyze: harness/runs/latest/claude_progress.md
# Look for validation attempts and self-healing

# 3. Document results
nano docs/TESTING_RESULTS_$(date +%Y%m%d).md
```

### This Week: Real-World Validation

```bash
# 1. Build actual agent (not test)
./harness/runner.py --agent <real_agent> --parallel 6

# 2. Measure all metrics
# 3. Compare to targets
# 4. Document issues
```

### This Month: User Testing

```bash
# 1. Find 3 team members
# 2. Run Tests 5-7 (documentation)
# 3. Collect feedback
# 4. Update docs based on feedback
```

---

## Success Criteria Summary

### Technical (Auto-Claude)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Speedup** | ≥4x | Sequential time / Parallel time |
| **Completion** | ≥90% | Completed / Total features |
| **Self-Healing Avg** | <3 attempts | Sum attempts / Features healed |
| **Manual Rate** | <10% | Manual reviews / Total features |
| **Rate Limits** | <5% | Rate limit errors / Total requests |
| **Main Branch Safety** | 0 commits | Git log during builds |

### Documentation (Workflow)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **User Accuracy** | >90% | Correct tool selections |
| **Comprehension Time** | <5 min | Time to find answers |
| **Confidence** | ≥4/5 | User survey (1-5 scale) |
| **Example Followability** | 100% | Can follow without changes |

---

## Iteration Cycle

```
Week 1: Test → Collect metrics
Week 2: Analyze → Identify issues
Week 3: Improve → Make changes
Week 4: Validate → Re-test

Repeat monthly
```

**Goal**: Continuous improvement based on real-world usage data

---

## Summary

**Testing Strategy**:
1. ✅ Unit tests (already done)
2. 🧪 Real-world builds (Test 1-4)
3. 🧪 User comprehension (Test 5-7)
4. 📊 Metrics collection (ongoing)

**Improvement Strategy**:
1. Collect data weekly
2. Analyze monthly
3. Improve based on patterns
4. Validate improvements
5. Repeat

**Success**: System gets better over time based on usage data

---

**Status**: Testing plan ready to execute
**Next**: Run Test 1 (Worktree safety with real build)

---

*Testing and Improvement Plan created 2025-12-22*
