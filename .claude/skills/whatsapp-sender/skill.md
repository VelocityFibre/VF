---
name: whatsapp-sender
version: 2.0.0
description: WhatsApp Sender Service - Automated messaging with session management
author: Claude
tags: [whatsapp, messaging, sender, notifications, feedback]
requires: [vf-server, network-access]
async: true
context_fork: true
hooks:
  pre_tool_use: "echo '[WA-Sender] Operation started at $(date)' >> /tmp/wa_sender.log"
  post_tool_use: "echo '[WA-Sender] Operation completed at $(date)' >> /tmp/wa_sender.log"
---

# WhatsApp Sender Skill

Comprehensive management of WhatsApp sender service for automated messaging, feedback delivery, and contractor notifications.

## Overview

The WhatsApp Sender service is a Go-based application using the whatsmeow library to send automated WhatsApp messages. It's critical for contractor feedback, notifications, and the WA Monitor system.

## Architecture

### Service Stack
```
WhatsApp Web API
       ↓
whatsmeow (Go library)
       ↓
whatsapp-sender (Go binary)
       ↓
HTTP API (port 8081)
       ↓
FibreFlow Apps
```

### Key Components

#### 1. WhatsApp Session
- **Technology**: whatsmeow (Go WhatsApp Web client)
- **Storage**: SQLite database (`~/whatsapp-sender/store/whatsapp.db`)
- **Security**: End-to-end encrypted, device linked
- **Phone**: User-provided number (to be configured)

#### 2. Service Configuration
- **Port**: 8081
- **Location**: VF Server (`~/whatsapp-sender/`)
- **Binary**: `whatsapp-sender` (Go compiled)
- **Logs**: `~/whatsapp-sender/whatsapp-sender.log`

#### 3. Integration Points
- WA Monitor (Foto Reviews) - sends evaluation feedback
- FibreFlow Apps - contractor notifications
- Alert System - critical notifications

## Session Management

### Critical Rules
1. **NEVER** run same session from multiple IPs
2. **NEVER** copy session while source is running
3. **ALWAYS** stop old service before migration
4. **ALWAYS** wait 30s between stop and start
5. **Session files are sacred** - deletion = re-pairing

### Pairing New Phone

#### Prerequisites
- WhatsApp installed on phone
- Phone number with WhatsApp account
- Access to VF Server
- No active rate limits (wait 1-24h if limited)

#### Step-by-Step Process

```bash
# 1. SSH to VF Server as louis
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105

# 2. Navigate to service directory
cd ~/whatsapp-sender

# 3. Backup existing session (if any)
if [ -f store/whatsapp.db ]; then
    cp -r store store.backup.$(date +%Y%m%d_%H%M%S)
fi

# 4. Clear old session
rm -rf store/*

# 5. Start service for pairing
./whatsapp-sender

# 6. Look for pairing code output
# Example: "Pairing code: XXXX-XXXX"

# 7. On phone: WhatsApp > Settings > Linked Devices
# 8. Scan code or enter manually
# 9. Wait for "Successfully logged in" message

# 10. Test with Ctrl+C and restart
./whatsapp-sender > whatsapp-sender.log 2>&1 &
echo $! > whatsapp-sender.pid
```

### Session Verification

```bash
# Check if session exists
ls -la ~/whatsapp-sender/store/whatsapp.db

# Verify service is running
ps aux | grep whatsapp-sender | grep -v grep

# Check logs for errors
tail -f ~/whatsapp-sender/whatsapp-sender.log

# Test health endpoint
curl http://localhost:8081/health
```

## API Endpoints

### Health Check
```bash
GET http://100.96.203.105:8081/health

Response:
{
  "status": "healthy",
  "connected": true,
  "phone": "+27XXXXXXXXX"
}
```

### Send Message
```bash
POST http://100.96.203.105:8081/send
Content-Type: application/json

{
  "phone": "+27711558396",
  "message": "Your DR evaluation is ready"
}

Response:
{
  "success": true,
  "message_id": "3EB0..."
}
```

### Session Status
```bash
GET http://100.96.203.105:8081/status

Response:
{
  "logged_in": true,
  "phone_number": "+27XXXXXXXXX",
  "battery": 85,
  "platform": "iPhone"
}
```

## Troubleshooting

### Common Issues

#### 1. Rate Limit (429 Error)
**Symptom**: `status 429: rate-overlimit`
**Cause**: Too many pairing attempts or API calls
**Solution**:
```bash
# Wait 1-24 hours
# Check time of last attempt
grep "rate-overlimit" ~/whatsapp-sender/whatsapp-sender.log | tail -1

# Clear session and retry after wait period
rm -rf ~/whatsapp-sender/store/*
```

#### 2. Session Destroyed
**Symptom**: Service won't connect, phone shows no linked device
**Cause**: Multi-IP usage, forced logout, or WhatsApp security
**Solution**:
```bash
# Complete re-pairing required
cd ~/whatsapp-sender
rm -rf store/*
./whatsapp-sender  # Get new pairing code
```

#### 3. Service Not Running
**Symptom**: Connection refused on port 8081
**Solution**:
```bash
# Start service
cd ~/whatsapp-sender
nohup ./whatsapp-sender > whatsapp-sender.log 2>&1 &
echo $! > whatsapp-sender.pid

# Verify it's running
sleep 2
curl http://localhost:8081/health
```

