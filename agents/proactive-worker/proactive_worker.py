#!/usr/bin/env python3
"""
Proactive Background Worker

Continuously processes the proactivity queue:
- Monitors queue every 60 seconds
- Auto-fixes high-confidence tasks
- Respects developer work hours (optional)
- Creates git commits for fixes
- Logs all activity

Designed to run as a systemd service or standalone daemon.

Part of FibreFlow Proactive Agent System (Phase 2).
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.confidence import ProactivityQueue
from shared.auto_fixer import AutoFixer


class ProactiveWorker:
    """Background worker that continuously processes proactive tasks"""

    def __init__(
        self,
        queue_file: str = "shared/proactivity_queue.json",
        check_interval: int = 60,
        max_fixes_per_cycle: int = 5,
        work_hours_start: Optional[dt_time] = None,
        work_hours_end: Optional[dt_time] = None
    ):
        self.queue = ProactivityQueue(queue_file)
        self.fixer = AutoFixer()
        self.check_interval = check_interval
        self.max_fixes_per_cycle = max_fixes_per_cycle
        self.work_hours_start = work_hours_start
        self.work_hours_end = work_hours_end

        # Setup logging
        self.logger = self._setup_logging()

        # Statistics
        self.stats = {
            "cycles_run": 0,
            "total_fixes_attempted": 0,
            "total_fixes_successful": 0,
            "total_fixes_failed": 0,
            "last_run": None
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging to file and console"""
        logger = logging.Logger("proactive_worker", level=logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "proactive_worker.log")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def is_work_hours(self) -> bool:
        """Check if current time is within work hours"""
        if not self.work_hours_start or not self.work_hours_end:
            return True  # No work hours restriction

        now = datetime.now().time()
        return self.work_hours_start <= now <= self.work_hours_end

    def run_cycle(self) -> Dict[str, Any]:
        """
        Run one processing cycle.

        Returns:
            Statistics for this cycle
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting proactive worker cycle")

        # Check work hours
        if not self.is_work_hours():
            self.logger.info("Outside work hours, skipping cycle")
            return {
                "skipped": True,
                "reason": "outside_work_hours"
            }

        # Load queue
        queue_data = self.queue.load_queue()
        total_tasks = queue_data["total_tasks"]
        high_conf_count = queue_data.get("high_confidence", 0)

        self.logger.info(f"Queue status: {total_tasks} total, {high_conf_count} high-confidence")

        if total_tasks == 0:
            self.logger.info("Queue is empty, nothing to do")
            return {
                "tasks_found": 0,
                "fixes_attempted": 0
            }

        # Get high-confidence auto-fixable tasks
        result = self.queue.get_tasks(
            filter_confidence="high",
            sort_by="effort",  # Do quick fixes first
            limit=self.max_fixes_per_cycle
        )

        auto_fixable = [
            t for t in result["tasks"]
            if t.get("auto_fixable") and t.get("status") == "queued"
        ]

        self.logger.info(f"Found {len(auto_fixable)} auto-fixable tasks")

        if not auto_fixable:
            self.logger.info("No auto-fixable tasks available")
            return {
                "tasks_found": result["filtered_tasks"],
                "fixes_attempted": 0
            }

        # Execute fixes
        batch_result = self.fixer.batch_fix(
            auto_fixable,
            max_fixes=self.max_fixes_per_cycle,
            dry_run=False
        )

        # Update task statuses
        for fix_result in batch_result["results"]:
            task_id = fix_result["task_id"]
            if fix_result["result"]["success"]:
                # Mark as completed and remove from queue
                self.queue.remove_task(task_id)
                self.logger.info(f"✓ Fixed and removed: {task_id}")
            else:
                # Mark as failed
                self.queue.update_task(task_id, {"status": "failed"})
                self.logger.warning(f"✗ Failed: {task_id} - {fix_result['result'].get('error')}")

        # Update statistics
        self.stats["cycles_run"] += 1
        self.stats["total_fixes_attempted"] += batch_result["total_attempted"]
        self.stats["total_fixes_successful"] += batch_result["successful"]
        self.stats["total_fixes_failed"] += batch_result["failed"]
        self.stats["last_run"] = datetime.now().isoformat()

        self.logger.info(f"Cycle complete: {batch_result['successful']} successful, "
                         f"{batch_result['failed']} failed")
        self.logger.info("=" * 60)

        return {
            "tasks_found": len(auto_fixable),
            "fixes_attempted": batch_result["total_attempted"],
            "successful": batch_result["successful"],
            "failed": batch_result["failed"]
        }

    def run_forever(self):
        """Run worker continuously"""
        self.logger.info("🤖 Proactive Worker Starting")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Max fixes per cycle: {self.max_fixes_per_cycle}")

        if self.work_hours_start and self.work_hours_end:
            self.logger.info(f"Work hours: {self.work_hours_start} - {self.work_hours_end}")
        else:
            self.logger.info("Work hours: Always active (no restrictions)")

        try:
            while True:
                try:
                    self.run_cycle()
                except Exception as e:
                    self.logger.error(f"Error in cycle: {e}", exc_info=True)

                # Sleep until next cycle
                self.logger.info(f"Sleeping for {self.check_interval}s until next cycle\n")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("\n🛑 Worker stopped by user")
            self._save_stats()
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}", exc_info=True)
            self._save_stats()
            raise

    def run_once(self):
        """Run worker for one cycle (for testing)"""
        self.logger.info("🤖 Proactive Worker - Single Cycle Mode")
        result = self.run_cycle()
        self._save_stats()
        return result

    def _save_stats(self):
        """Save statistics to file"""
        stats_file = project_root / "logs" / "worker_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        self.logger.info(f"Statistics saved to {stats_file}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            **self.stats,
            "uptime": self._calculate_uptime()
        }

    def _calculate_uptime(self) -> str:
        """Calculate worker uptime"""
        if not self.stats["last_run"]:
            return "N/A"

        last_run = datetime.fromisoformat(self.stats["last_run"])
        uptime = datetime.now() - last_run
        return str(uptime)


def main():
    """Entry point for worker"""
    import argparse

    parser = argparse.ArgumentParser(description="FibreFlow Proactive Background Worker")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--max-fixes",
        type=int,
        default=5,
        help="Max fixes per cycle (default: 5)"
    )
    parser.add_argument(
        "--work-start",
        type=str,
        help="Work hours start time (HH:MM format, e.g., 09:00)"
    )
    parser.add_argument(
        "--work-end",
        type=str,
        help="Work hours end time (HH:MM format, e.g., 18:00)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    # Parse work hours
    work_start = None
    work_end = None
    if args.work_start and args.work_end:
        try:
            work_start = datetime.strptime(args.work_start, "%H:%M").time()
            work_end = datetime.strptime(args.work_end, "%H:%M").time()
        except ValueError:
            print("Error: Invalid time format. Use HH:MM (e.g., 09:00)")
            sys.exit(1)

    # Create worker
    worker = ProactiveWorker(
        check_interval=args.interval,
        max_fixes_per_cycle=args.max_fixes,
        work_hours_start=work_start,
        work_hours_end=work_end
    )

    # Run
    if args.once:
        result = worker.run_once()
        print(f"\nCycle result: {json.dumps(result, indent=2)}")
    else:
        worker.run_forever()


if __name__ == "__main__":
    main()
