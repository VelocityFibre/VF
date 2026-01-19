#!/usr/bin/env python3
"""
Grok Voice Agent - Simple realtime voice interaction with xAI's Grok

This is a minimal implementation using LiveKit + Grok realtime API.
For voice interaction with Claude (better reasoning), see voice_agent_claude.py

Requirements:
    - XAI_API_KEY in .env (get from: https://x.ai/api)
    - LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env

LiveKit Setup:
    FibreFlow uses self-hosted LiveKit on Hostinger VPS (72.60.17.245:7880)
    Already configured in .env - no signup needed!

    For other projects, see: https://cloud.livekit.io (free tier available)

Usage:
    python voice_agent_grok.py
"""

import os
import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import xai

# Load environment variables
load_dotenv()


async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent"""

    # Connect to LiveKit room
    await ctx.connect()

    print(f"✅ Connected to room: {ctx.room.name}")

    # Define agent personality and behavior
    agent = Agent(
        instructions=(
            "You are a helpful assistant for FibreFlow, a fiber optic infrastructure company. "
            "You help with questions about contractors, projects, installations, and operations. "
            "Be concise and friendly. If you don't know something, say so."
        ),
        # Add tools here if needed (can call FibreFlow agents)
        tools=[],
    )

    # Configure Grok realtime voice session (this is all you need!)
    session = AgentSession(
        llm=xai.realtime.RealtimeModel(
            voice="Ara",  # Available voices: Ara, others TBD
            model="grok-beta",  # Grok realtime model
        ),
    )

    print("🎙️  Voice agent ready - speak to interact!")

    # Start the session
    await session.start(agent=agent, room=ctx.room)

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user briefly and ask how you can help with FibreFlow today."
    )


def main():
    """Run the voice agent worker"""

    # Validate environment variables
    required_vars = ["XAI_API_KEY", "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ Error: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease add these to your .env file. See .env.example for details.")
        print("\nGet your keys from:")
        print("  - xAI API key: https://x.ai/api")
        print("  - LiveKit: https://cloud.livekit.io")
        return

    print("🚀 Starting Grok Voice Agent...")
    print(f"   Room URL: {os.getenv('LIVEKIT_URL')}")

    # Run the agent worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )


if __name__ == "__main__":
    main()
