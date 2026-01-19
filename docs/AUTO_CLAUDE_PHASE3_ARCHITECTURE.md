# Auto-Claude Phase 3: Parallel Execution Architecture

**Date**: 2025-12-22
**Phase**: Parallel Execution
**Goal**: 16-24h → 2-4h build time (6-12x speedup)
**Status**: Design Phase

---

## Executive Summary

Phase 3 implements **concurrent feature development** by running multiple coding agent sessions simultaneously while respecting feature dependencies and API rate limits.

**Key Innovation**: Topological dependency scheduling enables maximum parallelism without breaking dependency constraints.

**Expected Impact**:
- **Sequential (Current)**: 50 features × 20 min = 16.7 hours
- **Parallel (Phase 3)**: 50 features / 6 workers × 20 min = 2.8 hours
- **Speedup**: 6x faster (conservative estimate with 6 workers)

---

## Architecture Overview

### Dependency-Aware Parallel Execution

```
feature_list.json
    ↓
Dependency Graph Analysis
    ↓
Topological Sort → Levels
    ↓
Level 0: [Features with no deps] → Run in parallel (6 workers)
    ↓ (wait for level completion)
Level 1: [Features depending on Level 0] → Run in parallel (6 workers)
    ↓ (wait for level completion)
Level 2: [Features depending on Level 0-1] → Run in parallel (6 workers)
    ↓
...continue until all features complete
```

**Key Principle**: Features in the same level have no dependencies on each other, so they can run concurrently.

---

## Component Design

### 1. DependencyGraph Class

**Purpose**: Analyze feature dependencies and compute execution levels

**Responsibilities**:
- Parse feature_list.json
- Build directed acyclic graph (DAG) of dependencies
- Perform topological sort
- Group features into dependency levels
- Detect circular dependencies

**Interface**:
```python
class DependencyGraph:
    def __init__(self, features: List[Dict])
    def build_graph(self) -> None
    def compute_levels(self) -> List[List[int]]  # Returns feature IDs grouped by level
    def get_feature(self, feature_id: int) -> Dict
    def validate_dependencies(self) -> bool  # Check for cycles
```

**Example**:
```python
# Input features:
features = [
    {"id": 1, "dependencies": []},
    {"id": 2, "dependencies": []},
    {"id": 3, "dependencies": [1]},
    {"id": 4, "dependencies": [1, 2]},
    {"id": 5, "dependencies": [3, 4]}
]

# Output levels:
levels = [
    [1, 2],        # Level 0: No dependencies
    [3, 4],        # Level 1: Depend on level 0
    [5]            # Level 2: Depend on levels 0-1
]
```

---

### 2. ParallelHarness Class

**Purpose**: Orchestrate parallel execution of coding agent sessions

**Responsibilities**:
- Initialize worker pool (default: 6 workers)
- Execute features level-by-level
- Monitor completion and failures
- Handle rate limit errors with backoff
- Aggregate results and metrics

**Interface**:
```python
class ParallelHarness:
    def __init__(self, agent_name: str, max_workers: int = 6)
    def run(self) -> Dict[str, Any]  # Returns execution summary
    def run_level(self, level: List[int]) -> List[bool]  # Returns success flags
    def run_feature(self, feature_id: int) -> bool  # Returns success/failure
    def handle_rate_limit(self, error: Exception) -> None  # Backoff strategy
```

**Worker Pool Strategy**:
- Use `concurrent.futures.ThreadPoolExecutor`
- Default: 6 workers (conservative, avoids rate limits)
- Configurable via `--parallel N` flag
- Each worker runs a full coding agent session

---

### 3. RateLimitHandler Class

**Purpose**: Manage Claude API rate limits with exponential backoff

**Responsibilities**:
- Detect rate limit errors (429 status codes)
- Implement exponential backoff
- Track retry attempts
- Provide backoff recommendations

