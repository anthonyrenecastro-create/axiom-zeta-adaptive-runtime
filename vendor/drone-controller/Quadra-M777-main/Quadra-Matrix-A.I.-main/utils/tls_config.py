"""
TLS/HTTPS Configuration Module

This module provides comprehensive TLS/HTTPS configuration for production deployments,
including certificate management, SSL context configuration, and security headers.

Features:
- Self-signed certificate generation
- Let's Encrypt integration
- SSL context configuration
- Security headers (HSTS, CSP, etc.)
- Certificate validation
- mTLS support
"""

import os
import ssl
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from flask import Flask, request, make_response
from werkzeug.middleware.proxy_fix import ProxyFix
import subprocess


class TLSConfig:
    """Manages TLS/HTTPS configuration for Flask application."""
    
    def __init__(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_file: Optional[str] = None,
        enable_hsts: bool = True,
        enable_csp: bool = True
    ):
        """
        Initialize TLS configuration.
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            ca_file: Path to CA certificate file (for mTLS)
            enable_hsts: Enable HTTP Strict Transport Security
            enable_csp: Enable Content Security Policy
        """
        self.cert_file = cert_file or os.getenv('TLS_CERT_FILE', 'certs/server.crt')
        self.key_file = key_file or os.getenv('TLS_KEY_FILE', 'certs/server.key')
        self.ca_file = ca_file or os.getenv('TLS_CA_FILE')
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp
        
        # TLS settings
        self.tls_version = os.getenv('TLS_VERSION', 'TLSv1.2')
        self.ciphers = os.getenv('TLS_CIPHERS', self._get_secure_ciphers())
        
    def _get_secure_ciphers(self) -> str:
        """Get recommended secure cipher suite."""
        return (
            'ECDHE+AESGCM:'
            'ECDHE+CHACHA20:'
            'DHE+AESGCM:'
            'DHE+CHACHA20:'
            '!aNULL:'
            '!MD5:'
            '!DSS:'
            '!SHA1:'
            '!SHA256:'
            '!SHA384'
        )
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context for HTTPS server.
        
        Returns:
            Configured SSL context
        """
        # Create SSL context with secure defaults
        if self.tls_version == 'TLSv1.3':
            protocol = ssl.PROTOCOL_TLS_SERVER
            context = ssl.SSLContext(protocol)
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        elif self.tls_version == 'TLSv1.2':
            protocol = ssl.PROTOCOL_TLS_SERVER
            context = ssl.SSLContext(protocol)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load certificate and private key
        if os.path.exists(self.cert_file) and os.path.exists(self.key_file):
            context.load_cert_chain(self.cert_file, self.key_file)
        else:
            raise FileNotFoundError(
                f"Certificate or key file not found: {self.cert_file}, {self.key_file}"
            )
        
        # Configure cipher suite
        context.set_ciphers(self.ciphers)
        
        # Enable mTLS if CA certificate provided
        if self.ca_file and os.path.exists(self.ca_file):
            context.load_verify_locations(self.ca_file)
            context.verify_mode = ssl.CERT_REQUIRED
        
        # Additional security settings
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
        
        return context
    
    def generate_self_signed_cert(
        self,
        cert_dir: str = 'certs',
        days_valid: int = 365,
        country: str = 'US',
        state: str = 'CA',
        locality: str = 'San Francisco',
        organization: str = 'Quadra Matrix AI',
        common_name: str = 'localhost'
    ) -> Tuple[str, str]:
        """
        Generate self-signed certificate for development.
        
        Args:
            cert_dir: Directory to store certificates
            days_valid: Certificate validity period in days
            country: Country code
            state: State or province
            locality: City or locality
            organization: Organization name
            common_name: Common name (hostname)
        
        Returns:
            Tuple of (cert_file, key_file) paths
        """
        # Create certificate directory
        cert_path = Path(cert_dir)
        cert_path.mkdir(parents=True, exist_ok=True)
        
        cert_file = cert_path / 'server.crt'
        key_file = cert_path / 'server.key'
        
        # Generate private key and certificate using OpenSSL
        subject = f"/C={country}/ST={state}/L={locality}/O={organization}/CN={common_name}"
        
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', str(key_file),
            '-out', str(cert_file),
            '-days', str(days_valid),
            '-nodes',
            '-subj', subject
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Generated self-signed certificate: {cert_file}")
            print(f"Generated private key: {key_file}")
            
            # Set appropriate permissions
            os.chmod(key_file, 0o600)
            os.chmod(cert_file, 0o644)
            
            return str(cert_file), str(key_file)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate certificate: {e.stderr.decode()}")
    
    def setup_letsencrypt(
        self,
        domain: str,
        email: str,
        cert_dir: str = '/etc/letsencrypt/live'
    ) -> Tuple[str, str]:
        """
        Setup Let's Encrypt certificate using certbot.
        
        Args:
            domain: Domain name for certificate
            email: Email for certificate notifications
            cert_dir: Directory for Let's Encrypt certificates
        
        Returns:
            Tuple of (cert_file, key_file) paths
        
        Note:
            Requires certbot to be installed:
            sudo apt-get install certbot
        """
        # Install certbot if not present
        try:
            subprocess.run(['certbot', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "certbot not found. Install with: sudo apt-get install certbot"
            )
        
        # Run certbot in standalone mode
        cmd = [
            'certbot', 'certonly',
            '--standalone',
            '--non-interactive',
            '--agree-tos',
            '--email', email,
            '-d', domain
        ]
        
        try:
            subprocess.run(cmd, check=True)
            
            cert_file = f"{cert_dir}/{domain}/fullchain.pem"
            key_file = f"{cert_dir}/{domain}/privkey.pem"
            
            if os.path.exists(cert_file) and os.path.exists(key_file):
                return cert_file, key_file
            else:
                raise FileNotFoundError(f"Certificate files not found in {cert_dir}/{domain}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to obtain Let's Encrypt certificate: {e}")
    
    def add_security_headers(self, app: Flask):
        """
        Add security headers to Flask responses.
        
        Args:
            app: Flask application instance
        """
        @app.after_request
        def set_security_headers(response):
            """Add security headers to all responses."""
            
            # HTTP Strict Transport Security (HSTS)
            if self.enable_hsts and request.is_secure:
                response.headers['Strict-Transport-Security'] = (
                    'max-age=31536000; includeSubDomains; preload'
                )
            
            # Content Security Policy
            if self.enable_csp:
                response.headers['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                    "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self' wss: ws:;"
                )
            
            # Additional security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=()'
            )
            
            return response
    
    def setup_proxy_fix(self, app: Flask, num_proxies: int = 1):
        """
        Configure ProxyFix middleware for applications behind reverse proxy.
        
        Args:
            app: Flask application instance
            num_proxies: Number of proxies in front of the application
        """
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=num_proxies,
            x_proto=num_proxies,
            x_host=num_proxies,
            x_prefix=num_proxies
        )
    
    def validate_certificate(self, cert_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate SSL certificate and return information.
        
        Args:
            cert_file: Path to certificate file
        
        Returns:
            Dictionary with certificate information
        """
        cert_path = cert_file or self.cert_file
        
        if not os.path.exists(cert_path):
            return {"valid": False, "error": "Certificate file not found"}
        
        try:
            # Read certificate
            with open(cert_path, 'r') as f:
                cert_data = f.read()
            
            # Get certificate info using OpenSSL
            cmd = ['openssl', 'x509', '-in', cert_path, '-noout', '-dates', '-subject', '-issuer']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            output_lines = result.stdout.strip().split('\n')
            info = {}
            
            for line in output_lines:
                if line.startswith('notBefore='):
                    info['not_before'] = line.split('=', 1)[1]
                elif line.startswith('notAfter='):
                    info['not_after'] = line.split('=', 1)[1]
                elif line.startswith('subject='):
                    info['subject'] = line.split('=', 1)[1]
                elif line.startswith('issuer='):
                    info['issuer'] = line.split('=', 1)[1]
            
            info['valid'] = True
            info['file'] = cert_path
            
            return info
        except Exception as e:
            return {"valid": False, "error": str(e)}


