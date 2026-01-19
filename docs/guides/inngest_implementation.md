# Inngest Implementation for FibreFlow

## Phase 1: Setup (Day 1)

### Installation
```bash
# Install Python SDK
./venv/bin/pip install inngest

# Install CLI for local dev
curl -sSL https://www.inngest.com/cli/install | sh

# Add to requirements/base.txt
echo "inngest>=0.3.0" >> requirements/base.txt
```

### Initial Configuration
```python
# inngest/client.py
from inngest import Inngest, Event

# Initialize client
inngest = Inngest(
    app_id="fibreflow-agents",
    signing_key=os.getenv("INNGEST_SIGNING_KEY"),
    event_key=os.getenv("INNGEST_EVENT_KEY")
)
```

## Phase 2: Migrate Agent Harness (Week 1)

### Current Process (Manual)
```python
# harness/runner.py - Sequential sessions
for i in range(50, 100):
    run_coding_agent(i)  # Can fail, no resume
```

### With Inngest (Durable)
```python
# inngest/functions/agent_builder.py
@inngest.create_function(
    fn_id="build-agent",
    trigger=inngest.Event("agent/build.requested"),
    retries=3,
    concurrency=[{
        "limit": 1,
        "key": "event.data.agent_name"  # One build per agent
    }]
)
async def build_agent(ctx, step):
    """Build agent with checkpoint/resume capability"""

    # Step 1: Initialize
    feature_list = await step.run(
        "initialize-agent",
        lambda: run_initializer_agent(ctx.event.data.agent_name)
    )

    # Step 2-100: Build features (can pause/resume)
    for feature in feature_list["features"]:
        if not feature["passes"]:
            await step.run(
                f"build-feature-{feature['id']}",
                lambda: implement_feature(feature),
                retry={"attempts": 3, "delay": "5s"}
            )

            # Checkpoint progress
            await step.sleep("pause-between-features", duration="30s")

    # Step 101: Deploy
    await step.run(
        "deploy-agent",
        lambda: deploy_to_production(ctx.event.data.agent_name)
    )

    return {"agent": ctx.event.data.agent_name, "status": "complete"}
```

## Phase 3: Database Sync Workflow (Week 1)

```python
# inngest/functions/database_sync.py
@inngest.create_function(
    fn_id="sync-databases",
    trigger=inngest.Cron("sync-neon-convex", "0 */6 * * *"),  # Every 6 hours
    concurrency=[{"limit": 1}]  # Prevent overlapping syncs
)
async def sync_databases(ctx, step):
    """Sync Neon to Convex with error handling"""

    # Get data from Neon
    neon_data = await step.run(
        "fetch-neon-data",
        lambda: fetch_all_neon_tables(),
        retry={"attempts": 3}
    )

    # Transform data
    convex_format = await step.run(
        "transform-data",
        lambda: transform_for_convex(neon_data)
    )

    # Push to Convex in batches
    for batch in chunk_data(convex_format, size=100):
        await step.run(
            f"sync-batch-{batch['id']}",
            lambda: push_to_convex(batch),
            retry={"attempts": 5, "delay": "exponential"}
        )

    # Send notification
    await step.run(
        "notify-complete",
        lambda: send_slack_notification("Database sync complete")
    )
```

## Phase 4: WhatsApp Queue (Week 2)

```python
# inngest/functions/whatsapp_queue.py
@inngest.create_function(
    fn_id="send-whatsapp",
    trigger=inngest.Event("whatsapp/message.queued"),
    throttle={
        "limit": 10,
        "period": "60s",  # 10 messages per minute
        "key": "event.data.phone"
    },
    retries=5
)
async def send_whatsapp_message(ctx, step):
    """Rate-limited WhatsApp sending with retries"""

    # Check if service is running
    service_status = await step.run(
        "check-service",
        lambda: check_whatsapp_service()
    )

    if not service_status["paired"]:
        # Pause and retry later
        await step.sleep("wait-for-pairing", duration="5m")
        raise Exception("Phone not paired")

    # Send message
    result = await step.run(
        "send-message",
        lambda: send_via_whatsapp_api(
            phone=ctx.event.data.phone,
            message=ctx.event.data.message
        ),
        retry={"attempts": 3, "delay": "30s"}
    )

    return result
```

## Phase 5: VLM Evaluation Pipeline (Week 2)

