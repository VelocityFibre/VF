# Claude Code Setup Checklist

Complete guide to setting up a robust Claude Code environment from scratch.

---

## 🎯 Phase 1: Foundation (30 minutes)

### Prerequisites

```bash
- [ ] VS Code installed
- [ ] Claude Code extension installed
- [ ] Anthropic API key obtained
- [ ] Git installed and configured
- [ ] Python 3.8+ or Node.js 18+ (depending on your stack)
```

### Initial Project Structure

```bash
# Create project directory
mkdir -p ~/projects/my-claude-project
cd ~/projects/my-claude-project

# Initialize Git
git init

# Create core structure
mkdir -p .claude/{agents,skills,commands}
mkdir -p docs
```

### Essential Files Checklist

```bash
- [ ] .gitignore created
- [ ] .env.example created
- [ ] .env created (with actual secrets)
- [ ] README.md created
- [ ] .claude/claude.md created
- [ ] .claudeignore created (optional but recommended)
```

### .gitignore Template

```bash
cat > .gitignore << 'EOF'
# Secrets
.env
.env.*
!.env.example
**/credentials.json
**/secrets.json
*.pem
*.key
.keys/

# Claude Code
.claude/conversations/
.claude/cache/
.claude/.settings.local.json
.claude/logs/

# Language-specific
__pycache__/
*.pyc
node_modules/
dist/
build/
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
EOF
```

### .env.example Template

```bash
cat > .env.example << 'EOF'
# Anthropic API
ANTHROPIC_API_KEY=your_key_here

# Database (if using)
DATABASE_URL=postgresql://user:pass@host:5432/db

# External APIs
GITHUB_TOKEN=your_token_here
NOTION_API_KEY=your_key_here

# Application
NODE_ENV=development
DEBUG=true
EOF
```

### Basic claude.md Template

```markdown
cat > .claude/claude.md << 'EOF'
# Project Name

## Purpose
[What this project does and why it exists]

## Current Status
- 🏗️ Initial setup in progress
- [ ] Core functionality to implement
- [ ] Tests to write
- [ ] Documentation to complete

## Technology Stack
- Language: [Python/TypeScript/etc.]
- Framework: [FastAPI/Express/etc.]
- Database: [PostgreSQL/MongoDB/etc.]
- Key Libraries: [list main dependencies]

## Architecture Overview
[Brief description or link to docs/ARCHITECTURE.md]

## Development Conventions

### Code Style
- Formatting: [Black/Prettier/etc.]
- Linting: [Ruff/ESLint/etc.]
- Max line length: 100 characters

### Git Workflow
- Branch naming: feature/*, fix/*, docs/*
- Commit format: Conventional Commits
- PR requirements: Tests pass, review approved

### Testing
- Framework: [pytest/Jest/etc.]
- Coverage target: 80%+
- Test location: tests/ directory

## Project Structure
```
.
├── .claude/           # Claude Code config
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Environment Setup
```bash
# Install dependencies
[pip install -r requirements.txt / npm install]

# Set up database
[migration commands]

# Run tests
[test commands]

# Start development server
[run commands]
```

## Common Tasks

### Run Tests
```bash
[your test command]
```

### Database Migrations
```bash
[your migration commands]
```

### Deploy
```bash
[your deployment process]
```

## External Resources
- Documentation: [URL]
- API Docs: [URL]
- Design Specs: [URL]
- Production: [URL]

## Team & Communication
- Project Lead: [Name]
- Repository: [GitHub URL]
- Issue Tracker: [URL]
- Chat: [Slack/Discord channel]

## Notes
[Any additional context, decisions, or important information]
EOF
```

### Initialize Git Repository

```bash
# Create initial commit
git add .
git commit -m "Initial project setup with Claude Code"

# Create GitHub repo (if using)
gh repo create my-claude-project --private --source=.
git push -u origin main
```

**Checklist:**
```bash
- [ ] All files created
- [ ] .env contains actual secrets (verified)
- [ ] claude.md customized for your project
- [ ] Git initialized and first commit made
- [ ] Secrets NOT committed (check: git log --all --full-history -- .env)
```

---

## 🔐 Phase 2: Security Hardening (15 minutes)

### API Key Security Audit

```bash
# 1. Verify .env is in .gitignore
grep -q "^\.env$" .gitignore && echo "✅ .env ignored" || echo "❌ ADD .env to .gitignore!"

