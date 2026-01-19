"""
Simple health check module for testing Inngest workflows

This module demonstrates:
- Scheduled health checks (every 5 minutes)
- Multi-step workflow execution
- Database logging (mocked)
- WhatsApp alerting
- Retry logic with exponential backoff
"""

import os
import sys
import json
import psutil
import requests
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inngest import Inngest, Function, TriggerCron, TriggerEvent
from client import inngest_client, Events

# Add new event for health checks
Events.HEALTH_CHECK_SCHEDULED = "health/check.scheduled"
Events.HEALTH_CHECK_ALERT = "health/alert.triggered"

# Health check thresholds
THRESHOLDS = {
    "cpu_percent": 80.0,      # Alert if CPU > 80%
    "memory_percent": 85.0,   # Alert if Memory > 85%
    "disk_percent": 90.0,     # Alert if Disk > 90%
}

@inngest_client.create_function(
    fn_id="server-health-check",
    trigger=TriggerCron(cron="*/5 * * * *"),  # Every 5 minutes
    retries=3
)
async def check_server_health(ctx, step):
    """
    Perform a comprehensive server health check.

    This demonstrates a multi-step workflow with:
    1. Collect metrics
    2. Analyze thresholds
    3. Log to database
    4. Send alerts if needed
    """

    # Step 1: Collect system metrics
    metrics = await step.run(
        "collect-metrics",
        lambda: _collect_system_metrics()
    )

    # Step 2: Analyze metrics against thresholds
    analysis = await step.run(
        "analyze-metrics",
        lambda: _analyze_metrics(metrics)
    )

    # Step 3: Log to database (mocked for demo)
    log_result = await step.run(
        "log-to-database",
        lambda: _log_health_check(metrics, analysis),
        retry={"attempts": 3, "delay": "10s"}
    )

    # Step 4: Send alert if issues found
    if analysis["alert_needed"]:
        alert_result = await step.send_event(
            "trigger-alert",
            {
                "name": Events.HEALTH_CHECK_ALERT,
                "data": {
                    "metrics": metrics,
                    "issues": analysis["issues"],
                    "severity": analysis["severity"]
                }
            }
        )

        # Also queue WhatsApp message
        await step.send_event(
            "queue-whatsapp-alert",
            {
                "name": Events.WHATSAPP_MESSAGE_QUEUED,
                "data": {
                    "phone": os.getenv("ALERT_PHONE", "+27123456789"),
                    "message": _format_alert_message(analysis),
                    "priority": "high" if analysis["severity"] == "critical" else "normal"
                }
            }
        )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "alert_sent": analysis["alert_needed"],
        "status": "healthy" if not analysis["alert_needed"] else analysis["severity"]
    }

@inngest_client.create_function(
    fn_id="manual-health-check",
    trigger=TriggerEvent(event=Events.HEALTH_CHECK_SCHEDULED)
)
async def manual_health_check(ctx, step):
    """
    Manually triggered health check.

    This allows testing the workflow on-demand.
    """

    # Get target server from event data
    target = ctx.event.data.get("target", "local")

    # Step 1: Check if target is reachable
    reachable = await step.run(
        "check-reachability",
        lambda: _check_target_reachable(target),
        retry={"attempts": 2, "delay": "5s"}
    )

    if not reachable:
        # Send immediate alert
        await step.send_event(
            "unreachable-alert",
            {
                "name": Events.WHATSAPP_MESSAGE_QUEUED,
                "data": {
                    "phone": os.getenv("ALERT_PHONE", "+27123456789"),
                    "message": f"🔴 CRITICAL: Server {target} is unreachable!",
                    "priority": "high"
                }
            }
        )
        return {"status": "unreachable", "target": target}

    # Step 2: Collect metrics from target
    metrics = await step.run(
        "collect-target-metrics",
        lambda: _collect_target_metrics(target)
    )

    # Step 3: Generate report
    report = await step.run(
        "generate-report",
        lambda: _generate_health_report(target, metrics)
    )

    return report

# Helper functions
def _collect_system_metrics() -> Dict[str, Any]:
    """Collect current system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get network stats
        net = psutil.net_io_counters()

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "network_sent_mb": net.bytes_sent / (1024**2),
            "network_recv_mb": net.bytes_recv / (1024**2),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def _analyze_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze metrics against thresholds."""
    issues = []
    severity = "healthy"

    if "error" in metrics:
        return {
            "alert_needed": True,
            "issues": [f"Failed to collect metrics: {metrics['error']}"],
            "severity": "critical"
        }

    # Check CPU
    if metrics["cpu_percent"] > THRESHOLDS["cpu_percent"]:
        issues.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
        severity = "warning"

    # Check Memory
    if metrics["memory_percent"] > THRESHOLDS["memory_percent"]:
        issues.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
        severity = "warning" if severity == "healthy" else "critical"

    # Check Disk
    if metrics["disk_percent"] > THRESHOLDS["disk_percent"]:
        issues.append(f"Low disk space: {metrics['disk_percent']:.1f}% used")
        severity = "critical"

    return {
        "alert_needed": len(issues) > 0,
        "issues": issues,
        "severity": severity,
        "analyzed_at": datetime.utcnow().isoformat()
    }

def _log_health_check(metrics: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Log health check results (mocked for demo)."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "analysis": analysis,
        "logged": True
    }

    # In production, this would write to database
    print(f"[Health Check] {json.dumps(log_entry, indent=2)}")

    return {"success": True, "log_id": "mock_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")}

def _format_alert_message(analysis: Dict[str, Any]) -> str:
    """Format alert message for WhatsApp."""
    severity_emoji = {
        "warning": "⚠️",
        "critical": "🔴"
    }

    emoji = severity_emoji.get(analysis["severity"], "ℹ️")
    issues_text = "\n".join(f"• {issue}" for issue in analysis["issues"])

    return f"""
{emoji} Server Health Alert

Severity: {analysis["severity"].upper()}

Issues Found:
{issues_text}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

Check dashboard for details.
""".strip()

def _check_target_reachable(target: str) -> bool:
    """Check if target server is reachable."""
    if target == "local":
        return True

    try:
        # Try to reach VF server health endpoint
        if target == "vf-server":
            response = requests.get("http://100.96.203.105:3005/api/health", timeout=5)
            return response.status_code == 200

        # Default: assume reachable
        return True
    except:
        return False

def _collect_target_metrics(target: str) -> Dict[str, Any]:
    """Collect metrics from target server."""
    if target == "local":
        return _collect_system_metrics()

    # For remote servers, would use SSH or API
    # Mocked for demo
    return {
        "cpu_percent": 45.2,
        "memory_percent": 62.3,
        "disk_percent": 71.8,
        "target": target,
        "timestamp": datetime.utcnow().isoformat()
    }

def _generate_health_report(target: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive health report."""
    return {
        "target": target,
        "metrics": metrics,
        "status": "healthy" if metrics.get("cpu_percent", 0) < 80 else "degraded",
        "report_generated": datetime.utcnow().isoformat(),
        "recommendations": [
            "Monitor CPU usage" if metrics.get("cpu_percent", 0) > 60 else None,
            "Consider memory upgrade" if metrics.get("memory_percent", 0) > 70 else None,
            "Clean up disk space" if metrics.get("disk_percent", 0) > 80 else None
        ]
    }

# Export functions for registration
health_check_functions = [
    check_server_health,
    manual_health_check
]