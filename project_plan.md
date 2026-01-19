# VF Project Plan

**Last Updated**: 2026-01-19
**Status**: Building new structure

## Current Focus
Migrating from monolithic documentation to modular structure for 80% token reduction.

## Repository Structure
```
VF/ (NEW - Building here)
├── .claude/rules/        # Modular documentation
├── documentation/        # Detailed app docs
└── [migration in progress]

claude/ (ORIGINAL - Untouched)
├── .claude/             # 87 files, needs organization
└── CLAUDE.md           # 608 lines, too large
```

## Applications Overview

### 1. FibreFlow (Next.js)
- **Production**: https://app.fibreflow.app (port 3000)
- **Staging**: https://vf.fibreflow.app (port 3006)
- **Dev**: Port 3005 (Hein)
- **Tech**: Next.js 14, Neon, Convex, Clerk
- **Owner**: Hein (primary), Louis (staging)

### 2. QFieldCloud (Django)
- **Production**: https://qfield.fibreflow.app (port 8082)
- **Tech**: Django, PostgreSQL/PostGIS, Docker
- **Owner**: Louis
- **Status**: ✅ Migrated to VF Server (Jan 2026)

## Migration Progress

### Phase 1: Foundation ✅
- [x] Created VF/ directory structure
- [x] Minimal CLAUDE.md (200 lines)
- [x] Application rules created
- [x] Environment rules created
- [x] Infrastructure documentation

### Phase 2: Content Migration (Next)
- [ ] Copy skills from claude/.claude/skills/
- [ ] Copy modules from claude/.claude/modules/
- [ ] Copy commands from claude/.claude/commands/
- [ ] Migrate agent configurations

### Phase 3: Testing
- [ ] Test with Claude Code
- [ ] Verify token reduction
- [ ] Team review
- [ ] Switch over

## Key Decisions
1. **Separate directory** (VF/) for safe migration
2. **Modular rules** in .claude/rules/ for auto-loading
3. **Application separation** (FibreFlow vs QFieldCloud)
4. **Environment-specific** documentation

## Next Actions
1. Continue copying relevant content from claude/ to VF/
2. Test token usage with new structure
3. Get team feedback
4. Plan switchover strategy

## Success Metrics
- Token reduction: Target 80% (14.8K → 3.8K)
- Response speed: Target 3x faster
- Merge conflicts: Target 80% reduction
- Team adoption: Target 1 week

## Notes
- Original structure preserved in claude/ directory
- Can switch back anytime by changing directories
- All critical security rules in minimal CLAUDE.md
- Detailed docs in modular .claude/rules/ files