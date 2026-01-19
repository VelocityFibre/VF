#!/usr/bin/env python3
"""Push to remote repository"""
import subprocess
import json
import sys

def push_to_remote(branch='main', remote='origin'):
    """Push current branch to remote"""
    result = {}

    try:
        # Check if there are commits to push
        ahead_behind = subprocess.run(
            ['git', 'rev-list', '--count', '--left-right', f'HEAD...{remote}/{branch}'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ).stdout.strip()

        if ahead_behind:
            ahead, behind = ahead_behind.split('\t')
            result['commits_to_push'] = int(ahead)
            result['commits_behind'] = int(behind)
        else:
            result['commits_to_push'] = 0
            result['commits_behind'] = 0

        if result['commits_to_push'] == 0:
            result['success'] = True
            result['message'] = 'Already up to date'
            return result

        # Push to remote
        push_result = subprocess.run(
            ['git', 'push', remote, branch],
            capture_output=True, text=True, timeout=120
        )

        if push_result.returncode == 0:
            result['success'] = True
            result['message'] = f'Pushed {result["commits_to_push"]} commits to {remote}/{branch}'
            result['output'] = push_result.stderr  # Git outputs to stderr
        else:
            result['success'] = False
            result['error'] = push_result.stderr

    except subprocess.TimeoutExpired:
        result['success'] = False
        result['error'] = 'Push timed out after 120 seconds'
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

    return result

if __name__ == "__main__":
    branch = sys.argv[1] if len(sys.argv) > 1 else 'main'
    remote = sys.argv[2] if len(sys.argv) > 2 else 'origin'

    result = push_to_remote(branch, remote)
    print(json.dumps(result, indent=2))