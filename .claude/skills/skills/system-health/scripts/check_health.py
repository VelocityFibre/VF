#!/usr/bin/env python3
"""
Comprehensive system health check
Returns JSON with status of all critical services
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

def run_cmd(cmd, timeout=10):
    """Run command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_vf_server():
    """Check VF Server (100.96.203.105:3005)"""
    # Check if process is running
    ps_check = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep \"[n]ext-server\" | grep 3005'")

    # Check port
    port_check = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ss -tlnp | grep :3005'")

    # Check recent logs for errors
    log_check = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'tail -50 /tmp/next_vf.log 2>/dev/null | grep -i error | tail -5'")

    status = "healthy" if ps_check["success"] and port_check["success"] else "down"

    issues = []
    if not ps_check["success"]:
        issues.append("Process not running")
    if not port_check["success"]:
        issues.append("Port 3005 not listening")
    if log_check["output"]:
        issues.append(f"Errors in logs: {log_check['output'][:100]}")

    return {
        "service": "VF Server",
        "status": status,
        "details": {
            "process_running": ps_check["success"],
            "port_open": port_check["success"],
            "recent_errors": log_check["output"] if log_check["output"] else None
        },
        "issues": issues
    }

def check_qfield_worker():
    """Check QField worker container"""
    # Check if container is running
    container_check = run_cmd("docker ps --filter 'name=qfieldcloud-worker' --format '{{.Status}}'")

    # Check worker logs for errors
    log_check = run_cmd("docker logs qfieldcloud-worker --tail 50 --since 5m 2>&1 | grep -iE '(error|fail|exception)' | tail -3")

    # Check for stuck jobs
    stuck_jobs = run_cmd("""
        docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "
            SELECT COUNT(*) FROM core_job
            WHERE status IN ('pending', 'queued')
            AND created_at < NOW() - INTERVAL '10 minutes';"
    """)

    status = "healthy" if container_check["success"] and "Up" in container_check["output"] else "down"

    issues = []
    if not container_check["success"] or "Up" not in container_check["output"]:
        issues.append("Container not running")
    if log_check["output"]:
        issues.append(f"Recent errors: {log_check['output'][:100]}")
    if stuck_jobs["success"] and stuck_jobs["output"].strip() and int(stuck_jobs["output"].strip()) > 0:
        issues.append(f"{stuck_jobs['output'].strip()} stuck jobs (>10 min old)")

    return {
        "service": "QField Worker",
        "status": status,
        "details": {
            "container_status": container_check["output"] if container_check["success"] else "Not running",
            "stuck_jobs": int(stuck_jobs["output"].strip()) if stuck_jobs["success"] and stuck_jobs["output"].strip() else 0,
            "recent_errors": log_check["output"] if log_check["output"] else None
        },
        "issues": issues
    }

def check_cloudflared():
    """Check Cloudflared tunnel"""
    # Check if process running
    ps_check = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep \"[c]loudflared\"'")

    # Check logs
    log_check = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'tail -20 /tmp/cloudflared.log 2>/dev/null | grep -iE \"(error|fail|registered)\" | tail -3'")

    status = "healthy" if ps_check["success"] else "down"

    issues = []
    if not ps_check["success"]:
        issues.append("Cloudflared not running")
    if log_check["output"] and "error" in log_check["output"].lower():
        issues.append(f"Tunnel errors: {log_check['output'][:100]}")

    return {
        "service": "Cloudflared Tunnel",
        "status": status,
        "details": {
            "process_running": ps_check["success"],
            "recent_logs": log_check["output"] if log_check["output"] else None
        },
        "issues": issues
    }

def check_disk_space():
    """Check disk space on both servers"""
    # Local disk
    local_disk = run_cmd("df -h / | tail -1 | awk '{print $5}'")

    # VF server disk - the script returns JSON, so extract the actual output
    vf_disk_raw = run_cmd("VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'df -h / | tail -1 | awk \"{print \\$5}\"'")

    # Parse VF server response (it returns JSON)
    try:
        vf_result = json.loads(vf_disk_raw["output"])
        vf_disk_output = vf_result.get("output", "0%").strip()
    except:
        vf_disk_output = vf_disk_raw["output"].strip()

    local_usage = int(local_disk["output"].strip().strip('%')) if local_disk["success"] and local_disk["output"] else 0
    vf_usage = int(vf_disk_output.strip('%')) if vf_disk_output else 0

    status = "healthy"
    issues = []

    if local_usage > 85:
        status = "warning"
        issues.append(f"Local disk at {local_usage}%")
    if vf_usage > 85:
        status = "warning"
        issues.append(f"VF server disk at {vf_usage}%")

    return {
        "service": "Disk Space",
        "status": status,
        "details": {
            "local": f"{local_usage}%",
            "vf_server": f"{vf_usage}%"
        },
        "issues": issues
    }

def main():
    """Run all health checks"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": []
    }

    # Run all checks
    checks = [
        check_vf_server(),
        check_qfield_worker(),
        check_cloudflared(),
        check_disk_space()
    ]

    # Determine overall status
    has_down = any(c["status"] == "down" for c in checks)
    has_warning = any(c["status"] == "warning" for c in checks)

    if has_down:
        report["overall_status"] = "critical"
    elif has_warning:
        report["overall_status"] = "warning"

    report["checks"] = checks
    report["total_issues"] = sum(len(c["issues"]) for c in checks)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
