# Graceful Degradation Guide

**Purpose**: Make FibreFlow applications resilient to VF Server downtime (load shedding, network issues)
**Date**: 2025-12-23
**Target**: 85-95% VF Server uptime with zero customer-facing impact

## Core Philosophy

**"Fail gracefully, never hard-fail"**

When VF Server is unavailable:
- ✅ Queue jobs for later processing
- ✅ Use cached results
- ✅ Fallback to cloud services
- ✅ Show informative messages
- ❌ Never throw errors to users
- ❌ Never block critical workflows

## Pattern Library

### Pattern 1: Timeout + Fallback

**Use case**: Non-critical API calls that can fail gracefully

```typescript
// Example: VLM foto evaluation
async function evaluatePhoto(photoUrl: string, stepName: string) {
  try {
    // Try VF Server VLM first (better quality, free)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const result = await fetch('http://100.96.203.105:8100/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: photoUrl, step: stepName }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (result.ok) {
      return await result.json();
    }

    throw new Error('VLM server returned error');

  } catch (error) {
    console.log('VF Server VLM unavailable, queuing for later processing');

    // Fallback: Queue for later evaluation
    await queuePhotoEvaluation({
      photo_url: photoUrl,
      step_name: stepName,
      queued_at: new Date().toISOString(),
      retry_count: 0
    });

    return {
      status: 'queued',
      message: 'Evaluation queued - results available in 2-4 hours',
      passed: null, // Unknown until processed
      queued: true
    };
  }
}
```

**Key principles**:
- Short timeout (5 seconds) - don't wait forever
- Graceful fallback (queue job)
- User-friendly message
- Return partial result (status: queued)

---

### Pattern 2: Queue-Based Processing

**Use case**: Background jobs that don't need immediate results

```typescript
// Database: foto_evaluations_queue table
interface QueuedEvaluation {
  id: number;
  dr_number: string;
  photo_url: string;
  step_name: string;
  queued_at: string;
  retry_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: any;
}

// Queue job for later
async function queuePhotoEvaluation(data: {
  photo_url: string;
  step_name: string;
  queued_at: string;
  retry_count: number;
}) {
  await neonClient.query(`
    INSERT INTO foto_evaluations_queue
    (photo_url, step_name, queued_at, retry_count, status)
    VALUES ($1, $2, $3, $4, 'pending')
  `, [data.photo_url, data.step_name, data.queued_at, data.retry_count]);
}

// Cron job on VF Server: Process queue when power is back
// Runs every 5 minutes
async function processEvaluationQueue() {
  const pendingJobs = await neonClient.query(`
    SELECT * FROM foto_evaluations_queue
    WHERE status = 'pending' AND retry_count < 3
    ORDER BY queued_at ASC
    LIMIT 10
  `);

  for (const job of pendingJobs.rows) {
    try {
      // Mark as processing
      await neonClient.query(`
        UPDATE foto_evaluations_queue
        SET status = 'processing'
        WHERE id = $1
      `, [job.id]);

      // Evaluate with local VLM
      const result = await evaluatePhotoLocal(job.photo_url, job.step_name);

      // Save result to main table
      await neonClient.query(`
        UPDATE foto_ai_reviews
        SET step_result = $1, evaluated_at = NOW()
        WHERE photo_url = $2 AND step_name = $3
      `, [JSON.stringify(result), job.photo_url, job.step_name]);

      // Mark as completed
      await neonClient.query(`
        UPDATE foto_evaluations_queue
        SET status = 'completed', result = $1
        WHERE id = $2
      `, [JSON.stringify(result), job.id]);

    } catch (error) {
      // Increment retry count
      await neonClient.query(`
        UPDATE foto_evaluations_queue
        SET retry_count = retry_count + 1,
            status = CASE WHEN retry_count >= 2 THEN 'failed' ELSE 'pending' END
        WHERE id = $1
      `, [job.id]);
    }
  }
}
```

**Cron setup** (VF Server):
```bash
# /etc/cron.d/foto-evaluation-queue
*/5 * * * * node /srv/data/apps/fibreflow/scripts/process-evaluation-queue.js >> /var/log/evaluation-queue.log 2>&1
```

**Benefits**:
- Jobs survive power outages (persisted in database)
- Automatic retry logic (up to 3 attempts)
- Processing resumes when VF Server is back
- No data loss

---

### Pattern 3: Circuit Breaker

**Use case**: Prevent cascading failures when VF Server is down

