"""
Validation utilities for input/output data
"""
import torch
import numpy as np
from typing import Union, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_field_size(size: int) -> int:
    """
    Validate field size parameter
    
    Args:
        size: Field size to validate
        
    Returns:
        Validated size
        
    Raises:
        ValidationError: If size is invalid
    """
    if not isinstance(size, int):
        raise ValidationError(f"Field size must be integer, got {type(size)}")
    
    if size <= 0:
        raise ValidationError(f"Field size must be positive, got {size}")
    
    if size > 10000:
        logger.warning(f"Large field size {size} may impact performance")
    
    return size


def validate_tensor(
    tensor: Union[torch.Tensor, np.ndarray],
    expected_shape: Optional[tuple] = None,
    name: str = "tensor"
) -> torch.Tensor:
    """
    Validate and convert tensor input
    
    Args:
        tensor: Tensor to validate
        expected_shape: Expected shape (optional)
        name: Name for error messages
        
    Returns:
        Validated torch.Tensor
        
    Raises:
        ValidationError: If tensor is invalid
    """
    if tensor is None:
        raise ValidationError(f"{name} cannot be None")
    
    # Convert to tensor if needed
    if isinstance(tensor, np.ndarray):
        tensor = torch.tensor(tensor, dtype=torch.float32)
    elif not isinstance(tensor, torch.Tensor):
        raise ValidationError(
            f"{name} must be torch.Tensor or numpy.ndarray, got {type(tensor)}"
        )
    
    # Check for NaN or Inf
    if torch.isnan(tensor).any():
        raise ValidationError(f"{name} contains NaN values")
    
    if torch.isinf(tensor).any():
        raise ValidationError(f"{name} contains Inf values")
    
    # Check shape if specified
    if expected_shape is not None:
        if tensor.shape != expected_shape:
            raise ValidationError(
                f"{name} shape mismatch: expected {expected_shape}, got {tensor.shape}"
            )
    
    return tensor


def validate_text_input(text: str, max_length: int = 10000) -> str:
    """
    Validate text input
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated text
        
    Raises:
        ValidationError: If text is invalid
    """
    if not isinstance(text, str):
        raise ValidationError(f"Text must be string, got {type(text)}")
    
    if not text or not text.strip():
        raise ValidationError("Text cannot be empty")
    
    if len(text) > max_length:
        logger.warning(f"Text length {len(text)} exceeds recommended {max_length}")
        text = text[:max_length]
    
    return text


def validate_config_value(
    value: Any,
    name: str,
    value_type: type,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    allowed_values: Optional[list] = None
) -> Any:
    """
    Validate configuration value
    
    Args:
        value: Value to validate
        name: Parameter name
        value_type: Expected type
        min_value: Minimum allowed value (for numbers)
        max_value: Maximum allowed value (for numbers)
        allowed_values: List of allowed values
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, value_type):
        raise ValidationError(
            f"{name} must be {value_type.__name__}, got {type(value).__name__}"
        )
    
    if allowed_values is not None and value not in allowed_values:
        raise ValidationError(
            f"{name} must be one of {allowed_values}, got {value}"
        )
    
    if isinstance(value, (int, float)):
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{name} must be >= {min_value}, got {value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{name} must be <= {max_value}, got {value}"
            )
    
    return value


def validate_batch_size(batch_size: int) -> int:
    """Validate batch size"""
    return validate_config_value(
        batch_size,
        "batch_size",
        int,
        min_value=1,
        max_value=1000
    )


def validate_num_batches(num_batches: int) -> int:
    """Validate number of batches"""
    return validate_config_value(
        num_batches,
        "num_batches",
        int,
        min_value=1,
        max_value=100000
    )


def validate_learning_rate(lr: float) -> float:
    """Validate learning rate"""
    return validate_config_value(
        lr,
        "learning_rate",
        float,
        min_value=1e-6,
        max_value=1.0
    )


def validate_environment(env: str) -> str:
    """Validate environment setting"""
    return validate_config_value(
        env,
        "environment",
        str,
        allowed_values=['development', 'production', 'testing']
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    import os
    import re
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove special characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    if not filename:
        raise ValidationError("Invalid filename after sanitization")
    
    return filename


def validate_model_state(state_dict: dict) -> dict:
    """
    Validate model state dictionary
    
    Args:
        state_dict: Model state dictionary
        
    Returns:
        Validated state dictionary
        
    Raises:
        ValidationError: If state is invalid
    """
    if not isinstance(state_dict, dict):
        raise ValidationError(f"State must be dict, got {type(state_dict)}")
    
    if not state_dict:
        raise ValidationError("State dictionary is empty")
    
    # Check for reasonable size (prevent loading huge malicious files)
    import sys
    size = sys.getsizeof(state_dict)
    if size > 1e9:  # 1GB
        logger.warning(f"Large state dictionary: {size / 1e6:.1f} MB")
    
    return state_dict


def validate_metrics(metrics: dict) -> dict:
    """
    Validate training metrics
    
    Args:
        metrics: Metrics dictionary
        
    Returns:
        Validated metrics
        
    Raises:
        ValidationError: If metrics are invalid
    """
    if not isinstance(metrics, dict):
        raise ValidationError(f"Metrics must be dict, got {type(metrics)}")
    
    required_fields = ['loss', 'reward']
    for field in required_fields:
        if field not in metrics:
            raise ValidationError(f"Missing required metric: {field}")
        
        value = metrics[field]
        if not isinstance(value, (int, float, list)):
            raise ValidationError(
                f"Metric {field} must be numeric or list, got {type(value)}"
            )
    
    return metrics
