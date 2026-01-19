#!/usr/bin/env python3
"""Create a git commit"""
import subprocess
import json
import sys

def create_commit(message, add_all=False):
    """Create a commit with given message"""
    result = {}

    try:
        # Add files if requested
        if add_all:
            subprocess.run(['git', 'add', '-A'], check=True)
            result['added_all'] = True

        # Create commit
        commit_result = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True, text=True
        )

        if commit_result.returncode == 0:
            result['success'] = True
            result['output'] = commit_result.stdout

            # Get commit hash
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True
            ).stdout.strip()[:8]
            result['commit_hash'] = commit_hash
        else:
            result['success'] = False
            result['error'] = commit_result.stderr or commit_result.stdout

    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Please provide commit message'}))
        sys.exit(1)

    message = sys.argv[1]
    add_all = '--add-all' in sys.argv

    result = create_commit(message, add_all)
    print(json.dumps(result, indent=2))