```typescript
// Circuit breaker state
class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  private readonly FAILURE_THRESHOLD = 3;
  private readonly TIMEOUT = 60000; // 60 seconds
  private readonly HALF_OPEN_TIMEOUT = 30000; // 30 seconds

  async execute<T>(
    fn: () => Promise<T>,
    fallback: () => Promise<T>
  ): Promise<T> {
    // Circuit is open - use fallback immediately
    if (this.state === 'open') {
      const timeSinceFailure = Date.now() - this.lastFailureTime;

      if (timeSinceFailure > this.TIMEOUT) {
        // Try half-open (test if service recovered)
        this.state = 'half-open';
      } else {
        // Still in cooldown - use fallback
        console.log('Circuit breaker OPEN - using fallback');
        return await fallback();
      }
    }

    try {
      const result = await fn();

      // Success - reset circuit breaker
      if (this.state === 'half-open') {
        console.log('Circuit breaker recovered - closing');
        this.state = 'closed';
      }
      this.failureCount = 0;

      return result;

    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();

      // Too many failures - open circuit
      if (this.failureCount >= this.FAILURE_THRESHOLD) {
        console.log(`Circuit breaker OPENED after ${this.failureCount} failures`);
        this.state = 'open';
      }

      // Use fallback
      return await fallback();
    }
  }
}

// Usage
const vfServerCircuit = new CircuitBreaker();

async function callVFServerWithCircuitBreaker(url: string, data: any) {
  return await vfServerCircuit.execute(
    // Primary: Try VF Server
    async () => {
      const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(data),
        timeout: 5000
      });
      if (!response.ok) throw new Error('VF Server error');
      return response.json();
    },
    // Fallback: Queue for later
    async () => {
      await queueJob(data);
      return { status: 'queued', message: 'VF Server unavailable' };
    }
  );
}
```

**Benefits**:
- Stops hitting VF Server when it's clearly down (saves time)
- Automatic recovery detection
- Prevents request pile-up during outages
- Graceful transition back to normal

---

### Pattern 4: Cached Results

**Use case**: Show stale data when live data unavailable

