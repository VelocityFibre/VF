# Architectural Decisions

This file logs important architectural and design decisions made during development. Each entry should include the decision, rationale, and impact.

---

## 2025-10-21: Implemented Structured Note-Taking System

**Decision**: Created four core documentation files (claude.md, progress.md, decisions.md, bugs.md) for persistent project state.

**Rationale**:
- Based on Anthropic's context engineering research
- Provides persistence outside the context window
- Allows Claude to reference past decisions without context overhead
- Enables better continuity across sessions

**Impact**:
- Project state persists across sessions
- Reduced need for instruction repetition
- Claude can look up past decisions in files
- Better long-term project consistency

**Files Created**:
- `claude.md`: Master project documentation (auto-loaded)
- `progress.md`: Task tracking and next steps
- `decisions.md`: This file - decision log
- `bugs.md`: Bug tracking system

---

## 2025-10-21: Built Source of Truth Validation Skill

**Decision**: Create systematic validation framework as an Agent Skill to evaluate all new information against established sources of truth using first principles reasoning.

**Rationale**:
- Need systematic way to evaluate external content (blogs, videos, transcripts)
- Protect against misinformation, cargo culting, and poor practices
- Prevent cognitive biases from affecting decision-making
- Ensure consistency with Anthropic official sources (ground truth)
- Document reasoning for all adoption/rejection decisions
- Make validation process reusable and systematic

**Impact**:
- Created comprehensive validation framework with 5-question process:
  1. Authority Check (Tier 1-4 source hierarchy)
  2. Evidence Check (research backing, methodology)
  3. Consistency Check (alignment with sources of truth)
  4. Practical Check (cost/benefit, real-world value)
  5. Recency Check (current applicability)
- Established decision matrix: ADOPT/ADAPT/INVESTIGATE/REJECT/ARCHIVE
- Documented 8 common cognitive biases and mitigation strategies
- Defined Anthropic sources as Tier 1 (ground truth)
- Created bias-resistant evaluation workflow

**Implementation**:
- Built `skills/source-validation/SKILL.md`
- Created `source-hierarchy.md` defining authority tiers
- Created `validation-checklist.md` with systematic 5-question process
- Created `decision-matrix.md` for decision criteria
- Created `bias-detection.md` for identifying and mitigating biases

**Benefits**:
- Evidence-based over opinion-based decisions
- Protection against misinformation and trends
- Systematic over ad-hoc evaluation
- Documented reasoning for all decisions
- Maintains consistency with Anthropic principles
- Prevents cargo culting and bandwagon effects
- Identifies confirmation bias, novelty bias, authority bias, etc.

**Sources of Truth Established**:
- **Tier 1** (Ground Truth): Anthropic research, Claude Code docs, Anthropic API docs
- **Tier 2** (Verified): Your tested implementations (claude.md, guides, decisions.md)
- **Tier 3** (Community): Validated community sources
- **Tier 4** (Experimental): Opinions requiring extensive validation

**Usage**:
Activate when evaluating blogs, videos, transcripts, recommendations, or any new AI coding practices before considering adoption.

---

## 2025-10-21: Adopted Agent Skills Architecture

**Decision**: Implement Agent Skills with progressive disclosure for reusable, domain-specific expertise.

**Rationale**:
- Based on Anthropic's Agent Skills framework
- Progressive disclosure keeps context lean (metadata → SKILL.md → linked files)
- Skills are composable and portable across projects
- Reduces context overhead while maintaining deep expertise
- Complements existing context engineering techniques

**Impact**:
- Created `skills/` directory with first skill (context-engineering)
- Each skill has SKILL.md with metadata (name, description)
- Skills auto-discovered at startup (metadata only)
- Full skill content loaded on-demand when relevant
- Linked files loaded only when specifically needed
- Significantly reduces context window usage
- Makes expertise reusable across projects

**Implementation**:
- Built `skills/context-engineering/SKILL.md`
- Created supporting files: compaction-guide.md, memory-workflows.md, structured-notes.md
- Updated claude.md to reference Skills
- Created AGENT_SKILLS_GUIDE.md for implementation guidance

**Benefits**:
- Context efficiency through progressive disclosure
- Portability (can copy skills to other projects)
- Composability (combine multiple skills)
- Scalability (unbounded context in linked files)
- Complements MCP servers (Skills for workflows, MCP for tools)

---

## 2025-10-21: Established Context Management Protocol

**Decision**: Set context warning thresholds at 60% (warn) and 85% (strong warning) instead of waiting for auto-compact at 92%.

**Rationale**:
- Proactive compaction prevents unexpected interruptions
- Gives more control over what to retain vs discard
- Leaves buffer space for complex tasks
- Avoids context loss from automatic compaction

**Impact**:
- Claude will check context before major tasks
- User will be warned when context is high
- More predictable compaction schedule
- Better retention of important information

**Implementation**:
- Added context warning protocol to claude.md
- Defined retention instruction template
- Set monitoring as regular practice

---

## 2025-10-21: Created Comprehensive Context Engineering Guide

**Decision**: Developed CONTEXT_ENGINEERING_GUIDE.md as standalone implementation guide separate from claude.md.

**Rationale**:
- claude.md should be concise project instructions
- Full guide provides detailed implementation steps
- Separates "what to do" (claude.md) from "how to do it" (guide)
- Guide can be referenced by user and Claude
- Reusable template for future projects

**Impact**:
- Clear separation of concerns
- Easier to maintain both files
- Guide serves as training documentation
- Can be shared across projects

**Content Included**:
- 5 context engineering principles
- Implementation steps for each
- Best practices and workflows
- Quick start checklist
- Success metrics

---

## 2025-10-21: Chose File-Based Documentation Over Database

