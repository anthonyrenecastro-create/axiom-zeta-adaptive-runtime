"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'
    
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    
    yield flask_app
    
    # Cleanup
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture
def mock_model_path(temp_dir):
    """Create temporary model storage path"""
    model_dir = temp_dir / 'models'
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def mock_config(temp_dir):
    """Create mock configuration"""
    class MockConfig:
        BASE_DIR = temp_dir
        MODEL_ARTIFACTS_DIR = temp_dir / 'models'
        DASHBOARD_STATE_DIR = temp_dir / 'dashboard_state'
        LOGS_DIR = temp_dir / 'logs'
        DATA_DIR = temp_dir / 'data'
        FIELD_SIZE = 50
        NUM_BATCHES = 5
        BATCH_SIZE = 2
        DEBUG = True
        TESTING = True
        
        MODEL_ARTIFACTS_DIR.mkdir(exist_ok=True)
        DASHBOARD_STATE_DIR.mkdir(exist_ok=True)
        LOGS_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
    
    return MockConfig()
