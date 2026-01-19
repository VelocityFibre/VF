# Convex Database Agent - Complete Guide

## 🎯 Overview

The Convex Agent connects Claude AI with your Convex database, enabling natural language interactions with your company data. Users can query, analyze, and manage tasks using conversational AI.

## ✅ Setup Complete

Your Convex Agent is **ready to use**! The setup includes:

- ✅ Convex credentials configured in `.env`
- ✅ Connection to `https://quixotic-crow-802.convex.cloud`
- ✅ Agent tested and working
- ✅ All database tools configured

## 🚀 Quick Start

### Test the Connection

```bash
source venv/bin/activate
python test_convex.py
```

### Run Interactive Mode

```bash
python convex_examples.py
# Select option 4 for interactive chat
```

### Run Demos

```bash
python convex_agent.py
```

## 💬 Example Conversations

### Natural Language Queries

```python
from convex_agent import ConvexAgent

agent = ConvexAgent()

# Simple queries
agent.chat("How many tasks do we have?")
agent.chat("Show me all high-priority tasks")
agent.chat("What tasks are in progress?")

# Analysis
agent.chat("Give me a summary of our task status")
agent.chat("Which area needs the most attention?")

# Task management
agent.chat("Create a new task: 'Review API documentation' with high priority")
agent.chat("Mark task X as completed")
agent.chat("Search for tasks about 'authentication'")
```

## 🛠️ Available Tools

The agent has access to these Convex database operations:

### Task Management
- **list_tasks**: Get all tasks
- **add_task**: Create new tasks
- **get_task**: Get specific task by ID
- **update_task**: Modify existing tasks
- **delete_task**: Remove tasks
- **search_tasks**: Search by keyword
- **get_task_stats**: Get statistics

### Sync Operations
- **get_sync_stats**: Synchronization statistics
- **get_last_sync_time**: Last sync timestamp

## 📊 Use Cases

### 1. Daily Standup Assistant

```python
agent = ConvexAgent()

response = agent.chat(
    "Generate my daily standup report: "
    "What did I work on? What's in progress? Any blockers?"
)
print(response)
```

### 2. Task Analytics

```python
response = agent.chat(
    "Analyze our task distribution. "
    "How many tasks by priority? "
    "What percentage are completed?"
)
```

### 3. Project Management

```python
# Get overview
agent.chat("Show me all tasks related to the API project")

# Prioritization
agent.chat("What are the most urgent tasks right now?")

# Progress tracking
agent.chat("How much progress have we made this week?")
```

### 4. Smart Search

```python
agent.chat("Find all tasks mentioning 'authentication' or 'security'")
agent.chat("Show me stale tasks that haven't been updated")
```

### 5. Automated Reporting

```python
report = agent.chat(
    "Generate a comprehensive project status report including: "
    "1. Total tasks and breakdown by status "
    "2. High-priority items "
    "3. Completion rate "
    "4. Recommendations for what to focus on"
)
```

## 🎨 Customization

### Add Custom Tools

Edit `convex_agent.py` to add more Convex functions:

```python
def define_tools(self):
    return [
        # ... existing tools ...
        {
            "name": "get_project_details",
            "description": "Get details of a specific project",
            "input_schema": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "string"}
                },
                "required": ["projectId"]
            }
        }
    ]
```

Then implement in `execute_tool()`:

```python
def execute_tool(self, tool_name, tool_input):
    function_map = {
        # ... existing mappings ...
        "get_project_details": "projects/getProject"
    }
    # ... rest of implementation
```

### Change the Model

```python
# Use a more powerful model (if available)
agent = ConvexAgent(model="claude-3-opus-20240229")

# Or specify explicitly
agent = ConvexAgent(model="claude-3-haiku-20240307")  # Fast, default
```

### Custom Instructions

Add context to guide the agent's responses:

```python
system_prompt = (
    "You are a project management assistant. "
    "Be concise and action-oriented. "
    "Always prioritize high-priority tasks."
)

agent.chat(f"{system_prompt}\n\nWhat should I work on today?")
```

## 🔧 Architecture

### How It Works

```
User Input (Natural Language)
        ↓
Claude Agent (Reasoning)
        ↓
Tool Selection (Automatic)
        ↓
Convex API Call
        ↓
Database Query/Mutation
        ↓
Result Processing
        ↓
Natural Language Response
```

### Key Components

1. **ConvexClient**: Handles HTTP requests to Convex API
2. **ConvexAgent**: Claude agent with Convex tools
3. **Tool Definitions**: Describes available database operations
4. **Tool Execution**: Translates tool calls to Convex API calls

