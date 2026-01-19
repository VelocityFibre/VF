#!/usr/bin/env python3
"""
Dependency Graph Analysis for Parallel Harness

Analyzes feature dependencies from feature_list.json and computes execution levels
for parallel execution while respecting dependency constraints.

Phase 3: Auto-Claude Integration - Parallel Execution
"""

from typing import List, Dict, Any, Set
from collections import defaultdict, deque


class DependencyGraph:
    """
    Manages feature dependencies and computes parallel execution levels.

    Uses topological sorting (Kahn's algorithm) to group features into levels
    where features in the same level have no dependencies on each other and
    can execute in parallel.

    Example:
        features = [
            {"id": 1, "dependencies": []},
            {"id": 2, "dependencies": []},
            {"id": 3, "dependencies": [1]},
            {"id": 4, "dependencies": [1, 2]},
            {"id": 5, "dependencies": [3, 4]}
        ]

        graph = DependencyGraph(features)
        levels = graph.compute_levels()
        # Result: [[1, 2], [3, 4], [5]]
        # Level 0: Features 1, 2 (no dependencies - can run in parallel)
        # Level 1: Features 3, 4 (depend on level 0 - can run in parallel)
        # Level 2: Feature 5 (depends on levels 0-1)
    """

    def __init__(self, features: List[Dict[str, Any]]):
        """
        Initialize dependency graph with features.

        Args:
            features: List of feature dictionaries from feature_list.json
                      Each feature must have 'id' and 'dependencies' keys
        """
        self.features = features
        self.feature_map = {f['id']: f for f in features}
        self.graph = defaultdict(list)  # adjacency list: feature -> dependents
        self.in_degree = {}  # incoming edge count for each feature

    def build_graph(self) -> None:
        """
        Build directed acyclic graph (DAG) from feature dependencies.

        Creates adjacency list where an edge from A to B means "B depends on A"
        (i.e., A must complete before B can start).
        """
        # Initialize in-degree counter
        for feature in self.features:
            feature_id = feature['id']
            self.in_degree[feature_id] = len(feature.get('dependencies', []))

        # Build adjacency list (reverse edges for easier traversal)
        for feature in self.features:
            feature_id = feature['id']
            dependencies = feature.get('dependencies', [])

            for dep_id in dependencies:
                # Add edge: dep_id → feature_id
                # Meaning: feature_id depends on dep_id
                self.graph[dep_id].append(feature_id)

    def compute_levels(self) -> List[List[int]]:
        """
        Compute dependency levels using modified Kahn's algorithm.

        Features in the same level have no dependencies on each other,
        so they can execute in parallel.

        Returns:
            List of levels, where each level is a list of feature IDs.
            Features are grouped by dependency depth.

        Raises:
            ValueError: If circular dependency detected
        """
        if not self.graph and not self.in_degree:
            self.build_graph()

        # Copy in-degree for algorithm (we'll modify it)
        in_degree_copy = self.in_degree.copy()

        levels = []
        processed_count = 0

        # Start with features that have no dependencies
        current_level = [fid for fid, degree in in_degree_copy.items() if degree == 0]

        while current_level:
            levels.append(current_level)
            processed_count += len(current_level)
            next_level = []

            # Process each feature in current level
            for feature_id in current_level:
                # For each feature that depends on this one
                for dependent_id in self.graph[feature_id]:
                    # Decrement in-degree (one dependency satisfied)
                    in_degree_copy[dependent_id] -= 1

                    # If all dependencies satisfied, add to next level
                    if in_degree_copy[dependent_id] == 0:
                        next_level.append(dependent_id)

            current_level = next_level

        # Check if all features were processed (detect cycles)
        if processed_count != len(self.features):
            unprocessed = [
                fid for fid, degree in in_degree_copy.items() if degree > 0
            ]
            raise ValueError(
                f"Circular dependency detected! Unprocessed features: {unprocessed}"
            )

        return levels

    def get_feature(self, feature_id: int) -> Dict[str, Any]:
        """
        Get feature dictionary by ID.

        Args:
            feature_id: Feature ID

        Returns:
            Feature dictionary

        Raises:
            KeyError: If feature ID not found
        """
        if feature_id not in self.feature_map:
            raise KeyError(f"Feature ID {feature_id} not found")

        return self.feature_map[feature_id]

    def validate_dependencies(self) -> bool:
        """
        Validate that all dependencies exist and there are no cycles.

        Returns:
            True if dependencies are valid

        Raises:
            ValueError: If invalid dependencies or cycles found
        """
        # Check that all dependency IDs exist
        for feature in self.features:
            feature_id = feature['id']
            dependencies = feature.get('dependencies', [])

            for dep_id in dependencies:
                if dep_id not in self.feature_map:
                    raise ValueError(
                        f"Feature {feature_id} depends on non-existent feature {dep_id}"
                    )

        # Check for cycles by attempting to compute levels
        try:
            self.compute_levels()
        except ValueError as e:
            if "Circular dependency" in str(e):
                raise
            # Re-raise other errors
            raise

        return True

    def get_level_stats(self) -> Dict[str, Any]:
        """
        Get statistics about dependency levels.

        Returns:
            Dictionary with level statistics including:
            - total_levels: Number of dependency levels
            - features_per_level: List of feature counts per level
            - max_parallelism: Maximum features in any single level
            - avg_parallelism: Average features per level
        """
        levels = self.compute_levels()

        features_per_level = [len(level) for level in levels]

        return {
            'total_levels': len(levels),
            'features_per_level': features_per_level,
            'max_parallelism': max(features_per_level) if features_per_level else 0,
            'avg_parallelism': sum(features_per_level) / len(features_per_level) if levels else 0,
            'total_features': len(self.features)
        }

    def visualize_levels(self) -> str:
        """
        Generate text visualization of dependency levels.

        Returns:
            Multi-line string showing features grouped by level
        """
        levels = self.compute_levels()
        stats = self.get_level_stats()

        output = []
        output.append("=" * 60)
        output.append("Dependency Levels for Parallel Execution")
        output.append("=" * 60)
        output.append(f"Total Features: {stats['total_features']}")
        output.append(f"Total Levels: {stats['total_levels']}")
        output.append(f"Max Parallelism: {stats['max_parallelism']} features")
        output.append(f"Avg Parallelism: {stats['avg_parallelism']:.1f} features/level")
        output.append("=" * 60)
        output.append("")

        for level_num, level in enumerate(levels):
            output.append(f"Level {level_num} ({len(level)} features):")
            for feature_id in level:
                feature = self.get_feature(feature_id)
                desc = feature.get('description', 'No description')
                category = feature.get('category', 'unknown')
                deps = feature.get('dependencies', [])

                # Truncate description if too long
                if len(desc) > 50:
                    desc = desc[:47] + "..."

                output.append(f"  [{feature_id:3d}] {desc:<50} (cat: {category})")

                if deps:
                    output.append(f"        Dependencies: {deps}")

            output.append("")

        return "\n".join(output)


