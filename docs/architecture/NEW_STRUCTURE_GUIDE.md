# Quick Reference: New Repository Structure

**Last Updated**: 2025-12-17 (Post-Reorganization)

## Directory Structure

```
FibreFlow-Agent-Workforce/
├── 📄 README.md                    # Navigation hub
├── 📄 CLAUDE.md                    # Main reference for Claude Code
├── 📄 pyproject.toml               # Modern Python packaging
├── 📄 .env.example                 # Environment template
├── 📄 requirements.txt             # Points to requirements/base.txt
│
├── 📁 .claude/                     # Claude Code configuration
│   ├── config.yaml                 # Unified AI settings
│   ├── settings.local.json         # MCP configuration
│   ├── skills/                     # Production skills (7)
│   │   ├── database-operations/
│   │   ├── vf-server/
│   │   └── skill_version_manager.py
│   ├── agents/                     # Sub-agents (5)
│   └── commands/                   # Slash commands
│
├── 📁 docs/                        # All documentation (71 files)
│   ├── guides/                     # 18 how-to guides
│   ├── architecture/               # 7 design documents
│   ├── api/                        # 5 reference docs
│   └── archive/                    # 48 historical docs
│
├── 📁 agents/                      # Production agents
│   ├── neon-database/             # PostgreSQL agent
│   ├── convex-database/           # Convex backend agent
│   └── vps-monitor/               # VPS monitoring
│
├── 📁 tests/                       # All tests
│   ├── integration/               # 14 integration tests
│   ├── unit/                      # Unit tests (structure)
│   ├── conftest.py
│   └── README.md
│
├── 📁 scripts/                     # Utility scripts
│   ├── sharepoint/                # 4 SharePoint utilities
│   ├── convex/                    # 4 Convex utilities
│   └── sync/                      # 1 sync script
│
├── 📁 requirements/                # Structured dependencies
│   ├── base.txt                   # Core deps
│   ├── dev.txt                    # Dev tools
│   └── production.txt             # Production extras
│
├── 📁 shared/                      # Shared utilities
│   ├── base_agent.py
│   ├── config.py
│   └── logging_config.py          # NEW: Logging infrastructure
│
├── 📁 metrics/                     # NEW: Metrics collection
│   └── collector.py
│
├── 📁 benchmarks/                  # NEW: Performance testing
│   └── performance_suite.py
│
├── 📁 demos/                       # Demo applications
│   ├── demo_neon_agent.py
│   └── demo_convex_agent.py
│
├── 📁 legacy/                      # Archived old code
│   ├── agents/
│   ├── skills/
│   └── tests/
│
├── 📁 data/                        # JSON data files
├── 📁 artifacts/                   # Build artifacts
├── 📁 orchestrator/                # Task routing
├── 📁 harness/                     # Agent builder
├── 📁 convex/                      # Convex backend
├── 📁 memory/                      # Memory systems
└── 📁 deploy/                      # Deployment scripts
```

## File Locations Changed

### Documentation
| Old Location | New Location |
|--------------|--------------|
| `*.md` (69 files in root) | `docs/guides/`, `docs/architecture/`, `docs/api/`, `docs/archive/` |
| `QUICK_REFERENCE.md` | `docs/api/QUICK_REFERENCE.md` |
| `AGENT_INIT_GUIDE.md` | `docs/guides/AGENT_INIT_GUIDE.md` |

### Tests
| Old Location | New Location |
|--------------|--------------|
| `test_*.py` (14 files in root) | `tests/integration/test_*.py` |
| `demo_*.py` (2 files in root) | `demos/demo_*.py` |

### Scripts
| Old Location | New Location |
|--------------|--------------|
| `sync_neon_to_convex.py` | `scripts/sync/sync_neon_to_convex.py` |
| `*sharepoint*.py` | `scripts/sharepoint/*.py` |
| `*convex*.py` | `scripts/convex/*.py` |

### Dependencies
| Old Location | New Location |
|--------------|--------------|
| `requirements_superior_brain.txt` | `requirements/production.txt` (integrated) |
| `ui-module/requirements.txt` | `requirements/base.txt` (consolidated) |

## Common Tasks

### Installation
```bash
# Basic install
pip install -r requirements.txt

# Development install (includes test tools, linting, etc.)
pip install -r requirements/dev.txt

# Production install (includes monitoring, security, performance)
pip install -r requirements/production.txt

# Editable install with extras
pip install -e .[dev]           # Development
pip install -e .[brain]         # With Superior Brain
pip install -e .[production]    # Full production stack
```

