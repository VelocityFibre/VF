# Proactive Agent System Specification

## Purpose

Transform FibreFlow from a reactive (pull-based) agent system to a proactive (push-based) system that continuously monitors the codebase, learns developer patterns, and autonomously suggests/executes improvements. This implements the "Jules Level 1-2" proactive paradigm: observation, personalization, timeliness, and seamless integration.

## Problem Statement

Current FibreFlow agents are entirely reactive - they only act when explicitly invoked via commands or queries. This creates mental load on developers who must:
- Remember to ask for code reviews
- Manually discover TODO comments and tech debt
- Track test coverage gaps
- Monitor for security issues

The solution is a proactive system where agents continuously observe the codebase and surface high-value tasks autonomously.

## Capabilities

### 1. Continuous Observation (Level 1)
- Monitor git commits in real-time via hooks
- Scan codebase for TODO/FIXME/HACK comments
- Detect missing tests for new functions
- Identify security patterns (SQL injection, exposed secrets)
- Track technical debt accumulation

### 2. Proactivity Queue Management
- Maintain persistent task queue with confidence scoring
- Categorize tasks: bug_fix, test_coverage, security, performance, documentation
- Score confidence: high (auto-fixable), medium (needs review), low (advisory)
- Track task state: discovered, queued, in_progress, completed, dismissed

### 3. Automated Code Review (Critic Agent)
- Adversarial review on every commit
- Security analysis (SQL injection, secrets exposure, input validation)
- Performance analysis (N+1 queries, memory leaks)
- Best practices enforcement (error handling, logging)
- Output structured feedback with confidence scores

### 4. Developer Profile Learning (Level 2)
- Learn code style preferences from git history
- Identify avoided files/directories (never suggest edits)
- Track work hours (no interruptions outside preferred times)
- Detect preferred testing patterns
- Adapt suggestion style to developer preferences

### 5. Background Task Execution
- Auto-fix high-confidence tasks (unused imports, missing docstrings)
- Queue medium/low-confidence tasks for manual review
- Commit fixes with descriptive messages
- Run validation tests before committing

### 6. Proactivity View Interface
- CLI dashboard showing discovered tasks by confidence level
- Bulk actions: approve all high, dismiss low, review one-by-one
- Task detail view with reasoning and suggested fixes
- Historical view of completed proactive tasks

## Tools

### Tool 1: `scan_repository`
Scans git repository for proactive task opportunities.

**Parameters**:
- `scan_type` (string, required): Type of scan - "todos", "missing_tests", "security", "performance", "all"
- `path` (string, optional): Specific directory to scan (default: entire repo)
- `since_commit` (string, optional): Only scan changes since this commit hash

**Returns**:
```json
{
  "tasks_discovered": 15,
  "tasks": [
    {
      "id": "task-001",
      "type": "missing_test",
      "file": "agents/neon-database/agent.py",
      "line": 156,
      "description": "Function execute_query() has no test coverage",
      "confidence": "high",
      "estimated_effort": "5 minutes",
      "auto_fixable": false
    }
  ]
}
```

### Tool 2: `analyze_commit`
Analyzes a specific git commit for issues.

**Parameters**:
- `commit_hash` (string, required): Git commit SHA to analyze
- `analysis_types` (array, required): ["security", "performance", "best_practices", "tests"]

**Returns**:
```json
{
  "commit": "abc123",
  "issues_found": 3,
  "issues": [
    {
      "severity": "high",
      "type": "security",
      "description": "Potential SQL injection in query concatenation",
      "file": "neon_agent.py",
      "line": 234,
      "suggested_fix": "Use parameterized queries instead of string concatenation",
      "confidence": "high"
    }
  ]
}
```

### Tool 3: `update_proactivity_queue`
Adds, updates, or removes tasks from the proactivity queue.

**Parameters**:
- `action` (string, required): "add", "update", "remove"
- `task` (object, required for add/update): Task object with id, type, description, confidence, etc.
- `task_id` (string, required for remove): Task ID to remove

**Returns**:
```json
{
  "success": true,
  "queue_size": 42,
  "high_confidence_tasks": 8,
  "medium_confidence_tasks": 20,
  "low_confidence_tasks": 14
}
```

### Tool 4: `score_task_confidence`
Analyzes a task and assigns confidence score.

**Parameters**:
- `task_description` (string, required): What the task is
- `task_type` (string, required): "bug_fix", "test_coverage", "security", etc.
- `context` (object, required): {file, line, code_snippet, recent_changes}

**Returns**:
```json
{
  "confidence": "high",
  "reasoning": "Missing import is trivial to fix with zero risk",
  "auto_fixable": true,
  "estimated_effort": "1 minute",
  "risk_level": "low"
}
```

