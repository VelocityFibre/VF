#!/usr/bin/env python3
"""
Configuration and environment variable validation for agents.

This module provides utilities for validating required environment
variables and configuration management across all agents.

Resolves: DEBT-006 (Environment Variable Dependencies Not Documented)
"""

import os
from typing import List, Dict, Optional


class EnvironmentConfigError(Exception):
    """Raised when required environment variables are missing or invalid."""
    pass


def validate_env_vars(required_vars: List[str], optional_vars: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Validate and return environment variables.

    Args:
        required_vars: List of required environment variable names
        optional_vars: List of optional environment variable names

    Returns:
        Dictionary of all environment variables (required + available optional)

    Raises:
        EnvironmentConfigError: If any required variables are missing

    Example:
        env = validate_env_vars(
            required_vars=['ANTHROPIC_API_KEY', 'VPS_HOSTNAME'],
            optional_vars=['VPS_SSH_USER']
        )
        api_key = env['ANTHROPIC_API_KEY']
        ssh_user = env.get('VPS_SSH_USER', 'root')  # Default if not set
    """
    # Check for missing required variables
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentConfigError(
            f"Missing required environment variables: {', '.join(missing)}\n\n"
            f"Required variables:\n"
            + "\n".join(f"  - {var}" for var in required_vars)
            + "\n\n"
            f"Please set these variables in your environment or create a .env file.\n"
            f"See .env.example for setup instructions."
        )

    # Collect all variables
    result = {var: os.getenv(var) for var in required_vars}

    # Add optional variables if they exist
    if optional_vars:
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                result[var] = value

    return result


def get_agent_config(agent_type: str) -> Dict[str, str]:
    """
    Get configuration for a specific agent type.

    Args:
        agent_type: Type of agent ('vps', 'neon', 'convex', 'contractor', 'project')

    Returns:
        Dictionary of environment variables for the agent

    Raises:
        EnvironmentConfigError: If required variables are missing
        ValueError: If agent_type is unknown

    Example:
        config = get_agent_config('vps')
        agent = VPSMonitorAgent(config['VPS_HOSTNAME'], config['ANTHROPIC_API_KEY'])
    """
    # All agents require ANTHROPIC_API_KEY
    common_required = ['ANTHROPIC_API_KEY']

    # Agent-specific requirements
    agent_configs = {
        'vps': {
            'required': common_required + ['VPS_HOSTNAME'],
            'optional': ['VPS_SSH_USER', 'VPS_SSH_KEY_PATH']
        },
        'neon': {
            'required': common_required + ['NEON_DATABASE_URL'],
            'optional': []
        },
        'convex': {
            'required': common_required + ['CONVEX_URL'],
            'optional': ['SYNC_AUTH_KEY']
        },
        'contractor': {
            'required': common_required + ['CONVEX_URL'],
            'optional': []
        },
        'project': {
            'required': common_required + ['CONVEX_URL'],
            'optional': []
        }
    }

    if agent_type not in agent_configs:
        raise ValueError(
            f"Unknown agent type: '{agent_type}'. "
            f"Valid types: {', '.join(agent_configs.keys())}"
        )

    config = agent_configs[agent_type]
    return validate_env_vars(
        required_vars=config['required'],
        optional_vars=config['optional']
    )


def check_all_env_vars() -> Dict[str, Dict[str, bool]]:
    """
    Check status of all environment variables used across all agents.

    Returns:
        Dictionary mapping agent types to variable status

    Example:
        status = check_all_env_vars()
        print(f"VPS Agent ready: {all(status['vps'].values())}")
    """
    all_vars = {
        'common': ['ANTHROPIC_API_KEY'],
        'vps': ['VPS_HOSTNAME', 'VPS_SSH_USER', 'VPS_SSH_KEY_PATH'],
        'neon': ['NEON_DATABASE_URL'],
        'convex': ['CONVEX_URL', 'SYNC_AUTH_KEY']
    }

    status = {}
    for category, vars_list in all_vars.items():
        status[category] = {
            var: bool(os.getenv(var))
            for var in vars_list
        }

    return status


def print_env_status():
    """
    Print a formatted table of environment variable status.

    Useful for debugging configuration issues.
    """
    status = check_all_env_vars()

    print("\n" + "=" * 60)
    print("Environment Variable Status")
    print("=" * 60)

    for category, vars_status in status.items():
        print(f"\n{category.upper()}:")
        for var, is_set in vars_status.items():
            status_icon = "✅" if is_set else "❌"
            status_text = "SET" if is_set else "NOT SET"
            print(f"  {status_icon} {var}: {status_text}")

    print("\n" + "=" * 60)
    print("Tip: Set missing variables in .env file or your shell")
    print("See .env.example for reference")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # When run directly, print environment status
    print_env_status()
