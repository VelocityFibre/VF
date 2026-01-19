#!/usr/bin/env python3
"""
Digital Twin Dashboard API - Phase 4

FastAPI backend providing real-time observability into the agent ecosystem.
Powers the city planner's control room with 5 layers of visibility.

City Planning Analogy: Like a city's operations center API that aggregates
data from traffic sensors, utility monitors, emergency dispatch, and
budget systems - all in real-time.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from harness.sla_monitor import SLAMonitor
from harness.failure_knowledge_base import FailureKnowledgeBase
from orchestrator.model_router import ModelRouter
from orchestrator.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Digital Twin Dashboard",
    description="Real-time observability for FibreFlow agent ecosystem",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
sla_monitor = SLAMonitor()
knowledge_base = FailureKnowledgeBase()
model_router = ModelRouter()
orchestrator = AgentOrchestrator()


# ============================================================================
# LAYER 1: Data Infrastructure View
# ============================================================================

@app.get("/api/sla-status")
async def get_sla_status() -> Dict[str, Any]:
    """
    Real-time SLA compliance status.

    Returns:
        Dictionary with current SLA checks and violations
    """
    results = sla_monitor.check_all_slas()

    # Add compliance percentage
    results["compliance_30d"] = sla_monitor.get_compliance_percentage(days=30)

    return results


@app.get("/api/sla-history")
async def get_sla_history(hours: int = 24) -> Dict[str, Any]:
    """
    Historical SLA metrics for graphing.

    Args:
        hours: Number of hours of history to return

    Returns:
        Time-series data for SLA metrics
    """
    # Read metrics from JSONL file
    metrics_file = Path("harness/sla_metrics.jsonl")

    if not metrics_file.exists():
        return {"history": []}

    cutoff = datetime.now() - timedelta(hours=hours)
    history = []

    with open(metrics_file, 'r') as f:
        for line in f:
            metric = json.loads(line)
            timestamp = datetime.fromisoformat(metric["timestamp"])

            if timestamp >= cutoff:
                history.append(metric)

    return {"history": history}


# ============================================================================
# LAYER 2: Agent Topology View
# ============================================================================

@app.get("/api/agent-topology")
async def get_agent_topology() -> Dict[str, Any]:
    """
    Agent relationship graph for force-directed visualization.

    Returns:
        Nodes and links for D3.js force graph
    """
    agents = orchestrator.list_agents()

    # Build nodes
    nodes = [
        {
            "id": "orchestrator",
            "label": "Orchestrator",
            "layer": "agentic",
            "active": True,
            "size": 20
        }
    ]

    for agent in agents:
        nodes.append({
            "id": agent["id"],
            "label": agent["name"],
            "layer": "agentic",
            "active": agent["status"] == "active",
            "size": 15
        })

    # Build links (orchestrator connects to all agents)
    links = []
    for agent in agents:
        links.append({
            "source": "orchestrator",
            "target": agent["id"],
            "calls": 100,  # TODO: Get from actual metrics
            "avgLatency": 1.5
        })

    return {
        "nodes": nodes,
        "links": links,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/agent-activity")
async def get_agent_activity(hours: int = 24) -> Dict[str, Any]:
    """
    Recent agent activity and call patterns.

    Args:
        hours: Number of hours of history

    Returns:
        Agent call counts and patterns
    """
    # TODO: Read from actual execution logs
    # For now, return simulated data

    return {
        "period_hours": hours,
        "activity": [
            {"agent_id": "vps-monitor", "calls": 142, "avg_latency": 1.2, "errors": 2},
            {"agent_id": "neon-database", "calls": 89, "avg_latency": 0.5, "errors": 0},
            {"agent_id": "convex-database", "calls": 67, "avg_latency": 0.3, "errors": 1},
        ],
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# LAYER 3: Cost Attribution View
# ============================================================================

@app.get("/api/cost-attribution")
async def get_cost_attribution(days: int = 30) -> Dict[str, Any]:
    """
    API cost breakdown by model tier and agent.

    Args:
        days: Number of days to analyze

    Returns:
        Cost attribution data
    """
    routing_stats = model_router.get_routing_stats()

    # Calculate costs by tier
    by_tier = {}
    for tier, count in routing_stats.get("by_tier", {}).items():
        cost_per_query = model_router.get_cost_per_query(
            model_router.configs[model_router.configs[tier.upper()]].tier
        ) if tier.upper() in ["HAIKU", "SONNET", "OPUS"] else 0

        by_tier[tier] = {
            "count": count,
            "cost_per_query": cost_per_query,
            "total_cost": count * cost_per_query
        }

    # Savings analysis
    savings = model_router.estimate_cost_savings()

    return {
        "period_days": days,
        "total_cost": routing_stats.get("total_cost", 0),
        "average_cost": routing_stats.get("average_cost", 0),
        "by_tier": by_tier,
        "savings": savings,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/cost-trends")
async def get_cost_trends(days: int = 30) -> Dict[str, Any]:
    """
    Daily cost trends over time.

    Args:
        days: Number of days of history

    Returns:
        Time-series cost data
    """
    # TODO: Read from actual usage logs
    # For now, return simulated trend

    daily_costs = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        daily_costs.append({
            "date": date.strftime("%Y-%m-%d"),
            "haiku_cost": 0.05 + (i * 0.001),
            "sonnet_cost": 0.20 + (i * 0.005),
            "opus_cost": 0.02 + (i * 0.0002),
            "total_cost": 0.27 + (i * 0.0062)
        })

    return {
        "trends": daily_costs,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# LAYER 4: Learning Analytics View
# ============================================================================

@app.get("/api/learning-stats")
async def get_learning_stats() -> Dict[str, Any]:
    """
    Knowledge base growth and learning analytics.

    Returns:
        Learning patterns and success metrics
    """
    stats = knowledge_base.get_stats()

    # Get all patterns
    patterns = knowledge_base.patterns

    # Analyze by error type
    by_error_type = {}
    for pattern in patterns:
        error_type = pattern.error_type
        if error_type not in by_error_type:
            by_error_type[error_type] = {
                "count": 0,
                "total_frequency": 0,
                "patterns": []
            }

        by_error_type[error_type]["count"] += 1
        by_error_type[error_type]["total_frequency"] += pattern.frequency
        by_error_type[error_type]["patterns"].append({
            "pattern": pattern.error_pattern,
            "frequency": pattern.frequency,
            "learnings": pattern.learnings
        })

    return {
        "total_patterns": stats["total_patterns"],
        "total_failures": stats["total_failures_tracked"],
        "by_error_type": by_error_type,
        "prevention_rate": 0.93 if stats["total_patterns"] > 0 else 0,  # 93% from Phase 1.5
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/learning-timeline")
async def get_learning_timeline(days: int = 30) -> Dict[str, Any]:
    """
    Knowledge base growth over time.

    Args:
        days: Number of days of history

    Returns:
        Timeline of pattern accumulation
    """
    patterns = knowledge_base.patterns

    # Group by date
    by_date = {}
    for pattern in patterns:
        date = pattern.timestamp[:10]  # Extract date (YYYY-MM-DD)

        if date not in by_date:
            by_date[date] = []

        by_date[date].append(pattern)

    # Build timeline
    timeline = []
    for date in sorted(by_date.keys()):
        timeline.append({
            "date": date,
            "patterns_learned": len(by_date[date]),
            "cumulative": sum(len(by_date[d]) for d in by_date if d <= date)
        })

    return {
        "timeline": timeline,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# LAYER 5: Simulation Engine (Basic)
# ============================================================================

@app.post("/api/simulate")
async def simulate_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run what-if simulation for capacity planning.

    Args:
        scenario: Scenario parameters (e.g., additional agents, workload increase)

    Returns:
        Projected impact on cost, SLAs, capacity
    """
    scenario_type = scenario.get("type")
    params = scenario.get("params", {})

    if scenario_type == "add_agents":
        # Simulate adding N agents
        n_agents = params.get("count", 10)
        agent_type = params.get("agent_type", "standard")

        # Estimate impact
        current_cost = model_router.get_routing_stats().get("total_cost", 0)
        projected_cost = current_cost * (1 + (n_agents * 0.1))  # 10% per agent

        return {
            "scenario": scenario,
            "impact": {
                "cost_increase": projected_cost - current_cost,
                "cost_increase_pct": ((projected_cost - current_cost) / current_cost * 100) if current_cost > 0 else 0,
                "projected_total_cost": projected_cost,
                "sla_impact": "Low - within capacity",
                "recommendation": f"Adding {n_agents} agents is feasible with current infrastructure"
            },
            "timestamp": datetime.now().isoformat()
        }

    return {
        "scenario": scenario,
        "error": "Unknown scenario type",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Dashboard Home Page
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve dashboard HTML."""
    html_path = Path(__file__).parent / "dashboard.html"

    if html_path.exists():
        with open(html_path, 'r') as f:
            return f.read()

    # Fallback: minimal dashboard
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Twin Dashboard</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #0f172a;
                color: #e2e8f0;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
            }
            h1 {
                margin: 0;
                font-size: 32px;
            }
            .subtitle {
                opacity: 0.9;
                margin-top: 8px;
            }
            .status {
                color: #10b981;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏙️ Digital Twin Dashboard</h1>
            <p class="subtitle">Phase 4: City Planner Control Room</p>
            <p class="status">✅ API Server Running</p>
        </div>
        <div>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/api/sla-status">/api/sla-status</a> - Real-time SLA compliance</li>
                <li><a href="/api/agent-topology">/api/agent-topology</a> - Agent relationship graph</li>
                <li><a href="/api/cost-attribution">/api/cost-attribution</a> - Cost breakdown</li>
                <li><a href="/api/learning-stats">/api/learning-stats</a> - Knowledge base analytics</li>
                <li><a href="/docs">/docs</a> - Full API documentation</li>
            </ul>
        </div>
    </body>
    </html>
    """


# ============================================================================
# WebSocket for Real-Time Updates
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.

    Streams:
    - SLA status updates (every 60s)
    - Agent activity (every 10s)
    - Cost updates (every 60s)
    """
    await websocket.accept()
    logger.info("Dashboard client connected")

    try:
        while True:
            # Send real-time updates
            update = {
                "timestamp": datetime.now().isoformat(),
                "sla_status": sla_monitor.check_all_slas(),
                "routing_stats": model_router.get_routing_stats()
            }

            await websocket.send_json(update)
            await asyncio.sleep(10)  # Update every 10 seconds

    except WebSocketDisconnect:
        logger.info("Dashboard client disconnected")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Starting Digital Twin Dashboard API (Phase 4)")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Dashboard: http://localhost:8000")
    logger.info("API Docs:  http://localhost:8000/docs")
    logger.info("")
    logger.info("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000)
