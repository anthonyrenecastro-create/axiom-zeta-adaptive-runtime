"""
Tests for configuration module
"""
import os
import pytest
from pathlib import Path
from config import Config, DevelopmentConfig, ProductionConfig, get_config


def test_default_config():
    """Test default configuration values"""
    config = Config()
    assert config.APP_NAME == "Quadra Matrix A.I."
    assert config.VERSION == "1.0.0"
    assert config.FIELD_SIZE == 100
    assert config.DEVICE == 'cpu'


def test_development_config():
    """Test development configuration"""
    config = DevelopmentConfig()
    assert config.DEBUG is True
    assert config.FLASK_ENV == 'development'
    assert config.LOG_LEVEL == 'DEBUG'


def test_production_config():
    """Test production configuration"""
    config = ProductionConfig()
    assert config.DEBUG is False
    assert config.FLASK_ENV == 'production'
    assert config.LOG_LEVEL == 'WARNING'


def test_get_config():
    """Test config retrieval"""
    dev_config = get_config('development')
    assert isinstance(dev_config, type)
    assert dev_config.DEBUG is True
    
    # Production config requires SECRET_KEY to be set
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
    try:
        prod_config = get_config('production')
        assert prod_config.DEBUG is False
    finally:
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']


def test_model_paths():
    """Test model path generation"""
    config = Config()
    model_path = config.get_model_path('test.pth')
    assert isinstance(model_path, Path)
    assert model_path.name == 'test.pth'


def test_environment_override():
    """Test environment variable override"""
    original_value = os.getenv('FIELD_SIZE')
    os.environ['FIELD_SIZE'] = '200'
    try:
        # Need to reimport config to pick up environment changes
        import importlib
        import config as config_module
        importlib.reload(config_module)
        from config import Config
        assert Config.FIELD_SIZE == 200
    finally:
        if original_value:
            os.environ['FIELD_SIZE'] = original_value
        elif 'FIELD_SIZE' in os.environ:
            del os.environ['FIELD_SIZE']
        # Reload again to restore original state
        importlib.reload(config_module)


def test_directories_created():
    """Test that required directories are created"""
    config = Config()
    assert config.MODEL_ARTIFACTS_DIR.exists()
    assert config.DASHBOARD_STATE_DIR.exists()
    assert config.LOGS_DIR.exists()
