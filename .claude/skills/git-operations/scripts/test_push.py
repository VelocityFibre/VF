#!/usr/bin/env python3
"""Test push logic without actual push"""
import subprocess
import json

# Check commits to push
ahead_behind = subprocess.run(
    ['git', 'rev-list', '--count', '--left-right', 'HEAD...origin/main'],
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
).stdout.strip()

if ahead_behind:
    ahead, behind = ahead_behind.split('\t')
    print(json.dumps({
        'commits_to_push': int(ahead),
        'commits_behind': int(behind),
        'ready_to_push': True,
        'message': f'Would push {ahead} commits to origin/main'
    }, indent=2))
else:
    print(json.dumps({'ready_to_push': False, 'message': 'No upstream configured'}, indent=2))