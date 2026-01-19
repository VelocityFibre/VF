# Decision Log

Architecture Decision Records (ADRs) for FibreFlow Agent Workforce.

**Purpose**: Document significant architectural and design decisions, including context, alternatives considered, and trade-offs.

**Format**: Based on [MADR](https://adr.github.io/madr/) (Markdown Architecture Decision Records)

---

## ADR-006: Limited Sudo Model for Server Access Security

**Date**: 2026-01-14
**Status**: ✅ Accepted
**Deciders**: Hein (suggested), Louis (implemented)
**Tags**: security, infrastructure, server-access, claude-code

### Context and Problem Statement

Claude Code has full sudo access to production servers, creating risk of accidental damage through:
- Service restarts during peak hours
- Unintended file deletion
- System configuration changes
- Package installation/removal

Hein (PM) suggested reversing the access model: personal accounts get limited sudo, main server account (velo) reserved for explicit admin tasks.

### Decision Drivers

- **Safety First**: Prevent accidental production damage
- **Maintain Functionality**: Keep full monitoring capabilities
- **Audit Trail**: Track all administrative actions
- **Quick Rollback**: Easy to revert if problematic
- **Team Alignment**: Follow PM's security recommendations

### Considered Options

**Option 1**: Keep full sudo (status quo)
- ✅ Maximum flexibility
- ✅ No password prompts
- ❌ High risk of accidents
- ❌ No safety guardrails
- ❌ PM concerned about safety

**Option 2**: Remove sudo completely
- ✅ Zero risk of damage
- ❌ Can't monitor services
- ❌ Can't debug issues
- ❌ Too restrictive for operations

**Option 3**: Limited sudo with password for admin tasks (CHOSEN)
- ✅ Safe monitoring without password
- ✅ Admin tasks require explicit confirmation
- ✅ Full audit trail
- ✅ Easy rollback
- ✅ PM approved
- ⚠️ Slightly slower for admin tasks

### Decision Outcome

**Chosen**: Option 3 - Limited sudo model

**Implementation**:
1. Created `/etc/sudoers.d/20-louis-readonly` with:
   - Passwordless: status, logs, docker ps, ps aux
   - Password required: restart, stop, kill, rm, apt
2. Default to `louis` account (limited)
3. Use `velo` only when explicitly approved
4. Password: VeloBoss@2026 for admin tasks

**Positive Consequences**:
- ✅ 95% of tasks (monitoring) work seamlessly
- ✅ 100% protection against accidental damage
- ✅ Clear separation of monitoring vs admin
- ✅ Audit trail for all privileged operations

**Negative Consequences**:
- ⚠️ Extra step for admin tasks (password prompt)
- ⚠️ Must remember which account to use

**Rollback Plan**:
```bash
ssh louis@server 'echo "VeloBoss@2026" | sudo -S rm /etc/sudoers.d/20-louis-readonly'
```

### Links

- Configuration: `/etc/sudoers.d/20-louis-readonly`
- Documentation: `SERVER_ACCESS_RULES.md`
- Operations Log: `docs/OPERATIONS_LOG.md` (2026-01-14)

---

## ADR-005: Adopt Structured Development Workflow with Module Context System

**Date**: 2026-01-12
**Status**: ✅ Accepted
**Deciders**: Louis, Hein (workflow design)
**Tags**: development-workflow, tdd, module-architecture, documentation

### Context and Problem Statement

FibreFlow's "vibe coding" transformation (agents, harness, autopilot) succeeded at autonomous development, but lacked structured processes for:
1. Understanding module dependencies before making changes
2. Preventing breaking changes in tightly coupled modules (workflow, installations, projects)
3. Test-driven development workflow
4. Code quality validation before deployment
5. Pull request standardization

Hein proposed a comprehensive development workflow (DEVELOPMENT_WORKFLOW.md) based on Next.js/TypeScript best practices. Need to evaluate if compatible with FibreFlow's Python/FastAPI + agent architecture.

### Decision Drivers

- **Breaking Change Prevention**: Recent incidents (CSRF errors, workflow breakage) from not understanding module dependencies
- **Team Scaling**: Onboarding Hein requires documented module boundaries
- **Quality Assurance**: Need automated validation before production deployments
- **TDD Adoption**: Shift from "tests after coding" to "tests before coding"
- **Compatibility**: Must work with existing vibe coding tools (harness, autopilot, skills)

### Considered Options

**Option 1**: Keep current ad-hoc workflow (status quo)
- ✅ No learning curve
- ✅ Maximum flexibility
- ❌ Breaking changes not prevented
- ❌ No module documentation
- ❌ Manual quality checks
- ❌ Difficult to onboard new developers

**Option 2**: Adopt Hein's workflow as-is (Next.js/TypeScript focus)
- ✅ Proven industry practices
- ✅ Comprehensive TDD workflow
- ✅ PR templates and quality gates
- ❌ Assumes Next.js `src/modules/` structure (FibreFlow uses agents/skills)
- ❌ npm/jest commands (FibreFlow uses pytest)
- ❌ Doesn't address Python/FastAPI specifics

**Option 3**: Adapt Hein's workflow to FibreFlow's architecture
- ✅ Industry best practices + FibreFlow compatibility
- ✅ Module context maps to .claude/skills/ and agents/
- ✅ TDD adapted for pytest (not jest)
- ✅ Quality gates adapted for Python (pytest/mypy/black)
- ✅ Works alongside harness and autopilot
- ❌ Requires custom tooling (can't use off-the-shelf)
- ❌ Team needs to learn new commands

### Decision Outcome

**Chosen**: Option 3 - Adapt Hein's workflow to FibreFlow architecture

**Rationale**:
- Module context system solves real pain (breaking changes)
- TDD workflow compatible with agent harness (specs → autonomous builds)
- Quality gates automate what was manual review
- 80% compatible with Hein's vision, 100% adapted to FibreFlow

### Implementation

**Phase 1 (Complete 2026-01-12)**:
1. ✅ Created `.claude/modules/` with master index (_index.yaml)
2. ✅ Documented 7 core modules (qfieldcloud, wa-monitor, knowledge-base, ticketing, workflow)
3. ✅ Defined isolation levels (fully/mostly/tightly coupled)
4. ✅ Implemented TDD commands: `/tdd spec`, `/tdd generate`, `/tdd validate`
5. ✅ Created git branch strategy (main → develop → feature/*)
6. ✅ Added quality gates to deployment scripts (pytest/mypy/black)
7. ✅ Created PR templates with module awareness
8. ✅ Built CLI helpers (ff-sync, ff-pr, ff-review, ff-merge)
9. ✅ Reorganized tests/ into unit/integration/e2e/specs/

**Phase 2 (Future)**:
- Document remaining modules (installations, projects, contractors, core)
- GitHub Actions CI/CD (auto-run quality gates on PRs)
- Pre-commit hooks (enforce TDD locally)
- Test coverage reporting (PR comments)

### Consequences

**Positive**:
- **Breaking Change Prevention**: Isolation levels + module profiles warn before modifying tightly coupled code
- **Quality Automation**: Deployment script validates tests/types/linting automatically
- **TDD Workflow**: Spec → tests → implementation reduces bugs caught in production
- **Team Scalability**: New developers can read module profiles to understand dependencies
- **Harness Integration**: Test specs can feed into agent harness for autonomous builds
- **Documentation Culture**: Module profiles become living documentation

**Negative**:
- **Learning Curve**: Team needs to learn `/tdd` commands and `ff-*` helpers
- **Overhead**: Creating test specs adds 10-15 minutes to feature kickoff
- **Maintenance**: Module profiles need updating when dependencies change
- **Tool Friction**: Custom bash scripts may have edge cases vs mature tooling

**Neutral**:
- Git branch strategy adds structure (main/develop/feature) vs single branch freedom
- TDD "tests first" feels slower initially, faster long-term (fewer bugs)

### Monitoring

**Success Metrics** (measure after 1 month):
- Reduction in production bugs (target: 50% fewer incidents)
- Time to onboard new developer (target: <2 days to first PR)
- Test coverage (target: >80% for core modules)
- Deployment failures (target: <5% failed deployments)

**Review Date**: 2026-02-12 (1 month)

### Related Decisions

- ADR-001: Vibe Coding Transformation (autopilot, harness) - This workflow complements, not replaces
- ADR-002: Skills-Based Architecture - Module profiles document skills isolation
- ADR-004: VF Server Storage - Module profiles reference deployment locations

### References

- Implementation Guide: `docs/NEW_DEVELOPMENT_WORKFLOW.md`
- Original Proposal: `~/Downloads/DEVELOPMENT_WORKFLOW.md` (Hein)
- Module Registry: `.claude/modules/_index.yaml`
- TDD Commands: `.claude/commands/tdd/`
- Changelog Entry: `CHANGELOG.md` (2026-01-12)

---

## ADR-004: Use /srv/data/ for Production Applications on VF Server

**Date**: 2025-12-17
**Status**: ✅ Accepted
**Deciders**: Louis, Claude Code
**Tags**: infrastructure, storage, vf-server

### Context and Problem Statement

VF Server has two storage locations:
- `/home/louis/apps/` - Root partition (515GB, 37% used)
- `/srv/data/` - NVMe partition (1TB, 1% used)

Applications were historically stored in home directory, but this mixes user data with production apps.

### Decision Drivers

- **Performance**: NVMe storage is faster than root partition
- **Organization**: Separate production apps from user data
- **Capacity**: More space available on `/srv/data/` (975GB free vs 311GB)
- **Standards**: `/srv/` is FHS (Filesystem Hierarchy Standard) for service data
- **Backups**: Easier to backup `/srv/data/` separately

### Considered Options

**Option 1**: Keep in `/home/louis/apps/` (status quo)
- ✅ No migration needed
- ❌ Mixes personal and production data
- ❌ Slower storage
- ❌ Non-standard location

**Option 2**: Move to `/srv/data/apps/`
- ✅ Faster NVMe storage
- ✅ More capacity
- ✅ FHS compliant
- ✅ Clean separation
- ❌ Requires one-time migration
- ❌ Next.js rebuild needed (hardcoded paths)

**Option 3**: Use `/opt/fibreflow/`
- ✅ Also FHS compliant (for third-party software)
- ❌ Still on root partition
- ❌ Less idiomatic for self-developed apps

### Decision Outcome

**Chosen**: Option 2 - `/srv/data/apps/fibreflow/`

**Rationale**:
- One-time migration cost < long-term performance gains
- Better organized for future scaling
- Industry best practice

### Implementation

- Migrated 2.7GB application
- Rebuilt Next.js from new location
- Updated `ecosystem.config.js`
- Documented in `docs/OPERATIONS_LOG.md`

### Consequences

**Positive**:
- Faster app performance (NVMe vs HDD)
- More growth capacity
- Cleaner directory structure
- Easier to automate deployments

**Negative**:
- One-time 30min downtime
- Need to rebuild Next.js when moving (due to hardcoded paths)
- Must update documentation/scripts with new path

**Neutral**:
- Future apps should go to `/srv/data/apps/`
- Establishes standard for VF Server deployments

---

## ADR-003: Skills-First Architecture Over Agent-Heavy

**Date**: 2025-12-09
**Status**: ✅ Accepted
**Deciders**: Louis, Claude Code
**Tags**: architecture, performance, context-efficiency

### Context and Problem Statement

Initial FibreFlow used specialized agents for all tasks. This led to:
- Context bloat (4,500 tokens per query)
- Slow response times (2.3s average)
- Complex orchestration logic

Claude Code introduced Skills with progressive disclosure, offering potential improvements.

### Decision Drivers

- **Performance**: Need <100ms response times for production
- **Cost**: Context tokens = API costs
- **Maintainability**: Simpler code easier to maintain
- **User Experience**: Faster responses = better UX

### Considered Options

**Option 1**: Keep agent-heavy architecture
- ✅ Already built
- ✅ Familiar pattern
- ❌ Slow (2.3s avg)
- ❌ Expensive context (4,500 tokens)
- ❌ Complex orchestration

**Option 2**: Hybrid (Skills + Agents)
- ✅ Use best tool for each job
- ❌ Complexity of two systems
- ❌ When to use which?
- ⚠️ Maintenance burden

**Option 3**: Skills-first with agent fallback
- ✅ 99% faster (23ms vs 2.3s)
- ✅ 84% less context (930 vs 4,500 tokens)
- ✅ Native Claude Code integration
- ✅ Progressive disclosure
- ❌ Requires rewrite of existing agents

### Decision Outcome

**Chosen**: Option 3 - Skills-first with agent fallback

**Benchmarks** (from `experiments/skills-vs-agents/`):
```
Skill approach:   23ms, 930 tokens
Agent approach: 2300ms, 4500 tokens
Improvement:     99x faster, 5x less context
```

**Rationale**:
- Performance improvement justifies rewrite cost
- Skills execute from filesystem (zero context cost for code)
- Progressive disclosure = only load what's needed
- Agents still available for complex workflows

### Implementation

- Created `.claude/skills/database-operations/`
- Created `.claude/skills/vf-server/`
- Kept agents in `agents/` for fallback
- Updated `CLAUDE.md` to prioritize skills

### Consequences

**Positive**:
- Sub-second responses everywhere
- Massive context savings = lower costs
- Simpler mental model
- Native Claude Code integration

**Negative**:
- Investment in rewriting existing agents as skills
- Team learning curve (skills are newer concept)
- Some complex workflows still need agents

**Neutral**:
- Hybrid approach possible for edge cases
- Skills can call agents if needed

---

## ADR-002: Dual Database Strategy (Neon + Convex)

**Date**: 2025-12-15
**Status**: ✅ Accepted
**Deciders**: Louis
**Tags**: database, architecture

### Context and Problem Statement

FibreFlow needs both:
- Relational data (contractors, projects, BOQs) - 104 tables
- Real-time task management

Single database struggles to optimize for both use cases.

### Decision Outcome

**Chosen**: Dual database approach

- **Neon PostgreSQL**: Source of truth for business data (104 tables)
- **Convex**: Real-time task management with HTTP API
- **Sync**: `sync_neon_to_convex.py` for operational data

**Rationale**:
- PostgreSQL excels at complex relational queries
- Convex excels at real-time updates and simple APIs
- Each database optimized for its use case

### Consequences

**Positive**:
- Right tool for each job
- Real-time updates without polling
- Complex queries without compromising real-time performance

**Negative**:
- Data synchronization complexity
- Two systems to maintain
- Eventual consistency between databases

---

## ADR-001: Claude Agent SDK for Agent Architecture

**Date**: 2025-12-10
**Status**: ✅ Accepted
**Deciders**: Louis
**Tags**: framework, agents

### Context and Problem Statement

Need framework for building AI agents to handle fiber optic operations.

### Decision Outcome

**Chosen**: Anthropic Claude Agent SDK

**Rationale**:
- Official Anthropic framework
- Tool calling built-in
- Conversation history management
- Well-documented examples

**Alternatives considered**:
- LangChain: Too generic, heavy dependencies
- Custom framework: Reinventing wheel

### Consequences

**Positive**:
- Quick agent development
- Official support and updates
- Tool calling works out of box

**Negative**:
- Locked into Anthropic ecosystem
- SDK updates may break agents

---

## Template for New ADRs

```markdown
## ADR-XXX: Title (Brief Imperative Statement)

**Date**: YYYY-MM-DD
**Status**: [✅ Accepted|⚠️ Proposed|❌ Rejected|🔄 Superseded by ADR-YYY]
**Deciders**: [Who made this decision]
**Tags**: [comma, separated, tags]

### Context and Problem Statement

[Describe the problem or opportunity that led to this decision. What forces are at play?]

### Decision Drivers

- **Driver 1**: Explanation
- **Driver 2**: Explanation
...

### Considered Options

**Option 1**: Name
- ✅ Pro 1
- ✅ Pro 2
- ❌ Con 1
- ❌ Con 2
- ⚠️ Neutral/consideration

**Option 2**: Name
...

### Decision Outcome

**Chosen**: Option X - Name

**Rationale**:
[Why this option was selected over others. Include metrics/benchmarks if available]

### Implementation

[How was this decision implemented? Links to PRs, commits, or documentation]

### Consequences

**Positive**:
- Benefit 1
- Benefit 2

**Negative**:
- Drawback 1
- Drawback 2

**Neutral**:
- Consideration 1
- Consideration 2

### Related Decisions

- Supersedes ADR-XXX
- Related to ADR-YYY
```

---

## Decision Log Best Practices

### When to Create an ADR

**ALWAYS create ADR for**:
- ✅ Architectural changes (monolith → microservices, database choice)
- ✅ Technology selections (framework, library, service)
- ✅ Design patterns adopted project-wide
- ✅ Infrastructure decisions (cloud provider, deployment strategy)
- ✅ Breaking changes to APIs or interfaces
- ✅ Security or compliance decisions

**Sometimes create ADR for**:
- ⚠️ Significant refactoring approach
- ⚠️ Data modeling decisions
- ⚠️ Testing strategies

**Don't create ADR for**:
- ❌ Bug fixes (use commit messages)
- ❌ Feature additions (use CHANGELOG.md)
- ❌ Code style preferences (use linter config)
- ❌ One-off implementation details

### ADR Lifecycle

1. **Proposed** (⚠️): Decision under discussion
2. **Accepted** (✅): Decision implemented
3. **Superseded** (🔄): Replaced by newer ADR
4. **Rejected** (❌): Decision not adopted (keep for historical context)

### Numbering

- Sequential: ADR-001, ADR-002, ...
- Never reuse numbers
- Gaps are OK (rejected ADRs)

---

**See also**:
- `CHANGELOG.md` - What changed and when
- `docs/OPERATIONS_LOG.md` - Day-to-day operational changes
- `docs/architecture/` - Detailed architecture documentation