# Convenience function for quick analysis
def analyze_dependencies(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Quick dependency analysis of features.

    Args:
        features: List of feature dictionaries

    Returns:
        Dictionary with levels and statistics
    """
    graph = DependencyGraph(features)
    levels = graph.compute_levels()
    stats = graph.get_level_stats()

    return {
        'levels': levels,
        'stats': stats,
        'visualization': graph.visualize_levels()
    }


if __name__ == "__main__":
    # Example usage and testing
    print("Dependency Graph Analysis - Example")
    print()

    # Example features
    example_features = [
        {"id": 1, "category": "1_scaffolding", "description": "Create directory structure", "dependencies": []},
        {"id": 2, "category": "1_scaffolding", "description": "Create __init__.py", "dependencies": []},
        {"id": 3, "category": "2_base", "description": "Implement BaseAgent inheritance", "dependencies": [1, 2]},
        {"id": 4, "category": "2_base", "description": "Implement __init__()", "dependencies": [3]},
        {"id": 5, "category": "3_tools", "description": "Implement define_tools()", "dependencies": [4]},
        {"id": 6, "category": "3_tools", "description": "Implement execute_tool()", "dependencies": [5]},
        {"id": 7, "category": "3_tools", "description": "Add tool: query_data", "dependencies": [5, 6]},
        {"id": 8, "category": "4_testing", "description": "Create test file", "dependencies": [1, 2]},
        {"id": 9, "category": "4_testing", "description": "Test BaseAgent", "dependencies": [3, 8]},
        {"id": 10, "category": "4_testing", "description": "Test tools", "dependencies": [7, 8]},
    ]

    graph = DependencyGraph(example_features)

    print("Validating dependencies...")
    graph.validate_dependencies()
    print("✅ Dependencies are valid (no cycles)\n")

    print(graph.visualize_levels())

    print("\nStatistics:")
    stats = graph.get_level_stats()
    print(f"  Sequential time estimate: {len(example_features)} × 20 min = {len(example_features) * 20} min")
    print(f"  Parallel time estimate: {stats['total_levels']} levels × 20 min = {stats['total_levels'] * 20} min")
    speedup = len(example_features) / stats['total_levels']
    print(f"  Speedup factor: {speedup:.1f}x")