**Interface**:
```python
class RateLimitHandler:
    def __init__(self, initial_delay: float = 1.0, max_delay: float = 60.0)
    def should_retry(self, attempt: int) -> bool
    def get_delay(self, attempt: int) -> float  # Exponential backoff
    def handle_error(self, error: Exception) -> float  # Returns delay seconds
```

**Backoff Strategy**:
```python
# Exponential backoff with jitter
delay = min(initial_delay * (2 ** attempt) + random(0, 1), max_delay)

# Example progression:
# Attempt 1: 1-2 seconds
# Attempt 2: 2-3 seconds
# Attempt 3: 4-5 seconds
# Attempt 4: 8-9 seconds
# Attempt 5: 16-17 seconds
# Attempt 6: 32-33 seconds
# Attempt 7+: 60-61 seconds (max)
```

---

### 4. SessionManager Class

**Purpose**: Manage individual coding agent sessions with isolation

**Responsibilities**:
- Create worktree for session (Phase 1 integration)
- Run coding agent session in worktree
- Apply self-healing validation (Phase 2 integration)
- Track session metrics (attempts, duration, success)
- Cleanup worktree after completion

**Interface**:
```python
class SessionManager:
    def __init__(self, agent_name: str, feature_id: int)
    def setup_session(self) -> WorkspaceInfo  # Create worktree
    def run_session(self) -> bool  # Execute coding agent
    def cleanup_session(self) -> None  # Cleanup worktree
    def get_metrics(self) -> Dict[str, Any]  # Return session stats
```

**Integration**:
- Uses `WorktreeManager` from Phase 1
- Follows `coding_agent.md` prompt from Phase 2
- Each session is fully isolated (separate worktree)

---

## Execution Flow

### High-Level Flow

```
1. Initialize ParallelHarness
    ├─ Load feature_list.json
    ├─ Build dependency graph
    ├─ Compute execution levels
    └─ Validate no circular dependencies

2. For each level in dependency order:
    ├─ Get features in this level
    ├─ Create worker pool (6 workers)
    ├─ Submit feature tasks to pool
    ├─ Wait for all features in level to complete
    └─ Check for failures (handle or continue)

3. Aggregate results
    ├─ Count completions
    ├─ Calculate metrics (speedup, attempts, etc.)
    ├─ Generate report
    └─ Merge all worktrees to main

4. Cleanup
    ├─ Remove temporary files
    ├─ Prune worktrees
    └─ Return summary
```

### Per-Feature Execution

```
Worker receives feature ID
    ↓
1. Create isolated worktree
    ├─ WorktreeManager.create_workspace()
    └─ Change to worktree directory

2. Run coding agent session
    ├─ Load feature from feature_list.json
    ├─ Read claude_progress.md for context
    ├─ Implement feature
    ├─ Run validation (with self-healing)
    └─ Update feature_list.json

3. Commit changes
    ├─ Git add modified files
    └─ Git commit with feature summary

4. Return to main directory
    └─ Leave worktree for merge

5. Report success/failure
    └─ Return to ParallelHarness
```

**Note**: Worktrees are NOT merged until entire level completes successfully. This prevents partial merges if a feature fails.

---

## Dependency Graph Algorithm

### Topological Sort (Kahn's Algorithm)

```python
def compute_levels(self) -> List[List[int]]:
    """
    Compute dependency levels using modified Kahn's algorithm.

    Features in the same level have no dependencies on each other.
    """
    # Count incoming edges for each feature
    in_degree = {f['id']: len(f['dependencies']) for f in self.features}

    # Level 0: Features with no dependencies
    levels = []
    current_level = [fid for fid, deg in in_degree.items() if deg == 0]

    while current_level:
        levels.append(current_level)
        next_level = []

        # For each feature in current level
        for feature_id in current_level:
            # Find features that depend on this one
            for f in self.features:
                if feature_id in f['dependencies']:
                    in_degree[f['id']] -= 1

                    # If all dependencies satisfied, add to next level
                    if in_degree[f['id']] == 0:
                        next_level.append(f['id'])

        current_level = next_level

    # Check if all features scheduled (detect cycles)
    if sum(len(level) for level in levels) != len(self.features):
        raise ValueError("Circular dependency detected!")

    return levels
```