**Decision**: Use markdown files (progress.md, decisions.md, bugs.md) instead of a database or complex system.

**Rationale**:
- Markdown is human-readable and git-friendly
- No additional dependencies or setup
- Easy to edit manually or programmatically
- Claude has native markdown support
- Version control friendly
- Lightweight and portable

**Impact**:
- Zero setup overhead
- Easy integration with git workflow
- Readable by humans and AI
- Simple to backup and share
- No database management needed

**Alternatives Considered**:
- SQLite database: Too complex for this use case
- JSON files: Less human-readable
- Single combined file: Harder to maintain, bigger context footprint

---

## 2025-10-21: Disabled Auto-Compact to Reclaim 22.5% Context

**Decision**: Disable Claude Code's auto-compact feature

**Source**: Verified via Tier 3 community sources (Shuttle.dev blog) after evaluating Indie Devdan transcript

**Rationale**:
- Auto-compact consumes 45k tokens (22.5% of 200k context window) by default
- No visibility into buffer contents, can't edit/remove incorrect information
- Prefer manual proactive compaction at 60-70% (better control)
- Use structured notes (claude.md, progress.md, decisions.md) for persistence instead

**Impact**:
- Context availability: 155k → 176k free tokens (21k gained)
- Better control over what's in context
- Aligns with Tier 1 principle: maximize available context for current work
- Reinforces manual compaction workflow (60-70% threshold)

**Action Taken**:
- Run `/config` and toggle Auto-compact to `false`
- Continue manual compaction at 60-70% usage
- Document as standard practice in claude.md

**Full Evaluation**: See `evaluations/2025-10-21-indie-devdan-agentic-coding-transcript.md`

---

## 2025-11-26: Adopted Claude Code Optimization Plan

**Decision**: Implement comprehensive Claude Code productivity enhancements: custom slash commands, task-based sub-agents, MCP server integrations, and enhanced development principles documentation.

**Source**: Evaluated "800 Hours with Claude Code" video + Edmund's repository (Tier 2 verified expert)

**Rationale**:
- FibreFlow only has 1 custom command vs. industry best practice of 10-15
- Missing task-based sub-agents for code review, testing, documentation
- No MCP server integrations for enhanced capabilities
- Need documented development principles and workflow patterns
- Estimated 30-40% reduction in repetitive prompting
- 50% faster agent development cycle (2 days → 1 day)

**Impact**:
- **Phase 1 (Week 1)**: Create 9 custom slash commands
  - Agent commands: `/agent-test`, `/agent-new`, `/agent-document`
  - Database commands: `/db-query`, `/db-sync`
  - Deployment commands: `/vps-health`, `/deploy`
  - Testing commands: `/test-all`, `/code-review`
- **Phase 2 (Week 2)**: Create 5 task-based sub-agents in `.claude/agents/`
  - `code-reviewer.md` - Security, performance, error handling analysis
  - `test-generator.md` - Pytest test generation following FibreFlow patterns
  - `doc-writer.md` - Agent README.md generation
  - `deployment-checker.md` - Pre-deployment validation
  - `ui-tester.md` - Automated web interface testing (requires Playwright MCP)
- **Phase 3 (Week 3-4)**: MCP server integration
  - Context7 for documentation lookup (Python/FastAPI/PostgreSQL)
  - PostgreSQL/Neon MCP for direct database access
  - Playwright MCP for UI testing
- **Phase 4 (Week 2)**: Enhance CLAUDE.md with Development Principles section
  - Prompt engineering guidelines
  - Plan mode usage patterns
  - Code review standards
  - Quality over speed philosophy
  - Cost management strategies

**Expected Outcomes**:
- ⚡ 30-40% reduction in repetitive prompting (save ~80 words per command invocation)
- 🚀 50% faster agent development (2 days → 1 day)
- ✅ Automated code quality checks (consistent security/performance reviews)
- 📚 Self-documenting agent development process
- ⏱️ 10-15 hours saved per week = 2 additional development days

**What to ADOPT**:
- ✅ Task-based sub-agents (proven effective)
- ✅ Custom commands for repetitive workflows
- ✅ MCP servers for external tool integration
- ✅ Development principles documentation

**What to REJECT**:
- ❌ Role-based agents (video confirms this doesn't work - FibreFlow's domain-specialized approach is superior)
- ❌ JavaScript-specific MCPs (not relevant to Python/FastAPI stack)

**What to ADAPT**:
- ⚠️ Command patterns adapted for FibreFlow's Python/PostgreSQL stack (vs Edmund's Next.js/TypeScript)
- ⚠️ MCP selection prioritizes Python/PostgreSQL ecosystem

**Validation**:
- Video creator: 800+ hours of Claude Code experience
- GitHub repository with production implementations
- Aligns with Anthropic's official Claude Code documentation
- Consistent with FibreFlow's existing agent architecture
- No conflicts with established sources of truth (Tier 1)

**Implementation Timeline**:
- **Week 1**: Custom commands (highest ROI, lowest effort)
- **Week 2**: Sub-agents + documentation enhancement
- **Week 3-4**: MCP server research and configuration
- **Future**: Package as FibreFlow plugin for community sharing

**Full Evaluation**: See `evaluations/2025-11-26-claude-code-800-hours-video.md`
**Roadmap**: See `CLAUDE_CODE_OPTIMIZATION_ROADMAP.md`

---

## Template for Future Decisions

**Decision**: [What was decided]

**Rationale**: [Why this decision was made]

**Impact**: [How this affects the project]

**Alternatives Considered**: [What other options were evaluated]

---

## Notes on Using This File

- Add entries chronologically (newest at top, below this note section)
- Include date in YYYY-MM-DD format
- Be concise but complete
- Reference this file before making similar decisions
- Update claude.md if decisions change project direction significantly
