"""
Tests for error handling utilities
"""
import pytest
from utils.error_handling import (
    QuadraMatrixError,
    InitializationError,
    TrainingError,
    StateError,
    ConfigurationError,
    ValidationError,
    handle_errors,
    handle_api_errors,
    safe_execute,
    ErrorContext,
    retry_on_error,
    log_exceptions
)


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_base_exception(self):
        """Test base QuadraMatrixError"""
        error = QuadraMatrixError("Test error", details={'key': 'value'})
        assert error.message == "Test error"
        assert error.details == {'key': 'value'}
    
    def test_initialization_error(self):
        """Test InitializationError"""
        error = InitializationError("Init failed")
        assert isinstance(error, QuadraMatrixError)
    
    def test_training_error(self):
        """Test TrainingError"""
        error = TrainingError("Training failed")
        assert isinstance(error, QuadraMatrixError)


class TestHandleErrors:
    """Test error handling decorators"""
    
    def test_handle_errors_success(self):
        """Test decorator with successful execution"""
        @handle_errors
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_handle_errors_validation_error(self):
        """Test decorator with ValidationError"""
        @handle_errors
        def failing_function():
            raise ValidationError("Invalid input")
        
        with pytest.raises(ValidationError):
            failing_function()
    
    def test_handle_errors_unexpected_error(self):
        """Test decorator with unexpected error"""
        @handle_errors
        def failing_function():
            raise ValueError("Unexpected")
        
        with pytest.raises(QuadraMatrixError):
            failing_function()


class TestSafeExecute:
    """Test safe execution utility"""
    
    def test_safe_execute_success(self):
        """Test successful execution"""
        def func(x):
            return x * 2
        
        result = safe_execute(func, 5)
        assert result == 10
    
    def test_safe_execute_error(self):
        """Test error returns default"""
        def func():
            raise ValueError("Error")
        
        result = safe_execute(func, default="default value")
        assert result == "default value"


class TestErrorContext:
    """Test ErrorContext manager"""
    
    def test_error_context_no_error(self):
        """Test context without error"""
        with ErrorContext("test operation") as ctx:
            x = 1 + 1
        
        assert ctx.error is None
    
    def test_error_context_with_error_raise(self):
        """Test context with error (raise)"""
        with pytest.raises(ValueError):
            with ErrorContext("test operation", raise_on_error=True):
                raise ValueError("Test error")
    
    def test_error_context_with_error_suppress(self):
        """Test context with error (suppress)"""
        with ErrorContext("test operation", raise_on_error=False) as ctx:
            raise ValueError("Test error")
        
        assert ctx.error is not None


class TestRetryOnError:
    """Test retry decorator"""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        call_count = [0]
        
        @retry_on_error(max_attempts=3)
        def func():
            call_count[0] += 1
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_success_after_failures(self):
        """Test successful execution after failures"""
        call_count = [0]
        
        @retry_on_error(max_attempts=3, delay=0.01)
        def func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_all_attempts_fail(self):
        """Test all attempts fail"""
        @retry_on_error(max_attempts=3, delay=0.01)
        def func():
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError):
            func()


class TestLogExceptions:
    """Test exception logging decorator"""
    
    def test_log_exceptions_success(self):
        """Test decorator with successful execution"""
        @log_exceptions
        def func():
            return "success"
        
        result = func()
        assert result == "success"
    
    def test_log_exceptions_error(self):
        """Test decorator logs and re-raises"""
        @log_exceptions
        def func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            func()
