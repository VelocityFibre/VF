# Module: Ticketing

**Type**: module (Next.js app feature)
**Location**: `src/app/tickets/` (main FibreFlow app)
**Deployment**: app.fibreflow.app/tickets
**Isolation**: mostly_isolated
**Developers**: hein, louis
**Last Updated**: 2026-01-12

---

## Overview

Support ticket management system for contractors and internal staff. Handles issue creation, assignment, status tracking, comments, and attachments. Integrates with autonomous GitHub Actions ticketing system for automated issue resolution.

**Critical Context**: Mostly isolated - has its own tables but reads from contractors, projects, and users tables. Minimal writes to other modules. Safe to modify with awareness of shared data.

## Dependencies

### External Dependencies
- **Neon PostgreSQL**: Primary data storage
- **Convex**: Real-time ticket updates (`tickets_realtime` table)
- **GitHub API**: Autonomous ticketing integration
  - Repo: https://github.com/VelocityFibre/ticketing
  - Auto-triggers GitHub Actions for 80% of issues

### Internal Dependencies
- **Contractors Module** (read): Display contractor info, filter tickets by contractor
- **Projects Module** (read): Link tickets to projects
- **Users/Auth** (read): Ticket assignment, creator tracking
- **Workflow Module** (weak coupling): Some workflows may create tickets

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| tickets | Main ticket table | id, title, description, status, priority, contractor_id, project_id, assigned_to, created_by, created_at, updated_at |
| ticket_comments | Ticket discussions | id, ticket_id, user_id, comment_body, created_at |
| ticket_attachments | File uploads | id, ticket_id, file_url, file_name, uploaded_by, created_at |
| ticket_status_history | Audit trail | id, ticket_id, old_status, new_status, changed_by, changed_at |

**Common Queries**:
```sql
-- Get open tickets by contractor
SELECT * FROM tickets WHERE contractor_id = $1 AND status != 'closed' ORDER BY priority DESC, created_at DESC;

-- Get ticket with full context
SELECT t.*, c.name as contractor_name, p.name as project_name, u.email as assigned_email
FROM tickets t
LEFT JOIN contractors c ON t.contractor_id = c.id
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN users u ON t.assigned_to = u.id
WHERE t.id = $1;
```

### Tables Referenced
| Table | Owner | How Used |
|-------|-------|----------|
| contractors | core | Display contractor details, filter tickets |
| projects | core | Link tickets to projects, show project context |
| users | auth | Ticket assignment, creator info |

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /api/tickets | GET | List all tickets (filtered) | Yes |
| /api/tickets | POST | Create new ticket | Yes |
| /api/tickets/:id | GET | Get single ticket | Yes |
| /api/tickets/:id | PATCH | Update ticket | Yes |
| /api/tickets/:id/comments | POST | Add comment | Yes |
| /api/tickets/:id/attachments | POST | Upload attachment | Yes |
| /api/tickets/:id/assign | POST | Assign to user | Yes |
| /api/tickets/:id/close | POST | Close ticket | Yes |

**Frontend Routes**:
- `/tickets` - Ticket list page
- `/tickets/new` - Create ticket form
- `/tickets/:id` - Ticket detail view

## Services/Methods

### Core Services
- **TicketService** (`src/services/ticket-service.ts`)
  - `createTicket(data)` - Creates ticket in Neon + Convex
  - `updateTicket(id, updates)` - Updates ticket, logs status changes
  - `assignTicket(id, userId)` - Assigns ticket to user
  - `closeTicket(id, resolution)` - Closes ticket, creates history entry

- **GitHubTicketingService** (GitHub Actions integration)
  - Auto-triggers on ticket creation
  - Attempts autonomous resolution (80% success rate)
  - Escalates complex issues to human assignee
  - Response time: 25-30 seconds

- **NotificationService** (sends alerts)
  - Email notifications on ticket creation/assignment
  - Real-time updates via Convex subscriptions

## File Structure

```
src/app/tickets/
├── page.tsx                    # Ticket list view
├── new/
│   └── page.tsx               # Create ticket form
├── [id]/
│   ├── page.tsx               # Ticket detail view
│   └── edit/
│       └── page.tsx           # Edit ticket
├── components/
│   ├── TicketCard.tsx        # Ticket preview card
│   ├── TicketComments.tsx    # Comment thread
│   └── TicketFilters.tsx     # Filter sidebar
├── hooks/
│   └── useTickets.ts         # React hooks for tickets
└── types/
    └── ticket.ts             # TypeScript interfaces

src/services/
└── ticket-service.ts         # Business logic

convex/
└── tickets.ts               # Convex real-time functions
```

## Configuration

### Environment Variables
```bash
# Database
NEON_DATABASE_URL=postgresql://...
CONVEX_URL=https://quixotic-crow-802.convex.cloud

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_REPO=VelocityFibre/ticketing

# Notifications
SMTP_HOST=...
SMTP_USER=...
```

### Config Files
- `.env` - Environment variables
- `docs/guides/AUTONOMOUS_GITHUB_TICKETING.md` - GitHub Actions setup

## Common Operations

