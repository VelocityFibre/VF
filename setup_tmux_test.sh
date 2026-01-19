#!/bin/bash

# TMUX Collaboration Test Setup Script
# Run this on VF Server (100.96.203.105) as velo user

echo "🚀 Setting up tmux collaboration test environment..."

# 1. Check/Install tmux
if ! command -v tmux &> /dev/null; then
    echo "📦 Installing tmux..."
    sudo apt-get update && sudo apt-get install -y tmux
else
    echo "✅ tmux is already installed ($(tmux -V))"
fi

# 2. Create test project directory
TEST_DIR="/home/velo/collab-test"
echo "📁 Creating test project at $TEST_DIR..."
mkdir -p $TEST_DIR
cd $TEST_DIR

# 3. Create a simple React test page
cat > $TEST_DIR/CollabTestPage.tsx << 'EOF'
import React, { useState, useEffect } from 'react';

/**
 * Collaborative Test Page
 * Louis and Hein will edit this together via tmux + Claude Code
 *
 * TODO Tasks for collaboration test:
 * 1. Louis: Add a counter feature
 * 2. Hein: Add a user input form
 * 3. Both: Style the components
 * 4. Both: Add data persistence
 */

export default function CollabTestPage() {
  const [message, setMessage] = useState("Welcome to tmux collaboration!");
  const [timestamp, setTimestamp] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimestamp(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui' }}>
      <h1>🚀 Collaborative Development Test</h1>
      <p style={{ fontSize: '18px', color: '#666' }}>
        Louis and Hein are working on this page together
      </p>

      <div style={{
        background: '#f0f0f0',
        padding: '20px',
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h2>{message}</h2>
        <p>Current time: {timestamp}</p>

        {/* Louis will add counter here */}
        <div id="louis-section" style={{
          border: '2px dashed #007bff',
          padding: '20px',
          marginTop: '20px'
        }}>
          <h3>Louis's Section</h3>
          <p>TODO: Add counter feature</p>
        </div>

        {/* Hein will add form here */}
        <div id="hein-section" style={{
          border: '2px dashed #28a745',
          padding: '20px',
          marginTop: '20px'
        }}>
          <h3>Hein's Section</h3>
          <p>TODO: Add user input form</p>
        </div>
      </div>

      <div style={{ marginTop: '30px', padding: '20px', background: '#fff3cd' }}>
        <h3>📝 Collaboration Notes:</h3>
        <ul>
          <li>Both developers see this file in real-time</li>
          <li>Changes are instantly visible to both</li>
          <li>Claude Code context is shared</li>
          <li>No git sync needed during development</li>
        </ul>
      </div>
    </div>
  );
}
EOF

# 4. Create a test plan file
cat > $TEST_DIR/COLLABORATION_TEST_PLAN.md << 'EOF'
# Tmux Collaboration Test Plan

## Objective
Test real-time collaborative development using tmux + Claude Code

## Test Scenarios

### Scenario 1: Simultaneous Editing
1. Louis opens the file in Claude Code
2. Hein joins the session
3. Both developers can see the same Claude conversation
4. Louis asks Claude to add a counter
5. Hein sees the changes in real-time

### Scenario 2: Shared Context
1. Louis creates a TodoWrite list in Claude
2. Hein can see and update the same todo list
3. Both can mark items as complete

### Scenario 3: Collaborative Debugging
1. Introduce a bug in the code
2. Both developers work together to fix it
3. Share the terminal output and error messages

## Success Criteria
- [ ] Both developers can see the same terminal
- [ ] Changes are visible in real-time
- [ ] No sync commands needed
- [ ] Claude context is shared
- [ ] Both can interact with Claude

## Commands to Remember
Inside tmux:
- `Ctrl-b d` - Detach (leave session running)
- `Ctrl-b [` - Scroll mode (use arrow keys, q to exit)
- `Ctrl-b c` - New window
- `Ctrl-b n` - Next window
- `Ctrl-b p` - Previous window
EOF

# 5. Create startup script
cat > $TEST_DIR/start_collab_session.sh << 'EOF'
#!/bin/bash

SESSION_NAME="collab-test"

# Check if session exists
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    echo "🚀 Creating new tmux session: $SESSION_NAME"
    tmux new-session -d -s $SESSION_NAME -c /home/velo/collab-test

    # Set up the windows
    tmux rename-window -t $SESSION_NAME:0 'Claude'
    tmux send-keys -t $SESSION_NAME:0 'echo "Ready for Claude Code. Type: claude" && echo ""' Enter

    # Create second window for git/monitoring
    tmux new-window -t $SESSION_NAME:1 -n 'Git/Monitor'
    tmux send-keys -t $SESSION_NAME:1 'git status' Enter

    echo "✅ Session created! Connect with: tmux attach -t $SESSION_NAME"
else
    echo "📌 Session already exists! Connect with: tmux attach -t $SESSION_NAME"
fi

echo ""
echo "Quick tmux reference:"
echo "  Ctrl-b d     - Detach from session"
echo "  Ctrl-b [     - Scroll mode (q to exit)"
echo "  Ctrl-b c     - Create new window"
echo "  Ctrl-b n/p   - Next/Previous window"
echo "  Ctrl-b 0-9   - Switch to window number"
EOF

chmod +x $TEST_DIR/start_collab_session.sh

# 6. Create connection instructions
cat > $TEST_DIR/CONNECT_INSTRUCTIONS.md << 'EOF'
# How to Connect to the Shared Session

## For Louis (First Developer)

1. SSH to VF Server:
```bash
ssh velo@100.96.203.105
# Password: 2025
```

2. Start the collaboration session:
```bash
cd /home/velo/collab-test
./start_collab_session.sh
tmux attach -t collab-test
```

3. Start Claude Code:
```bash
claude
# or if resuming: claude --res
```

4. Tell Claude about the test:
```
We're testing tmux collaboration. Please help us build the CollabTestPage.tsx file together.
Open the file at /home/velo/collab-test/CollabTestPage.tsx
```

## For Hein (Second Developer)

1. SSH to VF Server:
```bash
ssh velo@100.96.203.105
# Password: 2025
```

2. Join the existing session:
```bash
tmux attach -t collab-test
```

**IMPORTANT**: You'll immediately see exactly what Louis sees!

3. You can now:
- See the Claude conversation
- Type commands
- Interact with Claude
- Everything is shared in real-time

## What to Test

1. **Both talk to Claude**: Take turns asking Claude questions
2. **Edit the file together**: Have Claude modify different sections
3. **Use TodoWrite**: Create a shared todo list
4. **Debug together**: Introduce a bug and fix it collaboratively

## Ending the Session

When done testing:
- Detach (keep running): `Ctrl-b d`
- Kill session: `tmux kill-session -t collab-test`
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Test project created at: $TEST_DIR"
echo "📄 Files created:"
echo "   - CollabTestPage.tsx (React component to edit)"
echo "   - COLLABORATION_TEST_PLAN.md (test scenarios)"
echo "   - CONNECT_INSTRUCTIONS.md (how to connect)"
echo "   - start_collab_session.sh (launch script)"
echo ""
echo "Next steps:"
echo "1. Run: ./start_collab_session.sh"
echo "2. Connect: tmux attach -t collab-test"
echo "3. Start Claude: claude"
echo "4. Have Hein connect using the same tmux attach command"
echo ""
echo "You'll both see the SAME terminal in real-time! 🎉"