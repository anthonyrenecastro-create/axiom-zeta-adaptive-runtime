"""
Chaos Engineering Test Framework

This module provides chaos engineering capabilities for testing system resilience
by intentionally introducing failures and observing system behavior.

Features:
- Network latency injection
- Service failure simulation
- Resource exhaustion tests
- Dependency failure tests
- Automated recovery verification
"""

import time
import random
import threading
import requests
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


@dataclass
class ChaosExperimentResult:
    """Result of a chaos experiment."""
    experiment_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    success: bool = False
    failures_injected: int = 0
    system_recovered: bool = False
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)


class ChaosExperiment:
    """Base class for chaos experiments."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize chaos experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
        """
        self.name = name
        self.description = description
        self.result = ChaosExperimentResult(
            experiment_name=name,
            started_at=datetime.now()
        )
    
    def setup(self):
        """Setup experiment (override in subclasses)."""
        pass
    
    def inject_chaos(self):
        """Inject chaos (override in subclasses)."""
        raise NotImplementedError
    
    def verify_system(self) -> bool:
        """Verify system state (override in subclasses)."""
        return True
    
    def cleanup(self):
        """Cleanup experiment (override in subclasses)."""
        pass
    
    def run(self, duration_seconds: int = 60) -> ChaosExperimentResult:
        """
        Run the chaos experiment.
        
        Args:
            duration_seconds: Duration to run experiment
        
        Returns:
            Experiment result
        """
        logger.info(f"Starting chaos experiment: {self.name}")
        
        try:
            # Setup
            self.setup()
            self.result.observations.append("Experiment setup completed")
            
            # Verify system is healthy before chaos
            if not self.verify_system():
                self.result.errors.append("System unhealthy before chaos injection")
                return self.result
            
            self.result.observations.append("System verified healthy before chaos")
            
            # Inject chaos
            logger.info(f"Injecting chaos for {duration_seconds} seconds...")
            self.inject_chaos()
            self.result.failures_injected += 1
            self.result.observations.append("Chaos injected")
            
            # Monitor system during chaos
            time.sleep(duration_seconds)
            
            # Cleanup chaos
            self.cleanup()
            self.result.observations.append("Chaos cleaned up")
            
            # Verify system recovery
            time.sleep(5)  # Grace period for recovery
            self.result.system_recovered = self.verify_system()
            
            if self.result.system_recovered:
                self.result.observations.append("System recovered successfully")
                self.result.success = True
            else:
                self.result.errors.append("System failed to recover")
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            self.result.errors.append(str(e))
            self.cleanup()
        
        finally:
            self.result.ended_at = datetime.now()
            self.result.duration_seconds = (
                self.result.ended_at - self.result.started_at
            ).total_seconds()
        
        return self.result


