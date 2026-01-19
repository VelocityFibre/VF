# VF Server - WA Monitor Endpoints

**Updated**: 2025-12-18
**Module**: WA Monitor / Foto Reviews

## Production Endpoints

### Base URL
```
http://100.96.203.105:3005
```

### API Endpoints

#### 1. List Pending Reviews
```http
GET /api/foto-reviews/pending
```
- **Query Parameters**:
  - `status`: 'pending_review' | 'sent'
  - `limit`: number (default: 20)
  - `offset`: number
  - `search`: string (DR number search)
- **Database**: `foto_ai_reviews` table
- **Updated**: Now uses Neon database instead of antigravity API

#### 2. Get Review Details
```http
GET /api/foto-reviews/{dr_number}
```
- **Example**: `/api/foto-reviews/DR1733758`
- **Returns**: Complete evaluation with step-by-step analysis

#### 3. List All Evaluations
```http
GET /api/foto/evaluations
```
- **Query Parameters**:
  - `feedback_sent`: 'true' | 'false'
  - `limit`: number
  - `offset`: number

#### 4. Get Single Evaluation
```http
GET /api/foto/evaluation/{dr_number}
```

#### 5. Trigger VLM Evaluation
```http
POST /api/foto/evaluate
```
- **Body**: `{"dr_number": "DR1234567"}`
- **Processing Time**: 15-30 seconds
- **VLM Model**: Qwen/Qwen3-VL-8B-Instruct

#### 6. Send WhatsApp Feedback
```http
POST /api/foto/feedback
```
- **Body**:
  ```json
  {
    "dr_number": "DR1234567",
    "phone_number": "+27711558396",
    "feedback": "markdown message"
  }
  ```

#### 7. Approve Review
```http
POST /api/foto-reviews/{dr_number}/approve
```
- **Body**: `{"edited_feedback": "optional edited message"}`

#### 8. Reject Review
```http
POST /api/foto-reviews/{dr_number}/reject
```
- **Body**: `{"rejection_reason": "reason text"}`

## Service Ports

### VLM Service
- **Port**: 8100
- **Health**: `http://100.96.203.105:8100/health`
- **Model**: Qwen/Qwen3-VL-8B-Instruct
- **Context**: 16384 tokens

### WhatsApp Sender
- **Port**: 8081
- **Health**: `http://100.96.203.105:8081/health`
- **QR Code**: `http://localhost:8081/qr` (from server)
- **Phone**: +27 71 155 8396 (must be paired)

### Next.js Application
- **Port**: 3005
- **Process**: next-server
- **Environment**: NODE_ENV=production

## Database

### Table: foto_ai_reviews
```sql
-- Key columns
dr_number VARCHAR PRIMARY KEY
overall_status VARCHAR -- 'PASS' or 'FAIL'
average_score NUMERIC(4,2)
total_steps INTEGER
passed_steps INTEGER
step_results JSONB
markdown_report TEXT
feedback_sent BOOLEAN DEFAULT false
feedback_sent_at TIMESTAMP
evaluation_date TIMESTAMP
```

### Connection
- **Database**: Neon PostgreSQL
- **URL**: Stored in `DATABASE_URL` environment variable
- **Client**: @neondatabase/serverless (tagged template literals required)

## File Locations

### API Routes
```
/home/louis/apps/fibreflow.OLD_20251217/
├── pages/api/foto/
│   ├── evaluate.ts
│   ├── evaluations.ts
│   ├── evaluation/[dr_number].ts
│   └── feedback.ts
└── pages/api/foto-reviews/
    ├── pending.ts (updated to use Neon)
    ├── [jobId].ts (updated to use Neon)
    └── [jobId]/
        └── history.ts
```

### React Components
```
src/modules/foto-reviews/
├── components/FotoReviewsDashboard.tsx
├── hooks/useFotoReviews.ts
└── services/fotoReviewsApiService.ts
```

## Testing

### Quick Test Commands
```bash
# Check pending reviews
curl "http://100.96.203.105:3005/api/foto-reviews/pending?limit=3" | jq '.'

# Get specific review
curl "http://100.96.203.105:3005/api/foto-reviews/DR1733758" | jq '.'

# Trigger evaluation
curl -X POST http://100.96.203.105:3005/api/foto/evaluate \
  -H "Content-Type: application/json" \
  -d '{"dr_number":"DRTEST999"}' | jq '.'

# Check VLM health
curl http://100.96.203.105:8100/health

# Check WhatsApp health
curl http://100.96.203.105:8081/health
```

## Restart Services

### Next.js
```bash
ssh louis@100.96.203.105
pkill -f "next-server"
cd /home/louis/apps/fibreflow.OLD_20251217
PORT=3005 NODE_ENV=production npm run start > /tmp/next.log 2>&1 &
```

### VLM Service
```bash
cd ~/vlm-service
./restart_vlm_server.sh
```

## Current Stats
- **Total Evaluations**: 27+
- **Pending Reviews**: 27
- **Average Score Range**: 1.5 - 9.2 out of 10
- **VLM Processing Time**: 15-30 seconds per DR