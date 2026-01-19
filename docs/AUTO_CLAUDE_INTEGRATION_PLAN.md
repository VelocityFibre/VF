# Auto-Claude Integration Plan for FibreFlow

**Date**: 2025-12-22
**Status**: Planning → Phase 1 Implementation
**Decision**: Extract patterns, don't clone repository

## Executive Summary

Auto-Claude is an autonomous AI coding framework that uses parallel execution, git worktrees, and self-healing validation to build software features faster than sequential approaches. This document analyzes Auto-Claude's key patterns and provides a phased integration plan for FibreFlow's agent harness system.

**Key Recommendation**: Extract and implement Auto-Claude's design patterns in FibreFlow's existing architecture rather than adopting their codebase directly.

---

## Auto-Claude Analysis

### Core Capabilities

1. **Multi-Stage Agent Pipeline**
   - Spec Creation Phase: Analyzes project, gathers requirements
   - Implementation Phase: Breaks tasks into subtasks, codes incrementally
   - Merge Resolution Phase: Automatically resolves code conflicts

2. **Parallel Execution**
   - Supports up to 12 simultaneous AI-powered terminals
   - Enables concurrent feature development
   - Respects dependency constraints

3. **Git Worktree Isolation**
   - Creates isolated development environments in `.worktrees/`
   - Keeps main branch stable during development
   - Automatic merge with conflict resolution

4. **Self-Healing Validation**
   - QA Reviewer checks acceptance criteria
   - QA Fixer attempts up to 50 iterations to resolve issues
   - Validates before proceeding to next stage

5. **FalkorDB Memory Layer**
   - Graph database for codebase patterns
   - Hybrid RAG (Retrieval-Augmented Generation) system
   - Cross-session context retention

### Technical Architecture

```
Auto-Claude Framework
│
├─ Parallel Terminal Manager (12x concurrent)
├─ Git Worktree System (.worktrees/ directory)
├─ FalkorDB Memory (graph-based RAG)
├─ Self-Healing Validator (50 iteration max)
└─ Multi-Tier Merge Resolver (3 fallback levels)
```

---

## Why NOT Clone Auto-Claude

### 1. License Incompatibility ⚠️
- **Auto-Claude**: AGPL-3.0 (viral copyleft license)
- **FibreFlow**: Proprietary/internal
- **Risk**: Using their code would legally require open-sourcing entire FibreFlow system

### 2. Architecture Mismatch
```python
# Auto-Claude's patterns
AutoClaudeAgent() → their_memory_system → their_validation

# FibreFlow's established patterns
BaseAgent() → feature_list.json → registry.json → orchestrator
```

Switching would break:
- 20+ existing agents in registry
- Orchestrator routing system
- Team knowledge and documentation
- Production workflows

### 3. Tech Stack Differences
- **Auto-Claude**: Desktop UI focused, custom framework
- **FibreFlow**: CLI/API focused, Claude Agent SDK, FastAPI
- **Impact**: Learning new system instead of improving existing one

---

## Recommended Approach: Selective Pattern Integration

**Philosophy**: *"Don't adopt a tool, adopt the patterns that make it successful."*

Extract design insights and implement them in FibreFlow's style:

```
Auto-Claude Repository
    ↓ (study patterns)
Design Insights
    ↓ (implement in FibreFlow style)
Enhanced Harness System
    ↓ (keep existing architecture)
Production Deployment
```

---

## Integration Value Analysis

### Performance Improvements

| Metric | Current (FibreFlow) | With Integration | Improvement |
|--------|---------------------|------------------|-------------|
| **Agent Build Time** | 16-24 hours | 2-4 hours | **6-12x faster** |
| **Success Rate** | ~70% (manual fixes) | ~90% (self-healing) | **+20% completion** |
| **Main Branch Risk** | High (direct commits) | Zero (worktrees) | **Production safety** |
| **Parallel Agents** | 1 at a time | 6-12 simultaneous | **12x throughput** |
| **Human Intervention** | Every ~10 sessions | Every ~50 sessions | **5x less babysitting** |

### Business Impact

