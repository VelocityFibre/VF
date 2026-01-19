# Proactive Task Queue Viewer

View and manage proactive tasks discovered by the git-watcher agent.

## Usage

```bash
/proactive
```

## Description

Interactive CLI for the FibreFlow Proactive Agent System. Shows tasks discovered by autonomous repository scanning:

- **High Confidence**: Trivial fixes, auto-fixable (unused imports, missing docstrings)
- **Medium Confidence**: Requires review (performance optimizations, missing error handling)
- **Low Confidence**: High risk, careful review needed (security issues, architecture changes)

## Features

- Filter tasks by confidence level
- Approve/dismiss tasks
- Search by keyword
- Auto-approve high-confidence tasks
- Review one-by-one with approve/skip/dismiss

## Task Discovery

Tasks are automatically discovered by:
- Git commit analysis (via hooks)
- Manual repository scans
- Continuous file watching (if daemon running)

## Examples

```bash
# View all tasks
/proactive
# Then choose [a] for all tasks

# Quick approve high-confidence
/proactive
# Then choose [aa] to approve all high

# Review carefully
/proactive
# Then choose [r] for one-by-one review
```

## Implementation

Run the proactivity view CLI:

```bash
./venv/bin/python3 orchestrator/proactivity_view.py
```
