#!/usr/bin/env python3
"""
Sandbox Configuration Templates (Phase 1)

Configuration templates and presets for E2B sandboxes.
Defines environment setups, resource limits, and profiles for different agent types.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class SandboxProfile(Enum):
    """Predefined sandbox profiles for different use cases."""
    LIGHTWEIGHT = "lightweight"  # Simple agents, minimal deps
    STANDARD = "standard"        # Most agents
    HEAVY = "heavy"             # Complex agents with ML/VLM
    DATABASE = "database"       # Agents needing DB access


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution."""
    timeout_seconds: int = 300      # 5 minutes default
    max_memory_mb: int = 2048       # 2GB default
    max_cpu_cores: int = 2          # 2 cores default
    max_disk_mb: int = 5120         # 5GB default


@dataclass
class EnvironmentConfig:
    """Environment configuration for sandbox."""
    python_version: str = "3.11"
    requirements_file: Optional[str] = None
    env_vars: Dict[str, str] = None
    pre_install_commands: List[str] = None
    post_setup_commands: List[str] = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}
        if self.pre_install_commands is None:
            self.pre_install_commands = []
        if self.post_setup_commands is None:
            self.post_setup_commands = []


@dataclass
class SandboxTemplate:
    """Complete sandbox template configuration."""
    name: str
    profile: SandboxProfile
    resources: ResourceLimits
    environment: EnvironmentConfig
    description: str = ""


# ============================================================================
# Predefined Templates
# ============================================================================

TEMPLATES = {
    SandboxProfile.LIGHTWEIGHT: SandboxTemplate(
        name="Lightweight Agent Sandbox",
        profile=SandboxProfile.LIGHTWEIGHT,
        resources=ResourceLimits(
            timeout_seconds=180,      # 3 minutes
            max_memory_mb=1024,       # 1GB
            max_cpu_cores=1,          # Single core
            max_disk_mb=2048          # 2GB
        ),
        environment=EnvironmentConfig(
            python_version="3.11",
            requirements_file="requirements/base.txt",
            env_vars={
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO"
            },
            pre_install_commands=[
                "pip install --upgrade pip",
            ],
            post_setup_commands=[
                "echo 'Lightweight sandbox ready'"
            ]
        ),
        description="For simple agents with minimal dependencies (health checks, file ops)"
    ),

    SandboxProfile.STANDARD: SandboxTemplate(
        name="Standard Agent Sandbox",
        profile=SandboxProfile.STANDARD,
        resources=ResourceLimits(
            timeout_seconds=300,      # 5 minutes
            max_memory_mb=2048,       # 2GB
            max_cpu_cores=2,          # 2 cores
            max_disk_mb=5120          # 5GB
        ),
        environment=EnvironmentConfig(
            python_version="3.11",
            requirements_file="requirements/base.txt",
            env_vars={
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO",
                "PYTEST_TIMEOUT": "60"
            },
            pre_install_commands=[
                "pip install --upgrade pip",
                "apt-get update && apt-get install -y git curl"
            ],
            post_setup_commands=[
                "pytest --version",
                "echo 'Standard sandbox ready'"
            ]
        ),
        description="For most agents (database ops, API integrations, testing)"
    ),

    SandboxProfile.HEAVY: SandboxTemplate(
        name="Heavy Agent Sandbox",
        profile=SandboxProfile.HEAVY,
        resources=ResourceLimits(
            timeout_seconds=600,      # 10 minutes
            max_memory_mb=4096,       # 4GB
            max_cpu_cores=4,          # 4 cores
            max_disk_mb=10240         # 10GB
        ),
        environment=EnvironmentConfig(
            python_version="3.11",
            requirements_file="requirements/base.txt",
            env_vars={
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO",
                "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
                "TRANSFORMERS_CACHE": "/tmp/transformers"
            },
            pre_install_commands=[
                "pip install --upgrade pip",
                "apt-get update && apt-get install -y git curl build-essential",
                "pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
            ],
            post_setup_commands=[
                "python -c 'import torch; print(f\"PyTorch {torch.__version__} ready\")'",
                "echo 'Heavy sandbox ready'"
            ]
        ),
        description="For complex agents with ML/VLM (image processing, model inference)"
    ),

    SandboxProfile.DATABASE: SandboxTemplate(
        name="Database Agent Sandbox",
        profile=SandboxProfile.DATABASE,
        resources=ResourceLimits(
            timeout_seconds=300,      # 5 minutes
            max_memory_mb=2048,       # 2GB
            max_cpu_cores=2,          # 2 cores
            max_disk_mb=5120          # 5GB
        ),
        environment=EnvironmentConfig(
            python_version="3.11",
            requirements_file="requirements/base.txt",
            env_vars={
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO",
                "PGCONNECT_TIMEOUT": "10",
                "DATABASE_POOL_SIZE": "5"
            },
            pre_install_commands=[
                "pip install --upgrade pip",
                "apt-get update && apt-get install -y git curl postgresql-client",
                "pip install psycopg2-binary asyncpg sqlalchemy"
            ],
            post_setup_commands=[
                "psql --version",
                "python -c 'import psycopg2; print(f\"psycopg2 {psycopg2.__version__} ready\")'",
                "echo 'Database sandbox ready'"
            ]
        ),
        description="For database agents (Neon queries, migrations, sync operations)"
    )
}