### Development
```bash
# Run dev server
npm run dev

# Navigate to tickets page
open http://localhost:3000/tickets

# Run type check
npm run type-check

# Run tests
npm test -- src/app/tickets/
```

### Deployment
```bash
# Deploy to production (app.fibreflow.app)
ssh velo@100.96.203.105
cd /srv/data/apps/fibreflow
git pull origin main
npm ci
npm run build
pm2 restart fibreflow-prod
```

### Database Migration
```bash
# Add new column to tickets table
psql $NEON_DATABASE_URL -c "ALTER TABLE tickets ADD COLUMN resolution_notes TEXT;"

# Update Convex schema
npx convex deploy
```

## Known Gotchas

### Issue 1: Real-Time Updates Not Working
**Problem**: Ticket status changes not reflected immediately in UI
**Root Cause**: Convex subscription not set up or connection lost
**Solution**:
```typescript
// In components, ensure Convex subscription is active
const tickets = useQuery(api.tickets.getTickets, {});

// Check Convex deployment
npx convex deploy
```
**Reference**: Convex docs

### Issue 2: GitHub Actions Ticketing Not Triggering
**Problem**: New tickets created but no autonomous resolution attempt
**Root Cause**: GitHub Actions workflow not configured or token expired
**Solution**:
```bash
# Check GitHub Actions status
gh workflow list --repo VelocityFibre/ticketing

# View recent runs
gh run list --repo VelocityFibre/ticketing --limit 5

# Re-trigger manually
gh workflow run autonomous-ticketing.yml --repo VelocityFibre/ticketing
```
**Reference**: `docs/guides/AUTONOMOUS_GITHUB_TICKETING.md`

### Issue 3: Ticket Assignment Fails (User Not Found)
**Problem**: Can't assign ticket, "User not found" error
**Root Cause**: User exists in auth system but not in users table
**Solution**:
```sql
-- Verify user exists
SELECT * FROM users WHERE email = 'user@example.com';

-- If missing, create user record
INSERT INTO users (id, email, name, role) VALUES (...);
```

### Issue 4: File Upload Fails (Storage API Down)
**Problem**: Can't attach files to tickets
**Root Cause**: VF Server storage API (port 8091) not running
**Solution**:
```bash
# Check storage API
curl http://100.96.203.105:8091/health

# Restart if needed
ssh velo@100.96.203.105
pm2 restart storage-api
```
**Reference**: `FIREBASE_STORAGE_MIGRATION_2026-01-09.md`

## Testing Strategy

### Unit Tests
- Location: `tests/unit/ticketing/`
- Coverage requirement: 80%+
- Key areas:
  - Ticket CRUD operations
  - Status transitions (pending → in_progress → closed)
  - Comment/attachment handling

### Integration Tests
- Location: `tests/integration/ticketing/`
- External dependencies: Test Neon database, mock Convex, mock GitHub API
- Key scenarios:
  - Create ticket → auto-trigger GitHub Actions → resolution
  - Update ticket → Neon + Convex sync
  - Filter tickets by contractor/project

### E2E Tests
- Location: `tests/e2e/ticketing/`
- Tool: Playwright
- Critical user flows:
  1. Login as contractor
  2. Navigate to /tickets/new
  3. Fill form (title, description, priority)
  4. Submit ticket
  5. Verify ticket appears in /tickets list
  6. Verify GitHub Actions triggered (check logs)
  7. Verify ticket auto-resolved or assigned

## Monitoring & Alerts

### Health Checks
- Endpoint: `/api/tickets?limit=1` (should return 200)
- Expected response: Array of tickets (even if empty)

### Key Metrics
- **Tickets created per day**: `SELECT COUNT(*) FROM tickets WHERE created_at > NOW() - INTERVAL '24 hours';`
- **Autonomous resolution rate**: Target 80% (from GitHub Actions logs)
- **Average resolution time**: Manual vs autonomous
- **Open tickets**: `SELECT COUNT(*) FROM tickets WHERE status != 'closed';`

### Logs
- Location: PM2 logs on VF Server
  - `pm2 logs fibreflow-prod | grep ticket`
- Key log patterns:
  - `Created ticket: ...` - Ticket creation
  - `GitHub Actions triggered` - Autonomous resolution started
  - `Ticket resolved autonomously` - Success
  - `ERROR: Failed to create ticket` - Database/validation issue

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| 2025-XX-XX | Added autonomous GitHub ticketing | Yes - Set up GitHub Actions | AUTONOMOUS_GITHUB_TICKETING.md |
| 2026-01-XX | Migrated to VF Server storage | Yes - Update NEXT_PUBLIC_STORAGE_URL | FIREBASE_STORAGE_MIGRATION.md |

## Related Documentation

- [Autonomous GitHub Ticketing Guide](docs/guides/AUTONOMOUS_GITHUB_TICKETING.md)
- [Neon Database Schema](docs/DATABASE_TABLES.md)
- [Convex Integration](CONVEX_AGENT_GUIDE.md)

## Contact

**Primary Owners**: Hein (frontend), Louis (backend/GitHub Actions)
**Team**: FibreFlow Core
**Deployment**: app.fibreflow.app (VF Server port 3000)
