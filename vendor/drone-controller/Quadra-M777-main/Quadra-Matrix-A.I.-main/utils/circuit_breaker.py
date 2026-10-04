"""
Circuit Breaker Pattern Implementation

This module implements the Circuit Breaker pattern for fault tolerance,
preventing cascading failures in distributed systems.

Features:
- Circuit breaker with open/half-open/closed states
- Configurable failure thresholds
- Automatic recovery attempts
- Fallback function support
- Monitoring and metrics
- Thread-safe implementation
"""

import time
import threading
from typing import Callable, Optional, Any, Dict
from functools import wraps
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation, requests allowed
    OPEN = "open"            # Too many failures, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: Dict[str, int] = field(default_factory=lambda: {
        "closed_to_open": 0,
        "open_to_half_open": 0,
        "half_open_to_closed": 0,
        "half_open_to_open": 0
    })
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit Breaker implementation for fault tolerance.
    
    The circuit breaker prevents cascading failures by:
    1. CLOSED: Allows all requests, monitors failures
    2. OPEN: Blocks requests after threshold, returns fallback
    3. HALF_OPEN: Allows test requests to check recovery
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery (half-open)
            expected_exception: Exception type to catch
            name: Circuit breaker name for identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "default"
        
        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_attempts = 0
        
        # Metrics
        self.metrics = CircuitBreakerMetrics()
        
        # Thread safety
        self._lock = threading.RLock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        with self._lock:
            if self._state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
                )
                old_state = self._state.value
                self._state = CircuitState.OPEN
                self._last_failure_time = time.time()
                self.metrics.state_changes[f"{old_state}_to_open"] += 1
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                logger.info(f"Circuit breaker '{self.name}' entering half-open state")
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
                self.metrics.state_changes["open_to_half_open"] += 1
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        with self._lock:
            if self._state != CircuitState.CLOSED:
                logger.info(f"Circuit breaker '{self.name}' closed (recovered)")
                old_state = self._state.value
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_attempts = 0
                self.metrics.state_changes[f"{old_state}_to_closed"] += 1
    
    def _check_recovery(self):
        """Check if circuit should attempt recovery."""
        with self._lock:
            if self._state == CircuitState.OPEN and self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._transition_to_half_open()
    
    def _record_success(self):
        """Record successful request."""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Successful request in half-open, consider closing
                self._half_open_attempts += 1
                if self._half_open_attempts >= 3:  # 3 successful attempts
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def _record_failure(self):
        """Record failed request."""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed during half-open, reopen circuit
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                # Increment failure count
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
    
    def _record_rejected(self):
        """Record rejected request."""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.rejected_requests += 1
    
    def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments for function
            fallback: Fallback function if circuit is open
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result or fallback result
        
        Raises:
            CircuitBreakerError: If circuit is open and no fallback provided
        """
        # Check if recovery should be attempted
        self._check_recovery()
        
        # Check circuit state
        with self._lock:
            if self._state == CircuitState.OPEN:
                self._record_rejected()
                if fallback:
                    logger.debug(f"Circuit '{self.name}' open, using fallback")
                    return fallback(*args, **kwargs)
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
        
        # Attempt to call function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            logger.error(
                f"Circuit breaker '{self.name}' caught exception: {e}"
            )
            
            # Use fallback if available
            if fallback:
                return fallback(*args, **kwargs)
            else:
                raise
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for circuit breaker.
        
        Example:
            >>> breaker = CircuitBreaker(failure_threshold=3)
            >>> @breaker
            >>> def unreliable_service():
            >>>     return external_api_call()
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.
        
        Returns:
            Dictionary of metrics
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "rejected_requests": self.metrics.rejected_requests,
                "success_rate": (
                    self.metrics.successful_requests / self.metrics.total_requests * 100
                    if self.metrics.total_requests > 0 else 0
                ),
                "state_changes": self.metrics.state_changes,
                "last_failure_time": (
                    self.metrics.last_failure_time.isoformat()
                    if self.metrics.last_failure_time else None
                ),
                "last_success_time": (
                    self.metrics.last_success_time.isoformat()
                    if self.metrics.last_success_time else None
                )
            }
    
    def reset(self):
        """Reset circuit breaker to closed state."""
        with self._lock:
            logger.info(f"Circuit breaker '{self.name}' manually reset")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_attempts = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        """Initialize circuit breaker registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.
        
        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before recovery attempt
            expected_exception: Exception type to catch
        
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name in self._breakers:
                return self._breakers[name]
            
            breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                name=name
            )
            self._breakers[name] = breaker
            return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get circuit breaker by name.
        
        Args:
            name: Circuit breaker name
        
        Returns:
            CircuitBreaker instance or None
        """
        with self._lock:
            return self._breakers.get(name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all circuit breakers.
        
        Returns:
            Dictionary mapping names to metrics
        """
        with self._lock:
            return {
                name: breaker.get_metrics()
                for name, breaker in self._breakers.items()
            }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global circuit breaker registry
_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator for applying circuit breaker to functions.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds before recovery attempt
        expected_exception: Exception type to catch
    
    Example:
        >>> @circuit_breaker("external_api", failure_threshold=3, recovery_timeout=30)
        >>> def call_external_api():
        >>>     return requests.get("https://api.example.com/data")
    """
    breaker = _registry.register(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception
    )
    return breaker


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """
    Get circuit breaker by name from global registry.
    
    Args:
        name: Circuit breaker name
    
    Returns:
        CircuitBreaker instance or None
    """
    return _registry.get(name)


def get_all_circuit_breaker_metrics() -> Dict[str, Dict[str, Any]]:
    """
    Get metrics for all circuit breakers.
    
    Returns:
        Dictionary mapping names to metrics
    """
    return _registry.get_all_metrics()


def reset_all_circuit_breakers():
    """Reset all circuit breakers in global registry."""
    _registry.reset_all()


# Example usage with external services
class ExternalServiceCircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, service_name: str):
        """
        Initialize external service circuit breaker.
        
        Args:
            service_name: Name of external service
        """
        self.breaker = _registry.register(
            name=f"external_service_{service_name}",
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
    
    def call(
        self,
        func: Callable,
        *args,
        fallback_value: Any = None,
        **kwargs
    ) -> Any:
        """
        Call external service with circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            fallback_value: Value to return if circuit is open
            **kwargs: Keyword arguments
        
        Returns:
            Function result or fallback value
        """
        def fallback(*args, **kwargs):
            return fallback_value
        
        return self.breaker.call(func, *args, fallback=fallback, **kwargs)