```typescript
// Cache layer with TTL
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // milliseconds
}

class ResultCache<T> {
  private cache = new Map<string, CacheEntry<T>>();

  set(key: string, data: T, ttl: number = 3600000) { // 1 hour default
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const age = Date.now() - entry.timestamp;
    if (age > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  getStale(key: string): T | null {
    const entry = this.cache.get(key);
    return entry ? entry.data : null;
  }
}

// Usage: Foto reviews with cache
const reviewCache = new ResultCache<FotoReview>();

async function getFotoReview(drNumber: string) {
  try {
    // Try fresh data from VF Server
    const result = await fetch(`http://100.96.203.105:3005/api/foto-reviews/${drNumber}`, {
      timeout: 5000
    });

    if (result.ok) {
      const data = await result.json();
      reviewCache.set(drNumber, data, 3600000); // Cache for 1 hour
      return { ...data, cached: false };
    }

    throw new Error('VF Server unavailable');

  } catch (error) {
    // Fallback: Try cache (even if stale)
    const cached = reviewCache.getStale(drNumber);

    if (cached) {
      console.log(`Serving stale cache for ${drNumber}`);
      return {
        ...cached,
        cached: true,
        cacheWarning: 'Data may be outdated - VF Server temporarily unavailable'
      };
    }

    throw new Error('No cached data available');
  }
}
```

**UI component** (show cache warning):
```tsx
function FotoReviewCard({ drNumber }: { drNumber: string }) {
  const [review, setReview] = useState<any>(null);

  useEffect(() => {
    getFotoReview(drNumber).then(setReview);
  }, [drNumber]);

  return (
    <div>
      {review?.cached && (
        <div className="bg-yellow-50 border border-yellow-200 p-3 rounded mb-4">
          ⚠️ {review.cacheWarning}
        </div>
      )}

      <h3>{review?.dr_number}</h3>
      {/* Rest of review display */}
    </div>
  );
}
```

**Benefits**:
- Users see data even during outages
- Clear indication when data is stale
- Degrades gracefully (stale > nothing)

---

### Pattern 5: Health Check + Status Display

**Use case**: Show system status to users

```typescript
// API endpoint: /api/system-status
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const services = [
    {
      name: 'Main App (Hostinger)',
      url: 'https://app.fibreflow.app/api/health',
      critical: true
    },
    {
      name: 'QFieldCloud (Hostinger)',
      url: 'https://qfield.fibreflow.app/api/v1/status/',
      critical: true
    },
    {
      name: 'VF Server (Processing)',
      url: 'http://100.96.203.105:3005/api/health',
      critical: false
    },
    {
      name: 'VLM Service',
      url: 'http://100.96.203.105:8100/health',
      critical: false
    }
  ];

  const statuses = await Promise.all(
    services.map(async (service) => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const response = await fetch(service.url, {
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        return {
          ...service,
          status: response.ok ? 'operational' : 'degraded',
          responseTime: response.headers.get('x-response-time') || 'N/A'
        };
      } catch (error) {
        return {
          ...service,
          status: service.critical ? 'down' : 'offline',
          message: service.critical
            ? '🚨 Critical service unavailable'
            : '⚠️ Non-critical service offline (expected during load shedding)'
        };
      }
    })
  );

  const overallStatus = statuses.every(s => s.status === 'operational')
    ? 'operational'
    : statuses.some(s => s.status === 'down')
    ? 'down'
    : 'degraded';

  res.status(200).json({
    status: overallStatus,
    services: statuses,
    timestamp: new Date().toISOString()
  });
}
```

**Status page UI**:
```tsx
function SystemStatusPage() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetch('/api/system-status')
      .then(res => res.json())
      .then(setStatus);

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetch('/api/system-status')
        .then(res => res.json())
        .then(setStatus);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">System Status</h1>

      <div className={`p-4 rounded mb-6 ${
        status?.status === 'operational' ? 'bg-green-50' :
        status?.status === 'degraded' ? 'bg-yellow-50' :
        'bg-red-50'
      }`}>
        <div className="font-semibold">
          {status?.status === 'operational' && '✅ All systems operational'}
          {status?.status === 'degraded' && '⚠️ Some services degraded'}
          {status?.status === 'down' && '🚨 Critical services down'}
        </div>
      </div>

      <div className="space-y-3">
        {status?.services.map((service: any) => (
          <div key={service.name} className="border rounded p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">{service.name}</div>
                {service.critical && (
                  <span className="text-xs text-red-600">CRITICAL</span>
                )}
              </div>
              <div className={`px-3 py-1 rounded text-sm ${
                service.status === 'operational' ? 'bg-green-100 text-green-800' :
                service.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                service.status === 'offline' ? 'bg-gray-100 text-gray-800' :
                'bg-red-100 text-red-800'
              }`}>
                {service.status}
              </div>
            </div>

            {service.message && (
              <div className="text-sm text-gray-600 mt-2">
                {service.message}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-500 mt-4">
        Last updated: {status?.timestamp}
      </div>
    </div>
  );
}
```

**Benefits**:
- Transparency for users
- Clear distinction between critical and non-critical services
- Proactive communication during outages

---

### Pattern 6: Progressive Enhancement

**Use case**: Core features always work, enhanced features degrade

```typescript
// Core functionality (always works - on Hostinger)
async function uploadPhoto(file: File, drNumber: string) {
  // Upload to QFieldCloud (Hostinger - always available)
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dr_number', drNumber);

  const response = await fetch('https://qfield.fibreflow.app/api/v1/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  const data = await response.json();
  return data;
}

// Enhanced functionality (VF Server - may be unavailable)
async function uploadPhotoWithAIEvaluation(file: File, drNumber: string, stepName: string) {
  // Step 1: Upload (critical - must succeed)
  const uploadResult = await uploadPhoto(file, drNumber);

  // Step 2: AI evaluation (optional - can fail gracefully)
  try {
    const evaluationResult = await fetch('http://100.96.203.105:8100/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_url: uploadResult.file_url,
        step: stepName
      }),
      timeout: 5000
    });

    if (evaluationResult.ok) {
      const evaluation = await evaluationResult.json();
      return {
        ...uploadResult,
        evaluation,
        aiEvaluated: true
      };
    }
  } catch (error) {
    console.log('AI evaluation unavailable - queuing for later');

    // Queue for later evaluation
    await queuePhotoEvaluation({
      photo_url: uploadResult.file_url,
      step_name: stepName,
      queued_at: new Date().toISOString(),
      retry_count: 0
    });
  }

  // Return upload result even if AI evaluation failed
  return {
    ...uploadResult,
    aiEvaluated: false,
    message: 'Photo uploaded successfully. AI evaluation will be available in 2-4 hours.'
  };
}
```

**UI feedback**:
```tsx
function UploadResult({ result }: { result: any }) {
  return (
    <div className="p-4 bg-white border rounded">
      <div className="flex items-center mb-2">
        <CheckCircle className="text-green-500 mr-2" />
        <span className="font-semibold">Photo uploaded successfully</span>
      </div>

      {result.aiEvaluated ? (
        <div className="mt-3 p-3 bg-blue-50 rounded">
          <div className="text-sm font-medium">✨ AI Evaluation</div>
          <div className="text-sm mt-1">
            Result: {result.evaluation.passed ? '✅ Passed' : '❌ Failed'}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {result.evaluation.feedback}
          </div>
        </div>
      ) : (
        <div className="mt-3 p-3 bg-yellow-50 rounded">
          <div className="text-sm font-medium">⏳ AI Evaluation Pending</div>
          <div className="text-xs text-gray-600 mt-1">
            {result.message}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Benefits**:
- Core workflow never blocked
- Enhanced features degrade gracefully
- Clear user communication
- No frustration (upload succeeded, just evaluation delayed)

---

## Implementation Checklist

### For Each VF Server Dependency

When you identify a service running on VF Server:

- [ ] **Classify criticality**
  - Critical: Must work 99.9% of time → Move to Hostinger
  - Non-critical: Can tolerate downtime → Keep on VF Server with patterns

- [ ] **Add timeout** (3-5 seconds max)
  ```typescript
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  ```

- [ ] **Implement fallback**
  - Queue job for later?
  - Use cached data?
  - Skip optional feature?
  - Show informative message?

- [ ] **Test failure mode**
  - Manually stop VF Server service
  - Verify graceful degradation
  - Check user experience

- [ ] **Add monitoring**
  - Log failures
  - Track queue depth
  - Alert if critical dependency failing

- [ ] **Document behavior**
  - Update API docs with degraded mode behavior
  - Add status indicators in UI
  - Communicate to users

---

## Service-Specific Implementations

### VLM Foto Evaluations

**Current**: Synchronous API call to VF Server

**Improved**:
```typescript
async function evaluateFoto(photoUrl: string, stepName: string) {
  try {
    // Try immediate evaluation (5 second timeout)
    const result = await fetch('http://100.96.203.105:8100/evaluate', {
      method: 'POST',
      body: JSON.stringify({ image_url: photoUrl, step: stepName }),
      timeout: 5000
    });

    if (result.ok) {
      return await result.json();
    }
  } catch (error) {
    // VF Server down - queue for batch processing
    console.log('VLM unavailable - queueing evaluation');
  }

  // Queue for later
  await queuePhotoEvaluation({
    photo_url: photoUrl,
    step_name: stepName,
    queued_at: new Date().toISOString(),
    retry_count: 0
  });

  return {
    status: 'queued',
    message: 'AI evaluation queued. Results in 2-4 hours (VF Server temporarily offline).',
    passed: null
  };
}
```

---

### WhatsApp Feedback Service

**Current**: Direct call to VF Server port 8081

**Improved**:
```typescript
async function sendWhatsAppFeedback(drNumber: string, message: string) {
  try {
    // Try immediate send (3 second timeout - WhatsApp should be fast)
    const result = await fetch('http://100.96.203.105:8081/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to: '27711558396',
        message: `DR ${drNumber}: ${message}`
      }),
      timeout: 3000
    });

    if (result.ok) {
      return { sent: true, immediate: true };
    }
  } catch (error) {
    console.log('WhatsApp service unavailable - queuing message');
  }

  // Queue for batch send when VF Server is back
  await queueWhatsAppMessage({
    dr_number: drNumber,
    message,
    queued_at: new Date().toISOString()
  });

  return {
    sent: true,
    immediate: false,
    message: 'Feedback queued. Will be sent when VF Server is online.'
  };
}
```

---

### Internal Tools (shadcn playground, downloads)

**Current**: Direct links to VF Server

**Improved**:
```tsx
function DownloadLink({ filename, url }: { filename: string; url: string }) {
  const [available, setAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    // Check if VF Server is reachable
    fetch('http://100.96.203.105:3005/api/health', { timeout: 3000 })
      .then(() => setAvailable(true))
      .catch(() => setAvailable(false));
  }, []);

  if (available === false) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
        <div className="font-medium">⚠️ Download temporarily unavailable</div>
        <div className="text-sm text-gray-600 mt-1">
          VF Server is offline (likely load shedding). Downloads will be available when power is restored.
        </div>
        <div className="text-sm text-gray-600 mt-2">
          Expected downtime: 2-4 hours during Stage 4-6 load shedding.
        </div>
      </div>
    );
  }

  return (
    <a
      href={url}
      download={filename}
      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
    >
      <Download className="mr-2 w-4 h-4" />
      Download {filename}
    </a>
  );
}
```

---

## Monitoring & Alerting

### VF Server Health Check

```bash
#!/bin/bash
# /srv/scripts/vf-server-health-check.sh

VF_SERVER="http://100.96.203.105:3005"
LOG_FILE="/var/log/vf-server-health.log"
ALERT_WEBHOOK="https://app.fibreflow.app/api/alerts/vf-server-down"

# Check if VF Server is responding
if ! curl -s -f --max-time 5 "${VF_SERVER}/api/health" > /dev/null; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  echo "${TIMESTAMP} - VF Server DOWN" >> "${LOG_FILE}"

  # Send alert (only once per outage)
  if [ ! -f /tmp/vf-server-down-alert-sent ]; then
    curl -X POST "${ALERT_WEBHOOK}" \
      -H "Content-Type: application/json" \
      -d '{"status": "down", "timestamp": "'${TIMESTAMP}'", "service": "VF Server"}'

    touch /tmp/vf-server-down-alert-sent
  fi
else
  # Server is up - remove alert flag if it exists
  if [ -f /tmp/vf-server-down-alert-sent ]; then
    rm /tmp/vf-server-down-alert-sent

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${TIMESTAMP} - VF Server RECOVERED" >> "${LOG_FILE}"

    # Send recovery alert
    curl -X POST "${ALERT_WEBHOOK}" \
      -H "Content-Type: application/json" \
      -d '{"status": "up", "timestamp": "'${TIMESTAMP}'", "service": "VF Server"}'
  fi
fi
```

**Cron setup** (Hostinger VPS):
```bash
# Check every 5 minutes
*/5 * * * * /srv/scripts/vf-server-health-check.sh
```

---

### Queue Depth Monitoring

```typescript
// API endpoint: /api/admin/queue-stats
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const stats = await neonClient.query(`
    SELECT
      status,
      COUNT(*) as count,
      MIN(queued_at) as oldest_job
    FROM foto_evaluations_queue
    GROUP BY status
  `);

  const queueDepth = stats.rows.find(r => r.status === 'pending')?.count || 0;
  const processingCount = stats.rows.find(r => r.status === 'processing')?.count || 0;
  const oldestJob = stats.rows.find(r => r.status === 'pending')?.oldest_job;

  // Alert if queue is growing too large
  if (queueDepth > 100) {
    await sendAlert({
      level: 'warning',
      message: `Queue depth: ${queueDepth} jobs (threshold: 100)`,
      action: 'Check VF Server status - may need manual intervention'
    });
  }

  // Alert if oldest job is >24 hours old
  if (oldestJob) {
    const ageHours = (Date.now() - new Date(oldestJob).getTime()) / 3600000;
    if (ageHours > 24) {
      await sendAlert({
        level: 'critical',
        message: `Oldest queued job: ${ageHours.toFixed(1)} hours old`,
        action: 'VF Server may be down - investigate immediately'
      });
    }
  }

  res.status(200).json({
    queueDepth,
    processingCount,
    oldestJobAge: oldestJob ? `${Math.floor((Date.now() - new Date(oldestJob).getTime()) / 60000)} minutes` : 'N/A',
    stats: stats.rows
  });
}
```

---

## Testing Graceful Degradation

### Manual Testing

```bash
# 1. Stop VF Server service (simulate load shedding)
ssh louis@100.96.203.105
sudo systemctl stop fibreflow

# 2. Test customer-facing workflows
# - Upload photo to QFieldCloud (should work)
# - View foto reviews dashboard (should show cached or queued)
# - Download APK (should show "temporarily unavailable" message)

# 3. Verify queue is working
# Check database for queued jobs
psql $NEON_DATABASE_URL -c "SELECT COUNT(*) FROM foto_evaluations_queue WHERE status = 'pending';"

# 4. Start VF Server (simulate power restoration)
sudo systemctl start fibreflow

# 5. Verify queue processing
# Wait 5 minutes, check queue cleared
psql $NEON_DATABASE_URL -c "SELECT COUNT(*) FROM foto_evaluations_queue WHERE status = 'completed';"
```

### Automated Testing

```typescript
// tests/graceful-degradation.test.ts
describe('Graceful Degradation', () => {
  beforeAll(async () => {
    // Mock VF Server as unavailable
    nock('http://100.96.203.105:8100')
      .post('/evaluate')
      .replyWithError({ code: 'ECONNREFUSED' });
  });

  it('should queue foto evaluation when VLM is down', async () => {
    const result = await evaluateFoto('https://example.com/photo.jpg', 'house_photo');

    expect(result.status).toBe('queued');
    expect(result.message).toContain('2-4 hours');

    // Verify job was queued in database
    const queued = await neonClient.query(
      'SELECT * FROM foto_evaluations_queue WHERE photo_url = $1',
      ['https://example.com/photo.jpg']
    );
    expect(queued.rows).toHaveLength(1);
  });

  it('should allow photo upload even when evaluation fails', async () => {
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const result = await uploadPhotoWithAIEvaluation(file, 'DR1234567', 'house_photo');

    expect(result.file_url).toBeDefined();
    expect(result.aiEvaluated).toBe(false);
    expect(result.message).toContain('2-4 hours');
  });

  it('should serve cached data when VF Server is down', async () => {
    // Pre-populate cache
    reviewCache.set('DR1234567', mockReview, 3600000);

    // VF Server unavailable
    const result = await getFotoReview('DR1234567');

    expect(result.cached).toBe(true);
    expect(result.cacheWarning).toBeDefined();
  });
});
```

---

## User Communication

### In-App Messages

**During VF Server downtime**, show informative banner:

```tsx
function VFServerStatusBanner() {
  const [vfServerDown, setVFServerDown] = useState(false);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        await fetch('http://100.96.203.105:3005/api/health', { timeout: 3000 });
        setVFServerDown(false);
      } catch {
        setVFServerDown(true);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  if (!vfServerDown) return null;

  return (
    <div className="bg-yellow-50 border-b border-yellow-200 p-3">
      <div className="container mx-auto flex items-start">
        <AlertTriangle className="text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="font-medium text-yellow-900">
            Some features temporarily unavailable
          </div>
          <div className="text-sm text-yellow-800 mt-1">
            Our processing server is offline (likely load shedding). All critical features
            (QFieldCloud sync, uploads) are working normally. AI evaluations and downloads
            will resume when power is restored (typically 2-4 hours).
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Email Notifications (Optional)

Send daily summary if VF Server had significant downtime:

```typescript
async function sendDailyDowntimeReport() {
  const downtimeEvents = await neonClient.query(`
    SELECT
      DATE_TRUNC('day', timestamp) as date,
      COUNT(*) as downtime_events,
      SUM(EXTRACT(EPOCH FROM (recovered_at - timestamp))) / 3600 as total_hours_down
    FROM vf_server_downtime_log
    WHERE timestamp > NOW() - INTERVAL '1 day'
    GROUP BY DATE_TRUNC('day', timestamp)
  `);

  if (downtimeEvents.rows.length > 0) {
    const event = downtimeEvents.rows[0];

    await sendEmail({
      to: 'admin@fibreflow.app',
      subject: `VF Server Downtime Report - ${event.date}`,
      body: `
        VF Server was offline ${event.downtime_events} time(s) yesterday.
        Total downtime: ${event.total_hours_down.toFixed(1)} hours

        Impact:
        - ${await getQueuedJobsCount()} jobs queued for processing
        - 0 critical services affected (all on Hostinger)

        Action required: None (expected during load shedding)
      `
    });
  }
}
```

---

## Success Metrics

Track these metrics to validate graceful degradation is working:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Critical service uptime** | 99.9% | Monitor QFieldCloud and app.fibreflow.app |
| **Customer complaints during VF outages** | 0 | Support ticket analysis |
| **Queue processing lag** | <6 hours | `MAX(NOW() - queued_at)` from queue table |
| **Cache hit rate during outages** | >80% | Log cache hits vs misses |
| **Failed uploads during outages** | 0 | QFieldCloud upload success rate |

## Related Documentation

- `INFRASTRUCTURE_RESILIENCE_STRATEGY.md` - Overall architecture strategy
- `docs/OPERATIONS_LOG.md` - Track outages and incidents
- `.claude/skills/vf-server/skill.md` - VF Server management

## Approval & Implementation

**Created**: 2025-12-23
**Status**: Ready for implementation
**Priority**: High (mitigates load shedding business risk)

**Next steps**:
1. Review patterns with team
2. Identify all VF Server dependencies
3. Implement patterns for each dependency
4. Test failure modes
5. Deploy to production
6. Monitor and iterate
