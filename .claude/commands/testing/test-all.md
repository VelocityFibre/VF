---
description: Run complete test suite with comprehensive summary
---

# Complete Test Suite Runner

Run the entire FibreFlow test suite with detailed analysis and reporting.

## Execution

```bash
./venv/bin/pytest tests/ -v --tb=short
```

## Test Coverage

FibreFlow uses pytest with organized test markers:

### Test Categories

#### Unit Tests (@pytest.mark.unit)
- **Characteristic**: Fast, isolated, no external dependencies
- **Purpose**: Test individual functions and methods
- **Run separately**: `./venv/bin/pytest -m unit -v`

#### Integration Tests (@pytest.mark.integration)
- **Characteristic**: Slower, requires external resources (databases, APIs)
- **Purpose**: Test component interactions
- **Run separately**: `./venv/bin/pytest -m integration -v`

#### Agent-Specific Tests
- `@pytest.mark.vps` - VPS Monitor agent tests
- `@pytest.mark.database` - Database agent tests
- `@pytest.mark.orchestrator` - Orchestrator tests

## Test Execution Strategy

### Step 1: Run Full Suite
```bash
./venv/bin/pytest tests/ -v --tb=short
```

Monitor for:
- Total tests found
- Tests passed/failed/skipped
- Warnings
- Execution time

### Step 2: Analyze Results

**If all tests pass**:
- Report total passed
- Highlight execution time
- Note any warnings
- Confirm production readiness

**If tests fail**:
- Categorize failures by severity
- Identify root causes
- Provide specific fixes
- Prioritize critical fixes

### Step 3: Coverage Analysis (if available)

```bash
./venv/bin/pytest tests/ --cov=agents --cov=orchestrator --cov-report=term-missing
```

Report:
- Overall coverage percentage
- Files with low coverage (<80%)
- Untested code paths
- Recommendations for additional tests

## Test Report Format

```markdown
## Test Suite Report
**Timestamp**: [YYYY-MM-DD HH:MM:SS]
**Python Version**: [Version from venv]
**Pytest Version**: [Version]

---

### Overall Status: ✅ PASSED / ❌ FAILED / ⚠️ PARTIAL

**Summary**:
- ✅ Passed: XXX tests
- ❌ Failed: XXX tests
- ⚠️ Skipped: XXX tests
- 📊 Total: XXX tests
- ⏱️ Duration: XX.XXs

---

### Test Breakdown by Category

#### Unit Tests
- Tests: XX/XX passed (XX%)
- Duration: X.Xs
- Status: ✅ All passing

#### Integration Tests
- Tests: XX/XX passed (XX%)
- Duration: X.Xs
- Status: ✅ All passing / ❌ X failures

#### VPS Monitor Tests
- Tests: XX/XX passed
- Status: ✅ / ❌

#### Database Agent Tests
- Tests: XX/XX passed
- Status: ✅ / ❌

#### Orchestrator Tests
- Tests: XX/XX passed
- Status: ✅ / ❌

---

### Test Files Summary

| File | Tests | Passed | Failed | Duration |
|------|-------|--------|--------|----------|
| test_vps_monitor.py | XX | XX | 0 | X.Xs |
| test_neon_database.py | XX | XX | 0 | X.Xs |
| test_orchestrator.py | XX | XX | 0 | X.Xs |
| [other files...] | XX | XX | X | X.Xs |

---

### Failures (if any)

#### 🔴 Critical Failures
**Test**: `test_function_name` in `test_file.py:123`
**Error**: [Error message]
**Cause**: [Root cause analysis]
**Fix**:
```python
# Suggested fix with code example
```

**Priority**: MUST FIX before deployment

#### 🟡 Non-Critical Failures
**Test**: `test_other_function` in `test_file.py:456`
**Error**: [Error message]
**Fix**: [Suggested fix]
**Priority**: Should fix soon

---

### Warnings

⚠️ **Warning 1**: [Description]
- **Location**: [File:line]
- **Impact**: [Low/Medium/High]
- **Recommendation**: [Action to take]

⚠️ **Warning 2**: [Description]
- **Recommendation**: [Action to take]

---

### Coverage Report (if available)

**Overall Coverage**: XX%

#### Coverage by Module
| Module | Coverage | Missing Lines |
|--------|----------|---------------|
| agents/vps-monitor/ | XX% | [lines] |
| agents/neon-database/ | XX% | [lines] |
| orchestrator/ | XX% | [lines] |

#### Low Coverage Areas (<80%)
- 🔴 `agents/module/file.py`: XX% - [Reason for low coverage]
- 🟡 `orchestrator/router.py`: XX% - [Needs more edge case tests]

**Recommendations**:
- Add tests for [specific uncovered code]
- Increase coverage in [module] to >80%

---

### Performance Metrics

**Slowest Tests** (>1 second):
1. `test_slow_function` - X.Xs
2. `test_another_slow` - X.Xs

**Recommendations**:
- Consider mocking external calls in slow tests
- Split long integration tests into smaller units

---

### Production Readiness

#### Deployment Blockers
[If any critical test failures:]
- 🔴 Fix: [Critical failure 1]
- 🔴 Fix: [Critical failure 2]

[If all tests pass:]
✅ No deployment blockers. All tests passing.

#### Pre-Deployment Checklist
- [ ] All critical tests passing
- [ ] No regressions from previous run
- [ ] Integration tests validate external dependencies
- [ ] Coverage >70% (target: 80%)
- [ ] No new warnings introduced

---

### Recommendations

#### Immediate Actions
1. [Action item 1 - Priority HIGH]
2. [Action item 2 - Priority MEDIUM]

#### Future Improvements
- [ ] Increase test coverage in [module]
- [ ] Add edge case tests for [feature]
- [ ] Optimize slow tests
- [ ] Add more integration test scenarios

---

### Next Steps

[If tests passed:]
✅ **Ready for deployment** - All tests passing
- Review code changes one more time
- Run `/code-review` for final security/performance check
- Proceed with deployment when ready

[If tests failed:]
❌ **Not ready for deployment** - Fix failures first
- Address critical failures immediately
- Re-run tests after fixes
- Consider adding regression tests

---

### Test History Comparison

[If available, compare to previous run:]
- **Previous Run**: XXX passed, XXX failed
- **Current Run**: XXX passed, XXX failed
- **Change**: ✅ +XX tests passing / ❌ +XX tests failing

---

### Commands Used

```bash
# Full test suite
./venv/bin/pytest tests/ -v --tb=short

