# Key Insights from Anthropic Agent Skills Talk

Source: Anthropic's presentation on Agent Skills paradigm (2025)

## Core Thesis

**"We stopped building agents and started building skills instead."**

The paradigm shift:
- **OLD**: Build specialized agent for each domain (VPS agent, database agent, etc.)
- **NEW**: Build ONE general agent + library of skills that load on-demand

## The Problem Statement

> "Agents have intelligence and capabilities, but not always expertise."

**The Tax Accountant Analogy**:
- **Option 1**: 300 IQ mathematical genius (raw intelligence)
- **Option 2**: Experienced tax professional (domain expertise)

For taxes, you want **Option 2 every time** - you don't want genius figuring out tax code from first principles.

**Current AI agents = Option 1**: Brilliant but lacking procedural knowledge.

**Skills = Option 2**: Packaged domain expertise.

## What Are Agent Skills?

**Definition**: Organized collections of files that package composable procedural knowledge for agents.

**Format** (deliberately simple):
```
skill-name/
├── skill.md              # Metadata + core instructions
├── scripts/              # Tools as executable code
├── assets/               # Supporting files
└── docs/                 # Additional documentation
```

**Why folders?**
- Universal format (humans and agents understand)
- Works with existing tools (Git, Google Drive, zip files)
- Self-documenting (code is documentation)
- Modifiable by agents themselves

## Progressive Disclosure - The Key Innovation

**Problem**: 100 skills × 500 tokens = 50K tokens before doing any work (context explosion)

**Solution**: Only show metadata initially, load full content when needed

```yaml
# Shown to agent initially (50 tokens):
name: database-operations
description: Natural language SQL interface to Neon PostgreSQL
triggers: [database, sql, query, table]

# Loaded only when skill activated (500 tokens):
[Full instructions, tool definitions, examples, etc.]
```

**Result**: Agent can have hundreds of skills without context exhaustion.

## Skills vs Tools (Traditional)

**Traditional Tools** (MCP servers):
- Live in context window permanently
- Hard to modify at runtime
- Poorly documented instructions
- Agent can't fix broken tools

**Skills as Code**:
- ✅ Self-documenting (code is clear)
- ✅ Modifiable (agent can update scripts)
- ✅ File system storage (not context)
- ✅ Progressively disclosed (lazy loading)

**Example**: Claude kept rewriting the same Python styling script for slides. Solution: Save it as a skill tool. Now just run the script.

## Skills + MCP = Complete Solution

**MCP (Model Context Protocol)**: Connection to external world
- APIs, databases, services, browser automation

**Skills**: Expertise and orchestration
- HOW to use those MCP tools effectively
- Multi-step workflows combining tools
- Domain-specific patterns

**Example**:
- Browserbase MCP = browser automation capability
- Browserbase Skill = expertise in navigating websites effectively
- Notion MCP = access to Notion data
- Notion Skill = deep research workflows across workspaces

**For FibreFlow**:
- postgres-mcp = database connectivity
- database-operations skill = business intelligence expertise
- github MCP = GitHub API access
- deployment skill = orchestrating releases

## The Computing Stack Analogy

```
Traditional Computing     AI/Agent Stack
─────────────────────    ─────────────────
Processor                Model (Claude)
Operating System         Agent Runtime (SDK, loops)
Applications             Skills (domain expertise)
```

**Implication**:
- Few companies build processors/OS
- Millions build applications
- Same should be true for agents: Few build runtimes, millions build skills

## Skills Can Be Built by Non-Technical People

**Key observation**: Finance, recruiting, accounting, legal professionals building skills without coding.

**Why this matters**: Domain experts encode their knowledge directly, no developer intermediary needed.

**For FibreFlow**: Fiber optic engineers, project managers could build skills for:
- BOQ validation procedures
- Contractor evaluation criteria
- Project timeline analysis
- Compliance checking workflows

## Continuous Learning Through Skills

**The Vision**: Agents create their own skills as they learn.

**Day 1 Claude**: General intelligence, no expertise
**Day 30 Claude**: General intelligence + 50 skills learned from working with you

**Current state**: Claude can already create skills using "skill creator skill"

**FibreFlow connection**: This is what Domain Memory (`feature_list.json`, `claude_progress.md`) tries to achieve - but skills provide the standardized format.

## Three Types of Skills in Ecosystem

### 1. Foundational Skills
Built by Anthropic or major providers - general capabilities
- Document generation (Office, PDF)
- Scientific research (EHR analysis, bioinformatics)

### 2. Third-Party Skills
Built by partners for their products
- Browserbase: Browser automation workflows
- Notion: Deep workspace research
- (Opportunity for FibreFlow: Fiber optic industry skills)

### 3. Enterprise Skills
Built within organizations for internal use
- Company best practices
- Internal software workflows
- Organizational knowledge
- Code style guides (developer productivity teams)

## Observed Trends

### 1. Skills Getting More Complex
- Simple: `skill.md` with prompts (minutes to build)
- Moderate: Software, scripts, assets (hours to build)
- Complex: Full applications packaged as skills (weeks to build)

### 2. Skills Complement MCP
- MCP provides connectivity
- Skills provide expertise
- Together = complete solution

### 3. Non-Technical Builders
- Validation of vision: skills democratize agent extension
- People in non-coding roles extending agents for their work

## Open Questions (Anthropic's Roadmap)

### Testing & Evaluation
Treat skills like software:
- Unit tests for skill logic
- Integration tests for skill + agent
- Quality metrics for outputs

### Versioning
- Track skill evolution over time
- Clear lineage of changes
- Rollback capability

### Dependencies
- Skills depend on other skills
- Skills depend on MCP servers
- Skills depend on packages/libraries
- Predictable behavior across environments

## Implications for FibreFlow

### What We Should Do

✅ **Use progressive disclosure format** for any new capabilities
- Even if we keep multi-agent architecture
- Skills format is good documentation regardless

✅ **Experiment with skills-based approach** (this POC!)
- Claude Code has native skills support
- We're pre-production - now is the time to test

✅ **Think about skills + MCP composition**
- We have postgres-mcp, github, playwright-mcp
- Skills could orchestrate these into workflows

### What We Should NOT Do

❌ **Refactor working agents to skills without data**
- Don't chase paradigms without measurement
- But we're not production yet, so this doesn't apply

❌ **Over-engineer hybrid architectures**
- Smart routers, complexity analyzers, escalation logic
- KISS: Pick ONE approach based on experiment results

❌ **Assume skills solve problems we don't have**
- Context exhaustion? Not proven yet.
- Cross-domain queries? Unknown frequency.
- Measure first, then decide.

## The Meta-Lesson

**When you see a shiny new paradigm**:
1. What problem does it solve?
2. Do I have that problem?
3. Is my current solution broken?

If answers are unclear → **Experiment and measure**, don't theorize and guess.

**That's why this POC exists.**

## Decision Criteria Summary

Choose **Skills-Based** if experiment shows:
- Context efficiency gains are significant (>30% reduction)
- Cross-domain queries work better
- Implementation is simpler
- Quality equals or exceeds specialists

Choose **Multi-Agent** if experiment shows:
- Complex queries need dedicated context
- Specialists provide better quality
- Cross-domain is rare
- Parallel execution is valuable

Choose **Hybrid** if:
- Both have clear strengths for different scenarios
- But only if complexity is justified by measured benefit

## Bottom Line

**Anthropic's vision**: Skills are the future of agent capabilities.

**FibreFlow's reality**: TBD - that's what this experiment will tell us.

**Philosophy**: Let data decide, not trends.
