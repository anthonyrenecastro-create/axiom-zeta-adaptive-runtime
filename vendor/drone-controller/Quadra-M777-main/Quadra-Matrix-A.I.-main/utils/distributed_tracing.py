"""
Distributed Tracing Module

This module provides distributed tracing integration with Jaeger and Zipkin
for monitoring request flows across microservices.

Features:
- Jaeger integration
- Zipkin integration
- OpenTelemetry support
- Automatic span creation
- Context propagation
- Custom instrumentation
"""

import os
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from flask import Flask, request, g
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
import socket


class DistributedTracing:
    """Manages distributed tracing configuration."""
    
    def __init__(
        self,
        service_name: str = "quadra-matrix",
        service_version: str = "1.0.0",
        environment: str = "production",
        exporter_type: str = "jaeger"
    ):
        """
        Initialize distributed tracing.
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Deployment environment
            exporter_type: Type of exporter (jaeger, zipkin)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.exporter_type = exporter_type.lower()
        
        # Tracing configuration
        self.jaeger_host = os.getenv('JAEGER_HOST', 'localhost')
        self.jaeger_port = int(os.getenv('JAEGER_PORT', '6831'))
        self.zipkin_url = os.getenv('ZIPKIN_URL', 'http://localhost:9411/api/v2/spans')
        
        # Initialize tracer
        self.tracer = None
        self._setup_tracer()
    
    def _setup_tracer(self):
        """Setup OpenTelemetry tracer with appropriate exporter."""
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "host.name": socket.gethostname()
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Setup exporter
        if self.exporter_type == "jaeger":
            exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )
        elif self.exporter_type == "zipkin":
            exporter = ZipkinExporter(
                endpoint=self.zipkin_url
            )
        else:
            raise ValueError(f"Unsupported exporter type: {self.exporter_type}")
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
    
    def instrument_flask(self, app: Flask):
        """
        Instrument Flask application for automatic tracing.
        
        Args:
            app: Flask application instance
        """
        # Instrument Flask
        FlaskInstrumentor().instrument_app(app)
        
        # Instrument requests library
        RequestsInstrumentor().instrument()
        
        # Add custom middleware for additional context
        @app.before_request
        def before_request():
            """Add request context to trace."""
            span = trace.get_current_span()
            if span:
                span.set_attribute("http.route", request.endpoint or "unknown")
                span.set_attribute("http.client_ip", request.remote_addr)
                
                # Add custom headers
                if 'User-Agent' in request.headers:
                    span.set_attribute("http.user_agent", request.headers['User-Agent'])
                
                # Store start time
                g.request_start_time = time.time()
        
        @app.after_request
        def after_request(response):
            """Add response context to trace."""
            span = trace.get_current_span()
            if span:
                span.set_attribute("http.response.status_code", response.status_code)
                span.set_attribute("http.response.content_type", response.content_type)
                
                # Calculate request duration
                if hasattr(g, 'request_start_time'):
                    duration = time.time() - g.request_start_time
                    span.set_attribute("http.request.duration_ms", duration * 1000)
            
            return response
    
    def trace_function(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to trace a function.
        
        Args:
            name: Span name (defaults to function name)
            attributes: Additional span attributes
        
        Example:
            >>> @tracing.trace_function(name="train_model")
            >>> def train_model(data):
            >>>     # training logic
            >>>     pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # Add attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function arguments
                    if args:
                        span.set_attribute("function.args_count", len(args))
                    if kwargs:
                        span.set_attribute("function.kwargs_count", len(kwargs))
                    
                    try:
                        # Execute function
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        # Record exception
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            return wrapper
        return decorator
    
    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new span manually.
        
        Args:
            name: Span name
            attributes: Span attributes
        
        Returns:
            Span context manager
        
        Example:
            >>> with tracing.create_span("database_query") as span:
            >>>     span.set_attribute("query", "SELECT * FROM users")
            >>>     result = db.execute(query)
        """
        span = self.tracer.start_as_current_span(name)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to the current span.
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """
        Set attribute on current span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """
        Record an exception in the current span.
        
        Args:
            exception: Exception to record
        """
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


def setup_distributed_tracing(
    app: Flask,
    service_name: str = "quadra-matrix",
    exporter_type: str = "jaeger"
) -> DistributedTracing:
    """
    Setup distributed tracing for Flask application.
    
    Args:
        app: Flask application instance
        service_name: Name of the service
        exporter_type: Type of exporter (jaeger, zipkin)
    
    Returns:
        DistributedTracing instance
    
    Example:
        >>> app = Flask(__name__)
        >>> tracing = setup_distributed_tracing(app, exporter_type="jaeger")
        >>> 
        >>> @tracing.trace_function(name="process_data")
        >>> def process_data(data):
        >>>     with tracing.create_span("validate_data"):
        >>>         validate(data)
        >>>     with tracing.create_span("transform_data"):
        >>>         return transform(data)
    """
    # Get configuration from environment
    service_name = os.getenv('SERVICE_NAME', service_name)
    service_version = os.getenv('SERVICE_VERSION', '1.0.0')
    environment = os.getenv('ENVIRONMENT', 'production')
    exporter_type = os.getenv('TRACING_EXPORTER', exporter_type)
    
    # Create tracing instance
    tracing = DistributedTracing(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        exporter_type=exporter_type
    )
    
    # Instrument Flask app
    tracing.instrument_flask(app)
    
    return tracing


# Docker Compose configuration for Jaeger
JAEGER_DOCKER_COMPOSE = """
# Jaeger Distributed Tracing

version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "5775:5775/udp"    # Zipkin compatible endpoint
      - "6831:6831/udp"    # Jaeger agent
      - "6832:6832/udp"    # Jaeger agent
      - "5778:5778"        # Configuration server
      - "16686:16686"      # Jaeger UI
      - "14250:14250"      # gRPC
      - "14268:14268"      # Jaeger collector
      - "14269:14269"      # Health check
      - "9411:9411"        # Zipkin compatible endpoint
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - monitoring

  # Your application
  quadra-matrix:
    build: .
    environment:
      - JAEGER_HOST=jaeger
      - JAEGER_PORT=6831
      - TRACING_EXPORTER=jaeger
      - SERVICE_NAME=quadra-matrix
    depends_on:
      - jaeger
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
"""

# Docker Compose configuration for Zipkin
ZIPKIN_DOCKER_COMPOSE = """
# Zipkin Distributed Tracing

version: '3.8'

services:
  zipkin:
    image: openzipkin/zipkin:latest
    container_name: zipkin
    ports:
      - "9411:9411"  # Zipkin UI and API
    environment:
      - STORAGE_TYPE=mem
    networks:
      - monitoring

  # Your application
  quadra-matrix:
    build: .
    environment:
      - ZIPKIN_URL=http://zipkin:9411/api/v2/spans
      - TRACING_EXPORTER=zipkin
      - SERVICE_NAME=quadra-matrix
    depends_on:
      - zipkin
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
"""
