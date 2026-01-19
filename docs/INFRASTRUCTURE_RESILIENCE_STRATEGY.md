# Infrastructure Resilience Strategy

**Date**: 2025-12-23 (Updated: 2026-01-08)
**Context**: Load shedding concerns and server architecture optimization
**Status**: ✅ UPDATED - Battery Backup Acquired, Architecture Revised

## Executive Summary

**UPDATED Decision (Jan 2026)**: VF Server becomes primary production with battery backup, Hostinger VPS as backup.

**Key Change**: Battery backup system acquired for VF Server (100.96.203.105), enabling it to run all production services.

**New Rationale**:
- VF Server now has battery backup (99%+ uptime achievable)
- Consolidate all production to VF Server (already has infrastructure)
- Keep one Hostinger VPS (72.61.197.178) as backup/failover (R20-30/month)
- Saves money while maintaining disaster recovery capability
- VF Server continues hosting dev/staging alongside production

## 🔋 Battery Backup Changes Everything (NEW)

### What Changed
In January 2026, we acquired a UPS (Uninterruptible Power Supply) system for our private server infrastructure. This fundamental change allows us to:

1. **Achieve 99%+ uptime** on private infrastructure
2. **Run QFieldCloud locally** without datacenter dependency
3. **Save R40-60/month** in Hostinger hosting costs
4. **Simplify architecture** from 3 servers to 2
5. **Maintain full control** over production infrastructure

### UPS Specifications
- **Capacity**: 1500-2000VA (sufficient for 1-2 hours during load shedding)
- **Cost**: R5,000-8,000 (one-time investment)
- **ROI**: Pays for itself in 2-3 years through hosting savings
- **Protection**: Also guards against power surges and voltage fluctuations

### Why This Works Now
Previously, the decision was "NEVER move QFieldCloud to VF Server" because:
- Load shedding would cause 4-8 hour outages
- Field workers couldn't sync during power cuts
- Revenue and productivity would stop

With battery backup:
- ✅ 1-2 hours of backup power covers most load shedding slots
- ✅ Graceful shutdown if extended outage (rare)
- ✅ Automatic restart when power returns
- ✅ 99%+ uptime achievable (comparable to budget datacenter)

## Current Infrastructure

### Updated Two-Server Architecture (January 2026)

| Server | Location | Purpose | Uptime SLA | Cost |
|--------|----------|---------|------------|------|
| **VF Server** | On-premises (SA) | PRIMARY: All production + dev/staging | 99%+ (battery backup) | Electricity + UPS (~R300/month) |
| **IP: 100.96.203.105** | With UPS backup | app.fibreflow.app, qfield.fibreflow.app, dev, staging | Protected from load shedding | One-time UPS cost: R5-8k |
| **Hostinger VPS** | Lithuania datacenter | BACKUP: Cold standby & disaster recovery | 99.9% | R20-30/month |
| **IP: 72.61.197.178** | Datacenter | Failover only (not active) | Always available | Insurance policy |

**Previous Architecture (Deprecated)**:
- ~~Hostinger VPS (72.60.17.245)~~ - Being decommissioned (saving R30/month)
- ~~Dual Hostinger production~~ - Consolidated to VF Server with backup

### Production URLs

```
Production Services (99%+ uptime with battery backup):
  ✅ https://app.fibreflow.app → VF Server 100.96.203.105 (main app - port 3000)
  ✅ https://qfield.fibreflow.app → VF Server 100.96.203.105 (GIS sync - port 8080)

Development/Staging (same server, different ports):
  🏢 https://vf.fibreflow.app → VF Server port 3006 (staging - Louis)
  🏢 Port 3005 → VF Server (development - Hein)
  🏢 https://support.fibreflow.app → VF Server (support portal)
  🏢 Internal tools → VF Server (shadcn playground, foto-reviews)

Backup (cold standby):
  💤 Hostinger 72.61.197.178 → Not active (failover only)
```

## Load Shedding Impact Analysis

### Critical Services (Must Be 99.9% Available)

**QFieldCloud (qfield.fibreflow.app)**
- **Why critical**: Field workers synchronize project data
- **Impact if down**: Work stops, revenue stops
- **Current status**: ✅ On Hostinger VPS #2 (safe from load shedding)
- **Action**: NEVER move to VF Server

