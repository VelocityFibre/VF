# Module: Workflow

**Type**: module (Next.js app feature)
**Location**: `src/app/workflow/` (main FibreFlow app)
**Deployment**: app.fibreflow.app/workflow
**Isolation**: tightly_coupled
**Developers**: hein, louis
**Last Updated**: 2026-01-12

---

## Overview

Business process automation system that orchestrates multi-step workflows across installations, projects, and ticketing. Defines workflow templates, tracks execution, manages state transitions, and triggers actions. Uses Inngest for background job orchestration.

**⚠️ CRITICAL CONTEXT**: Tightly coupled module - affects installations, projects, and ticketing. Changes require comprehensive integration testing. This is the "nervous system" of FibreFlow operations.

## Dependencies

### External Dependencies
- **Neon PostgreSQL**: Workflow definitions, execution state
- **Convex**: Real-time workflow status updates
- **Inngest**: Background job orchestration, retries, error handling
  - Handles async workflow steps (email, API calls, database updates)
  - Manages retries and failure recovery

### Internal Dependencies (TIGHTLY COUPLED)
- **Installations Module** (read/write): Workflows trigger installation phases, update status
- **Projects Module** (read/write): Project workflows (approval, planning, execution)
- **Ticketing Module** (write): Auto-create tickets on workflow failures
- **Contractors Module** (read): Contractor approval workflows

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| workflows | Workflow templates | id, name, description, type (installation/project/approval), steps_json, created_at |
| workflow_instances | Active workflow executions | id, workflow_id, entity_type, entity_id, status, current_step, started_at, completed_at |
| workflow_steps | Individual step tracking | id, instance_id, step_name, status, input_data, output_data, started_at, completed_at |
| workflow_triggers | Automated triggers | id, workflow_id, trigger_type (schedule/event), trigger_config, enabled |

**Common Queries**:
```sql
-- Get active workflows for an installation
SELECT wi.*, w.name, w.steps_json
FROM workflow_instances wi
JOIN workflows w ON wi.workflow_id = w.id
WHERE wi.entity_type = 'installation' AND wi.entity_id = $1 AND wi.status = 'running';

-- Get workflow execution history
SELECT ws.step_name, ws.status, ws.started_at, ws.completed_at, ws.output_data
FROM workflow_steps ws
WHERE ws.instance_id = $1
ORDER BY ws.started_at;
```

### Tables Referenced (Read/Write)
| Table | Owner | How Used |
|-------|-------|----------|
| installations | installations | Update installation status based on workflow progress |
| projects | projects | Trigger project approval workflows, update project state |
| tickets | ticketing | Create tickets when workflows fail or require intervention |
| contractors | core | Contractor approval workflows (read contractor data) |

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /api/workflows | GET | List workflow templates | Yes |
| /api/workflows/:id | GET | Get workflow definition | Yes |
| /api/workflows/:id/trigger | POST | Manually trigger workflow | Yes (admin) |
| /api/workflows/instances | GET | List active workflow instances | Yes |
| /api/workflows/instances/:id | GET | Get workflow execution details | Yes |
| /api/workflows/instances/:id/cancel | POST | Cancel running workflow | Yes (admin) |
| /api/workflows/instances/:id/retry | POST | Retry failed workflow | Yes |

**Frontend Routes**:
- `/workflow` - Workflow dashboard
- `/workflow/templates` - Workflow template list
- `/workflow/instances` - Active workflow executions
- `/workflow/:id` - Workflow execution detail

## Services/Methods

### Core Services
- **WorkflowEngine** (`src/services/workflow-engine.ts`)
  - `startWorkflow(workflowId, entityType, entityId)` - Initiates workflow execution
  - `executeStep(instanceId, stepName)` - Runs individual workflow step
  - `transitionWorkflow(instanceId, newStatus)` - Updates workflow state
  - `cancelWorkflow(instanceId)` - Stops running workflow

- **InngestWorkflowService** (Inngest integration)
  - Handles async workflow steps
  - Manages retries (exponential backoff)
  - Error recovery and alerting
  - Step completion callbacks

- **WorkflowBuilder** (Template management)
  - `createWorkflow(definition)` - Creates workflow template
  - `validateWorkflow(steps)` - Validates workflow definition
  - `duplicateWorkflow(id)` - Clones existing workflow

