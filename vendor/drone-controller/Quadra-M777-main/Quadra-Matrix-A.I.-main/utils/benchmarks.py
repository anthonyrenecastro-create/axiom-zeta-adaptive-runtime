"""
Performance Benchmarks for Quadra Matrix A.I.
Measure and track system performance
"""
import time
import statistics
import json
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ============================================================
# BENCHMARK UTILITIES
# ============================================================

class BenchmarkResult:
    """Store benchmark results"""
    
    def __init__(self, name: str):
        self.name = name
        self.measurements: List[float] = []
        self.metadata: Dict[str, Any] = {}
        self.timestamp = datetime.utcnow()
    
    def add_measurement(self, duration: float):
        """Add a timing measurement"""
        self.measurements.append(duration)
    
    def calculate_stats(self) -> Dict[str, float]:
        """Calculate statistics from measurements"""
        if not self.measurements:
            return {}
        
        return {
            'count': len(self.measurements),
            'mean': statistics.mean(self.measurements),
            'median': statistics.median(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'stdev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0,
            'total': sum(self.measurements),
            'p50': statistics.median(self.measurements),
            'p95': self._percentile(95),
            'p99': self._percentile(99),
        }
    
    def _percentile(self, percentile: int) -> float:
        """Calculate percentile"""
        if not self.measurements:
            return 0.0
        sorted_vals = sorted(self.measurements)
        index = int(len(sorted_vals) * percentile / 100)
        return sorted_vals[min(index, len(sorted_vals) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'measurements': self.measurements,
            'stats': self.calculate_stats(),
            'metadata': self.metadata
        }


class PerformanceBenchmark:
    """
    Performance benchmark runner
    
    Usage:
        benchmark = PerformanceBenchmark('my_operation')
        
        with benchmark.measure():
            # code to benchmark
            pass
        
        print(benchmark.get_results())
    """
    
    def __init__(self, name: str):
        self.name = name
        self.result = BenchmarkResult(name)
        self._start_time: Optional[float] = None
    
    def measure(self):
        """Context manager for timing measurements"""
        return self._MeasureContext(self)
    
    class _MeasureContext:
        def __init__(self, benchmark: 'PerformanceBenchmark'):
            self.benchmark = benchmark
            self.start_time: Optional[float] = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.perf_counter() - self.start_time
            self.benchmark.result.add_measurement(duration)
            return False
    
    def get_results(self) -> Dict[str, Any]:
        """Get benchmark results"""
        return self.result.to_dict()
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata for this benchmark"""
        self.result.metadata[key] = value


# ============================================================
# BENCHMARK SUITE
# ============================================================

class BenchmarkSuite:
    """Collection of benchmarks"""
    
    def __init__(self, name: str = 'Quadra Matrix Performance'):
        self.name = name
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
    
    def create_benchmark(self, name: str) -> PerformanceBenchmark:
        """Create and register a new benchmark"""
        benchmark = PerformanceBenchmark(name)
        self.benchmarks[name] = benchmark
        return benchmark
    
    def run_benchmark(self, name: str, func: Callable, *args, iterations: int = 100, **kwargs):
        """
        Run a function multiple times and measure performance
        
        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of times to run
            *args, **kwargs: Arguments for the function
        """
        benchmark = self.create_benchmark(name)
        
        for i in range(iterations):
            with benchmark.measure():
                func(*args, **kwargs)
        
        return benchmark.get_results()
    
    def finalize(self):
        """Finalize suite"""
        self.end_time = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all benchmarks"""
        self.finalize()
        
        return {
            'suite_name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'benchmarks': {
                name: bench.get_results()
                for name, bench in self.benchmarks.items()
            }
        }
    
    def save_results(self, output_file: Path):
        """Save results to JSON file"""
        results = self.get_summary()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_file}")
    
    def print_summary(self):
        """Print formatted summary"""
        print(f"\n{'='*80}")
        print(f"BENCHMARK SUITE: {self.name}")
        print(f"{'='*80}\n")
        
        for name, benchmark in self.benchmarks.items():
            results = benchmark.get_results()
            stats = results['stats']
            
            print(f"📊 {name}")
            print(f"   Iterations: {stats.get('count', 0)}")
            print(f"   Mean:       {stats.get('mean', 0)*1000:.2f} ms")
            print(f"   Median:     {stats.get('median', 0)*1000:.2f} ms")
            print(f"   Min:        {stats.get('min', 0)*1000:.2f} ms")
            print(f"   Max:        {stats.get('max', 0)*1000:.2f} ms")
            print(f"   P95:        {stats.get('p95', 0)*1000:.2f} ms")
            print(f"   P99:        {stats.get('p99', 0)*1000:.2f} ms")
            print(f"   StdDev:     {stats.get('stdev', 0)*1000:.2f} ms")
            print()
        
        print(f"{'='*80}\n")


