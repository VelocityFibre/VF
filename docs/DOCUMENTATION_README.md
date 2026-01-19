# Documentation System - Quick Start

**Everything you need to know about FibreFlow's documentation system**

---

## 📚 **The Three Documentation Files**

### 1. CHANGELOG.md - "What Changed"
**When to use**: Feature releases, bug fixes, version history

**Example**:
```markdown
## [Unreleased]

### Added
- WhatsApp integration for contractor feedback (2025-12-17)

### Fixed
- Contractor query performance optimization (2025-12-17)
```

**Quick add**:
```bash
./scripts/add-changelog-entry.sh  # Interactive, 30 seconds
```

---

### 2. docs/OPERATIONS_LOG.md - "How It Runs"
**When to use**: Deployments, migrations, incidents, server changes

**Example**:
```markdown
## 2025-12-17

### 20:40 UTC - VF Server: FibreFlow Migration

**Type**: Migration
**Severity**: Medium
**Status**: ✅ Complete

**Change**: Moved from /home/louis/apps/fibreflow/ to /srv/data/apps/fibreflow/

**Rollback Procedure**:
1. Stop services
2. Move back to /home/louis/apps/
3. Restart
```

**Quick add**:
```bash
./scripts/add-operations-entry.sh  # Template + editor, 2 minutes
```

---

### 3. docs/DECISION_LOG.md - "Why We Chose This"
**When to use**: Architecture decisions, technology choices, major trade-offs

**Example**:
```markdown
## ADR-004: Use /srv/data/ for Production Apps

**Decision**: Move to NVMe storage
**Rationale**: 99x faster, more capacity, FHS compliant
**Alternatives**: Stay in /home/, use /opt/
**Trade-offs**: One-time migration cost vs long-term performance
```

**Quick add**: Copy existing ADR as template, edit manually

---

## 🔧 **Automation: The Four Layers**

### Layer 1: Git Hooks (Local)
**Installed**: ✅ Yes (you just ran install script)

**What they do**:
- `commit-msg`: Blocks bad commit messages
- `pre-push`: Warns if docs not updated

**Test**:
```bash
git commit -m "bad message"  # ❌ Blocked
git commit -m "test: good message"  # ✅ Passes
```

---

### Layer 2: Helper Scripts (Easy)
**Location**: `scripts/`

**Available**:
- `add-changelog-entry.sh` - Interactive CHANGELOG
- `add-operations-entry.sh` - Pre-filled OPS_LOG template
- `install-git-hooks.sh` - Install hooks (already done)

**Time saved**: 5 minutes → 30 seconds

---

### Layer 3: CI/CD (GitHub)
**Location**: `.github/workflows/documentation-check.yml`

**What it does**:
- Validates every push/PR
- Comments on PRs if docs missing
- Checks conventional commit format

**Example output**:
```
⚠️ CHANGELOG.md not updated (feat commits detected)
⚠️ OPERATIONS_LOG.md not updated (deployment commits detected)
```

---

### Layer 4: Culture (Process)
**Tools**:
- Definition of Done checklists
- PR template with docs section
- Quarterly reviews

**See**: `docs/DOCUMENTATION_AUTOMATION.md`

---

## 🚀 **Daily Workflows**

### Adding a Feature

```bash
# 1. Code
nano agents/new_feature.py

# 2. Commit (enforced format)
git commit -m "feat(agents): Add new feature"
# 💡 TIP: Consider updating CHANGELOG.md

# 3. Quick CHANGELOG entry
./scripts/add-changelog-entry.sh
# Select: Added
# Enter: New feature description
# ✓ Done!

# 4. Include in commit
git add CHANGELOG.md
git commit --amend --no-edit

# 5. Push
git push
# ✅ All documentation up to date
```

---

### Deploying Changes

```bash
# 1. Deploy
./deploy.sh production

# 2. Document
./scripts/add-operations-entry.sh
# Title: Production deployment
# Type: Deployment
# Severity: Medium
# Editor opens with template
# Fill in: what, why, how, rollback
# ✓ Done!

# 3. Commit
git add docs/OPERATIONS_LOG.md
git commit -m "docs: Document production deployment"
git push
```

---

### Making Architecture Decision

```bash
# 1. Discuss and decide
# (Team meeting, design review, etc.)

# 2. Document decision
nano docs/DECISION_LOG.md
# Copy existing ADR as template
# Fill in: context, alternatives, decision, trade-offs

# 3. Update CHANGELOG
./scripts/add-changelog-entry.sh
# Select: Changed
# Enter: New architecture for X

# 4. Commit
git add docs/DECISION_LOG.md CHANGELOG.md
git commit -m "docs: ADR-005 - Why we chose X architecture"
git push
```

---

## 🎯 **Decision Tree: Which Doc?**

