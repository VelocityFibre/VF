# OCR Service Setup & Deployment Guide

**Last Updated**: 2026-01-12 21:45 SAST
**Status**: ✅ PRODUCTION READY
**Server**: VF Server (100.96.203.105)
**Port**: 8095 (internal)

## Overview

FastAPI-based OCR service with 4-tier cascade processing for document extraction and classification.

## Access Configuration

### Developer Accounts

| Developer | Username | SSH Access | Group |
|-----------|----------|------------|-------|
| Louis Dup | louis | `ssh louis@100.96.203.105` | ocr-devs |
| Hein Van Vuuren | hein | `ssh hein@100.96.203.105` (pw: OCRDeploy2025!) | ocr-devs |

### Directory Permissions
- **Location**: `/opt/ocr-service/`
- **Owner**: louis
- **Group**: ocr-devs
- **Permissions**: 775 with setgid (drwxrwsr-x)
- **Effect**: Both developers can read/write/deploy

## Service Architecture

### 4-Tier OCR Cascade
1. **Tesseract** (local, free) - Fastest, basic OCR
2. **PaddleOCR** (local, free) - Better for tables and structured documents
3. **OCR.space API** (free tier, 25K/month) - Cloud-based fallback
4. **Gemini Vision** (paid) - Ultimate fallback for complex documents

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ocr/extract-text` | POST | Raw OCR text extraction using 4-tier cascade |
| `/ocr/extract-fields` | POST | Document classification + structured field extraction |
| `/ocr/classify` | POST | Document type classification only |
| `/ocr/health` | GET | Service health check |

### Key Files
- `main.py` - FastAPI application and endpoints
- `ocr_cascade.py` - 4-tier OCR processing logic
- `field_extraction.py` - Document classification & field extraction
- `config.py` - Settings, API keys, thresholds

## Deployment Instructions

### Deploy Code Updates
```bash
# Copy updated files
scp field_extraction.py hein@100.96.203.105:/opt/ocr-service/

# SSH and restart service
ssh hein@100.96.203.105
sudo systemctl restart ocr-service
sudo systemctl status ocr-service
```

### View Logs
```bash
sudo journalctl -u ocr-service -f
```

## Bug Fixes & Updates

### 2026-01-12: Field Extraction Enhancement
- **Issue**: Derived fields (DOB, gender, expiry) not extracted from ID/passport documents
- **Fix**: Moved derived fields outside conditional block, added passport-specific extraction
- **Files**: `field_extraction.py`
- **Developer**: Hein Van Vuuren

## Public API Exposure (Planned)

### Option 1: Cloudflare Tunnel (Recommended)
```yaml
# Add to tunnel configuration
- hostname: ocr.fibreflow.app
  service: http://localhost:8095
```

### Option 2: Nginx Reverse Proxy
```nginx
# In app.fibreflow.app nginx config
location /api/ocr/ {
    proxy_pass http://100.96.203.105:8095/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Rate limiting
    limit_req zone=ocr_limit burst=10 nodelay;
}
```

## Authentication & Security

### API Key Authentication (To Be Implemented)
```python
# Add to main.py or middleware
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    valid_keys = os.getenv("OCR_API_KEYS", "").split(",")
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Apply to routes
@app.post("/ocr/extract-fields", dependencies=[Depends(verify_api_key)])
```

### Rate Limiting Considerations
- Tesseract/PaddleOCR: Unlimited (local processing)
- OCR.space: 25,000 requests/month limit
- Gemini Vision: Paid per request
- **Recommendation**: Implement request quotas per API key

## Systemd Service Configuration

### Service File: `/etc/systemd/system/ocr-service.service`
```ini
[Unit]
Description=OCR Service API
After=network.target

[Service]
Type=simple
User=www-data
Group=ocr-devs
WorkingDirectory=/opt/ocr-service
Environment="PATH=/opt/ocr-service/venv/bin"
ExecStart=/opt/ocr-service/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8095
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Environment Variables

Create `/opt/ocr-service/.env`:
```bash
# OCR.space API
OCR_SPACE_API_KEY=your_key_here

# Gemini Vision API
GEMINI_API_KEY=your_key_here

# Service Configuration
OCR_CASCADE_TIMEOUT=30
MAX_FILE_SIZE_MB=10

# Future: API Keys for authentication
OCR_API_KEYS=key1,key2,key3
```

## Testing the Service

### Local Test
```bash
# Health check
curl http://100.96.203.105:8095/ocr/health

# Extract text from image
curl -X POST http://100.96.203.105:8095/ocr/extract-text \
  -F "file=@/path/to/document.jpg"

# Extract fields from ID document
curl -X POST http://100.96.203.105:8095/ocr/extract-fields \
  -F "file=@/path/to/id_document.jpg" \
  -F "document_type=id_document"
```

### From Next.js App
```javascript
// Current (internal)
const ocrUrl = 'http://100.96.203.105:8095/ocr/extract-fields';

// Future (public via Cloudflare)
const ocrUrl = 'https://ocr.fibreflow.app/extract-fields';
```

## Monitoring & Maintenance

### Check Service Status
```bash
sudo systemctl status ocr-service
```

### View Recent Logs
```bash
sudo journalctl -u ocr-service --since "1 hour ago"
```

### Restart Service
```bash
sudo systemctl restart ocr-service
```

### Check Disk Usage
```bash
du -sh /opt/ocr-service/
df -h /opt
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure user is in `ocr-devs` group
   - May need to log out and back in after group changes

2. **Service Won't Start**
   - Check Python virtual environment: `/opt/ocr-service/venv`
   - Verify all dependencies installed: `pip list`
   - Check for port conflicts: `sudo netstat -tlpn | grep 8095`

3. **OCR Cascade Failures**
   - Check API keys in `.env` file
   - Monitor OCR.space monthly quota
   - Verify Tesseract/PaddleOCR installations

## Future Enhancements

- [ ] API key authentication system
- [ ] Request rate limiting per client
- [ ] Usage metrics and monitoring dashboard
- [ ] Webhook notifications for errors
- [ ] Document preview generation
- [ ] Batch processing endpoint
- [ ] WebSocket support for real-time updates

## Contact

- **OCR Service Lead**: Hein Van Vuuren
- **Infrastructure**: Louis Dup
- **Slack Channel**: #ocr-service (if applicable)