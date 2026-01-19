# VPS Monitor Agent

**AI-Powered Infrastructure Monitoring with Claude**

---

## What This Does

The VPS Monitor Agent provides a **natural language interface** to monitor VPS servers. Instead of running complex SSH commands and parsing output manually, you can ask questions like "Is the server healthy?" and get intelligent, actionable responses.

**Supported Servers**:
- **Hostinger VPS** (72.60.17.245): Public-facing FibreFlow deployment
- **VF Server** (100.96.203.105 via Tailscale): Internal operations
  - Production paths: `/srv/data/apps/`, `/srv/scripts/cron/`
  - See `.claude/skills/vf-server/README.md` for VF-specific operations

**Example:**
```
You: "What's the CPU usage?"
Agent: "CPU usage is 12.4% (normal). The server is running well with low resource usage."
```

---

## Quick Start

### Prerequisites

```bash
# 1. Ensure you have SSH access to the VPS
ssh root@srv1092611.hstgr.cloud

# 2. Set environment variables
export ANTHROPIC_API_KEY="your_api_key_here"
export VPS_HOSTNAME="srv1092611.hstgr.cloud"
```

###Run the Agent

```bash
# From the agents/vps-monitor directory
cd /home/louisdup/Agents/claude/agents/vps-monitor

# Run demo
../../venv/bin/python3 demo.py

# Or use the agent directly
../../venv/bin/python3 agent.py
```

---

## Project Structure

```
agents/vps-monitor/
├── agent.py                # Main agent implementation
├── demo.py                 # Interactive demo script
├── config.json             # Agent metadata
├── README.md               # This file
└── __pycache__/            # Python cache (auto-generated)

Related files:
../../orchestrator/registry.json    # Agent registration
```

---

## Key Concepts

### 1. SSH-Based Monitoring

**How it works:**
- Agent connects to VPS via SSH
- Executes system commands (`top`, `free`, `df`, etc.)
- Parses output into structured data
- Claude AI analyzes and presents results

**Why SSH:** Direct access to real-time system metrics without installing monitoring software on the VPS.

### 2. Tool-Based Architecture

The agent has **9 monitoring tools** that Claude can call:

```python
Tools Available:
1. get_system_info()       # Hostname, OS, kernel, uptime
2. get_cpu_usage()         # CPU percentage and status
3. get_memory_usage()      # RAM usage and availability
4. get_disk_usage()        # Disk space statistics
5. get_top_processes()     # Top CPU-consuming processes
6. get_network_stats()     # Network traffic (RX/TX)
7. get_load_average()      # System load (1, 5, 15 min)
8. get_services_status()   # Service health (nginx, docker, etc.)
9. get_full_health_report() # Comprehensive system report
```

**Why tool-based:** Claude decides which metrics to check based on your question, making monitoring intelligent and context-aware.

### 3. Intelligent Analysis

The agent doesn't just return raw metrics—it **analyzes them**:

```
Raw metric: cpu_percent = 89.2
Agent says: "CPU usage is 89.2% (WARNING). This is higher than normal. Top
            processes: nginx (45%), python (23%), node (12%). Consider
            scaling or optimizing nginx configuration."
```

**Thresholds:**
- **CPU:** >80% warning, >90% critical
- **Memory:** >85% warning, >95% critical
- **Disk:** >80% warning, >90% critical
- **Load average:** >2.0 high (for 2-core server)

---

## Common Tasks

### Task 1: Check System Health

```python
from agents.vps_monitor.agent import VPSMonitorAgent

agent = VPSMonitorAgent(
    vps_hostname="srv1092611.hstgr.cloud",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

response = agent.chat("Is the server healthy?")
print(response)
```

### Task 2: Investigate Performance Issues

```python
response = agent.chat("Why is the server slow?")
```

Agent will check CPU, memory, top processes, load average, identify bottlenecks, and provide recommendations.

### Task 3: Monitor Specific Service

```python
response = agent.chat("Is nginx running? How much CPU is it using?")
```

### Task 4: Get Comprehensive Report

```python
response = agent.chat("Give me a full system health report")
```

---

## Related Documentation

- **Orchestrator System:** `../../orchestrator/README.md`
- **Agent Workforce Guide:** `../../AGENT_WORKFORCE_GUIDE.md`
- **Project Summary:** `../../PROJECT_SUMMARY.md`

---

**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
**Agent Type:** Infrastructure Monitoring
**Model:** Claude 3.5 Haiku
**Cost:** ~$0.001 per query
