# ML PRODUCTION CHECKLIST

## ✅ Pre-Deployment Checklist

### Security Configuration
- [ ] Set `QUADRA_SECRET_KEY` to a strong random value
- [ ] Enable authentication: `QUADRA_AUTH_ENABLED=true`
- [ ] Generate and register admin API keys
- [ ] Enable rate limiting: `QUADRA_RATE_LIMIT_ENABLED=true`
- [ ] Configure appropriate rate limits for your use case
- [ ] Remove or restrict DEBUG mode in production
- [ ] Use HTTPS for all API endpoints
- [ ] Rotate API keys regularly (recommended: every 90 days)

### Model Versioning
- [ ] Create models directory: `mkdir -p dashboard_state/models`
- [ ] Set production model as baseline
- [ ] Enable integrity verification: `QUADRA_VERIFY_INTEGRITY=true`
- [ ] Document versioning strategy (semantic vs timestamp)
- [ ] Set up automatic backup of model registry
- [ ] Test model load/save operations
- [ ] Verify SHA256 hash verification works
- [ ] Create initial production version

### Model Monitoring
- [ ] Create monitoring directory: `mkdir -p dashboard_state/monitoring`
- [ ] Set appropriate drift threshold (default: 2.0)
- [ ] Configure monitoring window size (default: 1000)
- [ ] Set baseline after initial stable period
- [ ] Set up alerting for drift detection
- [ ] Monitor disk space for log files
- [ ] Configure log rotation
- [ ] Test drift detection with sample data

### Mode Management
- [ ] Set initial mode to INFERENCE
- [ ] Document mode transition procedures
- [ ] Set up mode change notifications
- [ ] Create runbook for switching modes
- [ ] Test mode guards and decorators
- [ ] Ensure training endpoints are protected
- [ ] Verify inference endpoints work in all modes

### Health Checks
- [ ] Test `/api/health` endpoint
- [ ] Test `/api/health/detailed` endpoint
- [ ] Set up monitoring for health endpoints
- [ ] Configure alerts for unhealthy status
- [ ] Verify all required files are present
- [ ] Check disk space thresholds
- [ ] Test health checks in CI/CD

### API Endpoints
- [ ] Test all 13 new ML endpoints
- [ ] Verify authentication on protected endpoints
- [ ] Test rate limiting behavior
- [ ] Check error handling and responses
- [ ] Validate request/response schemas
- [ ] Test with invalid inputs
- [ ] Verify CORS settings if needed

### Testing
- [ ] Run all unit tests: `pytest tests/`
- [ ] Verify 50+ tests pass
- [ ] Check test coverage (aim for >80%)
- [ ] Run integration tests
- [ ] Load test API endpoints
- [ ] Test with production-like data
- [ ] Verify error handling

### Documentation
- [ ] Read `ML_FEATURES.md` completely
- [ ] Review `ML_SUMMARY.md`
- [ ] Update team wiki/docs
- [ ] Create runbooks for common operations
- [ ] Document API endpoints
- [ ] Create troubleshooting guide
- [ ] Add inline code comments

### Infrastructure
- [ ] Set up model storage (local/S3)
- [ ] Configure backup strategy
- [ ] Set up log aggregation
- [ ] Configure monitoring/alerting
- [ ] Set up CI/CD pipeline
- [ ] Test rollback procedures
- [ ] Document disaster recovery

## 🔧 Configuration

### Required Environment Variables

```bash
# Security (REQUIRED in production)
QUADRA_SECRET_KEY=<generate-strong-random-key>
QUADRA_AUTH_ENABLED=true
QUADRA_RATE_LIMIT_ENABLED=true

# Paths (REQUIRED)
QUADRA_MODELS_DIR=./dashboard_state/models
QUADRA_MONITORING_DIR=./dashboard_state/monitoring

# Optional but Recommended
QUADRA_MAX_REQUESTS=100
QUADRA_RATE_WINDOW=60
QUADRA_DRIFT_THRESHOLD=2.0
QUADRA_VERIFY_INTEGRITY=true
```

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🚀 Deployment Steps

### 1. Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd Quadra-Matrix-A.I.-main

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements_dashboard.txt
pip install -r requirements.txt

# Create directories
mkdir -p dashboard_state/models
mkdir -p dashboard_state/monitoring
mkdir -p logs
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or your preferred editor