**Speed Multiplier**:
- Build 12 agents overnight instead of 1
- Faster iteration during prototyping
- Reduced development bottlenecks

**Quality Improvement**:
- Self-healing catches edge cases automatically
- Better dependency tracking
- Safer experimentation environment

**Developer Experience**:
- Less manual intervention required
- Safe parallel development
- Easy rollback on failures

---

## Phased Implementation Plan

### Phase 1: Git Worktree Safety (Week 1) ✅ **PRIORITY**

**Objective**: Isolate agent builds from main branch

**Value**:
- Zero risk to production code
- Easy rollback (delete worktree)
- Foundation for parallel execution

**Implementation**:
```python
# harness/worktree_manager.py (NEW)
class WorktreeManager:
    """Manage isolated git worktrees for agent builds."""

    def create_build_workspace(agent_name: str) -> str
    def merge_completed_build(worktree_path: str) -> bool
    def cleanup_worktree(worktree_path: str)
    def resolve_merge_conflicts(conflict_files: List[str]) -> bool
```

**Integration Point**: Modify `harness/runner.py` to use worktrees before/after sessions

**Effort**: 1-2 days
**Risk**: Low (isolated change, no dependencies)
**Testing**: Build test agent in worktree, verify main unchanged

---

### Phase 2: Self-Healing Validation (Week 2-3)

**Objective**: Automatic error fixing during validation

**Value**:
- 70% → 90% completion rate
- Fewer stuck sessions
- Better error diagnostics

**Implementation**:
```markdown
# harness/prompts/coding_agent.md (ENHANCE)

Add "Validation Loop" section:
- Run all validation steps
- On failure: analyze → fix → retry (10 iterations max)
- Mark complete only when validation passes
- Document failures for manual intervention
```

**Integration Point**: Prompt enhancement only (no code changes)

**Effort**: 2-3 days (prompt tuning + testing)
**Risk**: Low (prompt-only modification)
**Testing**: Build agent with intentionally failing tests

---

### Phase 3: Parallel Execution (Week 4-6)

**Objective**: Run multiple features concurrently

**Value**:
- 16-24h → 2-4h build time (6-12x faster)
- Better resource utilization
- Competitive advantage in agent development

**Implementation**:
```python
# harness/parallel_runner.py (NEW)
class ParallelHarness:
    """Execute features in parallel with dependency awareness."""

    def compute_dependency_levels() -> List[List[Feature]]
    def run_level_in_parallel(level: List[Feature], max_workers: int = 6)
    def monitor_api_rate_limits()
```

**Integration Point**:
```bash
./harness/runner.py --agent my_agent --parallel 6
```

**Effort**: 1-2 weeks
**Risk**: Medium (API rate limits, complexity)
**Testing**: Build agent with independent features, measure speedup

**Considerations**:
- Start with 6 terminals (not 12) to avoid rate limits
- Implement exponential backoff for API errors
- Monitor Anthropic usage dashboard

---

### Phase 4: Enhanced Merge Resolution (Week 7)

**Objective**: Automatic conflict resolution

**Value**:
- Fewer manual merge interventions
- Faster overnight builds
- Learning from conflict patterns

**Implementation**:
```python
# harness/merge_resolver.py (NEW)
class MergeResolver:
    """Multi-tier merge conflict resolution."""

    def resolve_conflicts(branch: str) -> bool:
        # Tier 1: Standard git merge
        # Tier 2: AI resolve conflicts only
        # Tier 3: AI regenerate entire file
```

**Integration Point**: Called by `WorktreeManager.merge_completed_build()`

**Effort**: 1 week
**Risk**: Medium (critical files could be overwritten)
**Testing**: Create intentional conflicts, verify resolution

---

### Phase 5: Graph Memory (Week 8+) - OPTIONAL

**Status**: ⚠️ **RECOMMEND SKIP**

**Why Skip FalkorDB?**

Current `feature_list.json` already provides:
- Feature dependencies (`"dependencies": [12, 13]`)
- Completion tracking (`"passes": true`)
- Fast, simple, works well