#### 4. Message Send Failures
**Symptom**: Messages not delivering
**Checks**:
```bash
# 1. Verify phone format (+27 prefix)
# 2. Check recipient has WhatsApp
# 3. Review logs for specific errors
tail -50 ~/whatsapp-sender/whatsapp-sender.log | grep ERROR

# 4. Test with known good number
curl -X POST http://localhost:8081/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "+27711558396", "message": "Test message"}'
```

## Quick Commands

### Service Management
```bash
# Start service
cd ~/whatsapp-sender && ./whatsapp-sender > whatsapp-sender.log 2>&1 & echo $! > whatsapp-sender.pid

# Stop service
kill $(cat ~/whatsapp-sender/whatsapp-sender.pid)

# Restart service
kill $(cat ~/whatsapp-sender/whatsapp-sender.pid) && sleep 2 && cd ~/whatsapp-sender && ./whatsapp-sender > whatsapp-sender.log 2>&1 & echo $! > whatsapp-sender.pid

# View logs
tail -f ~/whatsapp-sender/whatsapp-sender.log

# Check status
ps aux | grep whatsapp-sender && curl http://localhost:8081/health
```

### Session Management
```bash
# Backup session
cp -r ~/whatsapp-sender/store ~/whatsapp-sender/store.backup.$(date +%Y%m%d)

# Clear session (for re-pairing)
rm -rf ~/whatsapp-sender/store/*

# Check session age
stat ~/whatsapp-sender/store/whatsapp.db | grep Modify
```

### Testing
```bash
# Quick health check
curl http://100.96.203.105:8081/health | jq

# Send test message
curl -X POST http://100.96.203.105:8081/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "+27711558396", "message": "WhatsApp Sender Test: '$(date)'"}'

# Check recent activity
grep "message sent" ~/whatsapp-sender/whatsapp-sender.log | tail -10
```

## Integration Examples

### From WA Monitor
```javascript
// Send feedback after approval
async function sendWhatsAppFeedback(dr_number, phone_number, message) {
  const response = await fetch('http://100.96.203.105:8081/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone: phone_number,
      message: message
    })
  });
  return response.json();
}
```

### From Python Script
```python
import requests

def send_whatsapp(phone, message):
    url = "http://100.96.203.105:8081/send"
    payload = {
        "phone": phone,
        "message": message
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
send_whatsapp("+27711558396", "Your installation has been approved")
```

### From Bash
```bash
#!/bin/bash
send_whatsapp() {
  local phone=$1
  local message=$2

  curl -s -X POST http://100.96.203.105:8081/send \
    -H "Content-Type: application/json" \
    -d "{\"phone\": \"$phone\", \"message\": \"$message\"}" | jq
}

# Usage
send_whatsapp "+27711558396" "Test notification from bash"
```

## Security Considerations

### Session Security
- Session database contains encryption keys
- Never expose `whatsapp.db` publicly
- Use file permissions: `chmod 600 store/whatsapp.db`
- Regular backups before changes

### Network Security
- Service binds to all interfaces (0.0.0.0:8081)
- Consider firewall rules for production
- Use reverse proxy for external access
- Implement rate limiting for API

### Phone Number Privacy
- Store phone numbers encrypted in database
- Log minimal PII information
- Comply with WhatsApp Business policies
- Get user consent for messaging

## Monitoring

### Health Metrics
```bash
# Create monitoring script
cat > ~/monitor-whatsapp.sh << 'EOF'
#!/bin/bash

# Check service is running
if ! pgrep -f whatsapp-sender > /dev/null; then
  echo "ERROR: WhatsApp sender not running"
  exit 1
fi

# Check API health
if ! curl -s http://localhost:8081/health | grep -q "healthy"; then
  echo "ERROR: WhatsApp sender unhealthy"
  exit 1
fi

# Check session exists
if [ ! -f ~/whatsapp-sender/store/whatsapp.db ]; then
  echo "ERROR: WhatsApp session missing"
  exit 1
fi

echo "OK: WhatsApp sender operational"
EOF

chmod +x ~/monitor-whatsapp.sh

# Add to crontab for regular checks
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/monitor-whatsapp.sh >> /tmp/wa-monitor.log 2>&1") | crontab -
```

### Log Analysis
```bash
# Message statistics
grep "message sent" ~/whatsapp-sender/whatsapp-sender.log | wc -l

# Error frequency
grep ERROR ~/whatsapp-sender/whatsapp-sender.log | tail -20

# Daily message count
grep "message sent" ~/whatsapp-sender/whatsapp-sender.log | grep "$(date +%Y-%m-%d)" | wc -l
```

## Best Practices

### Do's
✅ Always backup session before changes
✅ Test with known numbers first
✅ Monitor logs for rate limits
✅ Use proper phone format (+27...)
✅ Implement retry logic for failures
✅ Keep service running continuously

### Don'ts
❌ Never run session on multiple servers
❌ Don't delete session without backup
❌ Don't spam messages (rate limits)
❌ Don't share session database
❌ Don't restart during active sending
❌ Don't ignore error messages

## Maintenance

### Daily
- Check service health
- Review error logs
- Monitor message delivery

### Weekly
- Backup session database
- Check disk space for logs
- Review message statistics

### Monthly
- Rotate log files
- Update dependencies
- Test disaster recovery

## Related Skills
- `wa-monitor` - Uses sender for feedback delivery
- `vf-server` - Host server management
- `system-health` - Overall system monitoring

## References
- [whatsmeow Documentation](https://github.com/tulir/whatsmeow)
- WhatsApp Business Policy
- Go WhatsApp Web API Guide
- Internal: `WHATSAPP_MIGRATION_FAILURE_2026-01-14.md`