### Tool 5: `execute_auto_fix`
Executes an auto-fix for high-confidence tasks.

**Parameters**:
- `task_id` (string, required): Task ID from proactivity queue
- `dry_run` (boolean, optional): Preview changes without applying (default: false)
- `auto_commit` (boolean, optional): Automatically commit changes (default: true)

**Returns**:
```json
{
  "success": true,
  "changes_made": [
    {
      "file": "agents/neon-database/agent.py",
      "type": "removed_unused_import",
      "line": 12
    }
  ],
  "commit_hash": "def456",
  "tests_passed": true
}
```

### Tool 6: `learn_developer_patterns`
Analyzes git history to learn developer preferences.

**Parameters**:
- `analyze_period` (string, required): "7d", "30d", "90d", "all"
- `pattern_types` (array, required): ["commit_style", "code_style", "testing_patterns", "work_hours"]

**Returns**:
```json
{
  "patterns_discovered": {
    "commit_style": "conventional_commits",
    "preferred_test_framework": "pytest",
    "work_hours": {"start": "09:00", "end": "18:00", "timezone": "UTC+2"},
    "avoided_files": ["convex/migrations/", "agents/legacy/"],
    "code_style": {
      "indentation": "spaces_4",
      "quote_style": "double",
      "line_length": 100
    }
  },
  "confidence": "high",
  "samples_analyzed": 247
}
```

### Tool 7: `get_proactivity_queue`
Retrieves current proactivity queue with filtering.

**Parameters**:
- `filter_confidence` (string, optional): "high", "medium", "low", "all" (default: "all")
- `filter_type` (string, optional): Task type filter
- `sort_by` (string, optional): "confidence", "age", "effort" (default: "confidence")
- `limit` (integer, optional): Max tasks to return (default: 50)

**Returns**:
```json
{
  "total_tasks": 42,
  "filtered_tasks": 8,
  "tasks": [
    {
      "id": "task-015",
      "type": "security",
      "confidence": "high",
      "description": "SQL injection risk in neon_agent.py:234",
      "age_hours": 2,
      "estimated_effort": "10 minutes"
    }
  ]
}
```

### Tool 8: `update_developer_profile`
Updates developer preferences and constraints.

**Parameters**:
- `profile_updates` (object, required): Key-value pairs to update
- `merge_mode` (string, optional): "merge" or "replace" (default: "merge")

**Returns**:
```json
{
  "success": true,
  "profile_path": "memory/developer_profile.json",
  "updated_fields": ["work_hours", "avoided_files"]
}
```

## Integration Requirements

### Environment Variables
```bash
# No new environment variables required
# Uses existing: ANTHROPIC_API_KEY, NEON_DATABASE_URL, VPS_HOSTNAME
```

### Dependencies
```bash
# Python packages (add to requirements.txt)
watchdog==4.0.0      # File system monitoring
gitpython==3.1.40    # Git operations
schedule==1.2.0      # Background task scheduling

# System packages
git                  # Git CLI access
```

### File System Structure
```
shared/
├── proactivity_queue.json       # Persistent task queue
└── confidence.py                # Confidence scoring logic

memory/
└── developer_profile.json       # Learned preferences

agents/
├── git-watcher/                 # Continuous git monitoring
│   ├── agent.py
│   ├── watcher_daemon.py        # Background process
│   └── README.md
└── code-critic/                 # Adversarial code review
    ├── agent.py
    ├── security_rules.py
    └── README.md

orchestrator/
├── proactivity_view.py          # CLI dashboard
└── convergence.py               # Multi-agent decision making

.claude/
└── hooks/
    ├── on-commit.sh             # Git commit hook
    └── on-file-change.sh        # File watcher hook

workers/
└── proactive_worker.py          # Background task executor (systemd service)
```

### Git Hooks Integration
The system must install git hooks automatically:
```bash
# .git/hooks/post-commit
#!/bin/bash
./venv/bin/python3 agents/git-watcher/analyze_commit.py $1
```

### Orchestrator Registration
Both agents must be registered in `orchestrator/registry.json`:

**Git Watcher Agent**:
```json
{
  "name": "git-watcher",
  "triggers": ["scan repository", "check for todos", "find technical debt"],
  "capabilities": ["repository_scanning", "todo_detection", "pattern_analysis"],
  "autonomous": true,
  "background_mode": true
}
```

**Code Critic Agent**:
```json
{
  "name": "code-critic",
  "triggers": ["review code", "check security", "analyze commit"],
  "capabilities": ["security_analysis", "performance_review", "best_practices"],
  "autonomous": true,
  "runs_on_commit": true
}
```

