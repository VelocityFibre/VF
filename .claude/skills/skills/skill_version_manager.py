"""
Skill Version Manager for FibreFlow Agent Workforce

Manages:
- Skill versioning (semver: major.minor.patch)
- Version compatibility checks
- Deprecation warnings
- Skill migration paths
- Performance tracking by version
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class SkillVersion:
    """Skill version information"""
    name: str
    version: str  # semver format: 1.0.0
    major: int
    minor: int
    patch: int
    deprecated: bool = False
    deprecation_date: Optional[str] = None
    replacement: Optional[str] = None
    performance_baseline: Optional[Dict] = None
    changelog: Optional[List[str]] = None


class VersionManager:
    """Manage skill versions"""

    VERSION_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')

    def __init__(self, skills_dir: Path = Path(".claude/skills")):
        self.skills_dir = skills_dir
        self.versions: Dict[str, SkillVersion] = {}
        self._load_versions()

    def _load_versions(self):
        """Load all skill versions from skill.md files"""
        if not self.skills_dir.exists():
            return

        for skill_path in self.skills_dir.iterdir():
            if not skill_path.is_dir():
                continue

            skill_md = skill_path / "skill.md"
            if not skill_md.exists():
                continue

            version_info = self._parse_skill_metadata(skill_md)
            if version_info:
                self.versions[version_info.name] = version_info

    def _parse_skill_metadata(self, skill_md: Path) -> Optional[SkillVersion]:
        """Parse skill metadata from skill.md YAML frontmatter"""
        try:
            with open(skill_md, 'r') as f:
                content = f.read()

            # Extract YAML frontmatter
            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            metadata = yaml.safe_load(parts[1])

            # Parse version
            version_str = metadata.get('version', '0.1.0')
            match = self.VERSION_PATTERN.match(version_str)
            if not match:
                return None

            major, minor, patch = map(int, match.groups())

            return SkillVersion(
                name=metadata.get('name', skill_md.parent.name),
                version=version_str,
                major=major,
                minor=minor,
                patch=patch,
                deprecated=metadata.get('deprecated', False),
                deprecation_date=metadata.get('deprecation_date'),
                replacement=metadata.get('replacement'),
                performance_baseline=metadata.get('performance'),
                changelog=metadata.get('changelog'),
            )

        except Exception as e:
            print(f"Warning: Failed to parse {skill_md}: {e}")
            return None

    def get_version(self, skill_name: str) -> Optional[SkillVersion]:
        """Get version info for a skill"""
        return self.versions.get(skill_name)

    def is_compatible(self, skill_name: str, required_version: str) -> bool:
        """Check if current version meets requirements"""
        current = self.versions.get(skill_name)
        if not current:
            return False

        req_match = self.VERSION_PATTERN.match(required_version)
        if not req_match:
            return False

        req_major, req_minor, req_patch = map(int, req_match.groups())

        # Major version must match
        if current.major != req_major:
            return False

        # Minor version must be >= required
        if current.minor < req_minor:
            return False

        # If minor matches, patch must be >= required
        if current.minor == req_minor and current.patch < req_patch:
            return False

        return True

    def check_deprecation(self, skill_name: str) -> Optional[Dict]:
        """Check if skill is deprecated"""
        version = self.versions.get(skill_name)
        if not version or not version.deprecated:
            return None

        return {
            "deprecated": True,
            "deprecation_date": version.deprecation_date,
            "replacement": version.replacement,
            "message": f"Skill '{skill_name}' is deprecated. "
                      f"Use '{version.replacement}' instead." if version.replacement else
                      f"Skill '{skill_name}' is deprecated.",
        }

    def increment_version(
        self,
        skill_name: str,
        bump_type: str = "patch"
    ) -> Optional[str]:
        """
        Increment skill version

        Args:
            skill_name: Name of skill
            bump_type: "major", "minor", or "patch"

        Returns:
            New version string
        """
        current = self.versions.get(skill_name)
        if not current:
            return None

        if bump_type == "major":
            new_version = f"{current.major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{current.major}.{current.minor + 1}.0"
        elif bump_type == "patch":
            new_version = f"{current.major}.{current.minor}.{current.patch + 1}"
        else:
            raise ValueError(f"Invalid bump_type: {bump_type}")

        return new_version

    def update_skill_version(
        self,
        skill_name: str,
        new_version: str,
        changelog_entry: Optional[str] = None
    ):
        """Update skill version in skill.md"""
        skill_path = self.skills_dir / skill_name / "skill.md"
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_name}")

        with open(skill_path, 'r') as f:
            content = f.read()

        # Update version in YAML frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("Invalid skill.md format")

        metadata = yaml.safe_load(parts[1])
        metadata['version'] = new_version

        if changelog_entry:
            if 'changelog' not in metadata:
                metadata['changelog'] = []
            metadata['changelog'].insert(0, {
                "version": new_version,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "changes": changelog_entry,
            })

        # Write updated content
        new_content = f"---\n{yaml.dump(metadata)}---{parts[2]}"
        with open(skill_path, 'w') as f:
            f.write(new_content)

        # Reload versions
        self._load_versions()

    def list_all_versions(self) -> List[Dict]:
        """List all skill versions"""
        return [
            {
                "name": v.name,
                "version": v.version,
                "deprecated": v.deprecated,
                "replacement": v.replacement,
            }
            for v in self.versions.values()
        ]

    def get_performance_baseline(self, skill_name: str) -> Optional[Dict]:
        """Get performance baseline for skill"""
        version = self.versions.get(skill_name)
        if not version:
            return None

        return version.performance_baseline

    def compare_performance(
        self,
        skill_name: str,
        actual_metrics: Dict
    ) -> Dict:
        """Compare actual performance against baseline"""
        baseline = self.get_performance_baseline(skill_name)
        if not baseline:
            return {"status": "no_baseline"}

        comparison = {}

        for metric, baseline_value in baseline.items():
            if metric not in actual_metrics:
                continue

            actual_value = actual_metrics[metric]

            # Handle different metric types
            if metric.endswith("_ms"):  # Duration metrics (lower is better)
                diff_pct = ((actual_value - baseline_value) / baseline_value) * 100
                status = "degraded" if diff_pct > 10 else "ok"
            elif metric.endswith("_tokens"):  # Token metrics (lower is better)
                diff_pct = ((actual_value - baseline_value) / baseline_value) * 100
                status = "degraded" if diff_pct > 20 else "ok"
            else:  # Generic metrics
                diff_pct = ((actual_value - baseline_value) / baseline_value) * 100
                status = "changed"

            comparison[metric] = {
                "baseline": baseline_value,
                "actual": actual_value,
                "diff_pct": diff_pct,
                "status": status,
            }

        return comparison


if __name__ == "__main__":
    # Test version manager
    manager = VersionManager()

    print("📦 Skill Version Manager Test\n")

    # List all versions
    print("All skills:")
    for version_info in manager.list_all_versions():
        status = " (deprecated)" if version_info['deprecated'] else ""
        print(f"  - {version_info['name']} v{version_info['version']}{status}")

    # Check compatibility
    print("\nCompatibility checks:")
    test_skills = ["database-operations", "vf-server"]
    for skill in test_skills:
        compatible = manager.is_compatible(skill, "1.0.0")
        print(f"  {skill} >= 1.0.0: {compatible}")

    # Check deprecation
    print("\nDeprecation checks:")
    for skill in test_skills:
        dep_info = manager.check_deprecation(skill)
        if dep_info:
            print(f"  ⚠️  {skill}: {dep_info['message']}")
        else:
            print(f"  ✅ {skill}: Active")

    print("\n✅ Version manager test complete")
