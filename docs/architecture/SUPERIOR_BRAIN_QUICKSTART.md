# Superior Agent Brain - Quick Start Guide

Get up and running in 5 minutes!

## TL;DR

```bash
# 1. Install Qdrant (Vector Database)
docker run -d -p 6333:6333 qdrant/qdrant

# 2. Install Python dependencies
pip install qdrant-client numpy

# 3. Verify environment variables
cat .env | grep -E "ANTHROPIC_API_KEY|NEON_DATABASE_URL"

# 4. Run the superior brain
python superior_agent_brain.py
```

## What You Get

🧠 **Complete AI Brain** with human-like cognition:
- ✅ Remembers past conversations (episodic memory)
- ✅ Learns from experience (meta-learning)
- ✅ Shares knowledge between agents (knowledge graph)
- ✅ Optimizes memory over time (consolidation)
- ✅ Routes to specialists (orchestration)

## 5-Minute Setup

### Step 1: Start Qdrant (30 seconds)

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  --name qdrant \
  qdrant/qdrant
```

Verify:
```bash
curl http://localhost:6333/
# Should return JSON with Qdrant info
```

### Step 2: Install Dependencies (1 minute)

```bash
pip install -r requirements_superior_brain.txt
```

Or manually:
```bash
pip install qdrant-client numpy
```

### Step 3: Test Components (2 minutes)

```bash
# Test vector memory
python memory/vector_memory.py

# Test complete brain
python superior_agent_brain.py
```

### Step 4: Use in Your Code (1 minute)

```python
from superior_agent_brain import SuperiorAgentBrain

# Initialize
brain = SuperiorAgentBrain()

# Ask anything
response = brain.chat("What contractors are in the system?")
print(response)

# It will:
# 1. Check if it's seen similar questions before
# 2. Route to the best specialist agent
# 3. Learn from the interaction
# 4. Remember for next time

# Cleanup
brain.close()
```

## Key Features

### 1. Episodic Memory (Remembers Past)

```python
# First time asking
response1 = brain.chat("How do I fix database errors?")
# Brain: *thinks hard, generates solution*

# Later, similar question
response2 = brain.chat("Database connection not working")
# Brain: "I remember solving something similar before! Here's what worked..."
```

### 2. Meta-Learning (Gets Better Over Time)

```python
# The brain automatically tracks:
# - Which agents work best for which tasks
# - Success rates over time
# - Performance improvements

# After 100 queries, it knows:
# "For database questions, neon-agent has 95% success rate"
# "VPS questions route to vps-monitor with 98% accuracy"
```

### 3. Cross-Agent Learning

```python
# When neon-agent solves a problem
brain.knowledge_graph.learn_from_success(
    problem="Connection timeout",
    solution="Increase pool size",
    agent_id="neon-agent"
)

# Now ALL agents can benefit from this knowledge
# convex-agent can use the same solution if it faces similar issues
```

### 4. Memory Consolidation (Like Sleep)

```python
# Run weekly to optimize memory
brain.sleep(conversation_days=7, performance_days=14)

# This:
# - Compresses old conversations into summaries
# - Aggregates performance data
# - Frees up space
# - Maintains memory quality
```

## Usage Patterns

### Pattern 1: Simple Chat

```python
from superior_agent_brain import SuperiorAgentBrain

brain = SuperiorAgentBrain()

# Just chat
print(brain.chat("List all contractors"))
print(brain.chat("How many projects?"))
print(brain.chat("VPS status?"))

brain.close()
```

### Pattern 2: Session Management

```python
brain = SuperiorAgentBrain()

# Multiple queries in a session
brain.chat("Query 1")
brain.chat("Query 2")
brain.chat("Query 3")

# Save session for later reference
brain.save_session(summary="Project status discussion")

brain.close()
```

### Pattern 3: Full Pipeline

```python
brain = SuperiorAgentBrain()

# Get detailed results
result = brain.process_query("Show active projects")