**Main FibreFlow App (app.fibreflow.app)**
- **Why critical**: Customer-facing business application
- **Impact if down**: Reduced productivity, customer dissatisfaction
- **Current status**: ✅ On Hostinger VPS #1 (safe from load shedding)
- **Action**: Keep on Hostinger

### Non-Critical Services (Can Tolerate Downtime)

**VLM Evaluations** (VF Server)
- **Impact if down**: Foto reviews delayed 2-4 hours
- **Mitigation**: Queue jobs, process when power returns
- **Value of keeping on VF Server**: Free GPU/CPU vs R2,000-R5,000/month cloud

**Internal Tools** (VF Server)
- shadcn playground, support portal, downloads
- **Impact if down**: Team inconvenienced, not customer-facing
- **Acceptable downtime**: 2-8 hours during load shedding

**Image Storage** (VF Server)
- Training datasets (~500GB+)
- **Value**: Free storage vs R500-R1,000/month cloud
- **Impact if down**: No new uploads, existing data safe

## Recommended Architecture

### Server Role Definition

**Hostinger VPS = Production Storefront**
- Customer-facing services
- Mission-critical operations
- 99.9% uptime requirement
- Professional, always open
- Cost: R40-60/month total (both VPS)

**VF Server = Development/Processing Workshop**
- Heavy compute (VLM, image processing)
- Development and testing environment
- Internal tools and automation
- Data storage and backups
- 85-95% uptime acceptable (workshop can close during power outages)
- Cost: R0/month (you own hardware) + electricity (~R200/month)

### Design Principle

**"Customer-critical on datacenter, compute-heavy on-premises"**

```
┌─────────────────────────────────────────────┐
│         HOSTINGER (Production)              │
│  - app.fibreflow.app (main app)            │
│  - qfield.fibreflow.app (GIS sync)         │
│  Cost: R40-60/month                         │
│  Uptime: 99.9%                              │
│  Purpose: Customer-facing services          │
└─────────────────────────────────────────────┘
                    ↑
                    │ API calls, webhooks
                    ↓
┌─────────────────────────────────────────────┐
│         VF SERVER (Development/Processing)  │
│  - VLM evaluations (heavy compute)         │
│  - Training image storage (500GB+)         │
│  - Development/testing environment         │
│  - Internal tools (docs, playground)       │
│  - Automation scripts (cron, background)   │
│  Cost: R0/month (you own it)               │
│  Uptime: 85-95% (acceptable)               │
│  Purpose: Backend processing, dev work     │
└─────────────────────────────────────────────┘
```

## VF Server Value Proposition

### Cost Savings vs Cloud Alternatives

| Service | Cloud Cost (Monthly) | VF Server Cost |
|---------|---------------------|----------------|
| VLM GPU instance (foto reviews) | R2,000-R5,000 | R0 (local GPU/CPU) |
| 500GB storage (training images) | R500-R1,000 | R0 (NVMe drives) |
| Dev/staging VPS | R200-R500 | R0 (same server) |
| Cloud backup storage | R200-R500 | R0 (local storage) |
| **Total** | **R2,900-R7,000** | **R200** (electricity) |

**Net savings**: R2,700-R6,800/month even with load shedding downtime

### Use Cases Where VF Server Excels

1. **Development & Testing Environment**
   - Test with production-like data without risking production
   - Break things safely
   - Full root access (install packages, restart services)
   - Experiment freely

2. **Heavy Compute/Data Processing**
   - VLM (Vision Language Model) evaluations
   - Image processing pipelines
   - AI-powered quality checks
   - Background job processing

3. **Integration Hub for Internal Systems**
   - Same network as internal tools
   - Direct database access (no internet latency)
   - Can access internal APIs that aren't public
   - Close to data sources (faster queries)

4. **Cost-Effective Storage & Backups**
   - Large datasets (training images, models)
   - File downloads (APKs, documents)
   - Archive old data without cloud storage fees

5. **Learning & Experimentation**
   - Learn DevOps (Docker, Nginx, systemd)
   - Test Claude Code skills on real infrastructure
   - Try new frameworks without production risk
   - Build agent harness experiments

6. **Documentation & Internal Tools**
   - shadcn/ui Interactive Playground
   - Support Portal (internal team)
   - Downloads Page (APKs for installers)
   - 90% uptime is acceptable for internal tools

## Rejected Alternatives