def setup_tls(
    app: Flask,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    enable_hsts: bool = True,
    enable_csp: bool = True
) -> TLSConfig:
    """
    Setup TLS/HTTPS for Flask application.
    
    Args:
        app: Flask application instance
        cert_file: Path to SSL certificate file
        key_file: Path to SSL private key file
        enable_hsts: Enable HTTP Strict Transport Security
        enable_csp: Enable Content Security Policy
    
    Returns:
        TLSConfig instance
    
    Example:
        >>> app = Flask(__name__)
        >>> tls_config = setup_tls(app)
        >>> 
        >>> # Generate self-signed certificate for development
        >>> cert, key = tls_config.generate_self_signed_cert()
        >>> 
        >>> # Run with HTTPS
        >>> ssl_context = tls_config.create_ssl_context()
        >>> app.run(ssl_context=ssl_context, host='0.0.0.0', port=443)
        >>> 
        >>> # Or use with Gunicorn:
        >>> # gunicorn --certfile=certs/server.crt --keyfile=certs/server.key app:app
    """
    tls_config = TLSConfig(cert_file, key_file, enable_hsts=enable_hsts, enable_csp=enable_csp)
    tls_config.add_security_headers(app)
    
    # Setup proxy fix if behind reverse proxy
    if os.getenv('BEHIND_PROXY', 'false').lower() == 'true':
        num_proxies = int(os.getenv('NUM_PROXIES', '1'))
        tls_config.setup_proxy_fix(app, num_proxies)
    
    return tls_config


# Nginx configuration template for TLS termination
NGINX_TLS_CONFIG = """
# Nginx TLS Configuration for Quadra Matrix A.I.

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL Protocol and Ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS';
    ssl_prefer_server_ciphers on;
    
    # SSL Session Settings
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
"""