**Complexity**: O(V + E) where V = features, E = dependencies

---

## Rate Limit Handling

### Strategy

**Problem**: Claude API has rate limits (~50 requests/min for some tiers)

**Solution**: Multi-tier backoff strategy

**Tier 1: Preventive (Reduce Request Rate)**
```python
# Add delay between parallel requests
request_delay = 0.1  # 100ms between requests
max_concurrent = 6   # Limit workers to 6 (not 12)
```

**Tier 2: Reactive (Exponential Backoff)**
```python
if error.status_code == 429:  # Rate limit exceeded
    delay = min(1.0 * (2 ** attempt), 60.0)
    time.sleep(delay)
    retry_request()
```

**Tier 3: Adaptive (Dynamic Worker Reduction)**
```python
if consecutive_rate_limits > 3:
    max_workers = max(max_workers // 2, 1)  # Reduce workers by half
    print(f"Reducing workers to {max_workers} due to rate limits")
```

**Monitoring**:
- Track rate limit errors per minute
- Adjust worker count dynamically
- Report rate limit statistics in summary

---

## Integration with Phases 1 & 2

### Phase 1: Worktrees (Isolation)

**Integration Point**: Each parallel worker gets its own worktree

```python
# In ParallelHarness.run_feature()
manager = WorktreeManager(agent_name=self.agent_name)
workspace = manager.create_workspace()

try:
    # Run session in isolated worktree
    success = self.run_coding_session(workspace, feature_id)
finally:
    # Cleanup handled by caller after level completion
    pass
```

**Benefit**: Multiple features can be developed simultaneously without conflicts

**Example**:
```
.worktrees/
├── agent_feature3_20251222_101530_123456/  # Worker 1
├── agent_feature5_20251222_101530_234567/  # Worker 2
├── agent_feature7_20251222_101530_345678/  # Worker 3
├── agent_feature9_20251222_101530_456789/  # Worker 4
├── agent_feature12_20251222_101530_567890/ # Worker 5
└── agent_feature15_20251222_101530_678901/ # Worker 6
```

### Phase 2: Self-Healing (Auto-Recovery)

**Integration Point**: Each worker session uses self-healing validation

```python
# In SessionManager.run_session()
# Load coding_agent.md prompt (with self-healing from Phase 2)
prompt = load_prompt("coding")

# Prompt already includes:
# - Self-healing validation loop (up to 10 attempts)
# - Error analysis and targeted fixes
# - Complete re-validation after each fix
```

**Benefit**: Parallel workers automatically fix errors without human intervention

**Example**:
```
Worker 1: Feature 3 → Syntax error → Self-heals in 2 attempts → Success
Worker 2: Feature 5 → Import error → Self-heals in 1 attempt → Success
Worker 3: Feature 7 → No errors → Success on first attempt
Worker 4: Feature 9 → Logic error → Self-heals in 3 attempts → Success
Worker 5: Feature 12 → Complex error → 10 attempts exhausted → Manual review
Worker 6: Feature 15 → Type error → Self-heals in 2 attempts → Success

Level Result: 5/6 features complete (83% success rate)
```

---

## Performance Analysis

### Sequential vs Parallel Comparison

**Assumptions**:
- 50 features total
- Average session time: 20 minutes per feature
- 6 parallel workers
- Dependency structure: ~8 levels (typical)

**Sequential Execution (Current)**:
```
Total time = 50 features × 20 min = 1000 minutes = 16.7 hours
```