# 2. Check no secrets in Git history
git log --all --full-history --source -- "*env*" "*secret*" "*key*"
# Should return nothing or only .env.example

# 3. Scan for hardcoded secrets
grep -r "sk-ant-" . --exclude-dir={.git,node_modules,venv}
# Should only appear in .env

# 4. Create .env.example if missing
grep -v "^#" .env | sed 's/=.*/=your_value_here/' > .env.example
```

### File Permissions

```bash
# Restrict .env to owner only
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (600)
```

### Settings Hierarchy Setup

```bash
# Create settings files
cat > .claude/settings.json << 'EOF'
{
  "allowed_tools": ["read_file", "write_file", "bash"],
  "context_window_threshold": 0.7,
  "auto_compact": false
}
EOF

# Personal overrides (not in git)
cat > .claude/settings.local.json << 'EOF'
{
  "theme": "dark",
  "notifications": false
}
EOF
```

**Checklist:**
```bash
- [ ] No secrets in Git history
- [ ] .env has 600 permissions
- [ ] .env.example created and safe to share
- [ ] settings.json configured
- [ ] settings.local.json in .gitignore
```

---

## 🧠 Phase 3: Context Optimization (20 minutes)

### Create .claudeignore

```bash
cat > .claudeignore << 'EOF'
# Dependencies
node_modules/
venv/
__pycache__/
.venv/
env/

# Build outputs
dist/
build/
*.egg-info/
.next/
out/

# Logs
*.log
logs/
.claude/logs/

# Test outputs
.pytest_cache/
.coverage
htmlcov/
coverage/
test-results/

# Large data files
*.csv
*.xlsx
*.db
*.sqlite
*.sqlite3

# Media
*.mp4
*.mov
*.avi
*.mp3
*.wav

# Archives
*.zip
*.tar.gz
*.rar

# Git
.git/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF
```

### Structure for Progressive Disclosure

```bash
# Split large documentation
mkdir -p docs/{api,database,deployment,architecture}

# Instead of one huge file:
# docs/everything.md (5000 lines)

# Create focused files:
# docs/api/endpoints.md
# docs/api/authentication.md
# docs/database/schema.md
# docs/database/migrations.md
# docs/deployment/production.md
# docs/deployment/staging.md
```

### Reference Files Organization

```markdown
# In claude.md, link strategically:

## Documentation

### API
- [Endpoints](./docs/api/endpoints.md)
- [Authentication](./docs/api/authentication.md)

### Database
- [Schema](./docs/database/schema.md)
- [Migrations](./docs/database/migrations.md)

### Deployment
- [Production](./docs/deployment/production.md)
- [Staging](./docs/deployment/staging.md)

# Claude loads only what's needed per context
```

**Checklist:**
```bash
- [ ] .claudeignore created
- [ ] Large files excluded from context
- [ ] Documentation split into focused files
- [ ] claude.md links to detailed docs
- [ ] Test context loading (should be < 30% at start)
```

---

## 🤖 Phase 4: First Agent & Skill (30 minutes)

### Create First Skill: Testing Workflow

```bash
mkdir -p .claude/skills/testing-workflow
```

```markdown
cat > .claude/skills/testing-workflow/SKILL.md << 'EOF'
---
name: Testing Workflow
description: Guides test writing, execution, and coverage analysis
---

# Testing Workflow

## When to Use
- Writing new tests
- Running test suites
- Analyzing coverage
- Debugging test failures

## Test Structure

### Unit Tests
Location: `tests/unit/`
Naming: `test_<module_name>.py`

### Integration Tests
Location: `tests/integration/`
Naming: `test_<feature_name>.py`

## Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_auth.py

# With coverage
pytest --cov=src --cov-report=html
```

## Writing Good Tests

### Pattern
```python
def test_function_scenario():
    # Arrange
    input_data = create_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Coverage Checklist
- [ ] Happy path tested
- [ ] Edge cases covered
- [ ] Error conditions handled
- [ ] Boundary values tested

