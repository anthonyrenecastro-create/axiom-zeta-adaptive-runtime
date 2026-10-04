"""
Utility functions package
"""
from .validation import (
    ValidationError,
    validate_field_size,
    validate_tensor,
    validate_text_input,
    validate_config_value,
    validate_batch_size,
    validate_num_batches,
    validate_learning_rate,
    sanitize_filename,
    validate_model_state,
    validate_metrics
)

from .error_handling import (
    QuadraMatrixError,
    InitializationError,
    TrainingError,
    StateError,
    ConfigurationError,
    handle_errors,
    handle_api_errors,
    safe_execute,
    ErrorContext,
    retry_on_error,
    log_exceptions,
    create_error_response
)

from .logging_config import (
    setup_logging,
    LoggerContext,
    log_function_call,
    log_performance,
    StructuredLogger,
    get_logger
)

__all__ = [
    # Validation
    'ValidationError',
    'validate_field_size',
    'validate_tensor',
    'validate_text_input',
    'validate_config_value',
    'validate_batch_size',
    'validate_num_batches',
    'validate_learning_rate',
    'sanitize_filename',
    'validate_model_state',
    'validate_metrics',
    
    # Error Handling
    'QuadraMatrixError',
    'InitializationError',
    'TrainingError',
    'StateError',
    'ConfigurationError',
    'handle_errors',
    'handle_api_errors',
    'safe_execute',
    'ErrorContext',
    'retry_on_error',
    'log_exceptions',
    'create_error_response',
    
    # Logging
    'setup_logging',
    'LoggerContext',
    'log_function_call',
    'log_performance',
    'StructuredLogger',
    'get_logger',
]