FalkorDB would add:
- Semantic queries ("what features need OAuth2?")
- Cross-session pattern learning
- Graph relationships

**Cost/Benefit Analysis**:
- **Cost**: Docker infrastructure, new DB to maintain, migration complexity
- **Benefit**: Marginal improvement over current JSON approach
- **Verdict**: High cost, low benefit → Skip for now

**Reconsider when**:
- Building 50+ agents (pattern learning becomes valuable)
- Need complex dependency queries
- Cross-agent knowledge sharing required

---

## Implementation Priority Matrix

| Phase | Value | Effort | Risk | Priority | Start Date |
|-------|-------|--------|------|----------|------------|
| **Phase 1: Worktrees** | High | Low | Low | ✅ **IMMEDIATE** | 2025-12-22 |
| **Phase 2: Self-Healing** | High | Low | Low | ⭐ HIGH | After Phase 1 |
| **Phase 3: Parallelism** | Very High | High | Medium | ⭐ HIGH | After Phase 2 |
| **Phase 4: Merge Resolution** | Medium | Medium | Medium | 📌 MEDIUM | After Phase 3 |
| **Phase 5: Graph Memory** | Low | Very High | High | ❌ SKIP | N/A |

---

## Risk Mitigation Strategies

### Risk 1: Claude API Rate Limits (Phase 3)
**Impact**: Parallel execution may hit API throttling

**Mitigation**:
- Start with 6 terminals (not 12)
- Implement exponential backoff
- Monitor Anthropic dashboard during builds
- Add queue system for overflow requests

### Risk 2: Complex Merge Conflicts (Phase 1, 4)
**Impact**: Automatic merge could break critical code

**Mitigation**:
- Implement 3-tier resolution with human fallback
- Never auto-merge files in `CRITICAL_FILES` list
- Log all conflicts for pattern analysis
- Require manual review for production agents

### Risk 3: FalkorDB Dependency (Phase 5 - if implemented)
**Impact**: New infrastructure component increases complexity

**Mitigation**:
- Keep `feature_list.json` as fallback
- Dual-write during transition (JSON + graph)
- Document rollback procedure
- Run FalkorDB in Docker (easy cleanup)

### Risk 4: Worktree Cleanup Failures (Phase 1)
**Impact**: Orphaned worktrees consume disk space

**Mitigation**:
- Add cleanup script: `./harness/cleanup_worktrees.sh`
- Run `git worktree prune` in CI/CD
- Monitor `.worktrees/` directory size
- Set retention policy (delete after 30 days)

---

## Success Metrics

Track these metrics after each phase:

### Phase 1 (Worktrees)
- ✅ **Main branch commits**: Should be 0 during builds
- ✅ **Rollback time**: <1 minute (delete worktree vs. git revert)
- ✅ **Failed builds**: No impact on main branch

### Phase 2 (Self-Healing)
- 📊 **Completion rate**: 70% → 90% target
- 📊 **Manual interventions**: Reduce by 50%
- 📊 **Iteration efficiency**: Average attempts to fix

### Phase 3 (Parallelism)
- 🚀 **Build time**: 16-24h → 2-4h target (6-12x improvement)
- 🚀 **Throughput**: 1 agent/night → 6-12 agents/night
- 🚀 **API costs**: Monitor for rate limit errors

### Phase 4 (Merge Resolution)
- 🔧 **Merge success rate**: Target 80% automatic resolution
- 🔧 **Conflict types**: Categorize for pattern learning
- 🔧 **Human reviews**: Track fallback frequency

---

## Code Integration Strategy

### Existing Harness Structure
```
harness/
├── config.json              # Existing configuration
├── runner.py                # Main orchestration (MODIFY)
├── README.md                # Documentation
├── prompts/
│   ├── initializer.md       # Session 1 prompt
│   └── coding_agent.md      # Sessions 2+ (ENHANCE in Phase 2)
├── specs/
│   └── *.md                 # Agent specifications
└── runs/
    └── latest/
        ├── feature_list.json    # State management
        └── claude_progress.md   # Progress tracking
```