## References
- Testing framework docs: [link]
- Coverage tool docs: [link]
EOF
```

### Create First Agent: Code Reviewer

```bash
mkdir -p .claude/agents/code-reviewer
```

```markdown
cat > .claude/agents/code-reviewer/agent.md << 'EOF'
---
name: Code Reviewer
description: Reviews code for quality, security, and best practices before commits
allowed_tools: ["read_file", "bash"]
---

# Code Reviewer Agent

## Responsibilities
- Review code changes before commits
- Check for security vulnerabilities
- Enforce coding standards
- Suggest improvements

## Review Checklist

### Code Quality
- [ ] Functions are small and focused
- [ ] Variable names are descriptive
- [ ] Comments explain "why", not "what"
- [ ] No dead code

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] XSS prevention (if web)

### Testing
- [ ] Tests exist for new functionality
- [ ] Edge cases covered
- [ ] Tests actually test behavior

### Performance
- [ ] No obvious N+1 queries
- [ ] Appropriate data structures used
- [ ] Caching where beneficial

## Commands

```bash
# Review current changes
git diff | python review.py

# Check specific file
python review.py --file src/module.py
```
EOF
```

**Checklist:**
```bash
- [ ] Testing skill created
- [ ] Code reviewer agent created
- [ ] Skills discoverable (check: ls .claude/skills/)
- [ ] Agents discoverable (check: ls .claude/agents/)
- [ ] Test invocation: "Use Testing Workflow skill"
- [ ] Test agent: "Review my recent changes"
```

---

## 🔗 Phase 5: External Integrations (Optional, 30-60 minutes)

### GitHub Integration

```bash
# Install GitHub CLI
# macOS: brew install gh
# Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Authenticate
gh auth login

# Test
gh repo view
```

### Database Connection (PostgreSQL example)

```bash
# Install client
pip install psycopg2-binary

# Test connection
python << 'EOF'
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print("✅ Database connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
```

### MCP Setup (if needed)

```bash
# Install recommended MCPs
claude-code mcp install filesystem
claude-code mcp install github

# Verify
claude-code mcp status
```

**Checklist:**
```bash
- [ ] GitHub CLI installed and authenticated
- [ ] Database connection tested
- [ ] MCPs installed (if using)
- [ ] All integrations documented in claude.md
- [ ] Connection strings in .env, not hardcoded
```

---

## 📊 Phase 6: Monitoring & Logging (20 minutes)

### Create Logging Structure

```bash
mkdir -p .claude/logs
mkdir -p logs/
```

### Basic Logging Setup

```python
# Create: scripts/setup_logging.py
cat > scripts/setup_logging.py << 'EOF'
import logging
from datetime import datetime

def setup_logging():
    log_file = f"logs/app_{datetime.now():%Y%m%d}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logging configured successfully")
EOF

# Test
python scripts/setup_logging.py
```

### Agent Usage Tracking

```bash
# Create tracking file structure
mkdir -p .claude/logs/agents
```

```python
# Create: .claude/scripts/track_usage.py
cat > .claude/scripts/track_usage.py << 'EOF'
import json
from datetime import datetime
from pathlib import Path