class LatencyInjectionExperiment(ChaosExperiment):
    """Inject network latency to test system tolerance."""
    
    def __init__(
        self,
        name: str = "latency_injection",
        target_url: str = "http://localhost:5000",
        latency_ms: int = 1000
    ):
        """
        Initialize latency injection experiment.
        
        Args:
            name: Experiment name
            target_url: URL to test
            latency_ms: Latency to inject in milliseconds
        """
        super().__init__(name, f"Inject {latency_ms}ms latency")
        self.target_url = target_url
        self.latency_ms = latency_ms
        self._original_request = None
    
    def inject_chaos(self):
        """Inject latency into requests."""
        # Monkey patch requests to add latency
        import requests
        
        self._original_request = requests.request
        
        def delayed_request(*args, **kwargs):
            time.sleep(self.latency_ms / 1000.0)
            return self._original_request(*args, **kwargs)
        
        requests.request = delayed_request
        logger.info(f"Injected {self.latency_ms}ms latency")
    
    def cleanup(self):
        """Remove latency injection."""
        if self._original_request:
            import requests
            requests.request = self._original_request
            logger.info("Removed latency injection")
    
    def verify_system(self) -> bool:
        """Verify system is responding."""
        try:
            response = requests.get(f"{self.target_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"System verification failed: {e}")
            return False


class ServiceFailureExperiment(ChaosExperiment):
    """Simulate service failure."""
    
    def __init__(
        self,
        name: str = "service_failure",
        failure_function: Callable = None,
        recovery_function: Callable = None
    ):
        """
        Initialize service failure experiment.
        
        Args:
            name: Experiment name
            failure_function: Function to trigger failure
            recovery_function: Function to recover from failure
        """
        super().__init__(name, "Simulate service failure")
        self.failure_function = failure_function
        self.recovery_function = recovery_function
    
    def inject_chaos(self):
        """Inject service failure."""
        if self.failure_function:
            self.failure_function()
            logger.info("Service failure injected")
    
    def cleanup(self):
        """Recover service."""
        if self.recovery_function:
            self.recovery_function()
            logger.info("Service recovered")


class ResourceExhaustionExperiment(ChaosExperiment):
    """Test system under resource exhaustion."""
    
    def __init__(
        self,
        name: str = "resource_exhaustion",
        resource_type: str = "memory",
        exhaust_percentage: int = 80
    ):
        """
        Initialize resource exhaustion experiment.
        
        Args:
            name: Experiment name
            resource_type: Type of resource (memory, cpu)
            exhaust_percentage: Percentage of resource to consume
        """
        super().__init__(name, f"Exhaust {exhaust_percentage}% of {resource_type}")
        self.resource_type = resource_type
        self.exhaust_percentage = exhaust_percentage
        self._resources = []
    
    def inject_chaos(self):
        """Exhaust system resources."""
        if self.resource_type == "memory":
            # Allocate memory
            logger.info(f"Allocating memory...")
            for _ in range(100):
                self._resources.append([0] * (1024 * 1024))  # 1MB chunks
                time.sleep(0.1)
        
        elif self.resource_type == "cpu":
            # CPU intensive operations
            logger.info("Starting CPU-intensive operations...")
            
            def cpu_burn():
                end_time = time.time() + 60
                while time.time() < end_time:
                    _ = [i**2 for i in range(10000)]
            
            threads = []
            for _ in range(4):  # 4 threads
                t = threading.Thread(target=cpu_burn)
                t.start()
                threads.append(t)
            
            self._resources = threads
    
    def cleanup(self):
        """Release resources."""
        logger.info("Releasing resources...")
        self._resources.clear()


class DependencyFailureExperiment(ChaosExperiment):
    """Test system with dependency failures."""
    
    def __init__(
        self,
        name: str = "dependency_failure",
        dependency_name: str = "database",
        failure_rate: float = 0.5
    ):
        """
        Initialize dependency failure experiment.
        
        Args:
            name: Experiment name
            dependency_name: Name of dependency to fail
            failure_rate: Probability of failure (0-1)
        """
        super().__init__(name, f"Fail {dependency_name} at {failure_rate*100}% rate")
        self.dependency_name = dependency_name
        self.failure_rate = failure_rate
    
    def inject_chaos(self):
        """Inject dependency failures."""
        logger.info(f"Injecting {self.failure_rate*100}% failure rate for {self.dependency_name}")
        # This would typically use circuit breaker or service mesh
        # to inject failures at the network level


class ChaosTestSuite:
    """Suite for running multiple chaos experiments."""
    
    def __init__(self, name: str = "chaos_test_suite"):
        """
        Initialize chaos test suite.
        
        Args:
            name: Suite name
        """
        self.name = name
        self.experiments: List[ChaosExperiment] = []
        self.results: List[ChaosExperimentResult] = []
    
    def add_experiment(self, experiment: ChaosExperiment):
        """
        Add experiment to suite.
        
        Args:
            experiment: Chaos experiment to add
        """
        self.experiments.append(experiment)
    
    def run_all(self, duration_per_experiment: int = 60) -> List[ChaosExperimentResult]:
        """
        Run all experiments in suite.
        
        Args:
            duration_per_experiment: Duration for each experiment
        
        Returns:
            List of experiment results
        """
        logger.info(f"Running chaos test suite: {self.name}")
        logger.info(f"Total experiments: {len(self.experiments)}")
        
        self.results = []
        
        for i, experiment in enumerate(self.experiments, 1):
            logger.info(f"\n=== Experiment {i}/{len(self.experiments)}: {experiment.name} ===")
            
            result = experiment.run(duration_per_experiment)
            self.results.append(result)
            
            # Print result
            status = "✓ PASSED" if result.success else "✗ FAILED"
            logger.info(f"{status} - {experiment.name}")
            logger.info(f"Duration: {result.duration_seconds:.2f}s")
            logger.info(f"Recovered: {result.system_recovered}")
            
            if result.errors:
                logger.error(f"Errors: {', '.join(result.errors)}")
            
            # Wait between experiments
            if i < len(self.experiments):
                logger.info("Waiting 30s before next experiment...")
                time.sleep(30)
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test suite summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        print("\n" + "="*60)
        print(f"CHAOS TEST SUITE SUMMARY: {self.name}")
        print("="*60)
        print(f"Total Experiments: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print("="*60)
        
        for result in self.results:
            status = "✓" if result.success else "✗"
            recovered = "✓" if result.system_recovered else "✗"
            print(f"{status} {result.experiment_name:30s} | Recovered: {recovered} | Duration: {result.duration_seconds:.1f}s")
        
        print("="*60)


# Pre-configured chaos test suite
def create_standard_chaos_suite(
    base_url: str = "http://localhost:5000"
) -> ChaosTestSuite:
    """
    Create standard chaos engineering test suite.
    
    Args:
        base_url: Base URL of application to test
    
    Returns:
        Configured chaos test suite
    
    Example:
        >>> suite = create_standard_chaos_suite("http://localhost:5000")
        >>> results = suite.run_all(duration_per_experiment=30)
    """
    suite = ChaosTestSuite("Standard Chaos Tests")
    
    # Latency tests
    suite.add_experiment(LatencyInjectionExperiment(
        name="low_latency_test",
        target_url=base_url,
        latency_ms=500
    ))
    
    suite.add_experiment(LatencyInjectionExperiment(
        name="high_latency_test",
        target_url=base_url,
        latency_ms=2000
    ))
    
    # Resource exhaustion
    suite.add_experiment(ResourceExhaustionExperiment(
        name="memory_pressure_test",
        resource_type="memory",
        exhaust_percentage=70
    ))
    
    suite.add_experiment(ResourceExhaustionExperiment(
        name="cpu_pressure_test",
        resource_type="cpu",
        exhaust_percentage=80
    ))
    
    return suite
