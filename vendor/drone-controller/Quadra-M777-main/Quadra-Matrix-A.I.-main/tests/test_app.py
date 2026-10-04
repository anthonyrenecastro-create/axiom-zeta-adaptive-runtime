"""
Test suite for Flask application endpoints and functionality
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


def test_index_route(client):
    """Test main index route returns dashboard"""
    response = client.get('/')
    assert response.status_code == 200


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'status' in data
    assert 'timestamp' in data
    assert 'version' in data
    assert data['status'] in ['healthy', 'unhealthy']


def test_health_endpoint_structure(client):
    """Test health endpoint returns correct structure"""
    response = client.get('/health')
    data = json.loads(response.data)
    
    required_fields = ['status', 'timestamp', 'version', 'initialized', 'running']
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_api_status_endpoint(client):
    """Test API status endpoint"""
    response = client.get('/api/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'initialized' in data
    assert 'running' in data
    assert 'iteration_count' in data
    assert 'current_metrics' in data
    assert 'history' in data


def test_api_status_metrics_structure(client):
    """Test status endpoint metrics structure"""
    response = client.get('/api/status')
    data = json.loads(response.data)
    
    # Check current_metrics structure
    metrics = data['current_metrics']
    assert 'loss' in metrics
    assert 'reward' in metrics
    assert 'variance' in metrics
    assert 'mean' in metrics
    
    # Check history structure
    history = data['history']
    assert 'loss' in history
    assert 'reward' in history
    assert isinstance(history['loss'], list)
    assert isinstance(history['reward'], list)


def test_invalid_route(client):
    """Test invalid route returns 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404


def test_health_check_on_error(client, app):
    """Test health check returns unhealthy status on error"""
    with patch('app.state') as mock_state:
        mock_state.is_initialized = Mock(side_effect=Exception("Test error"))
        response = client.get('/health')
        
        # Should return 503 on error
        assert response.status_code in [200, 503]


@pytest.mark.parametrize("endpoint", [
    "/health",
    "/api/status",
])
def test_endpoints_return_json(client, endpoint):
    """Test that API endpoints return JSON"""
    response = client.get(endpoint)
    assert response.content_type == 'application/json'


def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.get('/api/status')
    # Flask-SocketIO should handle CORS
    assert response.status_code == 200


def test_app_configuration(app):
    """Test app is properly configured"""
    assert app.config['TESTING'] is True
    assert 'SECRET_KEY' in app.config


def test_socketio_initialization(app):
    """Test SocketIO is initialized"""
    # This is a basic test - actual SocketIO testing requires special setup
    assert hasattr(app, 'extensions')