### Common Workflow Types
1. **Installation Workflow**: Planning → Contractor Assignment → Site Survey → Installation → QA → Completion
2. **Project Approval Workflow**: Submission → Manager Review → Budget Approval → Contractor Assignment
3. **DR Photo Review Workflow**: Photo Upload → VLM Analysis → Approval/Rejection → Contractor Notification

## File Structure

```
src/app/workflow/
├── page.tsx                      # Workflow dashboard
├── templates/
│   ├── page.tsx                 # Template list
│   ├── [id]/
│   │   └── page.tsx             # Template detail/edit
│   └── new/
│       └── page.tsx             # Create template
├── instances/
│   ├── page.tsx                 # Running workflows
│   └── [id]/
│       └── page.tsx             # Execution detail
├── components/
│   ├── WorkflowBuilder.tsx      # Visual workflow editor
│   ├── WorkflowStepCard.tsx     # Step status display
│   └── WorkflowTimeline.tsx     # Execution timeline
├── hooks/
│   └── useWorkflows.ts          # React hooks
└── types/
    └── workflow.ts              # TypeScript interfaces

src/services/
└── workflow-engine.ts           # Core workflow logic

inngest/
└── workflows/                   # Inngest function definitions
    ├── installation-workflow.ts
    ├── project-approval.ts
    └── dr-photo-review.ts
```

## Configuration

### Environment Variables
```bash
# Database
NEON_DATABASE_URL=postgresql://...
CONVEX_URL=https://quixotic-crow-802.convex.cloud

# Inngest
INNGEST_EVENT_KEY=xxx
INNGEST_SIGNING_KEY=xxx
INNGEST_APP_ID=fibreflow-workflows

# Integrations
SLACK_WEBHOOK_URL=xxx  # For workflow failure alerts
SMTP_HOST=...          # For email steps
```

### Workflow Definition Format (JSON)
```json
{
  "name": "Installation Workflow",
  "type": "installation",
  "steps": [
    {
      "id": "assign_contractor",
      "name": "Assign Contractor",
      "type": "database_update",
      "config": {
        "table": "installations",
        "field": "contractor_id",
        "value": "{{workflow.input.contractor_id}}"
      },
      "on_failure": "create_ticket"
    },
    {
      "id": "send_notification",
      "name": "Notify Contractor",
      "type": "email",
      "config": {
        "to": "{{contractor.email}}",
        "template": "contractor_assignment"
      }
    }
  ]
}
```

## Common Operations

### Development
```bash
# Run dev server
npm run dev

# Navigate to workflow dashboard
open http://localhost:3000/workflow

# Test Inngest functions locally
npx inngest-cli dev

# Run workflow engine tests
npm test -- src/services/workflow-engine.test.ts
```

### Deployment
```bash
# Deploy to production
ssh velo@100.96.203.105
cd /srv/data/apps/fibreflow
git pull origin main
npm ci
npm run build

# Deploy Inngest functions
npx inngest deploy

# Restart application
pm2 restart fibreflow-prod
```

### Manual Operations
```bash
# Trigger workflow via API
curl -X POST http://app.fibreflow.app/api/workflows/1/trigger \
  -H 'Authorization: Bearer xxx' \
  -d '{"entity_type": "installation", "entity_id": 123}'

# Cancel stuck workflow
curl -X POST http://app.fibreflow.app/api/workflows/instances/456/cancel \
  -H 'Authorization: Bearer xxx'
```

## Known Gotchas

### Issue 1: Workflow Stuck in "Running" State (COMMON)
**Problem**: Workflow instance shows "running" but no progress for >30 minutes
**Root Cause**: Inngest function failed silently or lost connection
**Solution**:
```bash
# Check Inngest function logs
open https://app.inngest.com/env/production/runs

# Retry workflow
curl -X POST http://app.fibreflow.app/api/workflows/instances/{id}/retry \
  -H 'Authorization: Bearer xxx'

# Or manually cancel and restart
curl -X POST http://app.fibreflow.app/api/workflows/instances/{id}/cancel \
  -H 'Authorization: Bearer xxx'
```
**Prevention**: Set timeouts on all workflow steps (max 5 minutes per step)
**Reference**: `docs/guides/inngest_implementation.md`

### Issue 2: Installation Status Not Updating
**Problem**: Workflow completes but installation status still shows old value
**Root Cause**: Database update step failed or was skipped
**Solution**:
```sql
-- Check workflow step logs
SELECT step_name, status, output_data
FROM workflow_steps
WHERE instance_id = $1
ORDER BY started_at;

-- Manually update installation if needed
UPDATE installations SET status = 'completed' WHERE id = $2;
```