# Set required variables
export QUADRA_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export QUADRA_AUTH_ENABLED=true
export QUADRA_RATE_LIMIT_ENABLED=true
```

### 3. Initialize Components

```python
# In Python console or script
from utils.model_versioning import ModelVersionManager
from utils.model_monitoring import ModelMonitor
from utils.security import AuthManager, secrets_manager

# Initialize version manager
version_manager = ModelVersionManager('./dashboard_state/models')

# Initialize monitoring
monitor = ModelMonitor('./dashboard_state/monitoring')

# Set up authentication
auth = AuthManager(
    secret_key=secrets_manager.get_secret('secret_key'),
    enabled=True
)

# Register admin API key
admin_key = secrets_manager.generate_api_key()
auth.register_api_key(
    api_key=admin_key,
    name="Admin Key",
    permissions=['admin']
)
print(f"Admin API Key: {admin_key}")
# SAVE THIS KEY SECURELY!
```

### 4. Start Application

```bash
# Development
python app.py

# Production (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet app:app
```

### 5. Verify Deployment

```bash
# Check health
curl http://localhost:5000/api/health

# Check detailed health
curl http://localhost:5000/api/health/detailed

# Check model mode
curl http://localhost:5000/api/mode

# Test authentication (should get 401)
curl http://localhost:5000/api/model/versions

# Test with API key
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/model/versions
```

## 📊 Monitoring Setup

### Set Initial Baseline

After your first stable deployment:

```bash
# Let system run for ~1000 predictions
# Then set baseline

curl -X POST http://localhost:5000/api/monitoring/baseline \
  -H "X-API-Key: your-admin-key"
```

### Check Monitoring Stats

```bash
# Get current statistics
curl http://localhost:5000/api/monitoring/stats

# Check for drift
curl http://localhost:5000/api/monitoring/drift
```

### Example Alert Script

```bash
#!/bin/bash
# check_drift.sh

DRIFT=$(curl -s http://localhost:5000/api/monitoring/drift)
DETECTED=$(echo $DRIFT | jq -r '.drift_detected')

if [ "$DETECTED" = "true" ]; then
    SCORE=$(echo $DRIFT | jq -r '.drift_score')
    echo "⚠️ DRIFT DETECTED! Score: $SCORE"
    # Send alert (Slack, email, etc.)
    # curl -X POST https://hooks.slack.com/... -d "..."
fi
```

## 🔄 Common Operations

### Save Model Version

```bash
curl -X POST http://localhost:5000/api/model/save \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "description": "Production release v1.0",
    "tags": ["production", "stable"]
  }'
```

### Load Specific Version

```bash
curl -X POST http://localhost:5000/api/model/load/1.0.0 \
  -H "X-API-Key: your-admin-key"
```

### Promote to Production

```bash
curl -X POST http://localhost:5000/api/model/promote/1.0.0 \
  -H "X-API-Key: your-admin-key"
```

### Switch to Training Mode

```bash
curl -X POST http://localhost:5000/api/mode/training \
  -H "X-API-Key: your-admin-key"
```

### Switch Back to Inference

```bash
curl -X POST http://localhost:5000/api/mode/inference \
  -H "X-API-Key: your-admin-key"