### Option A: Move app.fibreflow.app to VF Server ❌

**Why rejected**:
- Load shedding → app.fibreflow.app down → customers affected
- Internet outage → tunnel fails → total downtime
- R20/month savings not worth business disruption risk
- Development complexity doesn't justify marginal cost savings

### Option B: Active-Passive Failover ❌

**Architecture**:
```
🎯 app.fibreflow.app → VF Server (primary)
💤 app-backup.fibreflow.app → Hostinger (standby, auto-switch on failure)
```

**Why rejected**:
- Development time: 20-40 hours (@R1,000/hr = R20,000-R40,000)
- Ongoing maintenance: 2-4 hours/month
- Complexity: Code sync, health monitoring, DNS automation
- Testing burden: Monthly failover tests required
- Still need Hostinger ($20/month) - no cost savings
- **Verdict**: R20,000-R40,000 development cost >> R20/month hosting cost

### Option C: Load-Balanced Dual-Primary ❌

**Architecture**:
```
🌐 app.fibreflow.app → Cloudflare Load Balancer
                        ├─ VF Server (50% traffic)
                        └─ Hostinger (50% traffic)
```

**Why rejected**:
- Highest complexity (session sync, database routing)
- Additional cost: Cloudflare Load Balancer ($5-20/month)
- Overkill for internal business app (not high-traffic SaaS)
- Development time: 40+ hours
- No meaningful benefit over simpler alternatives

### Option D: Ditch VF Server Entirely ❌

**Why rejected**:
- Cloud GPU: R2,000-R5,000/month vs free
- Cloud storage: R500-R1,000/month vs free
- Dev VPS: R200-R500/month vs free
- Total cloud cost: R2,900-R7,000/month
- **Loss**: R2,700-R6,800/month in savings
- Less control, vendor lock-in, higher latency for internal operations

## Recommended Enhancements (Optional)

### If VF Server Downtime Becomes Problematic

**Measure first** (1 month monitoring):
```bash
# Track downtime
*/5 * * * * ~/monitor-vf-server.sh
# After 1 month, review ~/vf-downtime.log
```

**If downtime >5%**, invest in resilience:

1. **UPS (Uninterruptible Power Supply)** - R5,000-R8,000 (one-time)
   - 1-2 hours backup power
   - Protects against voltage spikes
   - Graceful shutdown capability
   - Recommended: APC Smart-UPS 1500VA

2. **LTE Backup Internet** - R500-R1,000/month
   - 4G/5G backup internet
   - Auto-failover if fiber down
   - Recommended: Telkom LTE router + Rain/Vodacom data SIM

3. **Generator** (if critical) - R15,000-R50,000 (one-time)
   - 8-24 hours runtime
   - Auto-start on power loss
   - Overkill for internal tools (not recommended)

**Investment threshold**: Only if downtime costs >R10,000/hour in lost productivity

**If downtime <2%**: Do nothing - current setup is optimal

## Implementation Guidelines

### Services to KEEP on VF Server

- ✅ VLM evaluations (heavy GPU/CPU)
- ✅ Training image storage (500GB+ datasets)
- ✅ shadcn playground (developer tool)
- ✅ WhatsApp automation (same network)
- ✅ Cron jobs/background processing
- ✅ Development/testing environments
- ✅ Internal documentation sites

### Services to KEEP on Hostinger

- ✅ QFieldCloud sync (qfield.fibreflow.app) - MISSION-CRITICAL
- ✅ Main FibreFlow app (app.fibreflow.app) - CUSTOMER-FACING
- ✅ Any customer-facing API endpoints
- ✅ Real-time notifications/alerts
- ✅ Authentication services

### Architectural Patterns

**Use graceful degradation** (see GRACEFUL_DEGRADATION_GUIDE.md):
- VF Server down → Queue jobs for later
- VF Server down → Use fallback cloud services
- VF Server down → Show cached results
- Never hard-fail when VF Server unavailable

**Communication flow example** (Foto Reviews):
1. Customer uploads photo → Hostinger QFieldCloud ✅
2. Hostinger triggers webhook → VF Server VLM (or queue if down) ⚠️
3. VF Server processes image → Returns result (when available) ⚠️
4. Hostinger stores result → Neon database ✅
5. Customer views dashboard → Hostinger FibreFlow ✅