### Issue 3: Workflow Triggers Installation Creation, Creates Duplicate
**Problem**: Starting workflow creates duplicate installation records
**Root Cause**: Workflow definition has duplicate "create_installation" step
**Solution**:
```typescript
// Validate workflow definition before saving
const steps = workflow.steps_json;
const stepNames = steps.map(s => s.id);
const duplicates = stepNames.filter((name, index) => stepNames.indexOf(name) !== index);
if (duplicates.length > 0) {
  throw new Error(`Duplicate step IDs: ${duplicates}`);
}
```

### Issue 4: Inngest Functions Not Deploying
**Problem**: Workflow changes not reflected, using old workflow logic
**Root Cause**: Inngest functions not re-deployed after code changes
**Solution**:
```bash
# Re-deploy Inngest functions
npx inngest deploy

# Verify deployment
npx inngest status
```

## Testing Strategy

### Unit Tests
- Location: `tests/unit/workflow/`
- Coverage requirement: 90%+ (critical path)
- Key areas:
  - Workflow engine state transitions
  - Step validation logic
  - Error handling and retries

### Integration Tests (CRITICAL)
- Location: `tests/integration/workflow/`
- External dependencies: Test Neon database, mock Inngest, mock Convex
- **Required scenarios**:
  - Installation workflow → updates installations table
  - Project workflow → updates projects table
  - Failure workflow → creates ticket in ticketing module
  - Email step → sends via SMTP (mocked)
  - Database step → updates correct table/field

### E2E Tests (ESSENTIAL FOR TIGHTLY COUPLED MODULE)
- Location: `tests/e2e/workflow/`
- Tool: Playwright + database snapshots
- **Critical user flows**:
  1. Create installation → auto-trigger workflow → verify installation updated
  2. Manual workflow trigger → verify all steps execute → verify final state
  3. Workflow failure → verify ticket created → verify notification sent
  4. Cancel running workflow → verify cleanup → verify rollback (if applicable)

**⚠️ NEVER deploy workflow changes without E2E tests passing**

## Monitoring & Alerts

### Health Checks
- Endpoint: `/api/workflows/instances?status=running&limit=1`
- Expected response: Array of running workflows (or empty)

### Key Metrics
- **Active workflows**: `SELECT COUNT(*) FROM workflow_instances WHERE status = 'running';`
- **Stuck workflows**: Running >30 min with no step progress (alert if >0)
- **Failed workflows**: `SELECT COUNT(*) FROM workflow_instances WHERE status = 'failed' AND created_at > NOW() - INTERVAL '24 hours';`
- **Average workflow duration**: By workflow type

### Logs
- Location: PM2 logs + Inngest dashboard
  - `pm2 logs fibreflow-prod | grep workflow`
  - https://app.inngest.com/env/production/runs
- Key log patterns:
  - `Started workflow: ...` - Workflow initiated
  - `Completed step: ...` - Step success
  - `ERROR: Workflow step failed` - Step failure (should retry)
  - `Workflow failed permanently` - Max retries exceeded (create ticket)

### Alerts (Slack/Email)
- Stuck workflow >30 minutes
- Workflow failure after max retries
- Installation workflow fail (high priority)
- >5 workflows failing in 1 hour (system issue)

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| 2025-XX-XX | Added Inngest integration | Yes - Set up Inngest, deploy functions | inngest_implementation.md |
| 2025-XX-XX | Workflow triggers installation updates | Yes - Update installations table schema | OPERATIONS_LOG.md |

## Related Documentation

- [Inngest Implementation Guide](docs/guides/inngest_implementation.md)
- [Agent OS Inngest Integration](docs/guides/agent_os_inngest_integration.md)
- [Installations Module](.claude/modules/installations.md) (if exists)
- [Projects Module](.claude/modules/projects.md) (if exists)

## Contact

**Primary Owners**: Hein (workflow builder UI), Louis (workflow engine/Inngest)
**Team**: FibreFlow Core
**Deployment**: app.fibreflow.app (VF Server port 3000)

---

**⚠️ REMINDER**: This is a tightly coupled module. Always:
1. Run full integration test suite before deploying
2. Test on staging environment (port 3006) first
3. Verify installations, projects, and ticketing not affected
4. Have rollback plan ready
5. Monitor Inngest dashboard for 30 minutes post-deployment