```python
# inngest/functions/vlm_evaluation.py
@inngest.create_function(
    fn_id="evaluate-foto",
    trigger=inngest.Event("foto/evaluation.requested"),
    concurrency=[{
        "limit": 5,  # Max 5 concurrent evaluations
        "key": "global"
    }]
)
async def evaluate_foto(ctx, step):
    """Process foto with VLM and store results"""

    # Download image
    image = await step.run(
        "download-image",
        lambda: download_from_s3(ctx.event.data.image_url)
    )

    # Run VLM evaluation
    evaluation = await step.run(
        "vlm-evaluate",
        lambda: call_qwen_vlm(image),
        timeout="5m"
    )

    # Store in Neon
    await step.run(
        "store-result",
        lambda: store_evaluation_neon(evaluation)
    )

    # Trigger WhatsApp notification
    await step.send_event(
        "queue-notification",
        Event(
            name="whatsapp/message.queued",
            data={
                "phone": ctx.event.data.contractor_phone,
                "message": f"Evaluation complete: {evaluation['score']}"
            }
        )
    )
```

## Integration Points

### 1. Orchestrator Enhancement
```python
# orchestrator/orchestrator.py
from inngest import Event
from inngest.client import inngest

class Orchestrator:
    def route_task(self, task):
        # Existing routing logic...

        # For long-running tasks, trigger Inngest
        if task.estimated_duration > 60:  # More than 1 minute
            inngest.send(Event(
                name=f"{task.agent}/{task.action}",
                data=task.to_dict()
            ))
            return {"status": "queued", "id": task.id}
```

### 2. Monitoring Dashboard

Inngest provides a built-in dashboard at `https://app.inngest.com` showing:
- Function runs and status
- Error rates and retries
- Execution timeline
- Event history

### 3. Local Development

```bash
# Start Inngest dev server
inngest dev

# Register your functions
./venv/bin/python inngest/register.py

# Test with events
inngest send agent/build.requested --data '{"agent_name": "sharepoint"}'
```

## Benefits for FibreFlow

### Immediate Wins
1. **Resilient Agent Building**: Harness can pause/resume, surviving crashes
2. **Automatic Retries**: No more manual intervention for transient failures
3. **Rate Limiting**: WhatsApp won't get banned for too many messages
4. **Concurrent Processing**: VLM evaluations process in parallel with limits
5. **Visibility**: See exactly where long-running tasks are

### Long-term Benefits
1. **Event-Driven Architecture**: Decouple components with events
2. **Workflow as Code**: Version control your workflows
3. **Cost Optimization**: Only pay for execution time, not idle waiting
4. **Team Collaboration**: Non-technical team can monitor progress
5. **Audit Trail**: Complete history of all executions

## Migration Strategy

### Week 1: Foundation
- [ ] Install Inngest SDK and CLI
- [ ] Set up development environment
- [ ] Create first function (database sync)
- [ ] Test locally with dev server

### Week 2: Critical Paths
- [ ] Migrate Agent Harness to Inngest
- [ ] Implement WhatsApp queue
- [ ] Add retry logic to deployments

### Week 3: Enhancement
- [ ] Add VLM evaluation pipeline
- [ ] Create monitoring alerts
- [ ] Document new workflows

### Week 4: Optimization
- [ ] Tune concurrency limits
- [ ] Add custom retry strategies
- [ ] Implement dead letter queues

## Environment Variables

Add to `.env`:
```bash
# Inngest Configuration
INNGEST_SIGNING_KEY=signkey_prod_...
INNGEST_EVENT_KEY=test_...
INNGEST_APP_ID=fibreflow-agents
INNGEST_API_BASE_URL=https://api.inngest.com  # Or self-hosted URL
```

## Cost Estimate

Inngest pricing (as of 2024):
- **Free tier**: 50K function runs/month
- **Pro**: $50/month for 500K runs
- **Enterprise**: Custom pricing

FibreFlow estimated usage:
- Agent builds: ~20/month × 100 steps = 2,000 runs
- Database syncs: 4/day × 30 = 120 runs
- WhatsApp messages: ~1000/month
- VLM evaluations: ~500/month

**Total: ~3,620 runs/month** (well within free tier)

## Alternatives Considered

1. **Celery + Redis**: More complex setup, less durability
2. **AWS Step Functions**: Vendor lock-in, complex pricing
3. **Temporal**: Overkill for current needs, steeper learning curve
4. **Apache Airflow**: Better for data pipelines, not event-driven

Inngest wins on simplicity, durability, and developer experience.