### Systemd Service (Background Worker)
```ini
# /etc/systemd/system/fibreflow-proactive.service
[Unit]
Description=FibreFlow Proactive Worker
After=network.target

[Service]
Type=simple
User=louisdup
WorkingDirectory=/home/louisdup/Agents/claude
ExecStart=/home/louisdup/Agents/claude/venv/bin/python3 workers/proactive_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Success Criteria

### Phase 1: Observation (Must Have)
- [x] Git watcher agent monitors commits in real-time
- [x] Proactivity queue populated with discovered tasks
- [x] Confidence scoring assigns high/medium/low to all tasks
- [x] CLI dashboard shows tasks grouped by confidence level
- [x] Git hooks automatically trigger analysis on commit
- [x] At least 3 task types detected: todos, missing_tests, security

### Phase 2: Automation (Must Have)
- [x] Code critic agent performs adversarial review on every commit
- [x] High-confidence tasks auto-fixed without interruption
- [x] Auto-fixes create git commits with descriptive messages
- [x] Background worker runs as systemd service
- [x] All auto-fixes run tests before committing
- [x] Failed auto-fixes revert changes and alert developer

### Phase 3: Personalization (Should Have)
- [x] Developer profile learns patterns from git history
- [x] Work hours respected (no interruptions outside preferred times)
- [x] Avoided files/directories never suggested for edits
- [x] Suggestion style adapts to developer preferences
- [x] Pattern learning runs weekly and updates profile
- [x] Profile manually editable via CLI or JSON

### Phase 4: Integration (Should Have)
- [x] Proactivity view integrated into orchestrator
- [x] Slash command `/proactive` shows queue
- [x] Sub-agent @proactive-manager for manual queue control
- [x] Metrics tracking: tasks discovered, auto-fixed, dismissed
- [x] Integration tests with existing agents (VPS, Neon, Convex)
- [x] Documentation in CLAUDE.md and README.md

### Phase 5: Advanced (Nice to Have)
- [x] Multi-agent convergence (critic + test-generator + doc-writer)
- [x] Live data integration (VPS metrics, Convex analytics)
- [x] "Best of N" parallel execution for complex tasks
- [x] Agent sandbox integration (E2B) for isolated execution
- [x] Proactivity view web interface (HTML dashboard)

## Performance Requirements

- **Git hook latency**: < 2 seconds per commit
- **Repository scan**: < 30 seconds for full scan
- **Confidence scoring**: < 1 second per task
- **Auto-fix execution**: < 10 seconds including tests
- **Background worker cycle**: Every 60 seconds
- **Pattern learning**: < 5 minutes for 90-day analysis

## Security Considerations

### Auto-Fix Safety
- **Whitelist approach**: Only predefined safe operations allowed
  - Unused import removal
  - Missing docstring addition
  - TODO comment formatting
  - Simple linting fixes
- **Blacklist**: Never auto-fix:
  - Database queries
  - Authentication/authorization code
  - Production configuration
  - Deployment scripts

### Developer Profile Privacy
- All profiles stored locally (never sent to external APIs)
- Profile data: work patterns only, no personal information
- Git history analysis: code patterns only, not commit messages

### Proactivity Queue Security
- Tasks include file paths and code snippets (sensitive data)
- Queue stored locally with restricted permissions (chmod 600)
- No network transmission of queue data

## Testing Requirements

### Unit Tests
- Confidence scoring logic (50+ test cases)
- Task queue operations (add, update, remove, filter)
- Developer profile learning (pattern detection)
- Auto-fix execution (dry run mode)

### Integration Tests
- Git hook triggering and execution
- Background worker scheduling
- Critic agent + git watcher cooperation
- Proactivity view + orchestrator integration

### End-to-End Tests
1. Make commit → git watcher triggers → tasks added to queue
2. High-confidence task → background worker auto-fixes → tests pass → commit created
3. Run `/proactive` → view shows tasks → approve one → task executed
4. Pattern learning → profile updated → suggestions adapt to preferences

### Performance Tests
- Repository scan on large codebase (10,000+ files)
- Concurrent auto-fix execution (5 tasks in parallel)
- Background worker memory usage over 24 hours
- Git hook impact on commit latency

## Documentation Requirements

### Agent README.md Files
- `agents/git-watcher/README.md` - Setup, configuration, usage
- `agents/code-critic/README.md` - Review rules, customization

### User Guides
- How to use proactivity view CLI
- How to configure developer profile
- How to add custom auto-fix rules
- How to disable proactive features (opt-out)

### Developer Guides
- How to add new task types
- How to implement custom confidence scoring
- How to extend critic agent rules
- How to create new auto-fix handlers

### CLAUDE.md Updates
- Proactive system architecture section
- Slash command reference
- Troubleshooting guide
- Performance tuning guide

## Example Workflows

### Workflow 1: Developer Makes Commit
```bash
$ git add .
$ git commit -m "Add contractor export feature"

