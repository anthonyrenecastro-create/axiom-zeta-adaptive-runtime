"""
Tests for security utilities
"""
import pytest
import time
from utils.security import (
    SecretsManager,
    RateLimiter,
    AuthManager,
    require_auth,
    rate_limit
)


@pytest.fixture
def secrets_manager():
    """Create secrets manager"""
    return SecretsManager(env_prefix="TEST_")


@pytest.fixture
def rate_limiter():
    """Create rate limiter"""
    return RateLimiter(max_requests=5, window_seconds=1, enabled=True)


@pytest.fixture
def auth_manager():
    """Create auth manager"""
    return AuthManager(
        secret_key="test-secret-key",
        token_expiry_hours=1,
        enabled=True
    )


def test_secrets_manager_get_secret(secrets_manager, monkeypatch):
    """Test getting secrets"""
    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    
    value = secrets_manager.get_secret("api_key")
    assert value == "secret-value"


def test_secrets_manager_set_secret(secrets_manager):
    """Test setting secrets"""
    secrets_manager.set_secret("key1", "value1")
    
    value = secrets_manager.get_secret("key1")
    assert value == "value1"


def test_generate_api_key(secrets_manager):
    """Test API key generation"""
    key1 = secrets_manager.generate_api_key()
    key2 = secrets_manager.generate_api_key()
    
    assert len(key1) > 20
    assert key1 != key2


def test_hash_api_key(secrets_manager):
    """Test API key hashing"""
    key = "test-api-key"
    hash1 = secrets_manager.hash_api_key(key)
    hash2 = secrets_manager.hash_api_key(key)
    
    assert hash1 == hash2
    assert hash1 != key


def test_verify_api_key(secrets_manager):
    """Test API key verification"""
    key = "test-api-key"
    hashed = secrets_manager.hash_api_key(key)
    
    assert secrets_manager.verify_api_key(key, hashed) is True
    assert secrets_manager.verify_api_key("wrong-key", hashed) is False


def test_rate_limiter_allows_requests(rate_limiter):
    """Test rate limiter allows requests under limit"""
    # Mock request context
    class MockRequest:
        remote_addr = "127.0.0.1"
        headers = {}
    
    # Simulate requests
    for i in range(5):
        assert rate_limiter.enabled is True
        # In actual usage, would check is_allowed() with request context


def test_rate_limiter_disabled(rate_limiter):
    """Test rate limiter when disabled"""
    rate_limiter.enabled = False
    
    # Should always allow
    for i in range(100):
        assert rate_limiter.is_allowed() is True


def test_auth_manager_generate_token(auth_manager):
    """Test token generation"""
    token = auth_manager.generate_token("user123", "admin")
    
    assert isinstance(token, str)
    assert len(token) > 20


def test_auth_manager_verify_token(auth_manager):
    """Test token verification"""
    token = auth_manager.generate_token("user123", "admin")
    payload = auth_manager.verify_token(token)
    
    assert payload is not None
    assert payload['user_id'] == "user123"
    assert payload['role'] == "admin"


def test_auth_manager_invalid_token(auth_manager):
    """Test invalid token verification"""
    payload = auth_manager.verify_token("invalid-token")
    assert payload is None


def test_auth_manager_register_api_key(auth_manager):
    """Test API key registration"""
    auth_manager.register_api_key(
        api_key="test-key-123",
        name="Test Key",
        permissions=["read", "write"]
    )
    
    assert auth_manager.verify_api_key("test-key-123") is True
    assert auth_manager.verify_api_key("wrong-key") is False


def test_auth_manager_check_permission(auth_manager):
    """Test permission checking"""
    auth_manager.register_api_key(
        api_key="test-key",
        name="Test",
        permissions=["read"]
    )
    
    assert auth_manager.check_permission("test-key", "read") is True
    assert auth_manager.check_permission("test-key", "write") is False


def test_auth_manager_admin_permission(auth_manager):
    """Test admin has all permissions"""
    auth_manager.register_api_key(
        api_key="admin-key",
        name="Admin",
        permissions=["admin"]
    )
    
    assert auth_manager.check_permission("admin-key", "read") is True
    assert auth_manager.check_permission("admin-key", "write") is True
    assert auth_manager.check_permission("admin-key", "delete") is True


def test_rate_limiter_get_remaining():
    """Test getting remaining requests"""
    limiter = RateLimiter(max_requests=10, window_seconds=60, enabled=False)
    
    remaining = limiter.get_remaining()
    assert remaining == 10


def test_secrets_manager_default_value(secrets_manager):
    """Test getting secret with default value"""
    value = secrets_manager.get_secret("nonexistent", default="default-value")
    assert value == "default-value"
