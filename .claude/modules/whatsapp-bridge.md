# WhatsApp Bridge Module

**Status**: ✅ Production Ready
**Last Updated**: 2026-01-15
**Location**: VF Server (`~/whatsapp-bridge-go/`)
**Port**: 8085 (REST API)
**Phone**: +27727665862
**Session**: Active (migrated from Hostinger)

## Overview

WhatsApp Bridge monitors WhatsApp groups for DR numbers and automatically creates entries in the `wa_monitor_drops` table. It's part of the complete WA Monitor flow: receive DRs from WhatsApp groups → process → show on monitor page → send feedback.

## Architecture

```
WhatsApp Groups → Bridge (Port 8085) → Neon DB (wa_monitor_drops)
                     ↓
                 SQLite (local backup)
```

## Key Events (2026-01-15)

### Session Migration Success
- **Problem**: Needed to move WhatsApp Bridge from Hostinger to VF Server
- **Challenge**: WhatsApp detects multi-IP usage and kills sessions permanently
- **Solution**: Copied existing session files from Hostinger (`/opt/velo-test-monitor/services/whatsapp-bridge/store/`)
- **Result**: Bridge connected without needing new QR code pairing

### Database Table Creation
- **Issue**: Bridge was trying to write to non-existent `wa_monitor_drops` table
- **Action**: Created table with proper schema matching bridge expectations
- **Test Entry**: DR9999009 from Velo Test group successfully stored

## Database Schema

```sql
CREATE TABLE wa_monitor_drops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drop_number VARCHAR(50) NOT NULL UNIQUE,
    project VARCHAR(255),
    status VARCHAR(20) DEFAULT 'incomplete',
    user_name VARCHAR(255),
    comment TEXT,
    sender_phone VARCHAR(50),
    completed_photos INTEGER DEFAULT 0,
    outstanding_photos INTEGER DEFAULT 12,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Monitored WhatsApp Groups

| Group Name | Project | Status | DRs Detected |
|------------|---------|--------|--------------|
| Velo Test | Velo Test | Active | DR9999009 (test) |
| Mohadin Activations 🥳 | Mohadin | Active | DR1858146, DR1858075, DR1858000 |
| Lawley Groups | Lawley | Monitoring | - |
| Mamelodi Groups | Mamelodi | Monitoring | - |

## Service Management

### Check Status
```bash
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'ps aux | grep whatsapp-bridge | grep -v grep'
```

### View Logs
```bash
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'tail -50 ~/whatsapp-bridge-go/bridge.log'
```

### Restart Service
```bash
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'pkill -f whatsapp-bridge; cd ~/whatsapp-bridge-go && PORT=8085 NEON_DATABASE_URL="postgresql://neondb_owner:npg_MIUZXrg1tEY0@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require" nohup ./whatsapp-bridge > bridge.log 2>&1 & echo "Bridge restarted on port 8085"'
```

### Check Database Entries
```bash
export PGPASSWORD='npg_MIUZXrg1tEY0'
psql -h ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech -U neondb_owner -d neondb \
  -c "SELECT drop_number, project, created_at FROM wa_monitor_drops ORDER BY created_at DESC LIMIT 10;"
```

## Files & Locations

- **Binary**: `~/whatsapp-bridge-go/whatsapp-bridge` (35MB Go executable)
- **Session DB**: `~/whatsapp-bridge-go/store/whatsapp.db` (3.5MB)
- **Messages DB**: `~/whatsapp-bridge-go/store/messages.db` (6.3MB)
- **Logs**: `~/whatsapp-bridge-go/bridge.log`
- **PID File**: `~/whatsapp-bridge-go/bridge.pid`

## API Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Check bridge status | `{"status": "connected", "phone": "+27727665862"}` |
| `/groups` | GET | List monitored groups | `{"groups": [...]}` |
| `/messages/{group_id}` | GET | Get recent messages | `{"messages": [...]}` |

## DR Detection Pattern

The bridge detects various DR formats:
- `DR1234567` (standard)
- `DR 1234567` (with space)
- `drop 1234567` (alternative)
- Case insensitive matching

## Troubleshooting

### Bridge Not Receiving Messages
1. Check if session is active: Look for "✅ Connected to WhatsApp" in logs
2. Verify phone is connected: Phone should show "WhatsApp Web" active
3. Check group membership: Ensure +27727665862 is in target groups

### Database Connection Issues
- Error: `pq: password authentication failed`
- Solution: Verify NEON_DATABASE_URL environment variable is correct

### Port Conflicts
- Error: `address already in use`
- Solution: Use different port (8085, 8086, etc.) or stop conflicting service

## Session Files Backup

Critical session files are backed up in multiple locations:
- **Primary**: `~/whatsapp-bridge-go/store/` (VF Server)
- **Backup**: `/tmp/bridge-store-latest/` (local)
- **Source**: `/opt/velo-test-monitor/services/whatsapp-bridge/store/` (Hostinger)

⚠️ **CRITICAL**: Never run the same session from multiple IPs simultaneously!

## Integration with WA Monitor

The bridge works with:
- **WA Monitor Page**: https://app.fibreflow.app/wa-monitor
- **WhatsApp Sender**: Port 8081 (sends feedback messages)
- **VLM Service**: Port 8100 (processes drop photos)

## Performance Metrics

- **Message Processing**: ~100ms per DR detection
- **Database Write**: ~50ms per entry
- **Memory Usage**: ~38MB resident
- **CPU Usage**: <1% idle, ~3% when processing

## Recent Issues & Fixes

### 2026-01-15: Database Table Missing
- **Issue**: `wa_monitor_drops` table didn't exist after Neon database changes
- **Fix**: Created table with proper schema and indexes
- **Test**: DR9999009 successfully stored

### 2026-01-15: Session Migration
- **Issue**: Needed to move bridge from Hostinger to VF Server
- **Fix**: Copied session files, started bridge with existing session
- **Result**: No QR code scan needed, seamless migration

## Related Services

- **WhatsApp Sender** (Port 8081): `.claude/skills/whatsapp-sender/skill.md`
- **WA Monitor** (Port 3005): `.claude/modules/wa-monitor.md`
- **VLM Service** (Port 8100): Photo analysis for drops

## Contact

For issues, check:
1. Bridge logs: `~/whatsapp-bridge-go/bridge.log`
2. Database entries: `wa_monitor_drops` table
3. WhatsApp connection: Phone shows "WhatsApp Web" active