# Behind the scenes:
# 1. Git hook triggers agents/git-watcher/analyze_commit.py
# 2. Watcher scans diff, finds new function without test
# 3. Task added to proactivity queue with high confidence
# 4. Background worker sees task, generates test stub
# 5. Test committed with message: "Add test for contractor export 🤖"
# 6. Developer notified via CLI on next command
```

### Workflow 2: Developer Checks Proactive Queue
```bash
$ /proactive

=== Proactive Task Queue ===
[HIGH CONFIDENCE] 3 tasks
  • Missing test coverage in agents/neon-database/agent.py:156
  • Unused import in convex_agent.py:12
  • SQL injection risk in neon_agent.py:234

[MEDIUM CONFIDENCE] 7 tasks
[LOW CONFIDENCE] 12 tasks

Commands: [a]pprove all high, [r]eview one-by-one, [d]ismiss low, [q]uit

> a

✓ Auto-fixed unused import (committed as def456)
✓ Generated test stub (committed as ghi789)
⚠ SQL injection requires manual review (queued for next session)
```

### Workflow 3: Weekly Pattern Learning
```bash
# Runs automatically via cron
$ ./venv/bin/python3 agents/pattern-learner/analyze_history.py

Analyzing 247 commits from last 90 days...
✓ Learned preferred commit style: conventional_commits
✓ Detected work hours: 09:00-18:00 UTC+2
✓ Identified avoided files: convex/migrations/*, agents/legacy/*
✓ Code style: 4 spaces, double quotes, 100 char lines

Developer profile updated: memory/developer_profile.json
```

## Dependencies on Existing FibreFlow Components

### Required Components
- `shared/base_agent.py` - Both agents inherit from BaseAgent
- `orchestrator/registry.json` - Agent registration
- `orchestrator/orchestrator.py` - Task routing
- Domain memory patterns (`feature_list.json`, `claude_progress.md`)
- Git repository (for commit analysis)
- Pytest test suite (for validation)

### Optional Integrations
- Superior Agent Brain (for cross-session learning)
- Existing sub-agents (code-reviewer, test-generator, doc-writer)
- VPS Monitor (for live metric integration)
- Neon/Convex agents (for data-driven decisions)

## Cost Estimates

### Development Effort
- Phase 1 (Observation): 2-3 days
- Phase 2 (Automation): 3-4 days
- Phase 3 (Personalization): 1 week
- Phase 4 (Integration): 2-3 days
- Phase 5 (Advanced): 2-3 weeks
- **Total**: 3-5 weeks for complete system

### API Usage (Anthropic)
- Git watcher: ~$0.01 per commit (Haiku)
- Code critic: ~$0.05 per commit (Sonnet)
- Pattern learning: ~$0.10 per week (Sonnet)
- Background worker: ~$5-10 per month (continuous)
- **Total**: ~$20-30/month operational cost

### Infrastructure
- Background worker: No additional compute (runs on dev machine)
- E2B sandboxes (optional): ~$20/month for always-on
- Storage: < 100MB for queues and profiles

## Notes for Agent Harness

### Harness Strategy
1. **Initialize with Phase 1**: Focus on git-watcher agent first
2. **Incremental builds**: Each agent is independent (git-watcher, then code-critic)
3. **Test-driven**: Every tool must have validation tests
4. **Integration last**: Build agents in isolation, integrate after both work

### Potential Challenges
- **Git hook installation**: Harness must write to `.git/hooks/` directory
- **Background worker**: Systemd service requires sudo (may need manual setup)
- **File watching**: `watchdog` library may have platform-specific issues
- **Confidence scoring**: Requires sophisticated logic (may need multiple iterations)

### Success Validation
After harness completes, validate:
```bash
# 1. Agents exist and work
./venv/bin/pytest tests/test_git_watcher.py -v
./venv/bin/pytest tests/test_code_critic.py -v

# 2. Git hooks installed
ls -la .git/hooks/post-commit

# 3. Proactivity queue functional
cat shared/proactivity_queue.json

# 4. CLI works
./venv/bin/python3 orchestrator/proactivity_view.py

# 5. Integration test
git commit --allow-empty -m "Test proactive system"
# Should trigger analysis and populate queue
```

## Version History
- v1.0 (2025-12-15): Initial specification for Agent Harness
