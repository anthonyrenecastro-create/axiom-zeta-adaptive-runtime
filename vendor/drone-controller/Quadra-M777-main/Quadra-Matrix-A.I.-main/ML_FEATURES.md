# ML-SPECIFIC FEATURES GUIDE

## Overview

This guide covers the machine learning-specific features added to the Quadra Matrix A.I. system, including:

- **Model Versioning**: Track and manage model versions with full metadata
- **Model Monitoring**: Monitor predictions for drift and failures
- **Inference/Training Boundaries**: Clear separation of serving modes
- **Security**: Authentication, rate limiting, and secrets management

## Table of Contents

1. [Model Versioning](#model-versioning)
2. [Model Monitoring](#model-monitoring)
3. [Model Modes](#model-modes)
4. [Security](#security)
5. [API Endpoints](#api-endpoints)
6. [Best Practices](#best-practices)

---

## Model Versioning

### Features

- **Version Tracking**: Every model save creates a version with metadata
- **Integrity Checks**: SHA256 hashing ensures model files haven't been corrupted
- **Metrics Storage**: Each version stores training metrics and configuration
- **Production Promotion**: Mark specific versions as production-ready
- **Comparison**: Compare metrics between versions

### Usage

```python
from utils.model_versioning import ModelVersionManager, generate_version_string

# Initialize version manager
version_manager = ModelVersionManager(models_dir="./models")

# Save a model version
metadata = version_manager.save_model(
    model=my_model,
    version="1.0.0",
    metrics={'loss': 0.5, 'accuracy': 0.92},
    config={'hidden_size': 256},
    training_info={'epochs': 50, 'batch_size': 32},
    description="Production model v1.0",
    tags=['production', 'stable']
)

# Load a specific version
version_manager.load_model(my_model, "1.0.0", verify_integrity=True)

# List all versions
versions = version_manager.list_versions()

# Get latest version
latest = version_manager.get_latest_version()

# Promote to production
version_manager.promote_to_production("1.0.0")

# Get production version
prod_version = version_manager.get_production_version()
```

### Version String Format

Use semantic versioning or timestamp-based versions:

```python
# Semantic versioning
version = "1.0.0"
version = "2.1.3-beta"

# Timestamp-based (auto-generated)
version = generate_version_string()  # "20241221-143022"
version = generate_version_string(prefix="train")  # "train-20241221-143022"
```

### Model Registry

All versions are tracked in `model_registry.json`:

```json
{
  "1.0.0": {
    "version": "1.0.0",
    "created_at": "2024-12-21T14:30:00",
    "model_hash": "abc123...",
    "metrics": {"loss": 0.5, "accuracy": 0.92},
    "config": {"hidden_size": 256},
    "training_info": {"epochs": 50},
    "file_path": "./models/model_v1.0.0.pth",
    "file_size": 10485760,
    "description": "Production model v1.0",
    "tags": ["production", "stable"]
  }
}
```

---

## Model Monitoring

### Features

- **Prediction Tracking**: Record every inference with timing and confidence
- **Drift Detection**: Detect when model behavior deviates from baseline
- **Error Tracking**: Monitor failure rates and error patterns
- **Performance Metrics**: Track latency, throughput, and confidence scores
- **Alert System**: Automatic warnings for anomalies

### Usage

```python
from utils.model_monitoring import ModelMonitor
import time

# Initialize monitor
monitor = ModelMonitor(
    monitoring_dir="./monitoring",
    window_size=1000,  # Rolling window size
    drift_threshold=2.0  # Standard deviations for drift
)

# Record a prediction
start = time.time()
prediction = model.predict(input_data)
prediction_time = time.time() - start

monitor.record_prediction(
    input_data=input_data,
    prediction_time=prediction_time,
    confidence=0.95,
    success=True
)

# Set baseline (do this after initial deployment)
monitor.set_baseline()

# Check for drift
drift_result = monitor.detect_drift()
if drift_result['drift_detected']:
    print(f"⚠️ Drift detected! Score: {drift_result['drift_score']:.2f}")

# Get statistics
stats = monitor.get_statistics()
print(f"Total predictions: {stats['total_predictions']}")
print(f"Error rate: {stats['error_rate']:.2%}")
print(f"Avg latency: {stats['prediction_time']['mean']:.3f}s")
```

### Drift Detection

Drift is detected by comparing current metrics to baseline:

```python
# Set baseline during stable operation
monitor.set_baseline()

# Later, check for drift
result = monitor.detect_drift()
# {
#     'drift_detected': True,
#     'drift_score': 2.5,  # > threshold
#     'threshold': 2.0,
#     'baseline_mean': 0.90,
#     'current_mean': 0.75,  # Degraded
#     'baseline_std': 0.05,
#     'current_std': 0.08,
#     'sample_count': 1000
# }
```

### Health Checks

```python
from utils.model_monitoring import HealthChecker

# Initialize checker
checker = HealthChecker(
    model_path="./models",
    required_files=["model.pth", "config.json", "model_registry.json"]
)

# Perform health check
health = checker.check_health()
# {
#     'healthy': True,
#     'model_dir_exists': True,
#     'required_files': {
#         'model.pth': True,
#         'config.json': True,
#         'model_registry.json': True
#     },
#     'disk_space_available': True,
#     'disk_space_mb': 1024.5
# }
```

---

## Model Modes

### Overview

Clear separation between inference and training modes prevents accidental modifications to production models.

### Available Modes

- **INFERENCE**: Model serves predictions (read-only)
- **TRAINING**: Model can be updated
- **MAINTENANCE**: System is under maintenance

### Usage

```python
from utils.model_modes import ModelMode, mode_manager, InferenceGuard, TrainingGuard

# Check current mode
if mode_manager.is_inference_mode():
    print("Ready for predictions")

# Change modes
mode_manager.enter_inference_mode()
mode_manager.enter_training_mode()
mode_manager.enter_maintenance_mode()

# Use guards for safety
with InferenceGuard(mode_manager):
    # This code only runs in inference mode
    prediction = model.predict(data)

with TrainingGuard(mode_manager):
    # This code only runs in training mode
    model.train_step(batch)
```

### Flask Decorators

```python
from utils.model_modes import inference_only, training_only, require_mode

@app.route('/api/predict', methods=['POST'])
@inference_only
def predict():
    """Only accessible in inference mode"""
    return model.predict(request.json)

@app.route('/api/train', methods=['POST'])
@training_only
def train():
    """Only accessible in training mode"""
    return model.train(request.json)

@app.route('/api/backup', methods=['POST'])
@require_mode(ModelMode.MAINTENANCE)
def backup():
    """Only accessible in maintenance mode"""
    return create_backup()
```

### Mode Callbacks

Register callbacks for mode changes:

```python
def on_enter_inference():
    print("Entering inference mode - model is now read-only")
    # Load production model
    # Enable monitoring
    # Disable training endpoints

mode_manager.register_callback(ModelMode.INFERENCE, on_enter_inference)
```

---

## Security

### Features

- **Authentication**: JWT tokens and API keys
- **Rate Limiting**: Protect against abuse
- **Secrets Management**: Secure credential storage
- **Permissions**: Role-based access control

### Secrets Management

```python
from utils.security import secrets_manager

# Get secrets from environment
api_key = secrets_manager.get_secret('api_key')
db_password = secrets_manager.get_secret('db_password', default='fallback')

# Generate secure API key
new_key = secrets_manager.generate_api_key()
print(f"API Key: {new_key}")

# Hash API key for storage
hashed = secrets_manager.hash_api_key(new_key)

# Verify API key
is_valid = secrets_manager.verify_api_key(new_key, hashed)
```

### Environment Variables

```bash
# .env file
QUADRA_SECRET_KEY=your-secret-key-here
QUADRA_AUTH_ENABLED=true
QUADRA_API_KEY=your-api-key
QUADRA_DB_PASSWORD=your-password
```

### Authentication

```python
from utils.security import AuthManager

# Initialize auth
auth = AuthManager(
    secret_key="your-secret-key",
    token_expiry_hours=24,
    enabled=True
)

# Generate JWT token
token = auth.generate_token(user_id="user123", role="admin")

# Verify token
payload = auth.verify_token(token)
if payload:
    print(f"User: {payload['user_id']}, Role: {payload['role']}")

# Register API key
auth.register_api_key(
    api_key="sk-abc123",
    name="Production API Key",
    permissions=['read', 'write']
)

# Check permissions
has_permission = auth.check_permission("sk-abc123", "write")
```

### Rate Limiting

```python
from utils.security import RateLimiter

# Initialize rate limiter
limiter = RateLimiter(
    max_requests=100,  # Max requests
    window_seconds=60,  # Per 60 seconds
    enabled=True
)

# Check if request allowed
if limiter.is_allowed():
    # Process request
    pass
else:
    # Return 429 Too Many Requests
    return {"error": "Rate limit exceeded"}, 429

# Get remaining requests
remaining = limiter.get_remaining()
```

### Flask Decorators

```python
from utils.security import require_auth, require_permission, rate_limit

@app.route('/api/data', methods=['GET'])
@rate_limit
@require_auth
def get_data():
    """Rate limited and requires authentication"""
    return {"data": "sensitive"}

@app.route('/api/admin', methods=['POST'])
@rate_limit
@require_permission('admin')
def admin_action():
    """Requires admin permission"""
    return {"success": True}
```

---

## API Endpoints

### Model Versioning Endpoints

#### List Versions
```http
GET /api/model/versions

Response:
{
  "versions": [
    {
      "version": "1.0.0",
      "created_at": "2024-12-21T14:30:00",
      "metrics": {"loss": 0.5, "accuracy": 0.92},
      "description": "Production model",
      "tags": ["production"],
      "file_size": 10485760
    }
  ],
  "count": 1
}
```

#### Save Model
```http
POST /api/model/save
Content-Type: application/json

{
  "description": "Manual save",
  "tags": ["backup", "stable"]
}

Response:
{
  "success": true,
  "version": "manual-20241221-143022",
  "metadata": {
    "created_at": "2024-12-21T14:30:22",
    "metrics": {"loss": 0.5},
    "file_size": 10485760
  }
}
```

#### Load Version
```http
POST /api/model/load/1.0.0

Response:
{
  "success": true,
  "version": "1.0.0",
  "metadata": {
    "created_at": "2024-12-21T14:30:00",
    "metrics": {"loss": 0.5}
  }
}
```

#### Promote to Production
```http
POST /api/model/promote/1.0.0
X-API-Key: your-api-key

Response:
{
  "success": true,
  "production_version": "1.0.0"
}
```

### Monitoring Endpoints

#### Get Statistics
```http
GET /api/monitoring/stats

Response:
{
  "total_predictions": 1000,
  "error_count": 5,
  "error_rate": 0.005,
  "window_size": 1000,
  "prediction_time": {
    "mean": 0.15,
    "std": 0.02,
    "min": 0.10,
    "max": 0.50,
    "p95": 0.20
  },
  "confidence": {
    "mean": 0.85,
    "std": 0.05,
    "min": 0.60,
    "max": 0.99
  }
}
```

#### Check Drift
```http
GET /api/monitoring/drift

Response:
{
  "drift_detected": false,
  "drift_score": 0.8,
  "threshold": 2.0,
  "baseline_mean": 0.85,
  "current_mean": 0.84,
  "baseline_std": 0.05,
  "current_std": 0.06,
  "sample_count": 1000
}
```

#### Set Baseline
```http
POST /api/monitoring/baseline
X-API-Key: your-admin-key

Response:
{
  "success": true,
  "message": "Baseline set"
}
```

### Mode Endpoints

#### Get Mode
```http
GET /api/mode

Response:
{
  "mode": "inference"
}
```

#### Set Mode
```http
POST /api/mode/training
X-API-Key: your-admin-key

Response:
{
  "success": true,
  "mode": "training"
}
```

### Health Endpoints

#### Detailed Health
```http
GET /api/health/detailed

Response:
{
  "status": "healthy",
  "timestamp": "2024-12-21T14:30:00",
  "system": {
    "initialized": true,
    "running": false,
    "iterations": 100
  },
  "model": {
    "healthy": true,
    "model_dir_exists": true,
    "required_files": {
      "model.pth": true,
      "config.json": true
    },
    "disk_space_available": true,
    "disk_space_mb": 1024.5
  },
  "version": {
    "current": "1.0.0",
    "production": "1.0.0"
  },
  "mode": "inference"
}
```

### Authentication Endpoints

#### Generate Token
```http
POST /api/auth/token
Content-Type: application/json

{
  "user_id": "user123",
  "role": "admin"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Best Practices

### Model Versioning

1. **Use Semantic Versioning**: `MAJOR.MINOR.PATCH` format
2. **Tag Important Versions**: `production`, `stable`, `experimental`
3. **Add Descriptions**: Document what changed
4. **Verify Integrity**: Always check hashes in production
5. **Regular Backups**: Keep multiple versions

```python
# Good practice
metadata = version_manager.save_model(
    model=model,
    version="1.2.0",
    metrics={'loss': 0.45, 'accuracy': 0.94, 'f1': 0.92},
    config={'architecture': 'transformer', 'layers': 12},
    training_info={'epochs': 100, 'dataset': 'v2.1'},
    description="Improved accuracy by 2% with new architecture",
    tags=['stable', 'tested', 'ready-for-prod']
)
```

### Model Monitoring

1. **Set Baseline Early**: After initial stable deployment
2. **Monitor Regularly**: Check drift daily in production
3. **Track All Predictions**: Including failures
4. **Set Appropriate Thresholds**: Based on your use case
5. **Alert on Anomalies**: Integrate with monitoring systems

```python
# Good practice
def predict_with_monitoring(input_data):
    start_time = time.time()
    try:
        prediction = model.predict(input_data)
        confidence = prediction.confidence
        success = True
        error = None
    except Exception as e:
        prediction = None
        confidence = None
        success = False
        error = str(e)
    finally:
        monitor.record_prediction(
            input_data=input_data,
            prediction_time=time.time() - start_time,
            confidence=confidence,
            success=success,
            error=error
        )
    return prediction
```

### Mode Management

1. **Start in Inference**: Default to read-only mode
2. **Explicit Mode Changes**: Require admin permission
3. **Use Guards**: Prevent accidents
4. **Register Callbacks**: Clean state transitions
5. **Log Mode Changes**: Audit trail

```python
# Good practice
@require_permission('admin')
def start_training():
    # Switch to training mode
    mode_manager.enter_training_mode()
    
    try:
        with TrainingGuard(mode_manager):
            # Safe to train here
            train_model()
    finally:
        # Always return to inference
        mode_manager.enter_inference_mode()
```

### Security

1. **Use Environment Variables**: Never hardcode secrets
2. **Enable Auth in Production**: Always protect endpoints
3. **Rate Limit Public APIs**: Prevent abuse
4. **Rotate Keys Regularly**: Change API keys periodically
5. **Use HTTPS**: Encrypt in transit

```python
# Good practice - .env file
QUADRA_SECRET_KEY=use-long-random-string-here
QUADRA_AUTH_ENABLED=true
QUADRA_RATE_LIMIT_ENABLED=true
QUADRA_MAX_REQUESTS=100
QUADRA_RATE_WINDOW=60

# In code
@app.route('/api/predict', methods=['POST'])
@rate_limit
@require_auth
def predict():
    return model.predict(request.json)
```

### Integration Example

Complete production setup:

```python
from utils.model_versioning import ModelVersionManager
from utils.model_monitoring import ModelMonitor
from utils.model_modes import mode_manager, InferenceGuard
from utils.security import init_auth, require_auth, rate_limit

# Initialize components
version_manager = ModelVersionManager("./models")
monitor = ModelMonitor("./monitoring")
init_auth(app)

# Load production model
prod_version = version_manager.get_production_version()
if prod_version:
    version_manager.load_model(model, prod_version, verify_integrity=True)

# Set mode
mode_manager.enter_inference_mode()

# Set monitoring baseline
monitor.set_baseline()

# Production endpoint
@app.route('/api/predict', methods=['POST'])
@rate_limit
@require_auth
def predict():
    with InferenceGuard(mode_manager):
        start = time.time()
        try:
            prediction = model.predict(request.json)
            monitor.record_prediction(
                input_data=request.json,
                prediction_time=time.time() - start,
                confidence=prediction.confidence,
                success=True
            )
            return jsonify({'prediction': prediction.result})
        except Exception as e:
            monitor.record_prediction(
                input_data=request.json,
                prediction_time=time.time() - start,
                success=False,
                error=str(e)
            )
            return jsonify({'error': str(e)}), 500
```

---

## Configuration

### Environment Variables

```bash
# Security
QUADRA_SECRET_KEY=your-secret-key
QUADRA_AUTH_ENABLED=true
QUADRA_API_KEY=your-api-key

# Rate Limiting
QUADRA_RATE_LIMIT_ENABLED=true
QUADRA_MAX_REQUESTS=100
QUADRA_RATE_WINDOW=60

# Monitoring
QUADRA_DRIFT_THRESHOLD=2.0
QUADRA_MONITORING_WINDOW=1000

# Paths
QUADRA_MODELS_DIR=./models
QUADRA_MONITORING_DIR=./monitoring
```

### config.py Integration

```python
class ProductionConfig(Config):
    # ML-specific
    MODELS_DIR = Path(BASE_DIR) / 'models'
    MONITORING_DIR = Path(BASE_DIR) / 'monitoring'
    
    # Security
    AUTH_ENABLED = True
    RATE_LIMIT_ENABLED = True
    MAX_REQUESTS = 100
    RATE_WINDOW = 60
    
    # Monitoring
    DRIFT_THRESHOLD = 2.0
    MONITORING_WINDOW = 1000
```

---

## Troubleshooting

### Model Loading Fails

```python
# Check integrity
try:
    version_manager.load_model(model, "1.0.0", verify_integrity=True)
except ValueError as e:
    print(f"Integrity check failed: {e}")
    # Re-download or restore from backup
```

### Drift Detected

```python
# Check drift details
result = monitor.detect_drift()
if result['drift_detected']:
    print(f"Current mean: {result['current_mean']}")
    print(f"Baseline mean: {result['baseline_mean']}")
    print(f"Drift score: {result['drift_score']}")
    
    # Options:
    # 1. Retrain model
    # 2. Update baseline if data distribution changed
    # 3. Investigate root cause
```

### Rate Limit Issues

```python
# Check remaining requests
remaining = rate_limiter.get_remaining()
reset_time = rate_limiter.get_reset_time()

print(f"Requests remaining: {remaining}")
print(f"Reset in: {reset_time:.0f} seconds")
```

### Mode Conflicts

```python
# Check current mode
current_mode = mode_manager.mode
print(f"Current mode: {current_mode.value}")

# Force mode change if needed
mode_manager.set_mode(ModelMode.INFERENCE)
```

---

## Summary

The ML-specific features provide enterprise-grade capabilities:

- ✅ **Version Control**: Track every model change
- ✅ **Integrity Checks**: Ensure model files aren't corrupted
- ✅ **Drift Detection**: Monitor model performance degradation
- ✅ **Mode Separation**: Prevent accidental production changes
- ✅ **Security**: Protect your APIs and data
- ✅ **Monitoring**: Real-time performance tracking

These features transform your ML system from a prototype into a production-ready platform.