# Unit tests only
./venv/bin/pytest -m unit -v

# Integration tests only
./venv/bin/pytest -m integration -v

# Specific agent tests
./venv/bin/pytest tests/test_vps_monitor.py -v

# With coverage
./venv/bin/pytest tests/ --cov=agents --cov=orchestrator --cov-report=html
```

---

**Report Generated**: [Timestamp]
**Saved To**: [Optional log file path]
```

## Advanced Options

### Run Specific Test Categories

```bash
# Only unit tests (fast)
./venv/bin/pytest -m unit -v

# Only integration tests
./venv/bin/pytest -m integration -v

# Only VPS monitor tests
./venv/bin/pytest -m vps -v

# Only database tests
./venv/bin/pytest -m database -v
```

### Verbose Output

```bash
# Extra verbose (show test docstrings)
./venv/bin/pytest tests/ -vv

# Show print statements
./venv/bin/pytest tests/ -v -s

# Full traceback (instead of short)
./venv/bin/pytest tests/ -v --tb=long
```

### Debugging Failed Tests

```bash
# Stop on first failure
./venv/bin/pytest tests/ -x

# Drop into debugger on failure
./venv/bin/pytest tests/ --pdb

# Re-run only failed tests from last run
./venv/bin/pytest tests/ --lf
```

### Performance Analysis

```bash
# Show slowest 10 tests
./venv/bin/pytest tests/ --durations=10

# Profile test execution
./venv/bin/pytest tests/ --profile
```

## Continuous Integration

This command can be used in CI/CD pipeline:

```bash
#!/bin/bash
# ci-test.sh

echo "Running FibreFlow test suite..."

# Run tests with coverage
./venv/bin/pytest tests/ -v --tb=short --cov=agents --cov=orchestrator --cov-report=xml

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
    exit 0
else
    echo "❌ Tests failed"
    exit 1
fi
```

## Test Maintenance

### Adding New Tests

When creating new agents or features:
1. Create test file: `tests/test_[feature].py`
2. Add appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`
3. Follow existing test patterns
4. Run full suite to ensure no regressions

### Test Quality Standards

Every test should:
- Have descriptive docstring
- Test one specific behavior
- Use appropriate fixtures
- Mock external dependencies (unit tests)
- Handle cleanup properly
- Run quickly (<1 second for unit tests)

### Coverage Goals

- **Overall**: >70% (target: 80%)
- **Critical Modules**: >90%
  - Orchestrator logic
  - Agent tool execution
  - Database queries
  - Security-related code

## Troubleshooting

### Tests Fail in CI but Pass Locally
**Possible Causes**:
- Environment differences
- Missing environment variables
- Different Python versions
- Timing issues

**Solutions**:
- Match CI environment locally
- Add explicit wait/timeouts
- Check `.env` variables

### Slow Test Suite
**Possible Causes**:
- Too many integration tests
- External API calls not mocked
- Large data fixtures

**Solutions**:
- Mock external calls
- Use smaller test datasets
- Run unit and integration tests separately

### Flaky Tests
**Possible Causes**:
- Race conditions
- External service instability
- Timing-dependent logic

**Solutions**:
- Add retries for external calls
- Use explicit waits instead of sleeps
- Mock unstable external services

## Integration with Other Commands

### Before Deployment
```bash
# Full workflow
/test-all          # Run all tests
/code-review       # Security/performance review
/deploy agent-name # Deploy if all pass
```

### After Code Changes
```bash
# Quick validation
/test-all
# If failures, fix and re-run specific tests
./venv/bin/pytest tests/test_[specific].py -v
```

### Regular Maintenance
```bash
# Weekly: Full suite with coverage
./venv/bin/pytest tests/ --cov=agents --cov=orchestrator --cov-report=html
# Review HTML coverage report
open htmlcov/index.html
```

## Success Criteria

Test run is successful when:
- ✅ All tests pass (100%)
- ✅ No critical warnings
- ✅ Coverage >70%
- ✅ Execution time reasonable (<2 minutes)
- ✅ No flaky tests (consistent results)

## Documentation

After adding new tests:
- [ ] Update test documentation
- [ ] Add test markers if needed
- [ ] Document any special setup requirements
- [ ] Update this command if new test categories added
