#!/usr/bin/env python3
"""
Work Log API - Serves git-based work logs as JSON for the web UI
Can be run standalone or integrated into existing FastAPI app
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Work Log API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the git repository (adjust if needed)
REPO_PATH = Path(__file__).parent.parent

def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git"] + cmd,
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_module_from_files(files: List[str]) -> str:
    """Determine module from changed files."""
    files_str = " ".join(files)

    if "agents/neon" in files_str:
        return "NEON-AGENT"
    elif "agents/convex" in files_str:
        return "CONVEX-AGENT"
    elif "agents/vps-monitor" in files_str:
        return "VPS-MONITOR"
    elif ".claude/skills/vf-server" in files_str:
        return "VF-SERVER"
    elif ".claude/skills/wa-monitor" in files_str:
        return "WA-MONITOR"
    elif ".claude/skills/database" in files_str:
        return "DATABASE"
    elif "qfield" in files_str.lower():
        return "QFIELD"
    elif "harness/" in files_str:
        return "HARNESS"
    elif "orchestrator/" in files_str:
        return "ORCHESTRATOR"
    elif "convex/" in files_str:
        return "CONVEX-BACKEND"
    elif "docs/" in files_str:
        return "DOCS"
    elif "tests/" in files_str:
        return "TESTS"
    elif "deployment/" in files_str or "deploy/" in files_str:
        return "DEPLOYMENT"
    elif ".claude/" in files_str:
        return "CLAUDE-CONFIG"
    else:
        return "CORE"

@app.get("/api/work-log")
async def get_work_log(days: int = Query(default=7, ge=1, le=365)):
    """Get work log for the specified number of days."""

    try:
        # Get dates with commits
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        dates_output = run_git_command([
            "log", f"--since={since_date}",
            "--pretty=format:%ad", "--date=short"
        ])

        if not dates_output:
            return JSONResponse(content={
                "days": days,
                "generated": datetime.now().isoformat(),
                "entries": [],
                "summary": {"commits": 0, "authors": 0, "files": 0}
            })

        dates = sorted(set(dates_output.split("\n")), reverse=True)

        entries = []
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        for date in dates:
            if not date:
                continue

            # Determine label
            label = ""
            if date == today:
                label = "Today"
            elif date == yesterday:
                label = "Yesterday"

            # Get commits for this date
            commits_output = run_git_command([
                "log", f"--since={date} 00:00:00", f"--until={date} 23:59:59",
                "--pretty=format:%H|%ad|%an|%s", "--date=format:%H:%M"
            ])

            if not commits_output:
                continue

            modules = {}
            for commit_line in commits_output.split("\n"):
                if not commit_line:
                    continue

                parts = commit_line.split("|", 3)
                if len(parts) < 4:
                    continue

                hash, time, author, message = parts

                # Get files changed
                files_output = run_git_command([
                    "diff-tree", "--no-commit-id", "--name-only", "-r", hash
                ])
                files = files_output.split("\n") if files_output else []

                # Determine module
                module = get_module_from_files(files)

                # Add to module
                if module not in modules:
                    modules[module] = []

                modules[module].append({
                    "time": time,
                    "author": author,
                    "message": message
                })

            if modules:
                entries.append({
                    "date": date,
                    "label": label,
                    "modules": modules
                })

        # Get summary stats
        total_commits = int(run_git_command([
            "rev-list", "--count", f"--since={since_date}", "HEAD"
        ]) or "0")

        authors_output = run_git_command([
            "log", f"--since={since_date}", "--pretty=format:%an"
        ])
        total_authors = len(set(authors_output.split("\n"))) if authors_output else 0

        files_output = run_git_command([
            "log", f"--since={since_date}", "--name-only", "--pretty=format:"
        ])
        total_files = len(set(f for f in files_output.split("\n") if f)) if files_output else 0

        return JSONResponse(content={
            "days": days,
            "generated": datetime.now().isoformat(),
            "entries": entries,
            "summary": {
                "commits": total_commits,
                "authors": total_authors,
                "files": total_files
            }
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/work-log")
async def serve_work_log_ui():
    """Serve the work log HTML UI."""
    html_path = REPO_PATH / "public" / "work-log.html"
    if html_path.exists():
        return FileResponse(html_path)
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "work-log.html not found"}
        )

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Work Log API",
        "endpoints": {
            "/work-log": "Web UI for viewing work logs",
            "/api/work-log": "JSON API for work log data"
        },
        "usage": "Visit /work-log to view the UI"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Work Log API server...")
    print("Visit http://localhost:8001/work-log to view the UI")
    uvicorn.run(app, host="0.0.0.0", port=8001)