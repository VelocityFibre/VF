#!/usr/bin/env python3
"""
Simple Web Interface for Staging Deployment
Run this locally: python3 staging-deploy-web.py
Access at: http://localhost:8888
"""

import subprocess
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import html

class DeployHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Get last deployment info
        try:
            result = subprocess.run(
                ['ssh', '-i', '~/.ssh/vf_server_key', 'hein@100.96.203.105', 'deployment-monitor last'],
                capture_output=True, text=True, timeout=5
            )
            last_deploy = html.escape(result.stdout) if result.returncode == 0 else "Unable to fetch"
        except:
            last_deploy = "Connection failed"

        html_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Staging Deployment</title>
            <style>
                body {{
                    font-family: -apple-system, system-ui, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 2px solid #007AFF;
                    padding-bottom: 10px;
                }}
                button {{
                    background: #007AFF;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 16px;
                    cursor: pointer;
                    margin: 5px;
                }}
                button:hover {{
                    background: #0051D5;
                }}
                button.danger {{
                    background: #FF3B30;
                }}
                button.danger:hover {{
                    background: #D70015;
                }}
                .status {{
                    background: #f0f0f0;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                    font-family: monospace;
                    white-space: pre-wrap;
                }}
                .actions {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    margin: 20px 0;
                }}
                #result {{
                    margin-top: 20px;
                    padding: 15px;
                    border-radius: 4px;
                    display: none;
                }}
                .success {{
                    background: #D1F2EB;
                    color: #0A7E5C;
                }}
                .error {{
                    background: #FFEBE9;
                    color: #C41E3A;
                }}
                .loading {{
                    background: #FFF3CD;
                    color: #856404;
                }}
                input {{
                    padding: 10px;
                    font-size: 16px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-right: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Staging Deployment Control</h1>

                <div class="status">
                    <strong>Last Deployment:</strong>
{last_deploy}
                </div>

                <div class="actions">
                    <button onclick="deploy()">📦 Deploy Current Branch</button>
                    <button onclick="deployBranch()">🌿 Deploy Specific Branch</button>
                    <button onclick="checkStatus()">📊 Check Status</button>
                    <button class="danger" onclick="rollback()">⏮️ Rollback</button>
                </div>

                <div style="margin-top: 20px;">
                    <input type="text" id="branchName" placeholder="Branch name (optional)">
                    <button onclick="deployCustom()">Deploy This Branch</button>
                </div>

                <div id="result"></div>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

                <h3>Quick Links</h3>
                <ul>
                    <li><a href="https://vf.fibreflow.app" target="_blank">View Staging Site</a></li>
                    <li><a href="https://github.com/VelocityFibre/FF_Next.js" target="_blank">GitHub Repository</a></li>
                </ul>
            </div>

            <script>
                function showResult(message, type) {{
                    const result = document.getElementById('result');
                    result.className = type;
                    result.innerText = message;
                    result.style.display = 'block';
                }}

                async function runCommand(command) {{
                    showResult('⏳ Running command...', 'loading');
                    try {{
                        const response = await fetch('/deploy', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{command}})
                        }});
                        const data = await response.json();
                        if (data.success) {{
                            showResult('✅ ' + data.message, 'success');
                        }} else {{
                            showResult('❌ ' + data.message, 'error');
                        }}
                    }} catch (error) {{
                        showResult('❌ Error: ' + error, 'error');
                    }}
                }}

                function deploy() {{
                    runCommand('deploy');
                }}

                function deployBranch() {{
                    const branch = prompt('Enter branch name:');
                    if (branch) {{
                        runCommand('deploy-staging ' + branch);
                    }}
                }}

                function deployCustom() {{
                    const branch = document.getElementById('branchName').value;
                    if (branch) {{
                        runCommand('deploy-staging ' + branch);
                    }} else {{
                        runCommand('deploy');
                    }}
                }}

                function checkStatus() {{
                    runCommand('status');
                }}

                function rollback() {{
                    if (confirm('Are you sure you want to rollback to the previous deployment?')) {{
                        runCommand('rollback');
                    }}
                }}
            </script>
        </body>
        </html>
        """

        self.wfile.write(html_page.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        command = data.get('command', '')

        # Map commands to actual SSH commands
        commands = {
            'deploy': 'deploy',
            'status': 'deployment-monitor last',
            'rollback': 'cd /home/louis/apps/fibreflow && git checkout $(git branch -a | grep backup | tail -1 | xargs) && npm install && npm run build && echo "VeloBoss@2026" | sudo -S systemctl restart fibreflow.service'
        }

        # Handle deploy-staging with branch
        if command.startswith('deploy-staging '):
            ssh_command = command
        else:
            ssh_command = commands.get(command, command)

        try:
            result = subprocess.run(
                ['ssh', '-i', '~/.ssh/vf_server_key', 'hein@100.96.203.105', ssh_command],
                capture_output=True, text=True, timeout=120
            )

            response = {
                'success': result.returncode == 0,
                'message': result.stdout if result.returncode == 0 else result.stderr
            }
        except subprocess.TimeoutExpired:
            response = {'success': False, 'message': 'Command timed out'}
        except Exception as e:
            response = {'success': False, 'message': str(e)}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    print("🌐 Staging Deployment Web Interface")
    print("📍 Access at: http://localhost:8888")
    print("Press Ctrl+C to stop")

    server = HTTPServer(('localhost', 8888), DeployHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()