def log_agent_usage(agent_name, success, execution_time):
    log_file = Path(".claude/logs/agents/usage.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "success": success,
        "execution_time_seconds": execution_time
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    # Test
    log_agent_usage("test-agent", True, 2.5)
    print("✅ Usage tracking configured")
EOF

# Test
python .claude/scripts/track_usage.py
```

**Checklist:**
```bash
- [ ] Logging directory structure created
- [ ] Basic logging script created
- [ ] Agent usage tracking implemented
- [ ] Log files in .gitignore
- [ ] Test logs generated successfully
```

---

## ✅ Phase 7: Verification & Testing (15 minutes)

### Comprehensive Test

```bash
#!/bin/bash
# Create: scripts/verify_setup.sh

echo "🔍 Verifying Claude Code Setup..."
echo

# Check environment
echo "1️⃣ Environment Variables"
[ -f .env ] && echo "✅ .env exists" || echo "❌ .env missing"
[ -f .env.example ] && echo "✅ .env.example exists" || echo "❌ .env.example missing"
echo

# Check Git
echo "2️⃣ Git Configuration"
git rev-parse --git-dir > /dev/null 2>&1 && echo "✅ Git initialized" || echo "❌ Git not initialized"
grep -q "^\.env$" .gitignore && echo "✅ .env in .gitignore" || echo "❌ .env NOT in .gitignore"
echo

# Check Claude structure
echo "3️⃣ Claude Code Structure"
[ -f .claude/claude.md ] && echo "✅ claude.md exists" || echo "❌ claude.md missing"
[ -d .claude/skills ] && echo "✅ skills/ exists" || echo "❌ skills/ missing"
[ -d .claude/agents ] && echo "✅ agents/ exists" || echo "❌ agents/ missing"
echo

# Check no secrets in Git
echo "4️⃣ Security Check"
if git log --all --full-history --source -- ".env" > /dev/null 2>&1; then
    echo "❌ WARNING: .env might be in Git history!"
else
    echo "✅ No secrets in Git history"
fi
echo

# Count files
echo "📁 Project Status"
echo "Skills: $(ls .claude/skills/ 2>/dev/null | wc -l)"
echo "Agents: $(ls .claude/agents/ 2>/dev/null | wc -l)"
echo "Docs: $(find docs/ -name '*.md' 2>/dev/null | wc -l)"
echo

echo "✅ Setup verification complete!"
```

```bash
# Make executable and run
chmod +x scripts/verify_setup.sh
./scripts/verify_setup.sh
```

### Test Claude Code

```bash
# Start Claude Code session
claude-code

# Test commands:
# 1. "Check context usage" → Should be < 30%
# 2. "List available skills" → Should show testing-workflow
# 3. "List available agents" → Should show code-reviewer
# 4. "Use Testing Workflow skill to explain testing" → Should invoke skill
```

**Final Checklist:**
```bash
- [ ] verify_setup.sh runs without errors
- [ ] No critical warnings
- [ ] Claude Code starts successfully
- [ ] Skills are discoverable
- [ ] Agents are discoverable
- [ ] Context usage is reasonable (< 30%)
```

---

## 🚀 Phase 8: First Real Task (Next Steps)

### Start Development

```markdown
# In Claude Code, try:

"I want to implement [your first feature].
Use plan mode to create an implementation strategy."

# This tests:
- Plan mode functionality
- Context understanding
- Agent orchestration
- Skill usage
```

### Document Learnings

```bash
# Create: docs/LESSONS_LEARNED.md
- What worked well
- What needs improvement
- Unexpected behaviors
- Optimization ideas
```

### Iterate

```markdown
# After first task:
- [ ] Review agent effectiveness
- [ ] Refine skill instructions
- [ ] Update claude.md with new learnings
- [ ] Add new skills as patterns emerge
- [ ] Commit changes to Git
```

---

## 📋 Quick Reference

### Daily Startup Routine

```bash
# 1. Pull latest changes
git pull

# 2. Check environment
source .env  # or: export $(cat .env | xargs)

# 3. Start Claude Code
claude-code

# 4. Check context
# In Claude: "Check context usage"
```

### Weekly Maintenance

```bash
- [ ] Review agent logs
- [ ] Update claude.md with new patterns
- [ ] Refine skill instructions
- [ ] Archive old conversations
- [ ] Check context efficiency
- [ ] Update documentation
- [ ] Git commit accumulated changes
```

---

## 🆘 Common Setup Issues

### "API key not found"
```bash
# Check .env exists
ls -la .env

# Verify format (no extra spaces/quotes)
cat .env
```

### "Permission denied"
```bash
# Fix .env permissions
chmod 600 .env

# Fix script permissions
chmod +x scripts/*.sh
```

### "Context immediately full"
```bash
# Check what's included
cat .claudeignore

# Add node_modules, venv, etc.
```

---

## 🎓 Next Steps After Setup

1. **Read:** `CLAUDE_CODE_BEST_PRACTICES.md`
2. **Review:** `TROUBLESHOOTING.md` for common issues
3. **Explore:** `AGENT_SKILLS_GUIDE.md` for advanced patterns
4. **Build:** Start your first real feature!

---

**Congratulations! Your Claude Code environment is ready for production use.** 🎉
