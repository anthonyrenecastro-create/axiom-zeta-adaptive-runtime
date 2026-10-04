"""
Redis Configuration for SocketIO Scaling
Enables horizontal scaling with multiple workers
"""
import os
from typing import Optional
import redis
from redis.sentinel import Sentinel
import logging

logger = logging.getLogger(__name__)

# ============================================================
# REDIS CONFIGURATION
# ============================================================

class RedisConfig:
    """Redis connection configuration"""
    
    def __init__(self):
        # Connection settings
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD')
        self.ssl = os.getenv('REDIS_SSL', 'false').lower() == 'true'
        
        # Sentinel configuration (for high availability)
        self.use_sentinel = os.getenv('REDIS_USE_SENTINEL', 'false').lower() == 'true'
        self.sentinel_hosts = self._parse_sentinel_hosts()
        self.sentinel_master = os.getenv('REDIS_SENTINEL_MASTER', 'mymaster')
        
        # Connection pooling
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
        self.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
        self.socket_connect_timeout = int(os.getenv('REDIS_CONNECT_TIMEOUT', 5))
        
        # Retry configuration
        self.retry_on_timeout = True
        self.health_check_interval = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', 30))
    
    def _parse_sentinel_hosts(self):
        """Parse sentinel hosts from environment variable"""
        hosts_str = os.getenv('REDIS_SENTINEL_HOSTS', '')
        if not hosts_str:
            return []
        
        # Format: host1:port1,host2:port2
        hosts = []
        for host_port in hosts_str.split(','):
            if ':' in host_port:
                host, port = host_port.split(':')
                hosts.append((host.strip(), int(port)))
        
        return hosts
    
    def get_connection_url(self) -> str:
        """Get Redis connection URL"""
        protocol = 'rediss' if self.ssl else 'redis'
        auth = f':{self.password}@' if self.password else ''
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"
    
    def get_socketio_config(self) -> dict:
        """Get configuration for Flask-SocketIO"""
        if self.use_sentinel:
            # Sentinel configuration
            return {
                'message_queue': None,  # Will use client directly
                'channel': 'flask-socketio',
            }
        else:
            # Direct Redis connection
            return {
                'message_queue': self.get_connection_url(),
                'channel': 'flask-socketio',
            }


# ============================================================
# REDIS CLIENT FACTORY
# ============================================================

class RedisClientFactory:
    """Factory for creating Redis clients"""
    
    _instance: Optional[redis.Redis] = None
    _sentinel: Optional[Sentinel] = None
    
    @classmethod
    def get_client(cls, config: Optional[RedisConfig] = None) -> redis.Redis:
        """
        Get or create Redis client
        
        Args:
            config: Redis configuration (creates default if None)
        
        Returns:
            Redis client instance
        """
        if cls._instance is None:
            if config is None:
                config = RedisConfig()
            
            cls._instance = cls._create_client(config)
            logger.info("Redis client initialized")
        
        return cls._instance
    
    @classmethod
    def _create_client(cls, config: RedisConfig) -> redis.Redis:
        """Create Redis client based on configuration"""
        
        if config.use_sentinel and config.sentinel_hosts:
            # Use Sentinel for high availability
            cls._sentinel = Sentinel(
                config.sentinel_hosts,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                password=config.password,
                ssl=config.ssl
            )
            
            client = cls._sentinel.master_for(
                config.sentinel_master,
                socket_timeout=config.socket_timeout,
                db=config.db,
                password=config.password,
                ssl=config.ssl
            )
            
            logger.info(f"Redis Sentinel client created for master: {config.sentinel_master}")
        else:
            # Direct connection
            connection_pool = redis.ConnectionPool(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                retry_on_timeout=config.retry_on_timeout,
                health_check_interval=config.health_check_interval,
                ssl=config.ssl
            )
            
            client = redis.Redis(connection_pool=connection_pool)
            logger.info(f"Redis client created: {config.host}:{config.port}")
        
        # Test connection
        try:
            client.ping()
            logger.info("✅ Redis connection successful")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        
        return client
    
    @classmethod
    def close(cls):
        """Close Redis connections"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis client closed")


# ============================================================
# REDIS UTILITIES
# ============================================================

def get_redis_client() -> redis.Redis:
    """Get global Redis client instance"""
    return RedisClientFactory.get_client()


def test_redis_connection() -> bool:
    """
    Test Redis connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = get_redis_client()
        client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False


# ============================================================
# DOCKER COMPOSE REDIS CONFIGURATION
# ============================================================

DOCKER_COMPOSE_REDIS = """
# Add to docker-compose.yml for Redis support

  redis:
    image: redis:7.2-alpine
    container_name: redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-}
    volumes:
      - redis-data:/data
    networks:
      - quadra-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Optional: Redis Sentinel for high availability
  redis-sentinel:
    image: redis:7.2-alpine
    container_name: redis-sentinel
    command: >
      sh -c "echo 'sentinel monitor mymaster redis 6379 2' > /tmp/sentinel.conf &&
             echo 'sentinel down-after-milliseconds mymaster 5000' >> /tmp/sentinel.conf &&
             echo 'sentinel parallel-syncs mymaster 1' >> /tmp/sentinel.conf &&
             echo 'sentinel failover-timeout mymaster 10000' >> /tmp/sentinel.conf &&
             redis-sentinel /tmp/sentinel.conf"
    depends_on:
      - redis
    networks:
      - quadra-network

volumes:
  redis-data:
    driver: local
"""

REDIS_ENV_VARS = """
# Add to .env file

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-secure-redis-password
REDIS_SSL=false
REDIS_MAX_CONNECTIONS=50

# Redis Sentinel (for high availability)
REDIS_USE_SENTINEL=false
REDIS_SENTINEL_HOSTS=sentinel1:26379,sentinel2:26379,sentinel3:26379
REDIS_SENTINEL_MASTER=mymaster
"""
