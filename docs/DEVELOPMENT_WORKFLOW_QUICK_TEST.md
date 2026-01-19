# Development Workflow - Quick Test Guide

**Purpose**: Fast 5-minute validation that everything works
**Use**: After pulling updates or before teaching workflow to team

---

## Quick Test (5 minutes)

### 1. Test TDD Commands (2 min)

```bash
# Create spec
.claude/commands/tdd/spec.sh test-example

# Generate tests
.claude/commands/tdd/generate.sh tests/specs/test-example.spec.md <<< "n"

# Check class name is valid Python (no hyphens)
grep "^class " tests/unit/test_test-example.py
# Expected: class TestTestExample:

# Validate
.claude/commands/tdd/validate.sh

# Cleanup
rm -rf tests/specs/test-example.spec.md tests/unit/test_test-example.py tests/integration/test_test-example_integration.py
```

**✅ Success**: Valid Python class names, no syntax errors

---

### 2. Test Module Profiles (1 min)

```bash
# Verify YAML is valid
cat .claude/modules/_index.yaml | head -20

# Check a module profile
cat .claude/modules/qfieldcloud.md | grep "^##" | head -10
```

**✅ Success**: YAML parses, markdown has clear structure

---

### 3. Test CLI Helpers (1 min)

```bash
# Source helpers
source scripts/gh-workflows.sh

# Should show help automatically
# Test a function exists
type ff-help
```

**✅ Success**: Help displays, functions defined

---

### 4. Test Quality Gates (1 min)

```bash
# Dry run (won't deploy, just shows options)
./sync-to-hostinger
```

**✅ Success**: Shows options, mentions quality gates for --code

---

## Common Issues

### Issue: "class Test-feature: SyntaxError"
**Cause**: Old version of generate.sh (before fix)
**Fix**: Pull latest changes, class names now auto-converted

### Issue: "/tdd: command not found"
**Cause**: Scripts not executable
**Fix**: `chmod +x .claude/commands/tdd/*.sh`

### Issue: "pytest: command not found"
**Cause**: pytest not installed
**Fix**: `./venv/bin/pip install pytest pytest-cov`

### Issue: "ff-sync: command not found"
**Cause**: Helpers not sourced
**Fix**: `source scripts/gh-workflows.sh`

---

## Full Test Report

See `docs/DEVELOPMENT_WORKFLOW_TEST_RESULTS.md` for comprehensive test results with all edge cases.

---

**Last Updated**: 2026-01-12