## 💡 Advanced Features

### Multi-Step Reasoning

The agent can chain multiple operations:

```python
agent.chat(
    "Find all high-priority tasks, "
    "tell me which ones are overdue, "
    "and suggest which to tackle first"
)
```

The agent will:
1. Call `list_tasks` to get all tasks
2. Call `get_task_stats` for additional context
3. Analyze the data
4. Provide recommendations

### Context Awareness

The agent maintains conversation context:

```python
agent.chat("Show me tasks for the API project")
agent.chat("Which of those are high priority?")  # Remembers "API project"
agent.chat("Create a task for the most urgent one")  # Still in context
```

### Intelligent Interpretation

The agent understands intent:

```python
# These all work:
agent.chat("How many tasks?")
agent.chat("Give me a task count")
agent.chat("What's our current task load?")
agent.chat("Tell me about our tasks")
```

## 🎯 Best Practices

### 1. Be Specific When Needed

```python
# Good
agent.chat("Show me high-priority tasks from the last week")

# Less specific (agent will ask or make assumptions)
agent.chat("Show me some tasks")
```

### 2. Use Context

```python
# Efficient - uses conversation context
agent.chat("Show me all tasks")
agent.chat("Filter those to high priority")
agent.chat("Mark the first one as completed")

# vs. repeating context each time
agent.chat("Show me all high-priority tasks and mark task X as completed")
```

### 3. Request Analysis

Let the agent help you understand your data:

```python
agent.chat(
    "Analyze our task completion rate and tell me if we're on track"
)
```

### 4. Reset When Switching Topics

```python
agent.reset_conversation()  # Clear context for new topic
```

## 🔍 Troubleshooting

### "Connection failed"

```bash
# Check Convex URL
echo $CONVEX_URL

# Test connection directly
curl https://quixotic-crow-802.convex.cloud/api/query

# Verify .env is loaded
python test_convex.py
```

### "Tool execution failed"

The function might not exist in your Convex deployment. Check:
- Function name matches Convex schema
- Function is deployed
- Auth permissions (if required)

### "Empty responses"

Your database might be empty. Add test data:

```python
agent.chat("Create a test task titled 'Sample Task' with high priority")
```

## 📚 Files Reference

- **`convex_agent.py`** - Main agent implementation
- **`convex_examples.py`** - Interactive examples and demos
- **`test_convex.py`** - Connection and setup tests
- **`.env`** - Convex credentials (gitignored)

## 🎬 Example Workflows

### Morning Routine

```python
agent = ConvexAgent()

# Get daily overview
agent.chat("What's on my plate today? Show tasks by priority")

# Get context
agent.chat("Any blockers or high-priority items I should know about?")

# Plan work
agent.chat("Based on priorities, what should I focus on first?")
```

### Weekly Review

```python
# Get statistics
agent.chat("Show me task statistics for this week")

# Analyze progress
agent.chat("Compare this week's completion rate to our average")

# Plan ahead
agent.chat("What tasks should we prioritize next week?")
```

### Team Collaboration

```python
# Status for team meeting
report = agent.chat(
    "Generate a team status report: "
    "completed tasks, in-progress tasks, and upcoming priorities"
)

# Save or share the report
with open("team_status.txt", "w") as f:
    f.write(report)
```

## 🚀 Next Steps

1. **Try Interactive Mode**
   ```bash
   python convex_examples.py
   ```

2. **Integrate into Your Workflow**
   - Add to your morning routine
   - Use for daily standups
   - Generate weekly reports

3. **Customize for Your Needs**
   - Add project-specific tools
   - Create custom queries
   - Build automated workflows

4. **Scale Up**
   - Connect to more Convex tables
   - Add authentication for team members
   - Build a web interface

## 💡 Key Insights

**What Makes This Powerful:**

1. **Natural Language Interface**: No need to remember database queries or API syntax
2. **Intelligent Reasoning**: Claude understands context and intent, not just keywords
3. **Multi-Step Operations**: Can chain queries and analysis automatically
4. **Conversational Memory**: Remembers context across the conversation
5. **Adaptive**: Works with any Convex schema - just add the tool definitions

**Real-World Impact:**

- **Save Time**: "Show me tasks" vs. writing database queries
- **Better Insights**: AI can spot patterns you might miss
- **Accessibility**: Non-technical team members can query the database
- **Automation**: Schedule reports, alerts, and updates

---

## 🎉 You're Ready!

Your Convex Agent is fully set up and tested. Start with the interactive examples and explore what's possible!

```bash
python convex_examples.py
```

Happy building! 🚀
