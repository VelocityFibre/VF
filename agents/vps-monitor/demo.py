#!/usr/bin/env python3
"""
Demo script for VPS Monitor Agent
Monitor srv1092611.hstgr.cloud via SSH and Claude AI
"""

import os
import sys
from dotenv import load_dotenv
from vps_monitor_agent import VPSMonitorAgent, SSHVPSClient

# Load environment variables
load_dotenv()


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def test_ssh_connection():
    """Test SSH connection to VPS."""
    print_header("🔌 Testing SSH Connection to srv1092611.hstgr.cloud")

    vps_hostname = os.getenv("VPS_HOSTNAME", "srv1092611.hstgr.cloud")
    client = SSHVPSClient(vps_hostname)

    print(f"Connecting to {vps_hostname}...")

    # Try simple command
    result = client._run_ssh_command("echo 'Connection successful'")

    if result.get("success"):
        print("✅ SSH connection working!")
        print(f"   Response: {result['stdout']}\n")

        # Get system info
        print("Fetching system info...")
        info = client.get_system_info()

        if "error" in info:
            print(f"❌ Error: {info['error']}")
        else:
            print("✅ System Info:")
            for key, value in info.items():
                print(f"   {key}: {value}")

        return True
    else:
        print("❌ SSH connection failed!")
        print(f"   Error: {result.get('error', result.get('stderr'))}\n")
        print("💡 Troubleshooting:")
        print("   1. Check if SSH key exists: ls -la ~/.ssh/")
        print("   2. Verify you can SSH manually: ssh root@srv1092611.hstgr.cloud")
        print("   3. Check SSH key permissions: chmod 600 ~/.ssh/id_ed25519")
        return False


def run_interactive_demo():
    """Run interactive chat with VPS monitoring agent."""
    print_header("🤖 VPS Monitor Agent - Interactive Mode")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    vps_hostname = os.getenv("VPS_HOSTNAME", "srv1092611.hstgr.cloud")

    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file")
        return

    print(f"✅ Initializing agent for {vps_hostname}...")
    agent = VPSMonitorAgent(vps_hostname, anthropic_api_key)
    print("✅ Agent ready!\n")

    print("💬 Examples:")
    print("   - What's the current system status?")
    print("   - Check CPU and memory usage")
    print("   - Show me top processes")
    print("   - Is nginx running?")
    print("   - Are there any issues?\n")

    print("💡 Commands: 'quit' to exit, 'clear' to reset conversation\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == 'clear':
                agent.clear_history()
                print("✅ Conversation cleared\n")
                continue

            print("\n🤖 Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_automated_demo():
    """Run automated demo with preset queries."""
    print_header("📊 VPS Monitor Agent - Automated Demo")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    vps_hostname = os.getenv("VPS_HOSTNAME", "srv1092611.hstgr.cloud")

    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return

    print(f"✅ Initializing agent for {vps_hostname}...\n")
    agent = VPSMonitorAgent(vps_hostname, anthropic_api_key)

    # Test queries
    queries = [
        "Give me a quick status overview of the server",
        "What's the CPU and memory usage?",
        "Show me the top 5 processes by CPU usage",
        "Check if nginx and neon-agent services are running",
        "How much disk space is available?",
        "Are there any performance issues I should know about?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query {i}/{len(queries)}")
        print(f"{'─' * 80}")
        print(f"\n💬 {query}\n")

        try:
            response = agent.chat(query)
            print(f"🤖 {response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

        # Clear history between queries for clean responses
        if i < len(queries):
            agent.clear_history()

    print_header("✅ Demo Complete")


def run_health_check():
    """Run comprehensive health check."""
    print_header("🏥 VPS Health Check")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    vps_hostname = os.getenv("VPS_HOSTNAME", "srv1092611.hstgr.cloud")

    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return

    print(f"Running health check for {vps_hostname}...\n")
    agent = VPSMonitorAgent(vps_hostname, anthropic_api_key)

    response = agent.chat(
        "Generate a comprehensive health report. "
        "Include CPU, memory, disk usage, load average, "
        "running services, and top processes. "
        "Highlight any issues or concerns."
    )

    print(response)
    print("\n" + "=" * 80)


def show_menu():
    """Show main menu."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              VPS Monitor Agent for srv1092611                     ║
║         Hostinger VPS Monitoring with Claude AI                   ║
╚══════════════════════════════════════════════════════════════════╝

Server Details:
  Hostname: srv1092611.hstgr.cloud
  IP: 72.60.17.245
  Location: Lithuania - Vilnius
  Specs: 2 CPU cores, 8 GB RAM, 100 GB disk

Choose a mode:

1. Test SSH Connection (verify connectivity)
2. Interactive Chat (ask questions)
3. Automated Demo (run preset queries)
4. Health Check (comprehensive report)
5. Exit

""")


def main():
    """Main entry point."""
    while True:
        show_menu()

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            test_ssh_connection()
            input("\nPress Enter to continue...")

        elif choice == "2":
            run_interactive_demo()

        elif choice == "3":
            run_automated_demo()
            input("\nPress Enter to continue...")

        elif choice == "4":
            run_health_check()
            input("\nPress Enter to continue...")

        elif choice == "5":
            print("\n👋 Goodbye!")
            sys.exit(0)

        else:
            print("❌ Invalid choice. Please select 1-5.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
