"""
Tests for validation utilities
"""
import pytest
import torch
import numpy as np
from utils.validation import (
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


class TestFieldSizeValidation:
    """Test field size validation"""
    
    def test_valid_field_size(self):
        """Test valid field sizes"""
        assert validate_field_size(100) == 100
        assert validate_field_size(1) == 1
        assert validate_field_size(1000) == 1000
    
    def test_invalid_field_size_type(self):
        """Test invalid type raises error"""
        with pytest.raises(ValidationError):
            validate_field_size("100")
        
        with pytest.raises(ValidationError):
            validate_field_size(100.5)
    
    def test_negative_field_size(self):
        """Test negative size raises error"""
        with pytest.raises(ValidationError):
            validate_field_size(-1)
        
        with pytest.raises(ValidationError):
            validate_field_size(0)


class TestTensorValidation:
    """Test tensor validation"""
    
    def test_valid_tensor(self):
        """Test valid tensor"""
        tensor = torch.randn(10)
        result = validate_tensor(tensor)
        assert isinstance(result, torch.Tensor)
    
    def test_numpy_conversion(self):
        """Test numpy array conversion"""
        array = np.random.randn(10)
        result = validate_tensor(array)
        assert isinstance(result, torch.Tensor)
    
    def test_nan_detection(self):
        """Test NaN detection"""
        tensor = torch.tensor([1.0, float('nan'), 3.0])
        with pytest.raises(ValidationError):
            validate_tensor(tensor)
    
    def test_inf_detection(self):
        """Test Inf detection"""
        tensor = torch.tensor([1.0, float('inf'), 3.0])
        with pytest.raises(ValidationError):
            validate_tensor(tensor)
    
    def test_shape_validation(self):
        """Test shape validation"""
        tensor = torch.randn(10, 5)
        validate_tensor(tensor, expected_shape=(10, 5))
        
        with pytest.raises(ValidationError):
            validate_tensor(tensor, expected_shape=(5, 10))
    
    def test_none_tensor(self):
        """Test None raises error"""
        with pytest.raises(ValidationError):
            validate_tensor(None)


class TestTextValidation:
    """Test text input validation"""
    
    def test_valid_text(self):
        """Test valid text"""
        text = "Hello, world!"
        assert validate_text_input(text) == text
    
    def test_empty_text(self):
        """Test empty text raises error"""
        with pytest.raises(ValidationError):
            validate_text_input("")
        
        with pytest.raises(ValidationError):
            validate_text_input("   ")
    
    def test_non_string(self):
        """Test non-string raises error"""
        with pytest.raises(ValidationError):
            validate_text_input(123)
    
    def test_long_text_truncation(self):
        """Test long text is truncated"""
        long_text = "a" * 15000
        result = validate_text_input(long_text, max_length=10000)
        assert len(result) == 10000


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_validate_batch_size(self):
        """Test batch size validation"""
        assert validate_batch_size(10) == 10
        
        with pytest.raises(ValidationError):
            validate_batch_size(0)
        
        with pytest.raises(ValidationError):
            validate_batch_size(10000)
    
    def test_validate_num_batches(self):
        """Test number of batches validation"""
        assert validate_num_batches(100) == 100
        
        with pytest.raises(ValidationError):
            validate_num_batches(0)
    
    def test_validate_learning_rate(self):
        """Test learning rate validation"""
        assert validate_learning_rate(0.001) == 0.001
        
        with pytest.raises(ValidationError):
            validate_learning_rate(0.0)
        
        with pytest.raises(ValidationError):
            validate_learning_rate(2.0)
    
    def test_allowed_values(self):
        """Test allowed values validation"""
        result = validate_config_value(
            "production",
            "env",
            str,
            allowed_values=["development", "production", "testing"]
        )
        assert result == "production"
        
        with pytest.raises(ValidationError):
            validate_config_value(
                "invalid",
                "env",
                str,
                allowed_values=["development", "production"]
            )


class TestFilenameValidation:
    """Test filename sanitization"""
    
    def test_sanitize_valid_filename(self):
        """Test valid filename"""
        filename = "model_weights.pth"
        assert sanitize_filename(filename) == filename
    
    def test_sanitize_path_traversal(self):
        """Test path traversal prevention"""
        filename = "../../../etc/passwd"
        result = sanitize_filename(filename)
        assert ".." not in result
        assert "/" not in result
    
    def test_sanitize_special_characters(self):
        """Test special character removal"""
        filename = "model@#$%weights.pth"
        result = sanitize_filename(filename)
        assert "@" not in result
        assert "#" not in result


class TestModelStateValidation:
    """Test model state validation"""
    
    def test_valid_state(self):
        """Test valid state dictionary"""
        state = {'weight': torch.randn(10, 10), 'bias': torch.randn(10)}
        result = validate_model_state(state)
        assert result == state
    
    def test_invalid_state_type(self):
        """Test invalid state type"""
        with pytest.raises(ValidationError):
            validate_model_state("not a dict")
    
    def test_empty_state(self):
        """Test empty state"""
        with pytest.raises(ValidationError):
            validate_model_state({})


class TestMetricsValidation:
    """Test metrics validation"""
    
    def test_valid_metrics(self):
        """Test valid metrics"""
        metrics = {'loss': 0.5, 'reward': 7.3, 'accuracy': 0.95}
        result = validate_metrics(metrics)
        assert result == metrics
    
    def test_missing_required_field(self):
        """Test missing required field"""
        metrics = {'reward': 7.3}
        with pytest.raises(ValidationError):
            validate_metrics(metrics)
    
    def test_list_metrics(self):
        """Test metrics with lists"""
        metrics = {'loss': [0.5, 0.4, 0.3], 'reward': [7.1, 7.2, 7.3]}
        result = validate_metrics(metrics)
        assert result == metrics