```
Is this important to remember?
│
├─ NO → Git commit message is enough
│
└─ YES → What type?
          │
          ├─ User-facing change? → CHANGELOG.md
          │   (features, fixes, breaking changes)
          │
          ├─ Operational change? → docs/OPERATIONS_LOG.md
          │   (deployments, migrations, incidents)
          │
          └─ Architecture decision? → docs/DECISION_LOG.md
              (technology choices, design patterns)
```

---

## ⚡ **Quick Reference**

| Action | Command | Time | Doc |
|--------|---------|------|-----|
| Add feature entry | `./scripts/add-changelog-entry.sh` | 30s | CHANGELOG.md |
| Document deployment | `./scripts/add-operations-entry.sh` | 2min | OPERATIONS_LOG.md |
| Create ADR | Copy template, edit | 10min | DECISION_LOG.md |
| Check hooks installed | `ls -la .git/hooks/commit-msg` | 1s | - |
| Bypass hooks | `git commit --no-verify` | - | - |
| View automation guide | `cat docs/DOCUMENTATION_AUTOMATION.md` | - | - |

---

## 📖 **Full Documentation**

| Document | Purpose |
|----------|---------|
| `CHANGELOG.md` | Version history and releases |
| `docs/OPERATIONS_LOG.md` | Server changes and procedures |
| `docs/DECISION_LOG.md` | Architecture decisions (ADRs) |
| `docs/DOCUMENTATION_FRAMEWORK.md` | **How to decide what to document** |
| `docs/DOCUMENTATION_AUTOMATION.md` | **How automation works** |
| `docs/DOCUMENTATION_README.md` | **This file - quick start** |

---

## 🛠️ **Troubleshooting**

### Hooks not working?
```bash
chmod +x .git/hooks/commit-msg .git/hooks/pre-push
```

### Need to bypass?
```bash
git commit --no-verify  # Skip commit-msg
git push --no-verify    # Skip pre-push
```

### Helper script fails?
```bash
# Check permissions
ls -la scripts/add-*.sh
# Should be: -rwxr-xr-x

# Fix
chmod +x scripts/add-*.sh
```

### CI check failing?
```bash
# Debug locally
git log @{u}..HEAD --oneline  # What commits?
git diff --name-only @{u}..HEAD  # What changed?
```

---

## 📊 **Success Metrics**

**Measure quarterly**:

```bash
# Commit format compliance
git log --oneline | grep -cE "^[a-f0-9]+ (feat|fix|docs)"

# Documentation coverage
# Compare: git log --grep="feat\|fix" vs CHANGELOG.md entries
```

**Targets**:
- ✅ 100% conventional commit compliance
- ✅ 90%+ features documented in CHANGELOG
- ✅ 100% deployments documented in OPERATIONS_LOG
- ✅ <1 minute to add docs

---

## 🎓 **For New Team Members**

**Onboarding checklist**:

```bash
# 1. Clone repo
git clone <repo-url>

# 2. Install hooks (one-time)
./scripts/install-git-hooks.sh

# 3. Test hooks
git commit -m "test message"  # Should fail
git commit -m "test: message"  # Should pass

# 4. Read docs
cat docs/DOCUMENTATION_README.md  # This file
cat docs/DOCUMENTATION_FRAMEWORK.md  # Decision guide
cat docs/DOCUMENTATION_AUTOMATION.md  # Automation deep-dive

# 5. Try helper scripts
./scripts/add-changelog-entry.sh

# Done! You're ready to document.
```

---

## 🔗 **Related Files**

**Core system**:
- `CHANGELOG.md` - The changelog
- `docs/OPERATIONS_LOG.md` - Operations log
- `docs/DECISION_LOG.md` - Architecture decisions

**Automation**:
- `.git/hooks/commit-msg` - Commit validation
- `.git/hooks/pre-push` - Pre-push reminder
- `scripts/install-git-hooks.sh` - Hook installer
- `scripts/add-changelog-entry.sh` - CHANGELOG helper
- `scripts/add-operations-entry.sh` - OPS_LOG helper
- `.github/workflows/documentation-check.yml` - CI validation

**Documentation**:
- `docs/DOCUMENTATION_FRAMEWORK.md` - **When & what to document**
- `docs/DOCUMENTATION_AUTOMATION.md` - **How automation works**
- `docs/DOCUMENTATION_README.md` - **This file**

---

## ✅ **You're All Set!**

The documentation system is:
- ✅ Installed (git hooks active)
- ✅ Automated (reminders at commit/push)
- ✅ Easy (helper scripts ready)
- ✅ Validated (CI checks on GitHub)

**Next time you commit/deploy**:
1. Follow the prompts
2. Use the helper scripts
3. Documentation happens automatically

**Questions?** See `docs/DOCUMENTATION_AUTOMATION.md` for complete guide.

---

**The Formula**: `Good Tools + Automation + Culture = Documentation That Actually Happens`
