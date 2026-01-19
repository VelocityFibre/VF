# FibreFlow Application Rules

## Context
This file loads when working on the FibreFlow Next.js application.

## Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Database**: Neon PostgreSQL (104 tables) + Convex (real-time)
- **Styling**: Tailwind CSS + shadcn/ui
- **Auth**: Clerk
- **Deployment**: VF Server via PM2

## Port Allocation
- **Production**: 3000 → https://app.fibreflow.app
- **Staging**: 3006 → https://vf.fibreflow.app (Louis)
- **Development**: 3005 → Local development (Hein)

## Key Modules
- **Workflow**: Project management and installations
- **WA Monitor**: WhatsApp QA drop monitoring
- **Ticketing**: Support ticket system
- **Contractor**: Contractor management

## Database Strategy
- **Neon**: Source of truth (PostgreSQL)
- **Convex**: Operational/real-time data
- **Sync**: Run `sync_neon_to_convex.py` after schema changes

## Deployment Process
```bash
# Standard deployment (includes tests)
./sync-to-hostinger --code

# Quick deployment (skip tests - use with caution)
./sync-to-hostinger --quick

# Rollback if needed
./sync-to-hostinger --rollback <commit-hash>
```

## Known Issues
1. **WA Monitor Send Feedback Button**
   - UI button broken due to Next.js API routing issue
   - Workaround: Direct call to port 8092
   - Never suggest client-side fixes

2. **Module Isolation**
   - wa-monitor is fully isolated (zero dependencies)
   - Never suggest breaking this isolation

## Testing Requirements
- Unit tests: 80% coverage minimum
- Run before deployment: `./venv/bin/pytest tests/ -v`
- E2E tests: Critical user flows only

## Development Patterns
- TypeScript strict mode enabled
- Use server actions for mutations
- Client components only when necessary
- All API calls through `/api` routes

## Environment Variables
Required in `.env`:
```
NEON_DATABASE_URL=postgresql://...
CONVEX_URL=https://...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

## Module Profiles
For detailed module information:
- WA Monitor: `.claude/modules/wa-monitor.md`
- Workflow: `.claude/modules/workflow.md`
- Ticketing: `.claude/modules/ticketing.md`