# ============================================================================
# Configuration Helper Functions
# ============================================================================

def get_template(profile: SandboxProfile) -> SandboxTemplate:
    """
    Get sandbox template by profile.

    Args:
        profile: Sandbox profile to use

    Returns:
        SandboxTemplate configuration

    Example:
        template = get_template(SandboxProfile.STANDARD)
        print(f"Using {template.name}")
        print(f"Timeout: {template.resources.timeout_seconds}s")
    """
    return TEMPLATES[profile]


def get_template_for_agent(agent_name: str) -> SandboxTemplate:
    """
    Get recommended template for agent type.

    Args:
        agent_name: Name of agent being built

    Returns:
        Recommended SandboxTemplate

    Example:
        template = get_template_for_agent("vlm-evaluator")
        # Returns HEAVY template (needs ML libraries)
    """
    # Map agent names to profiles
    profile_mapping = {
        # Lightweight agents
        "vps-monitor": SandboxProfile.LIGHTWEIGHT,
        "health-check": SandboxProfile.LIGHTWEIGHT,
        "file-ops": SandboxProfile.LIGHTWEIGHT,

        # Standard agents
        "qfield-sync": SandboxProfile.STANDARD,
        "wa-monitor": SandboxProfile.STANDARD,
        "api-integration": SandboxProfile.STANDARD,
        "test-runner": SandboxProfile.STANDARD,

        # Heavy agents
        "vlm-evaluator": SandboxProfile.HEAVY,
        "image-processor": SandboxProfile.HEAVY,
        "model-inference": SandboxProfile.HEAVY,

        # Database agents
        "neon-agent": SandboxProfile.DATABASE,
        "database-ops": SandboxProfile.DATABASE,
        "convex-sync": SandboxProfile.DATABASE,
    }

    # Extract agent type from name (e.g., "neon_agent_v2" → "neon-agent")
    agent_type = agent_name.lower().replace("_", "-")

    # Find matching profile
    for pattern, profile in profile_mapping.items():
        if pattern in agent_type:
            return TEMPLATES[profile]

    # Default to STANDARD if no match
    return TEMPLATES[SandboxProfile.STANDARD]


def create_custom_template(
    name: str,
    base_profile: SandboxProfile = SandboxProfile.STANDARD,
    **overrides
) -> SandboxTemplate:
    """
    Create custom template based on existing profile.

    Args:
        name: Custom template name
        base_profile: Base profile to extend
        **overrides: Fields to override

    Returns:
        Custom SandboxTemplate

    Example:
        template = create_custom_template(
            name="Fast Test Runner",
            base_profile=SandboxProfile.LIGHTWEIGHT,
            resources=ResourceLimits(timeout_seconds=60)
        )
    """
    base = TEMPLATES[base_profile]

    # Apply overrides
    resources = overrides.get("resources", base.resources)
    environment = overrides.get("environment", base.environment)
    description = overrides.get("description", f"Custom template based on {base.name}")

    return SandboxTemplate(
        name=name,
        profile=base_profile,
        resources=resources,
        environment=environment,
        description=description
    )


