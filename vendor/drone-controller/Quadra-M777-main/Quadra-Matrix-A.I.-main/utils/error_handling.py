"""
Error handling utilities and custom exceptions
"""
import logging
import traceback
import functools
from typing import Callable, Any, Optional
from flask import jsonify

logger = logging.getLogger(__name__)


class QuadraMatrixError(Exception):
    """Base exception for Quadra Matrix errors"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InitializationError(QuadraMatrixError):
    """Raised when system initialization fails"""
    pass


class TrainingError(QuadraMatrixError):
    """Raised when training fails"""
    pass


class StateError(QuadraMatrixError):
    """Raised when state operations fail"""
    pass


class ConfigurationError(QuadraMatrixError):
    """Raised when configuration is invalid"""
    pass


class ValidationError(QuadraMatrixError):
    """Raised when validation fails"""
    pass


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in functions
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation error in {func.__name__}: {e.message}")
            raise
        except QuadraMatrixError as e:
            logger.error(f"Quadra Matrix error in {func.__name__}: {e.message}")
            if e.details:
                logger.error(f"Details: {e.details}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            raise QuadraMatrixError(
                f"Unexpected error in {func.__name__}",
                details={'original_error': str(e)}
            )
    
    return wrapper


def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in API endpoints
    
    Args:
        func: API function to wrap
        
    Returns:
        Wrapped function with API error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return jsonify({
                'error': 'Validation Error',
                'message': e.message,
                'details': e.details
            }), 400
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e.message}")
            return jsonify({
                'error': 'Configuration Error',
                'message': e.message
            }), 500
        except QuadraMatrixError as e:
            logger.error(f"Quadra Matrix error: {e.message}")
            return jsonify({
                'error': e.__class__.__name__,
                'message': e.message,
                'details': e.details
            }), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }), 500
    
    return wrapper


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    error_msg: str = "Operation failed",
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Positional arguments
        default: Default value to return on error
        error_msg: Error message prefix
        **kwargs: Keyword arguments
        
    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_msg}: {str(e)}")
        return default


class ErrorContext:
    """Context manager for error handling"""
    
    def __init__(
        self,
        operation: str,
        raise_on_error: bool = True,
        log_level: int = logging.ERROR
    ):
        """
        Initialize error context
        
        Args:
            operation: Description of operation
            raise_on_error: Whether to re-raise exceptions
            log_level: Logging level for errors
        """
        self.operation = operation
        self.raise_on_error = raise_on_error
        self.log_level = log_level
        self.error: Optional[Exception] = None
    
    def __enter__(self):
        """Enter context"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and handle errors"""
        if exc_type is not None:
            self.error = exc_val
            logger.log(
                self.log_level,
                f"Error in {self.operation}: {exc_val}\n"
                f"{traceback.format_exc()}"
            )
            
            if self.raise_on_error:
                return False  # Re-raise exception
            else:
                return True  # Suppress exception
        
        return True


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry function on error
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for "
                            f"{func.__name__}: {str(e)}. Retrying in {current_delay}s"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


def log_exceptions(func: Callable) -> Callable:
    """
    Decorator to log exceptions without handling them
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
    
    return wrapper


def create_error_response(
    error: Exception,
    status_code: int = 500,
    include_details: bool = False
) -> tuple:
    """
    Create standardized error response
    
    Args:
        error: Exception that occurred
        status_code: HTTP status code
        include_details: Whether to include detailed error info
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'error': error.__class__.__name__,
        'message': str(error)
    }
    
    if include_details and isinstance(error, QuadraMatrixError):
        response['details'] = error.details
    
    return jsonify(response), status_code
