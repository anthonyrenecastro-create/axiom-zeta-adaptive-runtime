#!/usr/bin/env python3
"""
Performance Benchmark Script for Quadra Matrix A.I.
Run comprehensive performance tests
"""
import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.benchmarks import BenchmarkSuite, performance_monitor
import time
import numpy as np

def benchmark_numpy_operations():
    """Benchmark NumPy operations"""
    suite = BenchmarkSuite('NumPy Operations')
    
    # Matrix multiplication
    def matrix_mult():
        a = np.random.rand(100, 100)
        b = np.random.rand(100, 100)
        _ = np.dot(a, b)
    
    suite.run_benchmark('matrix_multiplication_100x100', matrix_mult, iterations=100)
    
    # FFT
    def fft_op():
        data = np.random.rand(1000)
        _ = np.fft.fft(data)
    
    suite.run_benchmark('fft_1000_elements', fft_op, iterations=100)
    
    # Eigenvalue computation
    def eigen_op():
        a = np.random.rand(50, 50)
        _ = np.linalg.eig(a)
    
    suite.run_benchmark('eigenvalue_50x50', eigen_op, iterations=50)
    
    return suite


def benchmark_field_operations():
    """Benchmark field operations"""
    suite = BenchmarkSuite('Field Operations')
    
    # Field initialization
    def init_field():
        field = np.random.randn(100, 100)
        return field
    
    suite.run_benchmark('field_init_100x100', init_field, iterations=100)
    
    # Field updates
    def update_field():
        field = np.random.randn(100, 100)
        field = field + np.random.randn(100, 100) * 0.1
        field = np.clip(field, -1, 1)
    
    suite.run_benchmark('field_update_100x100', update_field, iterations=100)
    
    # Field statistics
    def field_stats():
        field = np.random.randn(100, 100)
        mean = np.mean(field)
        var = np.var(field)
        std = np.std(field)
    
    suite.run_benchmark('field_statistics_100x100', field_stats, iterations=100)
    
    return suite


def benchmark_json_operations():
    """Benchmark JSON serialization"""
    suite = BenchmarkSuite('JSON Operations')
    
    import json
    
    data = {
        'field_size': 100,
        'iteration_count': 1000,
        'loss_history': list(np.random.rand(100)),
        'reward_history': list(np.random.rand(100)),
        'metadata': {
            'version': '1.0.0',
            'timestamp': '2025-12-21T00:00:00Z'
        }
    }
    
    def serialize():
        _ = json.dumps(data)
    
    suite.run_benchmark('json_serialize', serialize, iterations=100)
    
    serialized = json.dumps(data)
    
    def deserialize():
        _ = json.loads(serialized)
    
    suite.run_benchmark('json_deserialize', deserialize, iterations=100)
    
    return suite


def main():
    parser = argparse.ArgumentParser(description='Run Quadra Matrix performance benchmarks')
    parser.add_argument(
        '--output',
        type=str,
        default='benchmarks/results.json',
        help='Output file for results'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of iterations per benchmark'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed output'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("QUADRA MATRIX A.I. - PERFORMANCE BENCHMARKS")
    print("=" * 80)
    print()
    
    # Run benchmarks
    suites = []
    
    print("🔬 Running NumPy operations benchmark...")
    suite = benchmark_numpy_operations()
    suite.print_summary()
    suites.append(suite)
    
    print("🔬 Running field operations benchmark...")
    suite = benchmark_field_operations()
    suite.print_summary()
    suites.append(suite)
    
    print("🔬 Running JSON operations benchmark...")
    suite = benchmark_json_operations()
    suite.print_summary()
    suites.append(suite)
    
    # Combine results
    print("💾 Saving results...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    combined_results = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'iterations': args.iterations,
        'suites': [suite.get_summary() for suite in suites]
    }
    
    with open(output_path, 'w') as f:
        json.dump(combined_results, f, indent=2)
    
    print(f"✅ Results saved to {output_path}")
    print()
    print("=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