**Parallel Execution (Phase 3)**:
```
Level 0: 10 features / 6 workers = 2 batches × 20 min = 40 min
Level 1: 12 features / 6 workers = 2 batches × 20 min = 40 min
Level 2: 8 features / 6 workers = 2 batches × 20 min = 40 min
Level 3: 6 features / 6 workers = 1 batch × 20 min = 20 min
Level 4: 5 features / 6 workers = 1 batch × 20 min = 20 min
Level 5: 4 features / 6 workers = 1 batch × 20 min = 20 min
Level 6: 3 features / 6 workers = 1 batch × 20 min = 20 min
Level 7: 2 features / 6 workers = 1 batch × 20 min = 20 min

Total time = 220 minutes = 3.7 hours
```

**Speedup**: 16.7h / 3.7h = **4.5x faster**

### Speedup Factors

**Best Case (12 workers, wide graph)**:
- Many independent features
- Few dependency levels
- Perfect parallelism
- Speedup: 10-12x

**Average Case (6 workers, typical graph)**:
- Moderate dependencies
- ~8 dependency levels
- Good parallelism
- Speedup: 4-6x

**Worst Case (6 workers, linear dependencies)**:
- Features form long chain
- Each feature depends on previous
- No parallelism possible
- Speedup: 1x (no benefit)

---

## Risk Mitigation

### Risk 1: API Rate Limits

**Impact**: HIGH - Could slow down or fail builds

**Mitigation**:
- Start with conservative worker count (6, not 12)
- Implement exponential backoff
- Add request delay between calls
- Dynamically reduce workers if rate limits hit
- Monitor rate limit errors

**Fallback**: Reduce workers to 1 (sequential mode)

### Risk 2: Merge Conflicts

**Impact**: MEDIUM - Multiple worktrees changing same files

**Mitigation**:
- Merge level-by-level (not all at once)
- Use `--no-ff` merges to preserve history
- Run tests after each level merge
- If conflict, fall back to manual resolution

**Fallback**: Merge worktrees one-by-one (slower but safer)

### Risk 3: Inconsistent State

**Impact**: MEDIUM - One feature fails mid-level

**Mitigation**:
- Don't merge worktrees until entire level succeeds
- If level fails, mark incomplete features for manual review
- Preserve worktrees for debugging
- Continue with next level (best-effort)

**Fallback**: Stop on first level failure (conservative)

### Risk 4: Resource Exhaustion

**Impact**: LOW - Too many processes/worktrees

**Mitigation**:
- Limit workers to 6 (not 12)
- Monitor disk space (worktrees consume ~50-100MB each)
- Cleanup worktrees after merge
- Add memory/CPU monitoring

**Fallback**: Reduce workers if system struggles

---

## Configuration

### Command-Line Interface

**Enhanced `runner.py` flags**:

```bash
# Parallel execution with 6 workers (default)
./harness/runner.py --agent sharepoint --parallel 6

# Sequential execution (backward compatible)
./harness/runner.py --agent sharepoint --no-parallel

# Custom worker count
./harness/runner.py --agent sharepoint --parallel 12

# With rate limit handling
./harness/runner.py --agent sharepoint --parallel 6 --rate-limit-backoff

# Dry run (show levels without executing)
./harness/runner.py --agent sharepoint --parallel 6 --dry-run
```

### Configuration File

**Add to `harness/config.json`**:

```json
{
  "parallel_execution": {
    "enabled": true,
    "max_workers": 6,
    "default_workers": 6,
    "rate_limit_backoff": true,
    "initial_backoff_delay": 1.0,
    "max_backoff_delay": 60.0,
    "request_delay": 0.1,
    "merge_strategy": "level_by_level"
  }
}
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_dependency_graph.py
def test_compute_levels_no_dependencies()
def test_compute_levels_linear_dependencies()
def test_compute_levels_complex_graph()
def test_detect_circular_dependencies()

# tests/test_parallel_harness.py
def test_run_level_with_successes()
def test_run_level_with_failures()
def test_rate_limit_handling()
def test_worker_pool_management()

# tests/test_rate_limit_handler.py
def test_exponential_backoff()
def test_max_delay_limit()
def test_retry_count_limit()
```

