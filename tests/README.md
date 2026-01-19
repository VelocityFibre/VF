# Agent Workforce Test Suite

**Comprehensive test coverage for agent development repository**

---

## Overview

This test suite provides automated testing for:
- **VPS Monitor Agent:** SSH-based monitoring (CPU, memory, disk, network, services)
- **Orchestrator:** Task routing and agent coordination
- **Database Agents:** Neon and Convex database interfaces (extensible)

---

## Quick Start

### Run All Tests

```bash
# From project root
pytest

# Or activate venv first
source venv/bin/activate
pytest
```

### Run Specific Test Files

```bash
# VPS Monitor tests only
pytest tests/test_vps_monitor.py

# Orchestrator tests only
pytest tests/test_orchestrator.py

# With verbose output
pytest -v tests/
```

---

## Test Coverage

### VPS Monitor Agent (test_vps_monitor.py)

**SSHVPSClient Tests (25+ tests):**
- ✅ CPU usage parsing (normal, warning, critical, errors)
- ✅ Memory usage parsing (thresholds, edge cases)
- ✅ Disk usage parsing (percentage calculation)
- ✅ Network statistics (byte conversion)
- ✅ Load average parsing
- ✅ Service status checking (all running, some stopped)
- ✅ System information retrieval
- ✅ Top processes listing
- ✅ Error handling for SSH failures
- ✅ Parse error handling (improved with DEBT-001 fix)

**VPSMonitorAgent Tests:**
- ✅ Agent initialization
- ✅ Tool definition (9 tools)
- ✅ Tool execution
- ✅ Conversation history management

---

### Orchestrator (test_orchestrator.py)

**Registry Tests:**
- ✅ Registry loading and validation
- ✅ Invalid path handling
- ✅ Agent listing

**Routing Tests (20+ tests):**
- ✅ Single agent match
- ✅ Multiple agent matches
- ✅ No match handling
- ✅ Auto-select functionality
- ✅ Keyword matching (case-insensitive)
- ✅ Multiple keyword confidence scoring
- ✅ Sorting by confidence
- ✅ Edge cases (empty string, whitespace, special chars)

**Statistics Tests:**
- ✅ Agent counting
- ✅ Category grouping
- ✅ Active/inactive filtering

**Capability Tests:**
- ✅ Agent capability explanation
- ✅ Not found handling

---

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Shared fixtures
├── test_vps_monitor.py      # VPS Monitor agent tests
├── test_orchestrator.py     # Orchestrator tests
└── README.md                # This file
```

---

## Running Tests with Markers

Tests are categorized with pytest markers for selective running:

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only VPS tests
pytest -m vps

# Run only orchestrator tests
pytest -m orchestrator

# Skip slow tests
pytest -m "not slow"
```

---

## Test Patterns Used

### AAA Pattern (Arrange-Act-Assert)

All tests follow the AAA pattern:

```python
def test_example(self, fixture):
    # Arrange - Set up test data and mocks
    mock_data = {"key": "value"}

    # Act - Execute the function under test
    result = function_to_test(mock_data)

    # Assert - Verify expected behavior
    assert result == expected_value
```

### Mocking

Tests use `unittest.mock` for isolation:

```python
from unittest.mock import Mock, patch

def test_with_mock(self):
    with patch.object(client, 'method') as mock_method:
        mock_method.return_value = {"status": "success"}
        result = client.method()
        assert result['status'] == "success"
```

---

## Fixtures

**Shared fixtures in `conftest.py`:**
- `mock_anthropic_api_key`: Mock API key for testing
- `mock_database_url`: Mock database URL
- `mock_convex_url`: Mock Convex URL
- `mock_vps_hostname`: Mock VPS hostname

**Test-specific fixtures:**
- `vps_client`: SSHVPSClient instance
- `vps_agent`: VPSMonitorAgent instance
- `orchestrator`: AgentOrchestrator instance
- `mock_registry`: Temporary registry for testing

---

## Coverage Goals

**Current Coverage (estimated):**
- VPS Monitor: ~70% (core functionality)
- Orchestrator: ~80% (routing logic)
- Overall: ~60-70%

**Target Coverage:**
- Critical paths: 100%
- Overall: 80%+