def estimate_cost(
    template: SandboxTemplate,
    num_sandboxes: int,
    concurrent: bool = True
) -> Dict[str, float]:
    """
    Estimate E2B cost for sandbox usage.

    E2B Pricing (approximate):
    - Compute: $0.001 per vCPU-minute
    - Memory: $0.0001 per GB-minute
    - Storage: $0.00001 per GB-minute

    Args:
        template: Sandbox template
        num_sandboxes: Number of sandboxes to run
        concurrent: If True, sandboxes run in parallel (same duration)

    Returns:
        Dictionary with cost breakdown

    Example:
        cost = estimate_cost(
            template=get_template(SandboxProfile.STANDARD),
            num_sandboxes=15,
            concurrent=True
        )
        print(f"Total cost: ${cost['total']:.2f}")
    """
    # Extract resource specs
    timeout_min = template.resources.timeout_seconds / 60
    cpu_cores = template.resources.max_cpu_cores
    memory_gb = template.resources.max_memory_mb / 1024
    disk_gb = template.resources.max_disk_mb / 1024

    # Calculate per-sandbox costs
    compute_cost_per_sandbox = cpu_cores * timeout_min * 0.001
    memory_cost_per_sandbox = memory_gb * timeout_min * 0.0001
    storage_cost_per_sandbox = disk_gb * timeout_min * 0.00001

    per_sandbox_cost = (
        compute_cost_per_sandbox +
        memory_cost_per_sandbox +
        storage_cost_per_sandbox
    )

    # Total cost depends on concurrency
    if concurrent:
        # All sandboxes run in parallel → same total time
        total_cost = per_sandbox_cost * num_sandboxes
        total_duration_min = timeout_min
    else:
        # Sandboxes run sequentially → multiply time
        total_cost = per_sandbox_cost * num_sandboxes
        total_duration_min = timeout_min * num_sandboxes

    return {
        "per_sandbox": per_sandbox_cost,
        "compute": compute_cost_per_sandbox * num_sandboxes,
        "memory": memory_cost_per_sandbox * num_sandboxes,
        "storage": storage_cost_per_sandbox * num_sandboxes,
        "total": total_cost,
        "duration_minutes": total_duration_min,
        "cost_per_hour": (total_cost / total_duration_min) * 60 if total_duration_min > 0 else 0
    }


# ============================================================================
# Validation
# ============================================================================

def validate_template(template: SandboxTemplate) -> List[str]:
    """
    Validate sandbox template configuration.

    Args:
        template: Template to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Resource validation
    if template.resources.timeout_seconds < 30:
        errors.append("Timeout too short (min 30s)")
    if template.resources.timeout_seconds > 600:
        errors.append("Timeout too long (max 600s for E2B free tier)")

    if template.resources.max_memory_mb < 512:
        errors.append("Memory too low (min 512MB)")
    if template.resources.max_memory_mb > 8192:
        errors.append("Memory too high (max 8GB for E2B standard)")

    if template.resources.max_cpu_cores < 1:
        errors.append("CPU cores too low (min 1)")
    if template.resources.max_cpu_cores > 8:
        errors.append("CPU cores too high (max 8 for E2B standard)")

    # Environment validation
    if not template.environment.python_version:
        errors.append("Python version not specified")

    return errors


if __name__ == "__main__":
    # Example usage
    print("Sandbox Configuration Templates")
    print("=" * 70)
    print()

    # Show all templates
    for profile in SandboxProfile:
        template = get_template(profile)
        print(f"📦 {template.name}")
        print(f"   Profile: {template.profile.value}")
        print(f"   Timeout: {template.resources.timeout_seconds}s")
        print(f"   Memory: {template.resources.max_memory_mb}MB")
        print(f"   CPU: {template.resources.max_cpu_cores} cores")
        print(f"   Description: {template.description}")

        # Validate
        errors = validate_template(template)
        if errors:
            print(f"   ⚠️  Validation errors: {', '.join(errors)}")
        else:
            print(f"   ✅ Valid configuration")

        # Estimate cost for 15 concurrent sandboxes
        cost = estimate_cost(template, num_sandboxes=15, concurrent=True)
        print(f"   💰 Cost (15 concurrent): ${cost['total']:.3f}")
        print()

    # Test agent-specific template selection
    print("\nAgent-Specific Templates:")
    print("-" * 70)
    test_agents = [
        "vps-monitor",
        "neon-agent",
        "vlm-evaluator",
        "qfield-sync"
    ]

    for agent_name in test_agents:
        template = get_template_for_agent(agent_name)
        print(f"{agent_name:20} → {template.profile.value:15} ({template.resources.timeout_seconds}s)")
