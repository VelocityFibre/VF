# Documentation Framework

**How to decide what to document, where, and when**

This framework helps you assess whether an event or decision warrants documentation, and which system to use.

---

## Quick Decision Tree

```
Is this important to remember?
│
├─ NO → Don't document (trust git commits for code changes)
│
└─ YES → Ask: What type of event?
          │
          ├─ Code/Feature → CHANGELOG.md
          ├─ Server/Infrastructure → docs/OPERATIONS_LOG.md
          └─ Architecture/Design → docs/DECISION_LOG.md
```

---

## The Three Documentation Systems

### 1. CHANGELOG.md - **What** Changed

**Purpose**: Track feature releases, version history, user-facing changes

**When to use**:
- ✅ New features added
- ✅ Bug fixes deployed
- ✅ Breaking API changes
- ✅ Security patches
- ✅ Version releases

**Format**: Keep a Changelog standard (semantic versioning)

**Audience**: Developers, users, stakeholders

**Example**:
```markdown
## [1.1.0] - 2025-12-20
### Added
- WhatsApp integration for contractor feedback
```

---

### 2. docs/OPERATIONS_LOG.md - **How** It Runs

**Purpose**: Track operational changes, deployments, incidents

**When to use**:
- ✅ Server migrations (like today's FibreFlow move)
- ✅ Service deployments
- ✅ Configuration changes
- ✅ Security incidents
- ✅ Performance issues
- ✅ Database migrations
- ✅ Certificate renewals
- ✅ Access/permission changes

**Format**: Reverse chronological log with detailed procedures

**Audience**: Ops team, future you debugging at 2am

**Example**:
```markdown
## 2025-12-17
### 20:40 UTC - VF Server: FibreFlow Migration
**Type**: Infrastructure Migration
[Detailed procedure, rollback, verification]
```

---

### 3. docs/DECISION_LOG.md - **Why** We Chose This

**Purpose**: Track architectural decisions and trade-offs

**When to use**:
- ✅ Technology selections (database, framework)
- ✅ Architecture changes (monolith → microservices)
- ✅ Design patterns adopted
- ✅ Infrastructure decisions (cloud provider, storage)
- ✅ Breaking changes requiring justification
- ✅ Performance vs simplicity trade-offs

**Format**: Architecture Decision Records (ADR)

**Audience**: Future developers asking "why did they do it this way?"

**Example**:
```markdown
## ADR-004: Use /srv/data/ for Production Apps
**Decision**: Move to NVMe storage
**Rationale**: 99x faster, more capacity
**Alternatives considered**: Stay in /home/, use /opt/
```

---

## Assessment Criteria

### Is This Important to Remember?

**High Priority** (ALWAYS document):
- Changes requiring coordination across team
- Non-obvious decisions future developers will question
- Procedures needed for rollback/recovery
- Changes affecting production/users
- Security or compliance events
- Breaking changes

**Medium Priority** (SOMETIMES document):
- Significant refactoring approaches
- Performance optimizations with trade-offs
- Temporary workarounds (note when to revisit)
- Development environment changes affecting others

**Low Priority** (RARELY document):
- One-off bug fixes (git commit is enough)
- Code style preferences (use linter config)
- Personal dev environment tweaks
- Experimental code not merged

**Don't Document**:
- Every code change (that's what git log is for)
- Obvious implementation details
- Temporary debugging code
- Failed experiments (unless lesson learned)

---

## Real-World Examples

### Example 1: Today's FibreFlow Migration

**Event**: Moved `/home/louis/apps/fibreflow/` → `/srv/data/apps/fibreflow/`

**Documentation Actions**:

1. **✅ CHANGELOG.md** (Infrastructure section):
   ```markdown
   ### Infrastructure
   - VF Server: Moved FibreFlow to /srv/data/apps/fibreflow/ (2025-12-17)
   ```

2. **✅ docs/OPERATIONS_LOG.md** (Full procedure):
   - Complete step-by-step
   - Rollback procedure
   - Verification commands
   - Lessons learned

3. **✅ docs/DECISION_LOG.md** (ADR-004):
   - Why /srv/data/ over /home/
   - Performance benchmarks
   - Alternatives considered

4. **✅ CLAUDE.md** (Update paths):
   - VF Server section
   - Special Notes section

**Rationale**: Infrastructure changes affecting server locations need all three:
- CHANGELOG = "what changed" for quick reference
- OPERATIONS_LOG = "how to do it again" for ops
- DECISION_LOG = "why we did it" for future

---

### Example 2: Bug Fix - Contractor Query Slow

**Event**: Optimized slow query in `neon_agent.py:156`

**Documentation Actions**:

1. **✅ Git commit** (sufficient):
   ```bash
   git commit -m "perf: Add index to contractors.status for 90% query speedup"
   ```

2. **❌ CHANGELOG.md**: Too granular (not user-facing)
3. **❌ OPERATIONS_LOG.md**: No infrastructure change
4. **❌ DECISION_LOG.md**: No architectural decision

**Rationale**: Performance improvement without changing architecture → git commit is enough

---

### Example 3: Switching to Skills-First Architecture

**Event**: Migrated from agent-heavy to skills-first approach

**Documentation Actions**:

1. **✅ CHANGELOG.md**:
   ```markdown
   ### Changed
   - Migrated to skills-first architecture (99% faster queries)
   ```

2. **❌ OPERATIONS_LOG.md**: No operational deployment (code change only)

3. **✅ docs/DECISION_LOG.md** (ADR-003):
   - Performance benchmarks (2.3s → 23ms)
   - Context savings (4500 → 930 tokens)
   - Why skills beat agents
   - Trade-offs accepted

**Rationale**: Architectural shift with measurable impact → CHANGELOG + DECISION_LOG

---

## When in Doubt

**Use this heuristic**:

1. **Will someone need this in 6 months?**
   - YES → Document it
   - NO → Git commit is enough

2. **Could this cause production issues if forgotten?**
   - YES → docs/OPERATIONS_LOG.md
   - NO → CHANGELOG.md only

3. **Will future developers ask "why did they do it this way?"**
   - YES → docs/DECISION_LOG.md
   - NO → Skip ADR

4. **Is this a user-facing change?**
   - YES → CHANGELOG.md
   - NO → Assess if internal change warrants docs

---

## Documentation Workflow

### For Infrastructure Changes (like today)

1. **During Change**: Take notes on commands run, issues hit
2. **Immediately After**: Log in docs/OPERATIONS_LOG.md while fresh
3. **Same Day**: Update CHANGELOG.md and DECISION_LOG.md if applicable
4. **Within Week**: Update CLAUDE.md if paths/configs changed

**Don't delay**: Memory fades fast. Document while details are fresh.

### For Code Changes

1. **Always**: Good git commit message
2. **Sometimes**: CHANGELOG.md entry (for releases)
3. **Rarely**: DECISION_LOG.md (only for significant architecture)

### For Incidents

1. **During**: Brief notes in Slack/notepad
2. **After Resolution**: Full postmortem in docs/OPERATIONS_LOG.md
3. **Follow-up**: If root cause = architectural issue, create ADR

---

## Maintenance

### Periodic Reviews

**Monthly**:
- Review CHANGELOG.md for upcoming release notes
- Archive old OPERATIONS_LOG entries (>2 years) to `docs/archive/`

**Quarterly**:
- Review DECISION_LOG.md - mark superseded ADRs
- Update CLAUDE.md with lessons learned

**Annually**:
- Clean up obsolete documentation
- Update retention policies
- Review what was useful vs noise

### Retention

**Keep Forever**:
- Critical incidents
- Major architectural decisions
- Security events
- Compliance-related changes

**Archive After 2 Years**:
- Minor operational changes
- Routine deployments
- Development environment updates

**Delete After 1 Year**:
- Experimental features that were removed
- Temporary workarounds no longer relevant

---

## Documentation Anti-Patterns

**❌ Don't Do**:

1. **Over-documentation**: Documenting every code change in multiple places
2. **Under-documentation**: "I'll remember this" (you won't)
3. **Stale documentation**: Docs that contradict reality (worse than no docs)
4. **Vague documentation**: "Fixed the thing" (what thing? how?)
5. **Scattered documentation**: 10 different places to check
6. **Duplicate documentation**: Same info in 5 files that get out of sync

**✅ Do Instead**:

1. **DRY (Don't Repeat Yourself)**: Link to primary source, don't copy
2. **SPOT (Single Point of Truth)**: Each fact lives in exactly one place
3. **Timely**: Document within 24 hours while fresh
4. **Specific**: Commands, file paths, line numbers, error messages
5. **Searchable**: Use consistent terminology, keywords
6. **Maintained**: Update docs when code changes, or delete if obsolete

---

## Tools and Automation

**Current System** (Manual):
- CHANGELOG.md - Edit manually
- docs/OPERATIONS_LOG.md - Edit manually with template
- docs/DECISION_LOG.md - Edit manually using ADR format

**Future Enhancements**:
- Script to extract git commits → CHANGELOG.md (conventional commits)
- Slack bot to remind "Did you log this deployment?"
- Automated checks: "CHANGELOG.md not updated in 2 weeks"

**Simple Start**:
```bash
# Add to .git/hooks/pre-push
echo "Did you update docs? (CHANGELOG/OPERATIONS_LOG/DECISION_LOG)"
read -p "Continue? (y/n) " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
```

---

## Summary: The Golden Rule

> **If you'll need to remember it in 3 months, document it now.**

- **CHANGELOG.md** = What changed (features, versions)
- **docs/OPERATIONS_LOG.md** = How it runs (deployments, incidents)
- **docs/DECISION_LOG.md** = Why we chose this (architecture, trade-offs)

When in doubt, err on the side of documenting. Future you will thank present you.

---

**See Also**:
- `CHANGELOG.md` - Feature and version history
- `docs/OPERATIONS_LOG.md` - Operational changes and procedures
- `docs/DECISION_LOG.md` - Architectural decisions and trade-offs
- `CLAUDE.md` - Project overview and development guide
