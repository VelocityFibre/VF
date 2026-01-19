#!/usr/bin/env python3
"""
Main Inngest application for FibreFlow Agent Workforce

This module registers all Inngest functions and provides
the serve endpoint for the Inngest dev server.
"""

import os
import sys
from typing import List
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Inngest client
from client import inngest_client, Events

# Import all function modules
from functions.database_sync import database_sync_functions
from functions.whatsapp_queue import whatsapp_queue_functions
from functions.agent_builder import agent_builder_functions
from functions.vlm_evaluation import vlm_evaluation_functions
from functions.health_check import health_check_functions
from functions.simple_check import simple_check_functions

# Collect all functions
all_functions = (
    database_sync_functions +
    whatsapp_queue_functions +
    agent_builder_functions +
    vlm_evaluation_functions +
    health_check_functions +
    simple_check_functions
)

def create_inngest_app():
    """
    Create the Inngest app with all registered functions.

    Returns:
        The configured Inngest app ready to serve
    """
    print(f"✅ Registered {len(all_functions)} Inngest functions:")
    for func in all_functions:
        if hasattr(func, "_fn_id"):
            print(f"   - {func._fn_id}")

    return inngest_client

# For FastAPI integration
def create_fastapi_app():
    """
    Create a FastAPI app with Inngest integration.

    This allows running Inngest alongside your existing
    FibreFlow API server.
    """
    from fastapi import FastAPI
    from inngest.fast_api import serve

    app = FastAPI(title="FibreFlow Inngest Server")

    # Add Inngest serve endpoint
    serve(
        app,
        inngest_client,
        all_functions,
        serve_path="/api/inngest"
    )

    @app.get("/")
    async def root():
        return {
            "service": "FibreFlow Inngest Server",
            "functions": len(all_functions),
            "status": "running"
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app

# For Flask integration
def create_flask_app():
    """
    Create a Flask app with Inngest integration.

    Alternative to FastAPI if preferred.
    """
    from flask import Flask
    from inngest.flask import serve

    app = Flask(__name__)

    # Add Inngest serve endpoint
    serve(
        app,
        inngest_client,
        all_functions,
        serve_path="/api/inngest"
    )

    @app.route("/")
    def root():
        return {
            "service": "FibreFlow Inngest Server",
            "functions": len(all_functions),
            "status": "running"
        }

    return app

if __name__ == "__main__":
    # Run with FastAPI by default
    import uvicorn

    print("🚀 Starting FibreFlow Inngest Server")
    print(f"📍 Serve endpoint: http://localhost:3000/api/inngest")
    print(f"🔧 Dev server: Run 'npx inngest-cli@latest dev' in another terminal")

    app = create_fastapi_app()
    uvicorn.run(app, host="0.0.0.0", port=3000)