### Integration Tests

```python
# tests/test_parallel_integration.py
def test_parallel_build_simple_agent()
def test_parallel_build_with_dependencies()
def test_parallel_build_with_rate_limits()
def test_level_by_level_merge()
```

### Performance Tests

```bash
# Benchmark sequential vs parallel
./harness/runner.py --agent benchmark --sequential  # Baseline
./harness/runner.py --agent benchmark --parallel 3  # 3 workers
./harness/runner.py --agent benchmark --parallel 6  # 6 workers
./harness/runner.py --agent benchmark --parallel 12 # 12 workers

# Measure:
# - Total build time
# - Features completed
# - Average session time
# - Rate limit errors
# - Speedup factor
```

---

## Success Metrics

### Phase 3 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Speedup** | 4-6x | Total time (parallel) / Total time (sequential) |
| **Parallelism** | 6 workers | Concurrent sessions executing |
| **Completion Rate** | ≥90% | Same as Phase 2 (self-healing maintains quality) |
| **Rate Limit Errors** | <5% | Rate limit errors / Total requests |
| **Worker Efficiency** | >75% | Actual time / Theoretical max time |

### Metrics Collection

**Add to feature_list.json**:
```json
{
  "metrics": {
    "phase3_enabled": true,
    "parallel_workers": 6,
    "total_levels": 8,
    "sequential_time_estimate": 1000,  // minutes
    "actual_time": 220,                  // minutes
    "speedup_factor": 4.5,
    "rate_limit_errors": 12,
    "rate_limit_rate": 0.024,           // 2.4%
    "worker_efficiency": 0.82           // 82%
  }
}
```

---

## Rollback Plan

### If Phase 3 Causes Issues

**Immediate Rollback**:
```bash
# Disable parallel execution in config
nano harness/config.json
# Set: "enabled": false

# OR: Use --no-parallel flag
./harness/runner.py --agent sharepoint --no-parallel
```

**Code Rollback**:
```bash
# Revert parallel harness changes
git checkout harness/runner.py
git checkout harness/parallel_runner.py

# System falls back to sequential execution
```

**Worktree Cleanup** (if needed):
```bash
# Remove all worktrees
git worktree list | grep ".worktrees" | awk '{print $1}' | xargs -I {} git worktree remove {} --force

# Prune metadata
git worktree prune
```

---

## Implementation Phases

### Phase 3.1: Core Infrastructure (Days 1-2)
- ✅ Design architecture (this document)
- Implement `DependencyGraph` class
- Implement `RateLimitHandler` class
- Unit tests for core components

### Phase 3.2: Parallel Execution (Days 3-5)
- Implement `ParallelHarness` class
- Implement `SessionManager` class
- Integrate with Phase 1 (worktrees)
- Integrate with Phase 2 (self-healing)

### Phase 3.3: Testing & Refinement (Days 6-7)
- Integration tests
- Performance benchmarks
- Rate limit testing
- Bug fixes and optimizations

### Phase 3.4: Documentation (Day 7)
- Update CLAUDE.md
- Create Phase 3 completion report
- Update CHANGELOG.md

**Total Duration**: 7-10 days

---

## Next Steps

1. **Implement `DependencyGraph`** - Dependency analysis and level computation
2. **Implement `ParallelHarness`** - Parallel execution orchestration
3. **Test with real agent** - Validate speedup and metrics
4. **Refine based on results** - Adjust worker count, backoff strategy
5. **Document and deploy** - Production-ready parallel harness

---

**Architecture Status**: ✅ COMPLETE
**Next**: Implementation (Phase 3.1)
**Estimated Completion**: 2025-12-29 (7 days)

---

*Auto-Claude Integration - Phase 3 Architecture*
*Generated on 2025-12-22*
