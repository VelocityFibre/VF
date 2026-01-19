"""
Performance Benchmarking Suite for FibreFlow Agent Workforce

Benchmarks:
- Skills vs Agents performance comparison
- Database query response times
- Token usage efficiency
- Memory footprint
- Cold vs warm start times
"""

import time
import statistics
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    name: str
    category: str  # skill, agent, database, system
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    success_rate: float
    metadata: Dict[str, Any]


class PerformanceBenchmark:
    """Performance benchmarking harness"""

    def __init__(self, name: str, category: str = "general"):
        self.name = name
        self.category = category
        self.results: List[float] = []
        self.successes = 0
        self.failures = 0

    def run(
        self,
        func: Callable,
        iterations: int = 100,
        warmup: int = 5,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run benchmark

        Args:
            func: Function to benchmark
            iterations: Number of iterations
            warmup: Number of warmup iterations
            **kwargs: Arguments to pass to func

        Returns:
            BenchmarkResult
        """
        print(f"🏃 Running benchmark: {self.name}")
        print(f"   Iterations: {iterations}, Warmup: {warmup}")

        # Warmup
        for _ in range(warmup):
            try:
                func(**kwargs)
            except Exception:
                pass

        # Actual benchmark
        self.results = []
        self.successes = 0
        self.failures = 0

        for i in range(iterations):
            start = time.perf_counter()
            try:
                func(**kwargs)
                success = True
                self.successes += 1
            except Exception as e:
                success = False
                self.failures += 1

            end = time.perf_counter()
            duration_ms = (end - start) * 1000

            if success:  # Only count successful runs
                self.results.append(duration_ms)

            if (i + 1) % 10 == 0:
                print(f"   Progress: {i + 1}/{iterations}")

        # Calculate statistics
        if not self.results:
            raise ValueError("No successful iterations!")

        sorted_results = sorted(self.results)
        p95_idx = int(len(sorted_results) * 0.95)
        p99_idx = int(len(sorted_results) * 0.99)

        result = BenchmarkResult(
            name=self.name,
            category=self.category,
            iterations=len(self.results),
            avg_duration_ms=statistics.mean(self.results),
            min_duration_ms=min(self.results),
            max_duration_ms=max(self.results),
            std_dev_ms=statistics.stdev(self.results) if len(self.results) > 1 else 0,
            median_ms=statistics.median(self.results),
            p95_ms=sorted_results[p95_idx],
            p99_ms=sorted_results[p99_idx],
            success_rate=self.successes / (self.successes + self.failures),
            metadata=kwargs,
        )

        print(f"   ✅ Complete: {result.avg_duration_ms:.2f}ms avg")
        return result


class BenchmarkSuite:
    """Collection of benchmarks"""

    def __init__(self, name: str):
        self.name = name
        self.benchmarks: List[BenchmarkResult] = []

    def add_benchmark(
        self,
        name: str,
        func: Callable,
        category: str = "general",
        iterations: int = 100,
        **kwargs
    ):
        """Add and run a benchmark"""
        bench = PerformanceBenchmark(name, category)
        result = bench.run(func, iterations=iterations, **kwargs)
        self.benchmarks.append(result)
        return result

    def generate_report(self, output_file: Optional[Path] = None) -> Dict:
        """Generate benchmark report"""
        report = {
            "suite_name": self.name,
            "generated_at": datetime.utcnow().isoformat(),
            "total_benchmarks": len(self.benchmarks),
            "results": [asdict(b) for b in self.benchmarks],
            "summary_by_category": self._summarize_by_category(),
        }

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)

        return report

    def _summarize_by_category(self) -> Dict[str, Dict]:
        """Summarize results by category"""
        from collections import defaultdict

        summary = defaultdict(list)

        for bench in self.benchmarks:
            summary[bench.category].append(bench)

        result = {}
        for category, benches in summary.items():
            result[category] = {
                "count": len(benches),
                "avg_duration_ms": statistics.mean([b.avg_duration_ms for b in benches]),
                "avg_success_rate": statistics.mean([b.success_rate for b in benches]),
            }

        return result

    def print_summary(self):
        """Print benchmark summary"""
        print(f"\n{'='*70}")
        print(f"📊 Benchmark Suite: {self.name}")
        print(f"{'='*70}\n")

        # Group by category
        by_category = {}
        for bench in self.benchmarks:
            if bench.category not in by_category:
                by_category[bench.category] = []
            by_category[bench.category].append(bench)

        for category, benches in by_category.items():
            print(f"Category: {category.upper()}")
            print(f"{'-'*70}")

            for bench in benches:
                print(f"  {bench.name}")
                print(f"    Avg: {bench.avg_duration_ms:.2f}ms | "
                      f"Min: {bench.min_duration_ms:.2f}ms | "
                      f"Max: {bench.max_duration_ms:.2f}ms")
                print(f"    P95: {bench.p95_ms:.2f}ms | "
                      f"P99: {bench.p99_ms:.2f}ms | "
                      f"Success: {bench.success_rate*100:.1f}%")
                print()

            avg_category = statistics.mean([b.avg_duration_ms for b in benches])
            print(f"  Category Average: {avg_category:.2f}ms\n")

        print(f"{'='*70}\n")


if __name__ == "__main__":
    # Example benchmark suite
    suite = BenchmarkSuite("Example Performance Tests")

    # Dummy functions for testing
    def fast_operation():
        time.sleep(0.001)  # 1ms

    def medium_operation():
        time.sleep(0.010)  # 10ms

    def slow_operation():
        time.sleep(0.100)  # 100ms

    # Run benchmarks
    suite.add_benchmark(
        "Fast Operation",
        fast_operation,
        category="speed",
        iterations=50,
    )

    suite.add_benchmark(
        "Medium Operation",
        medium_operation,
        category="speed",
        iterations=50,
    )

    suite.add_benchmark(
        "Slow Operation",
        slow_operation,
        category="speed",
        iterations=20,
    )

    # Print summary
    suite.print_summary()

    # Save report
    report_file = Path("benchmarks/reports/example_report.json")
    suite.generate_report(report_file)
    print(f"📁 Report saved to: {report_file}")
