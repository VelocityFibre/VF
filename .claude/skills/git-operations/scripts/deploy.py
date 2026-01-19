#!/usr/bin/env python3
"""Complete deployment workflow"""
import subprocess
import json
import sys
import os

def deploy(message):
    """Full deployment: test, commit, push, deploy to VPS"""
    result = {'steps': []}

    # Configuration
    VPS_HOST = os.getenv('VPS_HOST', '72.60.17.245')
    VPS_USER = os.getenv('VPS_USER', 'louisdup')
    VPS_PATH = os.getenv('VPS_PATH', '/home/louisdup/agents')

    # Step 1: Run tests
    test_step = {'name': 'tests', 'status': 'running'}
    result['steps'].append(test_step)

    test_result = subprocess.run(
        ['./venv/bin/pytest', 'tests/', '-q'],
        capture_output=True, text=True
    )

    if test_result.returncode != 0:
        test_step['status'] = 'failed'
        test_step['error'] = 'Tests failed. Fix them before deploying.'
        result['success'] = False
        return result

    test_step['status'] = 'completed'

    # Step 2: Commit changes
    commit_step = {'name': 'commit', 'status': 'running'}
    result['steps'].append(commit_step)

    # Add all changes
    subprocess.run(['git', 'add', '-A'])

    # Create commit
    commit_result = subprocess.run(
        ['git', 'commit', '-m', message],
        capture_output=True, text=True
    )

    if 'nothing to commit' in commit_result.stdout:
        commit_step['status'] = 'skipped'
        commit_step['note'] = 'No changes to commit'
    else:
        commit_step['status'] = 'completed'
        # Get commit hash
        commit_hash = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True
        ).stdout.strip()[:8]
        commit_step['commit'] = commit_hash

    # Step 3: Push to GitHub
    push_step = {'name': 'push', 'status': 'running'}
    result['steps'].append(push_step)

    push_result = subprocess.run(
        ['git', 'push', 'origin', 'main'],
        capture_output=True, text=True, timeout=60
    )

    if push_result.returncode != 0:
        push_step['status'] = 'failed'
        push_step['error'] = push_result.stderr
        result['success'] = False
        return result

    push_step['status'] = 'completed'

    # Step 4: Deploy to VPS
    deploy_step = {'name': 'vps_deploy', 'status': 'running'}
    result['steps'].append(deploy_step)

    ssh_command = f"""
        cd {VPS_PATH} &&
        git pull origin main &&
        source venv/bin/activate &&
        pip install -r requirements.txt --quiet &&
        sudo systemctl restart fibreflow-api
    """

    vps_result = subprocess.run(
        ['ssh', f'{VPS_USER}@{VPS_HOST}', ssh_command],
        capture_output=True, text=True, timeout=120
    )

    if vps_result.returncode != 0:
        deploy_step['status'] = 'failed'
        deploy_step['error'] = vps_result.stderr
        result['success'] = False
        return result

    deploy_step['status'] = 'completed'

    # Step 5: Verify deployment
    verify_step = {'name': 'verify', 'status': 'running'}
    result['steps'].append(verify_step)

    verify_result = subprocess.run(
        ['curl', '-s', f'http://{VPS_HOST}/health'],
        capture_output=True, text=True, timeout=10
    )

    if verify_result.returncode == 0:
        verify_step['status'] = 'completed'
        verify_step['health'] = 'API responding'
    else:
        verify_step['status'] = 'warning'
        verify_step['note'] = 'Health check failed - service may still be starting'

    result['success'] = True
    result['message'] = f'Successfully deployed: {message}'
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Please provide deployment message'}))
        sys.exit(1)

    message = ' '.join(sys.argv[1:])
    result = deploy(message)
    print(json.dumps(result, indent=2))