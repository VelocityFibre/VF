"""
Database synchronization workflow using Inngest

This module provides a durable, scheduled workflow for syncing
data from Neon PostgreSQL to Convex backend.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inngest import Inngest, Function, TriggerCron, TriggerEvent
from client import inngest_client, Events, InngestConfig

# Import existing sync functionality
try:
    from sync_neon_to_convex import SyncNeonToConvex
except ImportError:
    print("Warning: sync_neon_to_convex module not found. Some functions will be mocked.")
    SyncNeonToConvex = None

@inngest_client.create_function(
    fn_id="sync-neon-to-convex",
    trigger=TriggerCron(cron="0 */6 * * *"),  # Every 6 hours
    concurrency=[{
        "limit": InngestConfig.DB_SYNC_CONCURRENCY,
        "scope": "fn"  # Function-level concurrency
    }],
    retries=InngestConfig.DEFAULT_RETRIES
)
async def sync_databases(ctx, step):
    """
    Sync data from Neon PostgreSQL to Convex backend.

    This function runs every 6 hours and ensures data consistency
    between our primary database (Neon) and operational backend (Convex).

    Steps:
    1. Fetch data from Neon
    2. Transform for Convex format
    3. Push to Convex in batches
    4. Log sync results
    """

    # Step 1: Initialize sync
    sync_started = await step.run(
        "initialize-sync",
        lambda: {
            "timestamp": datetime.utcnow().isoformat(),
            "sync_id": ctx.event.id if hasattr(ctx.event, 'id') else 'manual',
            "status": "started"
        }
    )

    # Step 2: Create sync instance
    syncer = await step.run(
        "create-syncer",
        lambda: _create_syncer()
    )

    if not syncer:
        await step.run(
            "log-error",
            lambda: _log_sync_error("Failed to initialize syncer - check database connections")
        )
        raise Exception("Failed to initialize database syncer")

    # Step 3: Sync contractors
    contractors_result = await step.run(
        "sync-contractors",
        lambda: _sync_table(syncer, "contractors"),
        retry={"attempts": 3, "delay": "30s"}
    )

    # Step 4: Sync projects
    projects_result = await step.run(
        "sync-projects",
        lambda: _sync_table(syncer, "projects"),
        retry={"attempts": 3, "delay": "30s"}
    )

    # Step 5: Sync tasks
    tasks_result = await step.run(
        "sync-tasks",
        lambda: _sync_table(syncer, "tasks"),
        retry={"attempts": 3, "delay": "30s"}
    )

    # Step 6: Sync BOQs (if applicable)
    boqs_result = await step.run(
        "sync-boqs",
        lambda: _sync_table(syncer, "boqs"),
        retry={"attempts": 3, "delay": "30s"}
    )

    # Step 7: Log sync results
    summary = await step.run(
        "log-summary",
        lambda: _create_sync_summary({
            "contractors": contractors_result,
            "projects": projects_result,
            "tasks": tasks_result,
            "boqs": boqs_result
        })
    )

    # Step 8: Send notification (optional)
    if os.getenv("ENABLE_SYNC_NOTIFICATIONS") == "true":
        await step.send_event(
            "notify-sync-complete",
            {
                "name": Events.DB_SYNC_COMPLETED,
                "data": summary
            }
        )

    return summary

@inngest_client.create_function(
    fn_id="sync-single-table",
    trigger=TriggerEvent(event=Events.DB_SYNC_SCHEDULED),
    retries=3
)
async def sync_single_table(ctx, step):
    """
    Sync a specific table from Neon to Convex.

    This can be triggered manually for specific tables.
    """
    table_name = ctx.event.data.get("table")

    if not table_name:
        raise ValueError("Table name is required")

    # Initialize syncer
    syncer = await step.run(
        "create-syncer",
        lambda: _create_syncer()
    )

    # Sync the specified table
    result = await step.run(
        f"sync-{table_name}",
        lambda: _sync_table(syncer, table_name),
        retry={"attempts": 5, "delay": "exponential"}
    )

    return result

# Helper functions
def _create_syncer():
    """Create and initialize the sync instance."""
    if SyncNeonToConvex:
        try:
            return SyncNeonToConvex()
        except Exception as e:
            print(f"Failed to create syncer: {e}")
            return None
    else:
        # Mock implementation for testing
        return {"mock": True}

def _sync_table(syncer, table_name: str) -> Dict[str, Any]:
    """Sync a specific table."""
    if isinstance(syncer, dict) and syncer.get("mock"):
        # Mock implementation
        return {
            "table": table_name,
            "records_synced": 0,
            "status": "mocked",
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        # Use the actual sync method
        if hasattr(syncer, f"sync_{table_name}"):
            method = getattr(syncer, f"sync_{table_name}")
            result = method()
            return {
                "table": table_name,
                "records_synced": result.get("count", 0),
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Generic sync method
            return {
                "table": table_name,
                "records_synced": 0,
                "status": "no_sync_method",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "table": table_name,
            "records_synced": 0,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def _create_sync_summary(results: Dict[str, Dict]) -> Dict[str, Any]:
    """Create a summary of sync results."""
    total_records = sum(r.get("records_synced", 0) for r in results.values())
    failed_tables = [k for k, v in results.items() if v.get("status") != "success"]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "tables_synced": len(results),
        "total_records": total_records,
        "failed_tables": failed_tables,
        "status": "completed" if not failed_tables else "partial",
        "details": results
    }

def _log_sync_error(error_message: str):
    """Log sync errors."""
    error_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_message,
        "severity": "error"
    }
    print(f"[DB SYNC ERROR] {json.dumps(error_log)}")
    return error_log

# Export functions for registration
database_sync_functions = [
    sync_databases,
    sync_single_table
]