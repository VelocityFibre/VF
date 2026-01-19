# Claude Agent SDK Setup Guide

Complete guide for setting up and using the Claude Agent SDK in Python and TypeScript.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Examples](#examples)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

## Prerequisites

- **Python 3.13+** (for Python examples)
- **Node.js 22+** (for TypeScript examples)
- **Anthropic API Key** - Get one from [console.anthropic.com](https://console.anthropic.com/account/keys)

## Installation

### Python Setup

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Verify installation:**
   ```bash
   python -c "import anthropic; print('✅ Anthropic SDK installed')"
   ```

### TypeScript Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Install TypeScript (if needed):**
   ```bash
   npm install -g typescript ts-node
   ```

## Configuration

### Set up your API key

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API key:**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   ```

3. **Load environment variables:**

   **For Python:**
   ```bash
   export $(cat .env | xargs)
   ```

   **For TypeScript:**
   ```bash
   export $(cat .env | xargs)
   ```

   Or use a package like `dotenv`:
   ```bash
   npm install dotenv
   ```

## Quick Start

### Python

```bash
# Activate virtual environment
source venv/bin/activate

# Set API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Run examples
python agent_example.py
```

### TypeScript

```bash
# Set API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Run with ts-node
npx ts-node agent_example.ts

# Or compile and run
tsc agent_example.ts && node agent_example.js
```

## Examples

### Example 1: Basic Tool Use

The agent can use tools to perform actions:

```python
from agent_example import ClaudeAgent

agent = ClaudeAgent()
response = agent.chat("What's the weather in San Francisco?")
print(response)
```

**What happens:**
1. Agent receives your message
2. Recognizes it needs weather data
3. Calls the `get_weather` tool
4. Returns a natural language response with the data

### Example 2: Continuous Conversations

The agent maintains context across multiple messages:

```python
agent = ClaudeAgent()

# First message
agent.chat("I'm planning a trip to New York")

# Second message - agent remembers context
agent.chat("What's the weather there?")

# Third message - still maintains context
agent.chat("Based on that, what should I pack?")
```

**Key feature:** The conversation history is maintained automatically via the `conversation_history` array.

### Example 3: Multi-Tool Research Agent

Combine multiple tools in one session:

```python
agent = ClaudeAgent()
response = agent.chat(
    "Research API design best practices. "
    "Search the database and calculate the average rating."
)
```

The agent will:
1. Search the database
2. Perform calculations
3. Synthesize results into a coherent response

## Advanced Usage

### Custom Tools

Add your own tools by extending the `define_tools()` method:

```python
def define_tools(self):
    return [
        {
            "name": "deploy_to_server",
            "description": "Deploy code to a server",
            "input_schema": {
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["staging", "production"]
                    },
                    "service": {
                        "type": "string"
                    }
                },
                "required": ["environment", "service"]
            }
        }
    ]
```

Then implement the tool in `execute_tool()`:

```python
def execute_tool(self, tool_name: str, tool_input: dict) -> str:
    if tool_name == "deploy_to_server":
        env = tool_input["environment"]
        service = tool_input["service"]
        # Your deployment logic here
        return json.dumps({"status": "deployed", "environment": env})
```

### Streaming Responses

For real-time streaming (useful for UIs):

```python
with client.messages.stream(
    model=self.model,
    max_tokens=self.max_tokens,
    messages=self.conversation_history,
    tools=tools
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Sub-Agents Pattern

Create specialized agents for different tasks:

```python
class ResearchAgent(ClaudeAgent):
    def __init__(self):
        super().__init__(model="claude-3-5-sonnet-20241022")

    def define_tools(self):
        # Research-specific tools
        return [
            {"name": "web_search", ...},
            {"name": "summarize", ...}
        ]

class CodingAgent(ClaudeAgent):
    def __init__(self):
        super().__init__(model="claude-3-5-sonnet-20241022")

    def define_tools(self):
        # Coding-specific tools
        return [
            {"name": "execute_code", ...},
            {"name": "run_tests", ...}
        ]
```

## Best Practices

### 1. Context Management

The SDK maintains up to 200K tokens of context, but be mindful:

```python
# Reset when starting a new task
agent.reset_conversation()

# Or create a new agent instance
agent = ClaudeAgent()
```

### 2. Tool Design

- **Keep tools focused:** Each tool should do one thing well
- **Clear descriptions:** Help the agent understand when to use each tool
- **Validate inputs:** Always validate tool inputs before execution
- **Sandbox code execution:** Never use `eval()` in production without sandboxing

### 3. Error Handling

Wrap agent calls in try-except blocks:

```python
try:
    response = agent.chat(user_input)
    print(response)
except Exception as e:
    print(f"Error: {e}")
    # Handle gracefully
```

### 4. Model Selection

Choose the right model for your use case:

- **claude-3-5-sonnet-20241022**: Best balance of speed and intelligence
- **claude-3-opus-20240229**: Maximum intelligence for complex tasks
- **claude-3-haiku-20240307**: Fastest for simple tasks

```python
# For complex reasoning
agent = ClaudeAgent(model="claude-3-opus-20240229")

# For speed
agent = ClaudeAgent(model="claude-3-haiku-20240307")
```

### 5. Cost Optimization

- Use Haiku for simple tasks
- Implement caching for repeated queries
- Monitor token usage via the API response
- Reset conversations when context is no longer needed

## Key Concepts

### Agentic Workflows

Unlike traditional APIs where you manage everything, the Agent SDK:
- **Maintains state automatically:** No manual history management
- **Orchestrates tool calls:** Agent decides when to use tools
- **Iterates intelligently:** Can chain multiple tool calls
- **Adapts to context:** Understands conversation flow

### Tool Calling Loop

1. User sends message
2. Agent analyzes and decides if tools are needed
3. If yes, calls tool(s) with parameters
4. Tool executes and returns results
5. Agent receives results and continues reasoning
6. Returns final response to user

### Context Window

- Claude maintains up to 200K tokens of context
- Includes conversation history, tool calls, and results
- Automatically managed by the SDK
- Reset when needed for new tasks

## Troubleshooting

### "API key not found"

```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### "Module not found" (Python)

```bash
source venv/bin/activate
pip install anthropic
```

### "Cannot find module" (TypeScript)

```bash
npm install @anthropic-ai/sdk
```

### Rate Limits

The API has rate limits. If you hit them:
- Implement exponential backoff
- Use lower-tier models for testing
- Contact Anthropic for higher limits

## Resources

- **Anthropic Console:** https://console.anthropic.com
- **API Documentation:** https://docs.anthropic.com
- **SDK Repository:** https://github.com/anthropics/anthropic-sdk-typescript
- **Python SDK:** https://github.com/anthropics/anthropic-sdk-python

## Next Steps

1. ✅ Set up your API key
2. ✅ Run the example scripts
3. 🔨 Customize tools for your use case
4. 🚀 Build your agent-powered application

Happy building with Claude Agent SDK!
