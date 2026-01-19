#!/usr/bin/env python3
"""
Voice Agent Setup Validator

Checks if all required environment variables and dependencies are configured
correctly before running the voice agent.

Usage:
    python test_voice_agent_setup.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_env_var(var_name: str, description: str) -> bool:
    """Check if an environment variable is set"""
    value = os.getenv(var_name)
    if not value or value.startswith("your_") or value == f"{var_name.lower()}_here":
        print(f"❌ {var_name}: Not set or using placeholder")
        print(f"   {description}")
        return False
    print(f"✅ {var_name}: Configured")
    return True


def check_import(module_name: str, package_name: str = None) -> bool:
    """Check if a Python module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {package_name or module_name}: Installed")
        return True
    except ImportError:
        print(f"❌ {package_name or module_name}: Not installed")
        if package_name:
            print(f"   Install with: pip install {package_name}")
        return False


def main():
    """Run all validation checks"""
    print("🔍 Validating Voice Agent Setup...\n")

    all_good = True

    # Check Python packages
    print("📦 Checking Python Dependencies:")
    all_good &= check_import("livekit.agents", "livekit-agents")
    all_good &= check_import("livekit.plugins.xai", "livekit-plugins-xai")
    all_good &= check_import("dotenv", "python-dotenv")
    print()

    # Check environment variables
    print("🔐 Checking Environment Variables:")

    env_checks = [
        ("XAI_API_KEY", "Get from: https://x.ai/api"),
        ("LIVEKIT_URL", "Get from: https://cloud.livekit.io (format: wss://project.livekit.cloud)"),
        ("LIVEKIT_API_KEY", "Get from: https://cloud.livekit.io → Settings → Keys"),
        ("LIVEKIT_API_SECRET", "Get from: https://cloud.livekit.io → Settings → Keys"),
    ]

    for var_name, description in env_checks:
        all_good &= check_env_var(var_name, description)

    print()

    # Additional validation
    print("🔧 Additional Checks:")

    # Check LiveKit URL format
    livekit_url = os.getenv("LIVEKIT_URL", "")
    if livekit_url:
        if livekit_url.startswith("wss://"):
            print("✅ LIVEKIT_URL: Correct format (wss://)")
        elif livekit_url.startswith("ws://"):
            # ws:// is fine for server-to-server API calls (like this voice agent)
            # wss:// is required for browser clients (NEXT_PUBLIC_LIVEKIT_URL)
            if "127.0.0.1" in livekit_url or "localhost" in livekit_url or os.getenv("NEXT_PUBLIC_LIVEKIT_URL", "").startswith("wss://"):
                print("✅ LIVEKIT_URL: Using ws:// (OK for server-side API)")
            else:
                print("⚠️  LIVEKIT_URL: Using ws:// (consider wss:// for security)")
        else:
            print("❌ LIVEKIT_URL: Invalid format (must start with wss:// or ws://)")
            all_good = False

    # Check xAI API key format
    xai_key = os.getenv("XAI_API_KEY", "")
    if xai_key and not xai_key.startswith("xai-"):
        print("⚠️  XAI_API_KEY: Doesn't start with 'xai-' (might be incorrect)")

    print()

    # Final verdict
    if all_good:
        print("=" * 70)
        print("✅ All checks passed! You're ready to run the voice agent.")
        print("=" * 70)
        print("\n🚀 Next steps:")
        print("   1. Run: ./venv/bin/python3 voice_agent_grok.py")
        print("   2. Connect from LiveKit Playground or web UI")
        print("   3. Start talking!\n")
        print("📖 See VOICE_AGENT_SETUP.md for detailed instructions")
        return 0
    else:
        print("=" * 70)
        print("❌ Setup incomplete. Please fix the issues above.")
        print("=" * 70)
        print("\n📖 See VOICE_AGENT_SETUP.md for setup instructions")
        print("💡 Tip: Copy .env.example to .env and fill in your actual values")
        return 1


if __name__ == "__main__":
    sys.exit(main())
