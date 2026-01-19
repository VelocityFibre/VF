# WA Monitor Send Feedback Fix Documentation

## Date: 2026-01-16

## Issue Summary
The Send Feedback button in wa-monitor fails with "Failed to communicate with WhatsApp API: fetch failed" despite the infrastructure being fully operational.

## Infrastructure Status (CONFIRMED WORKING)

### ✅ Working Components:
1. **WhatsApp Bridge** (Port 8083)
   - Successfully compiled from Go source
   - Running as systemd service: `whatsapp-bridge.service`
   - Sends messages successfully via direct API calls
   - Connected and receiving WhatsApp events

2. **WhatsApp Sender** (Port 8081)
   - Phone: +27 82 418 9511 (corrected from old number)
   - Status: Healthy and connected
   - Handles messages with @mentions

3. **Database Configuration**
   - Neon PostgreSQL configured correctly
   - wa_monitor_drops table accessible

4. **Direct Testing**
   - Node.js axios calls: Working perfectly
   - curl commands to ports: Successful
   - WhatsApp messages: Delivered to groups

## Root Cause Analysis

### The Problem:
Despite updating the code to use axios instead of fetch, the API endpoints still return "fetch failed" error. This occurs in both:
- Production: https://app.fibreflow.app/wa-monitor
- Staging: https://vf.fibreflow.app/wa-monitor

### Why It's Happening:
1. **Next.js bundling/runtime issue** - The error persists even with axios in the code
2. **Module resolution problems** - Next.js may be overriding the HTTP client
3. **Internal polyfills** - Next.js might be intercepting HTTP calls

## Proposed Solutions (In Order of Preference)

### Solution 1: Use Node.js Built-in HTTP Module (SIMPLEST & BEST)
**Why:** No external dependencies, guaranteed to work in Node.js environment
**Implementation:** Replace axios/fetch with native http/https module
**Pros:**
- No dependency issues
- Direct control over HTTP requests
- Works reliably in all Node.js environments
**Cons:**
- Slightly more verbose code

### Solution 2: Create Separate Microservice
**Why:** Completely bypass Next.js API route issues
**Implementation:** Simple Express server on different port
**Pros:**
- Complete isolation from Next.js
- Can be scaled independently
- Easier debugging
**Cons:**
- Additional service to maintain
- Another port to manage

### Solution 3: Direct Frontend Integration
**Why:** Bypass backend entirely
**Implementation:** Call WhatsApp services directly from React
**Pros:**
- Eliminates backend complexity
- Immediate user feedback
**Cons:**
- Security concerns (exposing endpoints)
- CORS configuration needed

## Current Port Configuration

```
VF Server (100.96.203.105):
- 3005 → Development (Hein)
- 3006 → Staging (Louis)
- 3007 → Production (velo)
- 3008 → Alternative Production
- 8081 → WhatsApp Sender
- 8083 → WhatsApp Bridge API
```

## Deployment Locations

- **Production:** `/home/velo/fibreflow/`
- **Staging:** `/home/louis/apps/fibreflow-production/`
- **API File:** `pages/api/wa-monitor-send-feedback.ts`

## Test Commands

### Direct WhatsApp Bridge Test:
```bash
curl -X POST http://localhost:8083/api/send \
  -H "Content-Type: application/json" \
  -d '{"recipient":"120363421664266245@g.us","message":"Test message"}'
```

### Direct Node.js Test:
```javascript
const axios = require('axios');
axios.post('http://localhost:8083/api/send', {
  recipient: '120363421664266245@g.us',
  message: 'Test from Node.js'
}).then(r => console.log(r.data));
```

## Implementation Results

### Solution 1 Attempt: Native HTTP Module
**Status**: ❌ Failed due to Next.js routing issues
**What happened**:
- Created implementation using Node.js native `http` module
- Code builds successfully
- API endpoints return 404 errors despite being built
- Appears to be a Next.js caching or routing issue

### Key Findings:
1. **Infrastructure**: 100% working - WhatsApp services fully operational
2. **Direct calls**: Work perfectly via curl or Node.js scripts
3. **Next.js API routes**: Persistent "fetch failed" error regardless of HTTP client used
4. **Root cause**: Deep Next.js internal issue, not HTTP client specific

## Recommended Next Steps

### Option 1: Express Microservice (RECOMMENDED)
Create a simple Express server on port 8090:
```javascript
const express = require('express');
const axios = require('axios');
const app = express();

app.post('/send-feedback', async (req, res) => {
  // Direct communication with WhatsApp services
  // Bypasses all Next.js issues
});

app.listen(8090);
```

### Option 2: Direct Integration
Update the frontend to call WhatsApp services directly:
- Configure CORS on WhatsApp services
- Call from React components
- Eliminates backend complexity

### Option 3: Serverless Function
Deploy as Vercel/Netlify function or AWS Lambda:
- Outside Next.js app context
- Clean environment
- No caching issues

## Current Workaround
Use direct curl commands or scripts to send WhatsApp messages:
```bash
curl -X POST http://localhost:8083/api/send \
  -H "Content-Type: application/json" \
  -d '{"recipient":"120363421664266245@g.us","message":"Your message"}'
```

## Lessons Learned
1. Next.js API routes have complex internal behaviors that can interfere with HTTP clients
2. The error "fetch failed" persists even when not using fetch
3. Direct Node.js scripts work perfectly, confirming infrastructure is solid
4. Solution needs to bypass Next.js API layer entirely