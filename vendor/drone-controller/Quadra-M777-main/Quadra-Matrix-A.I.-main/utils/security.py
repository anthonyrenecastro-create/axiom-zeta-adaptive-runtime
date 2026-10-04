"""
Security utilities: authentication, rate limiting, secrets management
"""
import os
import time
import logging
import hashlib
import secrets
from functools import wraps
from typing import Optional, Callable, Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import request, jsonify
import jwt

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manage application secrets securely"""
    
    def __init__(self, env_prefix: str = "QUADRA_"):
        """
        Initialize secrets manager
        
        Args:
            env_prefix: Prefix for environment variables
        """
        self.env_prefix = env_prefix
        self._secrets_cache = {}
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from environment or cache
        
        Args:
            key: Secret key name
            default: Default value if not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # Try environment variable
        env_key = f"{self.env_prefix}{key.upper()}"
        value = os.getenv(env_key, default)
        
        if value:
            self._secrets_cache[key] = value
        
        return value
    
    def set_secret(self, key: str, value: str):
        """
        Set secret in cache (not persisted)
        
        Args:
            key: Secret key name
            value: Secret value
        """
        self._secrets_cache[key] = value
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return self.hash_api_key(api_key) == hashed_key


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        enabled: bool = True
    ):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            enabled: Whether rate limiting is enabled
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def _get_client_id(self) -> str:
        """Get client identifier from request"""
        # Try API key first
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"key_{hashlib.md5(api_key.encode()).hexdigest()[:8]}"
        
        # Fall back to IP address
        return request.remote_addr or 'unknown'
    
    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limit"""
        if not self.enabled:
            return True
        
        client_id = self._get_client_id()
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Remove old requests
        while self.requests[client_id] and self.requests[client_id][0] < cutoff:
            self.requests[client_id].popleft()
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self) -> int:
        """Get remaining requests in current window"""
        if not self.enabled:
            return self.max_requests
        
        client_id = self._get_client_id()
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Count recent requests
        recent_requests = sum(1 for t in self.requests[client_id] if t >= cutoff)
        return max(0, self.max_requests - recent_requests)
    
    def get_reset_time(self) -> float:
        """Get time until rate limit reset"""
        if not self.enabled:
            return 0
        
        client_id = self._get_client_id()
        if not self.requests[client_id]:
            return 0
        
        oldest_request = self.requests[client_id][0]
        reset_time = oldest_request + self.window_seconds
        return max(0, reset_time - time.time())


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(
        self,
        secret_key: str,
        token_expiry_hours: int = 24,
        enabled: bool = True
    ):
        """
        Initialize auth manager
        
        Args:
            secret_key: Secret key for JWT signing
            token_expiry_hours: Token validity period
            enabled: Whether auth is enabled
        """
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours
        self.enabled = enabled
        self.api_keys: Dict[str, Dict[str, Any]] = {}  # API key -> metadata
    
    def generate_token(self, user_id: str, role: str = "user") -> str:
        """
        Generate JWT token
        
        Args:
            user_id: User identifier
            role: User role (user, admin, etc.)
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def register_api_key(
        self,
        api_key: str,
        name: str,
        permissions: list = None
    ):
        """
        Register an API key
        
        Args:
            api_key: The API key
            name: Key name/description
            permissions: List of permissions
        """
        self.api_keys[api_key] = {
            'name': name,
            'permissions': permissions or ['read'],
            'created_at': datetime.now().isoformat(),
            'last_used': None
        }
        logger.info(f"API key registered: {name}")
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify API key is valid
        
        Args:
            api_key: API key to verify
            
        Returns:
            True if valid
        """
        if api_key in self.api_keys:
            self.api_keys[api_key]['last_used'] = datetime.now().isoformat()
            return True
        return False
    
    def check_permission(self, api_key: str, permission: str) -> bool:
        """
        Check if API key has permission
        
        Args:
            api_key: API key
            permission: Permission to check
            
        Returns:
            True if has permission
        """
        if api_key not in self.api_keys:
            return False
        
        permissions = self.api_keys[api_key]['permissions']
        return permission in permissions or 'admin' in permissions


# Global instances
secrets_manager = SecretsManager()
rate_limiter = RateLimiter()
auth_manager: Optional[AuthManager] = None


def init_auth(app):
    """Initialize authentication with Flask app"""
    global auth_manager
    
    secret_key = secrets_manager.get_secret(
        'secret_key',
        app.config.get('SECRET_KEY', 'dev-secret-key')
    )
    
    auth_enabled = secrets_manager.get_secret('auth_enabled', 'false').lower() == 'true'
    
    auth_manager = AuthManager(
        secret_key=secret_key,
        token_expiry_hours=24,
        enabled=auth_enabled
    )
    
    logger.info(f"Auth initialized (enabled: {auth_enabled})")


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_manager or not auth_manager.enabled:
            return f(*args, **kwargs)
        
        # Check API key
        api_key = request.headers.get('X-API-Key')
        if api_key and auth_manager.verify_api_key(api_key):
            return f(*args, **kwargs)
        
        # Check JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = auth_manager.verify_token(token)
            if payload:
                request.user = payload
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Unauthorized'}), 401
    
    return decorated_function


def require_permission(permission: str) -> Callable:
    """Decorator to require specific permission"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager or not auth_manager.enabled:
                return f(*args, **kwargs)
            
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            if not auth_manager.check_permission(api_key, permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit(f: Callable) -> Callable:
    """Decorator to apply rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limiter.is_allowed():
            reset_time = int(rate_limiter.get_reset_time())
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': reset_time
            }), 429
        
        response = f(*args, **kwargs)
        
        # Add rate limit headers
        if hasattr(response, 'headers'):
            response.headers['X-RateLimit-Limit'] = str(rate_limiter.max_requests)
            response.headers['X-RateLimit-Remaining'] = str(rate_limiter.get_remaining())
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + rate_limiter.get_reset_time()))
        
        return response
    
    return decorated_function