# ============================================================
# SPECIFIC BENCHMARKS
# ============================================================

def benchmark_model_inference(model, sample_input, iterations: int = 100):
    """Benchmark model inference time"""
    suite = BenchmarkSuite('Model Inference')
    
    def inference():
        with torch.no_grad():
            _ = model(sample_input)
    
    suite.run_benchmark('inference_time', inference, iterations=iterations)
    return suite.get_summary()


def benchmark_database_operations(db, iterations: int = 100):
    """Benchmark database operations"""
    suite = BenchmarkSuite('Database Operations')
    
    # Benchmark insert
    def insert_operation():
        db.save_system_state({
            'field_size': 100,
            'iteration_count': 0,
            'is_running': False,
            'is_initialized': True
        })
    
    suite.run_benchmark('db_insert', insert_operation, iterations=iterations)
    
    # Benchmark select
    def select_operation():
        db.get_latest_system_state()
    
    suite.run_benchmark('db_select', select_operation, iterations=iterations)
    
    return suite.get_summary()


def benchmark_api_endpoints(client, iterations: int = 100):
    """Benchmark API endpoint response times"""
    suite = BenchmarkSuite('API Endpoints')
    
    endpoints = [
        ('/health', 'health_check'),
        ('/api/status', 'status'),
        ('/api/model/versions', 'model_versions'),
    ]
    
    for endpoint, name in endpoints:
        def api_call():
            client.get(endpoint)
        
        suite.run_benchmark(name, api_call, iterations=iterations)
    
    return suite.get_summary()


# ============================================================
# CONTINUOUS PERFORMANCE MONITORING
# ============================================================

class PerformanceMonitor:
    """
    Monitor performance metrics over time
    
    Usage:
        monitor = PerformanceMonitor()
        
        with monitor.track('operation_name'):
            # code to monitor
            pass
        
        monitor.save_metrics()
    """
    
    def __init__(self, metrics_file: Path = Path('performance_metrics.json')):
        self.metrics_file = metrics_file
        self.metrics: Dict[str, List[float]] = {}
    
    def track(self, operation_name: str):
        """Track operation performance"""
        return self._TrackContext(self, operation_name)
    
    class _TrackContext:
        def __init__(self, monitor: 'PerformanceMonitor', operation_name: str):
            self.monitor = monitor
            self.operation_name = operation_name
            self.start_time: Optional[float] = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.perf_counter() - self.start_time
            
            if self.operation_name not in self.monitor.metrics:
                self.monitor.metrics[self.operation_name] = []
            
            self.monitor.metrics[self.operation_name].append(duration)
            return False
    
    def get_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        if operation_name not in self.metrics:
            return {}
        
        measurements = self.metrics[operation_name]
        if not measurements:
            return {}
        
        return {
            'count': len(measurements),
            'mean': statistics.mean(measurements),
            'median': statistics.median(measurements),
            'min': min(measurements),
            'max': max(measurements),
            'stdev': statistics.stdev(measurements) if len(measurements) > 1 else 0
        }
    
    def save_metrics(self):
        """Save metrics to file"""
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operations': {
                name: {
                    'measurements': values,
                    'stats': self.get_stats(name)
                }
                for name, values in self.metrics.items()
            }
        }
        
        with open(self.metrics_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Performance metrics saved to {self.metrics_file}")


# Global performance monitor
performance_monitor = PerformanceMonitor()