### Testing
```bash
# All tests
./venv/bin/pytest tests/ -v

# Integration tests only
./venv/bin/pytest tests/integration/ -v

# Specific test file
./venv/bin/pytest tests/integration/test_neon.py -v

# With coverage
./venv/bin/pytest tests/ --cov=agents --cov=orchestrator --cov-report=html
```

### Running Demos
```bash
# Neon database demo
./venv/bin/python3 demos/demo_neon_agent.py

# Convex backend demo
./venv/bin/python3 demos/demo_convex_agent.py
```

### Monitoring
```bash
# Test logging system
./venv/bin/python3 -m shared.logging_config

# Test metrics collection
./venv/bin/python3 -m metrics.collector

# Run benchmarks
./venv/bin/python3 -m benchmarks.performance_suite

# Check skill versions
./venv/bin/python3 .claude/skills/skill_version_manager.py

# View logs
tail -f logs/fibreflow.log
tail -f logs/fibreflow_errors.log

# Generate metrics report
./venv/bin/python3 -c "from metrics.collector import get_collector; get_collector().generate_report()"
```

### Code Quality
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Format code
black .

# Lint code
ruff check .

# Type check
mypy agents/ orchestrator/ shared/
```

## Import Path Changes

### Tests
```python
# OLD (if imports were from root)
from test_neon import some_function

# NEW
from tests.integration.test_neon import some_function
```

### Scripts
```python
# OLD
from sync_neon_to_convex import sync_data

# NEW
from scripts.sync.sync_neon_to_convex import sync_data
```

### Demos
```python
# OLD
from demo_neon_agent import run_demo

# NEW
from demos.demo_neon_agent import run_demo
```

## Configuration Files

### Primary Configurations
| File | Purpose |
|------|---------|
| `pyproject.toml` | Python packaging, tool configs |
| `.claude/config.yaml` | AI/agent configuration |
| `.pre-commit-config.yaml` | Code quality automation |
| `.editorconfig` | Editor formatting standards |
| `pytest.ini` | Test configuration (legacy compat) |
| `.env.example` | Environment variable template |

### Tool Configuration Locations
All tool configs now in `pyproject.toml`:
- `[tool.black]` - Code formatting
- `[tool.ruff]` - Linting rules
- `[tool.mypy]` - Type checking
- `[tool.pytest.ini_options]` - Test settings
- `[tool.coverage.run]` - Coverage config

## Quick Commands

```bash
# Setup new environment
python3 -m venv venv && source venv/bin/activate
pip install -e .[dev]
pre-commit install

# Run full quality check
pre-commit run --all-files && pytest tests/ -v

# Generate all reports
./venv/bin/python3 -m metrics.collector
./venv/bin/python3 -m benchmarks.performance_suite

# Deploy to production
cd deploy && ./deploy_brain.sh

# Sync databases
./venv/bin/python3 scripts/sync/sync_neon_to_convex.py
```

## Documentation Locations

| Topic | Location |
|-------|----------|
| Getting Started | `README.md` |
| Claude Code Guide | `CLAUDE.md` |
| Transformation Summary | `TRANSFORMATION_COMPLETE.md` |
| Architecture | `docs/architecture/` |
| Development Guides | `docs/guides/` |
| API Reference | `docs/api/` |
| Historical Docs | `docs/archive/` |

## Support

- **Main Documentation**: `README.md` → links to everything
- **Claude Code**: `CLAUDE.md` → comprehensive reference
- **Transformation Details**: `TRANSFORMATION_COMPLETE.md`
- **Change Summary**: `REORGANIZATION_SUMMARY.md`

## Key Improvements

✅ **96% reduction** in root MD files (69 → 3)
✅ **100% elimination** of root Python files (30+ → 0)
✅ **Structured dependencies** with environment separation
✅ **Modern packaging** with pyproject.toml
✅ **Automated quality** with pre-commit hooks
✅ **Production monitoring** with logging, metrics, benchmarking
✅ **Skill versioning** with semver and deprecation

---

**Remember**: Always work from the new structure. If something seems missing, check:
1. `docs/` for documentation
2. `tests/integration/` for test files
3. `scripts/` for utility scripts
4. `demos/` for example code
5. `legacy/` for old archived code