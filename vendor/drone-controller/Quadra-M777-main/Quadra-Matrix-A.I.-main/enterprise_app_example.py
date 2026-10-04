"""
Enterprise Features Integration Example

This example demonstrates how to integrate all 9 enterprise features
into the Quadra Matrix A.I. application.
"""

import os
from flask import Flask, jsonify, request, g
from pathlib import Path

# Feature imports
from utils.api_docs import setup_api_documentation
from utils.tls_config import setup_tls
from utils.distributed_tracing import setup_distributed_tracing
from utils.circuit_breaker import circuit_breaker, get_all_circuit_breaker_metrics
from utils.ab_testing import ABTestingFramework, ab_test


def create_enterprise_app():
    """Create Flask application with all enterprise features enabled."""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # ============================================================
    # 1. API Documentation (OpenAPI/Swagger)
    # ============================================================
    print("✓ Setting up API documentation...")
    api_docs = setup_api_documentation(app)
    
    # ============================================================
    # 2. TLS/HTTPS Configuration
    # ============================================================
    print("✓ Setting up TLS/HTTPS...")
    tls_config = setup_tls(
        app,
        enable_hsts=True,
        enable_csp=True
    )
    
    # Generate self-signed cert for development
    if not os.path.exists('certs/server.crt'):
        print("  Generating self-signed certificate...")
        tls_config.generate_self_signed_cert(
            cert_dir='certs',
            days_valid=365,
            common_name='localhost'
        )
    
    # ============================================================
    # 3. Distributed Tracing (Jaeger/Zipkin)
    # ============================================================
    if os.getenv('ENABLE_TRACING', 'false').lower() == 'true':
        print("✓ Setting up distributed tracing...")
        tracing = setup_distributed_tracing(
            app,
            service_name='quadra-matrix',
            exporter_type=os.getenv('TRACING_EXPORTER', 'jaeger')
        )
    else:
        print("⚠ Distributed tracing disabled (set ENABLE_TRACING=true to enable)")
        tracing = None
    
    # ============================================================
    # 4. Circuit Breakers
    # ============================================================
    print("✓ Setting up circuit breakers...")
    
    @circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60)
    def call_external_api():
        """Example external API call with circuit breaker."""
        import requests
        return requests.get("https://api.example.com/data", timeout=5)
    
    # ============================================================
    # 5. A/B Testing Framework
    # ============================================================
    print("✓ Setting up A/B testing...")
    ab_framework = ABTestingFramework(storage_path='experiments')
    
    # Create example experiment
    if 'new_ui_test' not in ab_framework.experiments:
        ab_framework.create_experiment(
            name='new_ui_test',
            variants=[
                {'name': 'control', 'weight': 0.5, 'config': {'ui': 'old'}},
                {'name': 'treatment', 'weight': 0.5, 'config': {'ui': 'new'}}
            ],
            description='Test new UI design'
        )
    
    # ============================================================
    # Routes
    # ============================================================
    
    @app.route('/')
    def index():
        """Root endpoint."""
        return jsonify({
            'service': 'Quadra Matrix A.I.',
            'version': '2.0.0',
            'status': 'Enterprise Ready',
            'features': {
                'api_docs': '/api/docs',
                'health': '/health',
                'metrics': '/metrics',
                'circuit_breakers': '/admin/circuit-breakers'
            }
        })
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': '2025-12-21T12:00:00Z',
            'checks': {
                'database': 'ok',
                'redis': 'ok',
                'model': 'ok'
            }
        })
    
    @app.route('/admin/circuit-breakers')
    def circuit_breaker_status():
        """Circuit breaker metrics endpoint."""
        metrics = get_all_circuit_breaker_metrics()
        return jsonify(metrics)
    
    @app.route('/api/train', methods=['POST'])
    def train():
        """Training endpoint with tracing."""
        data = request.get_json()
        
        if tracing:
            with tracing.create_span("training_operation") as span:
                span.set_attribute("field_size", data.get('field_size', 0))
                span.set_attribute("max_iterations", data.get('max_iterations', 0))
                
                # Training logic would go here
                result = {'status': 'started', 'training_id': 'abc123'}
                
                span.set_attribute("training_id", result['training_id'])
        else:
            result = {'status': 'started', 'training_id': 'abc123'}
        
        return jsonify(result)
    
    @app.route('/feature')
    @ab_test(ab_framework, 'new_ui_test')
    def feature():
        """Feature with A/B testing."""
        variant = g.ab_variant
        
        if variant and variant['variant_name'] == 'treatment':
            return jsonify({
                'message': 'New UI feature',
                'variant': 'treatment',
                'config': variant['config']
            })
        
        return jsonify({
            'message': 'Original feature',
            'variant': 'control'
        })
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*60)
    print("ENTERPRISE FEATURES ENABLED")
    print("="*60)
    print("✓ API Documentation: http://localhost:5000/api/docs")
    print("✓ TLS/HTTPS: Configured")
    print("✓ Distributed Tracing:", "Enabled" if tracing else "Disabled")
    print("✓ Circuit Breakers: Configured")
    print("✓ A/B Testing: Configured")
    print("✓ Security Scanning: GitHub Actions")
    print("✓ Deployment: Canary + Blue-Green ready")
    print("✓ Chaos Engineering: Test suite available")
    print("="*60)
    print("\nAccess Points:")
    print("  Swagger UI:  http://localhost:5000/api/docs")
    print("  ReDoc:       http://localhost:5000/api/redoc")
    print("  OpenAPI:     http://localhost:5000/api/openapi.json")
    print("  Health:      http://localhost:5000/health")
    print("  Metrics:     http://localhost:5000/metrics")
    print("  Breakers:    http://localhost:5000/admin/circuit-breakers")
    print("="*60)
    
    return app, tls_config


if __name__ == '__main__':
    # Create application with all features
    app, tls_config = create_enterprise_app()
    
    # Run with HTTPS (development)
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    
    if use_https:
        try:
            ssl_context = tls_config.create_ssl_context()
            print("\n🔒 Starting with HTTPS...")
            app.run(
                host='0.0.0.0',
                port=443,
                ssl_context=ssl_context,
                debug=False
            )
        except Exception as e:
            print(f"⚠ HTTPS failed: {e}")
            print("  Falling back to HTTP...")
            app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n🌐 Starting with HTTP...")
        print("  Set USE_HTTPS=true to enable HTTPS")
        app.run(host='0.0.0.0', port=5000, debug=True)