```

## 🔍 Troubleshooting

### Issue: Authentication Not Working

**Symptoms**: All requests return 401

**Solutions**:
1. Check `QUADRA_AUTH_ENABLED` is set correctly
2. Verify API key is registered
3. Check header format: `X-API-Key: your-key`
4. Verify secret key is set

```bash
# Debug authentication
python -c "
from utils.security import AuthManager, secrets_manager
auth = AuthManager(secrets_manager.get_secret('secret_key'), enabled=True)
key = 'your-test-key'
auth.register_api_key(key, 'Test', ['read'])
print(auth.verify_api_key(key))
"
```

### Issue: Drift Always Detected

**Symptoms**: Every drift check returns true

**Solutions**:
1. Check if baseline is set: `monitor.baseline_metrics`
2. Verify sufficient data collected
3. Adjust threshold: `QUADRA_DRIFT_THRESHOLD=3.0`
4. Review data distribution changes

```python
# Reset baseline
from utils.model_monitoring import ModelMonitor
monitor = ModelMonitor('./monitoring')
monitor.reset_counters()
# Collect new data...
monitor.set_baseline()
```

### Issue: Model Integrity Check Fails

**Symptoms**: Cannot load model, hash mismatch

**Solutions**:
1. Verify file not corrupted
2. Check if model was modified
3. Re-save model version
4. Restore from backup

```python
# Disable integrity check temporarily
version_manager.load_model(model, "1.0.0", verify_integrity=False)
# Then re-save
version_manager.save_model(model, "1.0.0-recovered", ...)
```

### Issue: Rate Limit Too Strict

**Symptoms**: Getting 429 errors frequently

**Solutions**:
1. Increase limit: `QUADRA_MAX_REQUESTS=200`
2. Increase window: `QUADRA_RATE_WINDOW=120`
3. Use different API keys for different clients
4. Implement exponential backoff

```python
# Check rate limit status
from utils.security import rate_limiter
print(f"Remaining: {rate_limiter.get_remaining()}")
print(f"Reset in: {rate_limiter.get_reset_time()}")
```

## 📈 Performance Optimization

### Rate Limiting
- Use Redis for distributed rate limiting
- Implement per-user limits
- Add tier-based limits (free/premium)

### Model Loading
- Cache loaded models in memory
- Use lazy loading
- Implement model warm-up

### Monitoring
- Use time-series database for metrics
- Aggregate old data
- Implement sampling for high traffic

### Versioning
- Use S3/blob storage for large models
- Implement compression
- Archive old versions

## 🔐 Security Best Practices

1. **Never commit secrets** to version control
2. **Rotate keys regularly** (every 90 days)
3. **Use HTTPS** in production
4. **Enable rate limiting** always
5. **Monitor failed auth attempts**
6. **Use strong random secrets**
7. **Implement audit logging**
8. **Regular security audits**

## 📝 Maintenance Schedule

### Daily
- [ ] Check health endpoints
- [ ] Review error logs
- [ ] Monitor drift detection
- [ ] Check disk space

### Weekly
- [ ] Review monitoring stats
- [ ] Check model performance
- [ ] Review rate limit logs
- [ ] Backup model registry

### Monthly
- [ ] Rotate API keys
- [ ] Review and archive old logs
- [ ] Test disaster recovery
- [ ] Update documentation

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Dependency updates
- [ ] Capacity planning

## 🎯 Success Metrics

Track these metrics to measure ML operations health:

### Model Metrics
- Model version count
- Average model size
- Load/save time
- Integrity check failures

### Monitoring Metrics
- Prediction latency (p50, p95, p99)
- Error rate
- Drift detection frequency
- Confidence score distribution

### Security Metrics
- Failed authentication attempts
- Rate limit violations
- API key usage
- Token expiration rate

### Operational Metrics
- Uptime
- API response time
- Storage usage
- Memory consumption

## 🚨 Incident Response

### High Drift Detected

1. **Immediate**: Switch to maintenance mode
2. **Investigate**: Check data distribution, model performance
3. **Action**: Retrain model or update baseline
4. **Verify**: Test new model thoroughly
5. **Deploy**: Promote new version, return to inference mode
6. **Monitor**: Watch for continued drift

### Model Corruption

1. **Immediate**: Rollback to previous version
2. **Investigate**: Check integrity hash, file system
3. **Action**: Restore from backup
4. **Verify**: Test restored model
5. **Document**: Record incident details
6. **Prevent**: Improve backup strategy

### Security Breach

1. **Immediate**: Revoke compromised keys
2. **Investigate**: Check access logs, identify scope
3. **Action**: Rotate all keys, update secrets
4. **Verify**: Audit all model versions
5. **Document**: Create incident report
6. **Prevent**: Improve security measures

## 📚 Additional Resources

### Documentation
- `ML_FEATURES.md` - Complete feature guide
- `ML_SUMMARY.md` - Quick reference
- `COMPLETE_SUMMARY.md` - Full project overview
- `DEPLOYMENT.md` - Deployment guide

### Code Examples
- `tests/test_model_versioning.py` - Version management examples
- `tests/test_model_monitoring.py` - Monitoring examples
- `tests/test_security.py` - Security examples
- `tests/test_model_modes.py` - Mode management examples

### API Documentation
- All endpoints documented in `ML_FEATURES.md`
- OpenAPI/Swagger spec (TODO: add swagger UI)

## ✅ Sign-Off Checklist

Before going to production, verify:

- [ ] All environment variables configured
- [ ] Security enabled and tested
- [ ] Model versioning working
- [ ] Monitoring baseline set
- [ ] Health checks passing
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Team trained on new features
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured
- [ ] Incident response plan ready
- [ ] Security audit completed

---

**Production Ready**: Once all items are checked, your ML system is ready for enterprise deployment! 🚀