print(f"Response: {result['response']}")
print(f"Agent used: {result['metadata']['selected_agent']}")
print(f"Execution time: {result['metadata']['execution_time_seconds']}s")
print(f"Similar past queries: {result['metadata']['similar_experiences_found']}")

brain.close()
```

## Architecture at a Glance

```
User Query
    ↓
┌───────────────────────────────────────┐
│  Superior Agent Brain                 │
│                                       │
│  1. Recall Similar (Vector Memory)    │
│     "Have I seen this before?"        │
│                                       │
│  2. Route (Orchestrator)              │
│     "Which specialist handles this?"  │
│                                       │
│  3. Process (LLM + Context)           │
│     "Generate response"               │
│                                       │
│  4. Learn (Meta-Learner)              │
│     "Track performance"               │
│                                       │
│  5. Remember (Persistent Memory)      │
│     "Store for future"                │
│                                       │
│  6. Share (Knowledge Graph)           │
│     "Share with other agents"         │
└───────────────────────────────────────┘
    ↓
Response to User
```

## Memory Systems

| System | Purpose | Storage | Example |
|--------|---------|---------|---------|
| **Vector Memory** | "I've seen this before" | Qdrant | Similar queries, past solutions |
| **Persistent Memory** | Long-term conversations | Neon | Full chat histories |
| **Meta-Learner** | Performance tracking | Neon | Success rates, improvements |
| **Knowledge Graph** | Shared learning | Neon | Problem-solution pairs |
| **Working Memory** | Current context | RAM | Active conversation |

## Comparison: Before vs After

### Before (Basic Agent)
```python
# User asks same question twice
Q1: "Database error help"
A1: *thinks from scratch* → solution

Q2: "Database won't connect"  # Similar to Q1
A2: *thinks from scratch again* → solution

# No memory, no learning
```

### After (Superior Brain)
```python
# User asks same question twice
Q1: "Database error help"
A1: *thinks from scratch* → solution
    *stores in memory*

Q2: "Database won't connect"  # Similar to Q1
A2: "I remember Q1! Here's what worked..." → faster, better solution

# Has memory, learns, improves
```

## Performance Expectations

| Metric | First Query | After 100 Queries | After 1000 Queries |
|--------|-------------|-------------------|-------------------|
| Response Time | 2-3s | 1-2s | 1-2s |
| Accuracy | 85% | 92% | 95%+ |
| Memory Recall | 0% | 60% | 80% |
| Learning Applied | No | Yes | Always |

## Next Steps

1. **Try It**: Run `python superior_agent_brain.py`
2. **Integrate**: Add to your existing agents
3. **Monitor**: Check brain status regularly
4. **Optimize**: Run consolidation weekly
5. **Expand**: Add more specialized agents

## Common Questions

**Q: Do I need Qdrant running all the time?**
A: Yes, for vector memory. But you can disable it if not needed:
```python
brain = SuperiorAgentBrain(enable_vector_memory=False)
```

**Q: How much memory does it use?**
A: Minimal. Qdrant stores vectors efficiently. PostgreSQL handles the rest.

**Q: Can I use it without the orchestrator?**
A: Yes:
```python
brain = SuperiorAgentBrain(enable_orchestration=False)
```

**Q: How often should I run consolidation?**
A: Weekly for most use cases. Daily for high-volume systems.

**Q: Does it replace my existing agents?**
A: No! It enhances them. Your agents become specialized brain regions.

## Troubleshooting

**Qdrant not connecting:**
```bash
docker ps | grep qdrant
docker restart qdrant
curl http://localhost:6333/
```

**Memory errors:**
```python
# Run consolidation
brain.sleep()
```

**Database errors:**
```bash
# Check connection
echo $NEON_DATABASE_URL
psql $NEON_DATABASE_URL -c "SELECT version();"
```

## Resources

- **Full Setup**: `SUPERIOR_BRAIN_SETUP.md`
- **Architecture**: `AI_AGENT_BRAIN_ARCHITECTURE.md`
- **Code**: `superior_agent_brain.py` and `memory/`

---

**Ready to build a brain?** 🧠

```bash
python superior_agent_brain.py
```