**During load shedding**:
- Steps 1, 4, 5 continue (Hostinger + Neon)
- Steps 2-3 delayed (VF Server)
- Result: Graceful degradation, not total failure

## Monitoring & Validation

### VF Server Health Monitoring

```bash
# Simple uptime check (runs every 5 min)
cat > ~/monitor-vf-server.sh << 'EOF'
#!/bin/bash
if ! curl -s -f https://vf.fibreflow.app > /dev/null; then
  echo "$(date): VF Server DOWN" >> ~/vf-downtime.log
  # Optional: Send WhatsApp alert
fi
EOF

chmod +x ~/monitor-vf-server.sh
crontab -e
# Add: */5 * * * * ~/monitor-vf-server.sh
```

### Monthly Review Metrics

Track and review monthly:
- **VF Server uptime**: Target >85%, acceptable >80%
- **Downtime incidents**: Count and duration
- **Cost savings**: Calculate cloud equivalent costs avoided
- **Service degradation**: Customer complaints during VF Server outages

### Decision Points

**After 1 month of monitoring**:

| Metric | Action |
|--------|--------|
| Uptime >95% | ✅ Do nothing - current setup optimal |
| Uptime 85-95% | ⚠️ Monitor for 2 more months |
| Uptime 80-85% | ⚠️ Consider UPS investment |
| Uptime <80% | ❌ Invest in UPS + LTE backup |

**After 3 months of monitoring**:

| Customer Impact | Action |
|-----------------|--------|
| Zero complaints | ✅ Architecture validated |
| <5 complaints | ⚠️ Improve graceful degradation |
| >5 complaints | ❌ Re-evaluate critical service placement |

## Communication Strategy

### Afrikaans Response to Hein

```
Hein - jou bekommernis is 100% geldig. Ek het die infrastruktuur ondersoek:

GOEIE NUUS:
✅ QFieldCloud (qfield.fibreflow.app) is REEDS veilig op Hostinger
✅ Dit is ons kritiese diens - veldwerkers kan altyd sync
✅ Load shedding raak dit NIE

HUIDIGE SITUASIE:
- app.fibreflow.app (hoof app) - Hostinger (veilig)
- qfield.fibreflow.app (GIS sync) - Hostinger (veilig)
- vf.fibreflow.app (downloads/support) - VF Server (kan offline wees)

AANBEVELING:
Moenie app.fibreflow.app na VF Server skuif nie.

HOEKOM NIE:
1. R40-60/maand Hostinger is goedkoop vir peace of mind
2. Failover complexity (20-40 ure werk) is duurder as besparings
3. QFieldCloud is reeds beskerm - dis ons #1 prioriteit
4. VF Server perfek vir nie-kritiese tools (downloads, demos)
5. VF Server spaar ons R2,700-R6,800/maand in cloud koste

ALTERNATIEF (as VF Server baie downtime het):
- UPS (R5k-R8k) + LTE backup (R500/m) goedkoper as failover system
- Meet eers downtime vir 1 maand, dan besluit

BOTTOM LINE:
Hou huidige setup. Hostinger vir produksie, VF Server vir internal tools.
Slegs verander as ons bewys het dat downtime probleme veroorsaak.
VF Server spaar ons duisende rande per maand - dis baie waardevol.
```

## Success Criteria

This strategy is successful if:

1. ✅ **Zero customer-facing downtime** due to load shedding
2. ✅ **QFieldCloud 99.9%+ uptime** (field workers never blocked)
3. ✅ **R2,500+ monthly savings** vs cloud alternatives
4. ✅ **VF Server downtime <5% impact** on internal team productivity
5. ✅ **Graceful degradation working** (jobs queue, don't fail)
6. ✅ **Team confidence high** in architecture resilience

## Related Documentation

- `GRACEFUL_DEGRADATION_GUIDE.md` - Implementation patterns for VF Server downtime resilience
- `docs/OPERATIONS_LOG.md` - Track infrastructure changes and incidents
- `CLAUDE.md` - Updated with server role definitions

## Approval & Sign-off

**Recommended by**: Claude Code (AI Analysis)
**Date**: 2025-12-23
**Status**: Awaiting approval from Hein & Louis
**Next Steps**:
1. Review and approve strategy
2. Implement graceful degradation patterns
3. Set up VF Server monitoring (1 month baseline)
4. Validate with real-world data
