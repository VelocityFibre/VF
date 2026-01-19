#!/usr/bin/env python3
"""Get repository status"""
import subprocess
import json

def get_status():
    """Get comprehensive git status"""
    result = {}

    # Get branch info
    branch = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True, text=True
    ).stdout.strip()
    result['branch'] = branch

    # Get status
    status = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True
    ).stdout

    # Parse status
    modified = []
    untracked = []
    staged = []

    for line in status.split('\n'):
        if not line:
            continue
        status_code = line[:2]
        file_path = line[3:]

        if '??' in status_code:
            untracked.append(file_path)
        elif 'M' in status_code[1]:
            modified.append(file_path)
        if status_code[0] != ' ' and status_code[0] != '?':
            staged.append(file_path)

    result['modified'] = modified
    result['untracked'] = untracked
    result['staged'] = staged

    # Check if ahead/behind
    upstream = subprocess.run(
        ['git', 'rev-list', '--count', '--left-right', 'HEAD...@{upstream}'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    ).stdout.strip()

    if upstream:
        ahead, behind = upstream.split('\t')
        result['ahead'] = int(ahead)
        result['behind'] = int(behind)
    else:
        result['ahead'] = 0
        result['behind'] = 0

    # Get last commit
    last_commit = subprocess.run(
        ['git', 'log', '-1', '--oneline'],
        capture_output=True, text=True
    ).stdout.strip()
    result['last_commit'] = last_commit

    return result

if __name__ == "__main__":
    result = get_status()
    print(json.dumps(result, indent=2))