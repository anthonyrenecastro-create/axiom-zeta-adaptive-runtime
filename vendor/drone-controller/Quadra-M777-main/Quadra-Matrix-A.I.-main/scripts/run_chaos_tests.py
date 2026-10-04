#!/usr/bin/env python3
"""
Chaos Engineering Test Runner

This script runs chaos engineering experiments to test system resilience.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.chaos_engineering import (
    ChaosTestSuite,
    create_standard_chaos_suite,
    LatencyInjectionExperiment,
    ResourceExhaustionExperiment
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_standard_suite(base_url: str, duration: int):
    """Run standard chaos test suite."""
    logger.info("Creating standard chaos test suite...")
    suite = create_standard_chaos_suite(base_url)
    
    logger.info(f"Running {len(suite.experiments)} experiments...")
    results = suite.run_all(duration_per_experiment=duration)
    
    # Exit with error if any test failed
    if any(not r.success for r in results):
        sys.exit(1)


def run_latency_test(base_url: str, latency_ms: int, duration: int):
    """Run latency injection test."""
    logger.info(f"Running latency injection test ({latency_ms}ms)...")
    
    experiment = LatencyInjectionExperiment(
        name="latency_test",
        target_url=base_url,
        latency_ms=latency_ms
    )
    
    result = experiment.run(duration_seconds=duration)
    
    if result.success:
        logger.info("✓ Test PASSED")
    else:
        logger.error("✗ Test FAILED")
        sys.exit(1)


def run_resource_test(resource_type: str, duration: int):
    """Run resource exhaustion test."""
    logger.info(f"Running {resource_type} exhaustion test...")
    
    experiment = ResourceExhaustionExperiment(
        name=f"{resource_type}_exhaustion",
        resource_type=resource_type,
        exhaust_percentage=70
    )
    
    result = experiment.run(duration_seconds=duration)
    
    if result.success:
        logger.info("✓ Test PASSED")
    else:
        logger.error("✗ Test FAILED")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Chaos Engineering Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run standard test suite
  python scripts/run_chaos_tests.py --suite standard --duration 30

  # Run latency test
  python scripts/run_chaos_tests.py --test latency --latency 1000 --duration 60

  # Run resource exhaustion test
  python scripts/run_chaos_tests.py --test resource --resource cpu --duration 45
        """
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL of application to test (default: http://localhost:5000)'
    )
    
    parser.add_argument(
        '--suite',
        choices=['standard'],
        help='Run a predefined test suite'
    )
    
    parser.add_argument(
        '--test',
        choices=['latency', 'resource'],
        help='Run a specific test type'
    )
    
    parser.add_argument(
        '--latency',
        type=int,
        default=1000,
        help='Latency in milliseconds for latency test (default: 1000)'
    )
    
    parser.add_argument(
        '--resource',
        choices=['cpu', 'memory'],
        default='cpu',
        help='Resource type for exhaustion test (default: cpu)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration of each experiment in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Run tests
    try:
        if args.suite == 'standard':
            run_standard_suite(args.base_url, args.duration)
        
        elif args.test == 'latency':
            run_latency_test(args.base_url, args.latency, args.duration)
        
        elif args.test == 'resource':
            run_resource_test(args.resource, args.duration)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
