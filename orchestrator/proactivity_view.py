#!/usr/bin/env python3
"""
Proactivity View CLI - Interactive Task Queue Management

View, filter, approve, and dismiss proactive tasks discovered by git-watcher.
Provides user interface for the proactive agent system.

Usage:
    ./venv/bin/python3 orchestrator/proactivity_view.py
    /proactive  # Via slash command
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.confidence import ProactivityQueue
from typing import List, Dict, Any


class ProactivityView:
    """Interactive CLI for managing proactive task queue"""

    def __init__(self):
        self.queue = ProactivityQueue()

        # Colors
        self.HEADER = '\033[95m'
        self.BLUE = '\033[94m'
        self.CYAN = '\033[96m'
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.RED = '\033[91m'
        self.END = '\033[0m'
        self.BOLD = '\033[1m'

    def run(self):
        """Main interactive loop"""
        while True:
            self._show_queue_summary()
            self._show_menu()

            choice = input(f"\n{self.CYAN}Your choice:{self.END} ").strip().lower()

            if choice == 'q':
                print(f"\n{self.GREEN}✓ Exiting proactivity view{self.END}")
                break
            elif choice == 'h':
                self._show_high_confidence_tasks()
            elif choice == 'm':
                self._show_medium_confidence_tasks()
            elif choice == 'l':
                self._show_low_confidence_tasks()
            elif choice == 'a':
                self._show_all_tasks()
            elif choice == 'aa':
                self._approve_all_high()
            elif choice == 'r':
                self._review_one_by_one()
            elif choice == 'd':
                self._dismiss_low()
            elif choice == 'c':
                self._clear_queue()
            elif choice == 's':
                self._search_tasks()
            else:
                print(f"{self.RED}Invalid choice. Try again.{self.END}")

    def _show_queue_summary(self):
        """Display queue summary statistics"""
        result = self.queue.get_tasks(filter_confidence="all", limit=10000)
        tasks = result["tasks"]

        high = len([t for t in tasks if t["confidence"] == "high"])
        medium = len([t for t in tasks if t["confidence"] == "medium"])
        low = len([t for t in tasks if t["confidence"] == "low"])

        print(f"\n{self.HEADER}{'=' * 70}{self.END}")
        print(f"{self.HEADER}{self.BOLD}Proactive Task Queue{self.END}")
        print(f"{self.HEADER}{'=' * 70}{self.END}\n")

        print(f"{self.GREEN}[HIGH CONFIDENCE]{self.END} {high} tasks  ", end="")
        print(f"{self.YELLOW}[MEDIUM CONFIDENCE]{self.END} {medium} tasks  ", end="")
        print(f"{self.RED}[LOW CONFIDENCE]{self.END} {low} tasks")
        print(f"\n{self.BLUE}Total: {result['total_tasks']} tasks{self.END}")

    def _show_menu(self):
        """Display interactive menu"""
        print(f"\n{self.CYAN}Options:{self.END}")
        print(f"  {self.BOLD}[h]{self.END} Show high confidence tasks")
        print(f"  {self.BOLD}[m]{self.END} Show medium confidence tasks")
        print(f"  {self.BOLD}[l]{self.END} Show low confidence tasks")
        print(f"  {self.BOLD}[a]{self.END} Show all tasks")
        print(f"  {self.BOLD}[aa]{self.END} Approve all high confidence tasks")
        print(f"  {self.BOLD}[r]{self.END} Review tasks one-by-one")
        print(f"  {self.BOLD}[d]{self.END} Dismiss all low confidence tasks")
        print(f"  {self.BOLD}[c]{self.END} Clear entire queue")
        print(f"  {self.BOLD}[s]{self.END} Search tasks")
        print(f"  {self.BOLD}[q]{self.END} Quit")

    def _show_high_confidence_tasks(self):
        """Show high confidence tasks"""
        self._show_tasks_by_confidence("high", self.GREEN)

    def _show_medium_confidence_tasks(self):
        """Show medium confidence tasks"""
        self._show_tasks_by_confidence("medium", self.YELLOW)

    def _show_low_confidence_tasks(self):
        """Show low confidence tasks"""
        self._show_tasks_by_confidence("low", self.RED)

    def _show_all_tasks(self):
        """Show all tasks"""
        result = self.queue.get_tasks(filter_confidence="all", limit=100)
        self._display_tasks(result["tasks"], "All Tasks")

    def _show_tasks_by_confidence(self, confidence: str, color: str):
        """Show tasks filtered by confidence level"""
        result = self.queue.get_tasks(filter_confidence=confidence, limit=100)
        title = f"{confidence.capitalize()} Confidence Tasks"
        self._display_tasks(result["tasks"], title, color)

    def _display_tasks(self, tasks: List[Dict[str, Any]], title: str, color: str = None):
        """Display list of tasks"""
        if not color:
            color = self.BLUE

        print(f"\n{color}{'─' * 70}{self.END}")
        print(f"{color}{self.BOLD}{title} ({len(tasks)}){self.END}")
        print(f"{color}{'─' * 70}{self.END}\n")

        if not tasks:
            print(f"{self.YELLOW}  No tasks found.{self.END}")
            return

        for i, task in enumerate(tasks, 1):
            confidence_color = {
                "high": self.GREEN,
                "medium": self.YELLOW,
                "low": self.RED
            }.get(task["confidence"], self.BLUE)

            print(f"{self.BOLD}{i}.{self.END} [{confidence_color}{task['confidence'].upper()}{self.END}] "
                  f"{task['description']}")
            print(f"   {self.CYAN}File:{self.END} {task['file']}:{task.get('line', '?')}")
            print(f"   {self.CYAN}Type:{self.END} {task['type']}")
            print(f"   {self.CYAN}Effort:{self.END} ~{task['estimated_effort']} min  "
                  f"{self.CYAN}Risk:{self.END} {task['risk_level']}")
            print(f"   {self.CYAN}Auto-fix:{self.END} {'✓ Yes' if task['auto_fixable'] else '✗ No'}")
            print(f"   {self.CYAN}Reasoning:{self.END} {task['reasoning']}")
            print(f"   {self.CYAN}ID:{self.END} {task['id']}\n")

    def _approve_all_high(self):
        """Approve all high confidence tasks"""
        result = self.queue.get_tasks(filter_confidence="high", limit=1000)
        high_tasks = result["tasks"]

        if not high_tasks:
            print(f"{self.YELLOW}No high confidence tasks to approve.{self.END}")
            return

        print(f"\n{self.GREEN}Approving {len(high_tasks)} high confidence tasks...{self.END}")

        approved = 0
        for task in high_tasks:
            if task.get("auto_fixable"):
                # Mark as approved (in real implementation, this would trigger auto-fix)
                self.queue.update_task(task["id"], {"status": "approved"})
                approved += 1
                print(f"  ✓ Approved: {task['id']} - {task['description']}")
            else:
                print(f"  ⚠ Skipped (not auto-fixable): {task['id']}")

        print(f"\n{self.GREEN}✓ Approved {approved} tasks{self.END}")

    def _review_one_by_one(self):
        """Review tasks one by one with approve/skip/dismiss options"""
        result = self.queue.get_tasks(filter_confidence="all", sort_by="confidence", limit=100)
        tasks = result["tasks"]

        if not tasks:
            print(f"{self.YELLOW}No tasks to review.{self.END}")
            return

        for i, task in enumerate(tasks, 1):
            print(f"\n{self.HEADER}{'─' * 70}{self.END}")
            print(f"{self.BOLD}Task {i}/{len(tasks)}{self.END}")
            print(f"{self.HEADER}{'─' * 70}{self.END}\n")

            self._display_tasks([task], "Current Task")

            action = input(f"{self.CYAN}[a]pprove, [s]kip, [d]ismiss, [q]uit:{self.END} ").strip().lower()

            if action == 'a':
                self.queue.update_task(task["id"], {"status": "approved"})
                print(f"{self.GREEN}✓ Approved{self.END}")
            elif action == 'd':
                self.queue.remove_task(task["id"])
                print(f"{self.RED}✓ Dismissed{self.END}")
            elif action == 'q':
                break
            # 's' or anything else = skip

    def _dismiss_low(self):
        """Dismiss all low confidence tasks"""
        result = self.queue.get_tasks(filter_confidence="low", limit=1000)
        low_tasks = result["tasks"]

        if not low_tasks:
            print(f"{self.YELLOW}No low confidence tasks to dismiss.{self.END}")
            return

        confirm = input(f"{self.RED}Dismiss {len(low_tasks)} low confidence tasks? (y/n):{self.END} ")
        if confirm.lower() != 'y':
            print(f"{self.YELLOW}Cancelled.{self.END}")
            return

        for task in low_tasks:
            self.queue.remove_task(task["id"])

        print(f"{self.GREEN}✓ Dismissed {len(low_tasks)} tasks{self.END}")

    def _clear_queue(self):
        """Clear entire queue"""
        result = self.queue.get_tasks(filter_confidence="all", limit=10000)
        total = result["total_tasks"]

        if total == 0:
            print(f"{self.YELLOW}Queue already empty.{self.END}")
            return

        confirm = input(f"{self.RED}Clear ALL {total} tasks? This cannot be undone! (yes/no):{self.END} ")
        if confirm.lower() != 'yes':
            print(f"{self.YELLOW}Cancelled.{self.END}")
            return

        for task in result["tasks"]:
            self.queue.remove_task(task["id"])

        print(f"{self.GREEN}✓ Cleared {total} tasks{self.END}")

    def _search_tasks(self):
        """Search tasks by keyword"""
        keyword = input(f"{self.CYAN}Search keyword:{self.END} ").strip().lower()

        if not keyword:
            return

        result = self.queue.get_tasks(filter_confidence="all", limit=10000)
        matches = [
            task for task in result["tasks"]
            if keyword in task["description"].lower() or
               keyword in task["file"].lower() or
               keyword in task["type"].lower()
        ]

        self._display_tasks(matches, f"Search Results for '{keyword}'")


def main():
    """Entry point"""
    view = ProactivityView()

    try:
        view.run()
    except KeyboardInterrupt:
        print(f"\n\n{view.GREEN}✓ Exiting proactivity view{view.END}")
    except Exception as e:
        print(f"\n{view.RED}Error: {e}{view.END}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