### New Components (Phase 1-4)
```
harness/
├── worktree_manager.py      # Phase 1: NEW
├── parallel_runner.py       # Phase 3: NEW
├── merge_resolver.py        # Phase 4: NEW
└── lib/
    ├── validation.py        # Phase 2: Validation utilities
    └── conflict_analyzer.py # Phase 4: Conflict analysis
```

### Modified Components
```python
# harness/runner.py (Phase 1 changes)
class HarnessRunner:
    def run(self):
        # NEW: Create worktree
        workspace = WorktreeManager().create_build_workspace(self.agent_name)

        try:
            # EXISTING: Run sessions (unchanged)
            while not self.all_features_complete():
                self.run_coding_session()

            # NEW: Merge back to main
            workspace.merge_completed_build()
        finally:
            # NEW: Cleanup
            workspace.cleanup_worktree()
```

---

## Testing Strategy

### Phase 1: Worktree Testing

**Unit Tests**:
```python
# tests/test_worktree_manager.py
def test_create_worktree_creates_directory()
def test_worktree_isolates_from_main()
def test_merge_applies_changes_to_main()
def test_cleanup_removes_worktree()
def test_conflict_resolution_fallback()
```

**Integration Tests**:
```bash
# Build simple test agent in worktree
./harness/runner.py --agent test_simple --use-worktree

# Verify:
# 1. No commits to main during build
# 2. Worktree created in .worktrees/
# 3. Agent merged to main after completion
# 4. Worktree cleaned up
```

### Phase 2: Self-Healing Testing

**Test Scenarios**:
- Failing unit test (should auto-fix)
- Syntax error (should auto-fix)
- Import error (should auto-fix)
- Logic error (may need multiple attempts)
- Unfixable error (should document and continue)

### Phase 3: Parallel Testing

**Test Scenarios**:
- 3 independent features (all should complete)
- 6 features with dependencies (correct ordering)
- API rate limit simulation (should backoff)
- Mixed success/failure (should track correctly)

**Performance Benchmarks**:
```bash
# Sequential baseline
time ./harness/runner.py --agent benchmark_agent

# Parallel comparison
time ./harness/runner.py --agent benchmark_agent --parallel 6

# Target: 6x speedup (or explanation if less)
```

---

## Rollback Plan

### If Phase 1 Fails
```bash
# Remove worktree integration
git checkout harness/runner.py
git checkout harness/worktree_manager.py

# Continue using direct commits to main
./harness/runner.py --agent my_agent --no-worktree
```

### If Phase 3 Causes Rate Limits
```bash
# Reduce parallelism
./harness/runner.py --agent my_agent --parallel 3

# Or fallback to sequential
./harness/runner.py --agent my_agent
```

### Emergency Worktree Cleanup
```bash
# List all worktrees
git worktree list

# Remove orphaned worktrees
git worktree prune

# Force remove stuck worktree
rm -rf .worktrees/agent_name_timestamp
git worktree prune
```

---

## Documentation Updates Required

After each phase, update:

### Phase 1
- [ ] `harness/README.md` - Add worktree usage section
- [ ] `CLAUDE.md` - Update harness workflow description
- [ ] `.claude/commands/agents/build.md` - Add `--use-worktree` flag
- [ ] `docs/OPERATIONS_LOG.md` - Document Phase 1 deployment

### Phase 2
- [ ] `harness/prompts/coding_agent.md` - Document new validation loop
- [ ] `harness/README.md` - Add self-healing section

### Phase 3
- [ ] `harness/README.md` - Add parallel execution guide
- [ ] `CLAUDE.md` - Update cost estimates (faster = more builds)
- [ ] `docs/DECISION_LOG.md` - Document parallelism decision

### Phase 4
- [ ] `harness/README.md` - Add merge resolution section
- [ ] `docs/OPERATIONS_LOG.md` - Track conflict resolution patterns

---

## Cost Analysis

### Development Costs (Engineering Time)