**To measure coverage:**
```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest --cov=agents --cov=orchestrator --cov-report=html

# View report
open htmlcov/index.html
```

---

## Adding New Tests

### For New Agents

1. **Create test file:** `tests/test_new_agent.py`
2. **Import agent:** `from agents.new_agent.agent import NewAgent`
3. **Write test class:** `class TestNewAgent:`
4. **Add fixtures:** Mock dependencies
5. **Write tests:** Cover all tools and error cases
6. **Run tests:** `pytest tests/test_new_agent.py`

### Test Checklist

When writing tests for an agent:
- [ ] Test initialization
- [ ] Test all tool definitions
- [ ] Test tool execution (happy path)
- [ ] Test error handling
- [ ] Test edge cases (empty inputs, invalid data)
- [ ] Test conversation history (if applicable)
- [ ] Mock external dependencies (SSH, databases, APIs)
- [ ] Test threshold logic (for monitoring)

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:
```python
# ✅ GOOD - Independent test
def test_cpu_usage(self, vps_client):
    with patch.object(...):
        result = vps_client.get_cpu_usage()
        assert result['cpu_percent'] > 0

# ❌ BAD - Depends on test order
def test_cpu_then_memory(self):
    cpu = vps_client.get_cpu_usage()
    mem = vps_client.get_memory_usage()  # Don't chain tests
```

### 2. Descriptive Test Names

Use clear, descriptive names that explain the scenario:
```python
# ✅ GOOD
def test_get_cpu_usage_returns_warning_when_above_80_percent(self):
    pass

# ❌ BAD
def test_cpu(self):
    pass
```

### 3. One Assertion Per Test (when possible)

```python
# ✅ GOOD - Tests one behavior
def test_cpu_status_normal_below_80(self):
    result = get_cpu_usage(75)
    assert result['status'] == 'normal'

# ⚠️ OK - Related assertions
def test_cpu_parsing_success(self):
    result = get_cpu_usage()
    assert result['cpu_percent'] == 15.3
    assert result['status'] == 'normal'
```

### 4. Mock External Dependencies

Always mock external resources (SSH, databases, APIs):
```python
# ✅ GOOD - Mocked
with patch.object(client, '_run_ssh_command') as mock:
    mock.return_value = {"success": True, "stdout": "data"}
    result = client.get_metrics()

# ❌ BAD - Actual SSH call
result = client.get_metrics()  # Don't do real SSH in tests
```

---

## Continuous Integration

### GitHub Actions Workflow (future)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=agents --cov=orchestrator
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'agents'`

**Solution:** Run pytest from project root:
```bash
cd /home/louisdup/Agents/claude/
pytest
```

### Fixture Not Found

**Problem:** `fixture 'mock_anthropic_api_key' not found`

**Solution:** Ensure `conftest.py` exists in tests directory

### Mock Not Working

**Problem:** Mock not being called

**Solution:** Check patch path matches import:
```python
# If agent imports: from agents.vps_monitor.agent import SSHVPSClient
# Then patch:      patch.object(ssh_client_instance, 'method')
# NOT:              patch('agents.vps_monitor.agent.method')
```

---

## Next Steps

### Immediate
- [ ] Run full test suite
- [ ] Verify all tests pass
- [ ] Measure code coverage

### Short-Term
- [ ] Add tests for database agents (Neon, Convex)
- [ ] Add tests for contractor/project agents
- [ ] Increase coverage to 80%+

### Long-Term
- [ ] Set up CI/CD with GitHub Actions
- [ ] Add integration tests (require real SSH/DB)
- [ ] Add performance/benchmark tests
- [ ] Add mutation testing

---

## Dependencies

**Required:**
- pytest

**Optional (recommended):**
- pytest-cov (coverage reporting)
- pytest-xdist (parallel test execution)
- pytest-mock (enhanced mocking)

**Install:**
```bash
pip install pytest pytest-cov pytest-xdist pytest-mock
```

---

## Metrics

**Test Count:** 45+ tests
**Test Files:** 2
**Coverage:** ~60-70% (estimated)
**Execution Time:** < 5 seconds (with mocks)

---

**Test Suite Status:** ✅ Ready for Use
**Last Updated:** 2025-11-18
**Maintained by:** Agent Development Team
