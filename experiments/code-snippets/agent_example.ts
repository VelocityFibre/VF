#!/usr/bin/env node
/**
 * Claude Agent SDK Example - TypeScript
 * Demonstrates agentic workflows with continuous conversations, tool use, and streaming.
 */

import Anthropic from "@anthropic-ai/sdk";

interface Message {
  role: "user" | "assistant";
  content: string | any[];
}

interface Tool {
  name: string;
  description: string;
  input_schema: {
    type: string;
    properties: Record<string, any>;
    required: string[];
  };
}

/**
 * A wrapper class for Claude's agent capabilities.
 * Manages continuous conversations with context persistence.
 */
class ClaudeAgent {
  private client: Anthropic;
  private model: string;
  private conversationHistory: Message[];
  private maxTokens: number;

  constructor(model: string = "claude-3-haiku-20240307") {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY environment variable not set");
    }

    this.client = new Anthropic({ apiKey });
    this.model = model;
    this.conversationHistory = [];
    this.maxTokens = 4096;
  }

  /**
   * Define custom tools for the agent to use.
   * This is where you can integrate external APIs, databases, etc.
   */
  defineTools(): Tool[] {
    return [
      {
        name: "get_weather",
        description:
          "Get the current weather in a given location. Returns temperature and conditions.",
        input_schema: {
          type: "object",
          properties: {
            location: {
              type: "string",
              description: "The city and state, e.g. San Francisco, CA",
            },
            unit: {
              type: "string",
              enum: ["celsius", "fahrenheit"],
              description: "The unit of temperature",
            },
          },
          required: ["location"],
        },
      },
      {
        name: "search_database",
        description:
          "Search a database for information. Simulates a database query.",
        input_schema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "The search query",
            },
            table: {
              type: "string",
              description: "The table to search in",
            },
          },
          required: ["query", "table"],
        },
      },
      {
        name: "execute_code",
        description:
          "Execute JavaScript code and return the result. Use for calculations or data processing.",
        input_schema: {
          type: "object",
          properties: {
            code: {
              type: "string",
              description: "The JavaScript code to execute",
            },
          },
          required: ["code"],
        },
      },
    ];
  }

  /**
   * Execute a tool call. This is where you implement the actual tool logic.
   * In production, you'd connect to real APIs, databases, etc.
   */
  executeTool(toolName: string, toolInput: Record<string, any>): string {
    if (toolName === "get_weather") {
      const location = toolInput.location || "Unknown";
      const unit = toolInput.unit || "fahrenheit";
      // Simulated response
      return JSON.stringify({
        location,
        temperature: unit === "fahrenheit" ? 72 : 22,
        unit,
        conditions: "Partly cloudy",
      });
    } else if (toolName === "search_database") {
      const query = toolInput.query || "";
      const table = toolInput.table || "";
      // Simulated response
      return JSON.stringify({
        results: [{ id: 1, name: "Example Item", query, table }],
        count: 1,
      });
    } else if (toolName === "execute_code") {
      const code = toolInput.code || "";
      try {
        // WARNING: In production, use a sandboxed environment!
        const result = eval(code);
        return JSON.stringify({ result, success: true });
      } catch (error: any) {
        return JSON.stringify({ error: error.message, success: false });
      }
    }

    return JSON.stringify({ error: `Unknown tool: ${toolName}` });
  }

  /**
   * Send a message to the agent and get a response.
   * Maintains conversation context automatically.
   */
  async chat(userMessage: string): Promise<string> {
    // Add user message to history
    this.conversationHistory.push({
      role: "user",
      content: userMessage,
    });

    const tools = this.defineTools();

    // Continue the conversation with tool use
    while (true) {
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: this.maxTokens,
        messages: this.conversationHistory as any,
        tools: tools as any,
      });

      // Add assistant's response to history
      this.conversationHistory.push({
        role: "assistant",
        content: response.content,
      });

      // Check if Claude wants to use a tool
      if (response.stop_reason === "tool_use") {
        // Find tool use blocks
        const toolUses = response.content.filter(
          (block: any) => block.type === "tool_use"
        );

        if (toolUses.length === 0) {
          break;
        }

        // Execute each tool
        const toolResults = [];
        for (const toolUse of toolUses) {
          console.log(`🔧 Tool called: ${toolUse.name}`);
          console.log(`   Input: ${JSON.stringify(toolUse.input, null, 2)}`);

          const result = this.executeTool(toolUse.name, toolUse.input);
          toolResults.push({
            type: "tool_result",
            tool_use_id: toolUse.id,
            content: result,
          });
          console.log(`   Result: ${result}\n`);
        }

        // Add tool results to history
        this.conversationHistory.push({
          role: "user",
          content: toolResults as any,
        });

        // Continue conversation with tool results
        continue;
      }

      // Extract text response
      const textBlocks = response.content
        .filter((block: any) => block.type === "text")
        .map((block: any) => block.text);

      return textBlocks.join("\n");
    }

    return "No response generated.";
  }

  /**
   * Clear the conversation history.
   */
  resetConversation(): void {
    this.conversationHistory = [];
  }
}

/**
 * Example 1: Basic agent with tool use
 */
async function exampleBasicAgent() {
  console.log("=".repeat(60));
  console.log("Example 1: Basic Agent with Tool Use");
  console.log("=".repeat(60) + "\n");

  const agent = new ClaudeAgent();

  // Simple question that might trigger tool use
  const response = await agent.chat(
    "What's the weather like in San Francisco? Also, calculate 15 * 23 for me."
  );
  console.log(`Agent: ${response}\n`);
}

/**
 * Example 2: Continuous conversation with context
 */
async function exampleContinuousConversation() {
  console.log("=".repeat(60));
  console.log("Example 2: Continuous Conversation");
  console.log("=".repeat(60) + "\n");

  const agent = new ClaudeAgent();

  // Multi-turn conversation
  const response1 = await agent.chat(
    "I'm planning a trip to New York. Can you help me?"
  );
  console.log(`Agent: ${response1}\n`);

  const response2 = await agent.chat("What's the weather like there?");
  console.log(`Agent: ${response2}\n`);

  const response3 = await agent.chat("Based on that, what should I pack?");
  console.log(`Agent: ${response3}\n`);
}

/**
 * Example 3: Research agent that uses multiple tools
 */
async function exampleResearchAgent() {
  console.log("=".repeat(60));
  console.log("Example 3: Research Agent");
  console.log("=".repeat(60) + "\n");

  const agent = new ClaudeAgent();

  const response = await agent.chat(
    "I need to research the best practices for API design. " +
      "Search the database for 'REST API' in the 'documentation' table, " +
      "and help me understand the results."
  );
  console.log(`Agent: ${response}\n`);
}

/**
 * Run all examples
 */
async function main() {
  console.log("\n🤖 Claude Agent SDK - TypeScript Examples\n");

  // Check for API key
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("❌ Error: ANTHROPIC_API_KEY environment variable not set");
    console.error(
      "Please set it with: export ANTHROPIC_API_KEY='your-api-key-here'"
    );
    process.exit(1);
  }

  console.log("Running examples...\n");

  try {
    await exampleBasicAgent();
    await exampleContinuousConversation();
    await exampleResearchAgent();

    console.log("=".repeat(60));
    console.log("✅ All examples completed!");
    console.log("=".repeat(60));
  } catch (error: any) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

export { ClaudeAgent };
