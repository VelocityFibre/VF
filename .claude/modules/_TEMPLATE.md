# Module: [Module Name]

**Type**: [agent/skill/module/infrastructure]
**Location**: [filesystem path]
**Deployment**: [URL or server location]
**Isolation**: [fully_isolated/mostly_isolated/tightly_coupled]
**Developers**: [comma-separated list]
**Last Updated**: YYYY-MM-DD

---

## Overview

Brief description of what this module does and why it exists.

## Dependencies

### External Dependencies
- **Service/Library 1**: Why it's needed
- **Service/Library 2**: Why it's needed

### Internal Dependencies
- **Module 1**: What functionality is shared
- **Module 2**: What functionality is shared

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| table_name | Purpose | id, column1, column2 |

### Tables Referenced
| Table | Owner | How Used |
|-------|-------|----------|
| other_table | other_module | Read-only queries |

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /api/resource | GET | List resources | Yes |
| /api/resource/:id | POST | Create resource | Yes |

## Services/Methods

### Core Services
- **ServiceName.method()** - What it does, parameters, return value
- **AnotherService.process()** - What it does

## File Structure

```
module_root/
├── services/       # Business logic
├── types/          # Type definitions
├── components/     # UI (if applicable)
├── utils/          # Helpers
└── tests/          # Test files
```

## Configuration

### Environment Variables
```bash
MODULE_API_KEY=xxx          # Description
MODULE_DATABASE_URL=xxx     # Description
```

### Config Files
- `config.yaml` - Main configuration
- `.env.example` - Environment template

## Common Operations

### Development
```bash
# Start development server
command here

# Run tests
command here

# Build
command here
```

### Deployment
```bash
# Deploy to staging
command here

# Deploy to production
command here

# Rollback
command here
```

## Known Gotchas

### Issue 1: [Title]
**Problem**: Description of the problem
**Solution**: How to fix/avoid it
**Reference**: Link to documentation or PR

### Issue 2: [Title]
**Problem**: Description
**Solution**: How to fix/avoid it

## Testing Strategy

### Unit Tests
- Location: `tests/unit/`
- Coverage requirement: 80%+
- Key areas to test: List critical paths

### Integration Tests
- Location: `tests/integration/`
- External dependencies: How they're mocked
- Key scenarios: List integration scenarios

### E2E Tests (if applicable)
- Location: `tests/e2e/`
- Browser/tool: Playwright, etc.
- Critical user flows: List

## Monitoring & Alerts

### Health Checks
- Endpoint: `/health` or monitoring command
- Expected response: What indicates healthy

### Key Metrics
- Metric 1: What to monitor
- Metric 2: Threshold for alerts

### Logs
- Location: Where logs are stored
- Key log patterns: What to grep for

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| YYYY-MM-DD | Description | Yes/No | PR/commit link |

## Related Documentation

- [Link to guide 1](path)
- [Link to guide 2](path)

## Contact

**Primary Owner**: Name
**Team**: Team name
**Slack Channel**: #channel-name