| Phase | Implementation | Testing | Documentation | Total |
|-------|----------------|---------|---------------|-------|
| Phase 1 | 1 day | 0.5 days | 0.5 days | **2 days** |
| Phase 2 | 2 days | 1 day | 0.5 days | **3.5 days** |
| Phase 3 | 1 week | 0.5 weeks | 0.5 weeks | **2 weeks** |
| Phase 4 | 4 days | 2 days | 1 day | **1 week** |
| **Total** | | | | **~4.5 weeks** |

### API Cost Impact

**Current (Sequential)**:
- 1 agent build = 50-100 sessions = $10-30 with Haiku
- 1 agent/night throughput

**After Phase 3 (Parallel)**:
- 6 agents simultaneously = 6x API usage = $60-180/night
- BUT: 6-12 agents/night throughput
- **Net efficiency**: 6x more output for 6x cost = same cost per agent

**Recommendation**: Use Claude Code unlimited subscription ($20/month) instead of pay-per-use API

---

## Decision Log Entry

**Date**: 2025-12-22
**Decision**: Extract Auto-Claude patterns, implement incrementally in FibreFlow
**Context**: Need faster agent builds, safer development, less manual intervention
**Alternatives Considered**:
1. ❌ Clone Auto-Claude repo (license issues, architecture mismatch)
2. ❌ Run both tools (maintenance overhead, duplication)
3. ✅ Extract patterns, implement in FibreFlow style (CHOSEN)

**Rationale**:
- Maintains FibreFlow architecture and team knowledge
- No license complications (AGPL-3.0 avoided)
- Incremental adoption reduces risk
- Can cherry-pick highest-value features (worktrees, parallelism)

**Success Criteria**:
- Phase 1: Zero main branch commits during builds
- Phase 2: 90% completion rate (up from 70%)
- Phase 3: 6x faster builds (2-4h vs 16-24h)

**Review Date**: 2025-02-22 (2 months)

---

## Next Steps (Immediate)

### Today (2025-12-22)
1. ✅ Save this analysis document
2. ✅ Implement `harness/worktree_manager.py`
3. ✅ Modify `harness/runner.py` to use worktrees
4. ✅ Test with simple agent build
5. 📝 Document Phase 1 completion

### Week 2 (After Phase 1 validation)
1. Enhance `harness/prompts/coding_agent.md` with validation loop
2. Test self-healing with intentionally failing tests
3. Measure completion rate improvement

### Week 3-4 (After Phase 2 validation)
1. Design parallel execution architecture
2. Implement `harness/parallel_runner.py`
3. Test with 3, 6, and 12 parallel terminals
4. Monitor API rate limits

---

## References

- **Auto-Claude Repository**: https://github.com/AndyMik90/Auto-Claude
- **FibreFlow Harness**: `harness/README.md`
- **Agent OS Integration**: `CLAUDE.md` (Spec-Driven Development section)
- **Domain Memory Guide**: `DOMAIN_MEMORY_GUIDE.md`
- **Documentation Framework**: `docs/DOCUMENTATION_FRAMEWORK.md`

---

## Appendix: Auto-Claude Key Insights

### What We're Taking
1. **Git Worktree Pattern** - Isolation prevents production breaks
2. **Parallel Execution Model** - Speed through concurrency (6-12x)
3. **Self-Healing Validation** - Automatic error fixing (90% success)
4. **Multi-Tier Merge Resolution** - Fallback strategies for conflicts

### What We're Leaving
1. **FalkorDB Graph Memory** - feature_list.json already works
2. **Desktop UI Framework** - FibreFlow is CLI/API focused
3. **Auto-Claude Framework Code** - License incompatibility, pattern mismatch
4. **Their Orchestration System** - FibreFlow orchestrator already established

### Philosophy
> "Don't adopt a tool, adopt the patterns that make it successful."
> - Focus on design insights, not code reuse
> - Implement in FibreFlow's established style
> - Incremental adoption over big-bang rewrites
> - Keep existing architecture and team knowledge

---

**Document Version**: 1.0
**Last Updated**: 2025-12-22
**Status**: Phase 1 Implementation Started
**Next Review**: After Phase 1 completion (estimated 2025-12-24)
