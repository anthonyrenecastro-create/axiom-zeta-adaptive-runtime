# 🚀 Enterprise Features - Quick Reference

## Installation
```bash
pip install -r requirements.txt
```

## 1️⃣ API Documentation
```python
from utils.api_docs import setup_api_documentation
api_docs = setup_api_documentation(app)
```
**Access:** http://localhost:5000/api/docs

## 2️⃣ TLS/HTTPS
```python
from utils.tls_config import setup_tls
tls = setup_tls(app)
cert, key = tls.generate_self_signed_cert()
ssl_context = tls.create_ssl_context()
app.run(ssl_context=ssl_context)
```

## 3️⃣ Dependency Scanning
**Automatic** via GitHub Actions
- Add `SNYK_TOKEN` to secrets
- Runs on push/PR + daily

## 4️⃣ Distributed Tracing
```python
from utils.distributed_tracing import setup_distributed_tracing
tracing = setup_distributed_tracing(app, exporter_type="jaeger")

@tracing.trace_function(name="process")
def process(): pass
```
**Start Jaeger:** 
```bash
docker run -d -p 16686:16686 -p 6831:6831/udp jaegertracing/all-in-one
```

## 5️⃣ Circuit Breakers
```python
from utils.circuit_breaker import circuit_breaker

@circuit_breaker("api", failure_threshold=5, recovery_timeout=60)
def call_api(): pass
```

## 6️⃣ A/B Testing
```python
from utils.ab_testing import ABTestingFramework
fw = ABTestingFramework()
exp = fw.create_experiment("test", variants=[...])
variant = fw.get_variant("test", "user123")
```

## 7️⃣ Canary Deployment
```bash
./scripts/canary-deploy.sh deploy 1.1.0    # Gradual rollout
./scripts/canary-deploy.sh scale 25        # 25% traffic
./scripts/canary-deploy.sh rollback        # Rollback
```

## 8️⃣ Blue-Green Deployment
```bash
./scripts/blue-green-deploy.sh deploy 1.1.0  # Deploy to inactive
./scripts/blue-green-deploy.sh switch green  # Switch traffic
./scripts/blue-green-deploy.sh rollback      # Instant rollback
```

## 9️⃣ Chaos Engineering
```bash
python scripts/run_chaos_tests.py --suite standard --duration 30
python scripts/run_chaos_tests.py --test latency --latency 1000
python scripts/run_chaos_tests.py --test resource --resource cpu
```

---

## Key URLs
- **Swagger UI:** http://localhost:5000/api/docs
- **ReDoc:** http://localhost:5000/api/redoc
- **Health:** http://localhost:5000/health
- **Metrics:** http://localhost:5000/metrics
- **Breakers:** http://localhost:5000/admin/circuit-breakers
- **Jaeger:** http://localhost:16686

## Environment Variables
```bash
USE_HTTPS=true
ENABLE_TRACING=true
TRACING_EXPORTER=jaeger
JAEGER_HOST=localhost
SERVICE_NAME=quadra-matrix
SECRET_KEY=your-secret-key
```

## Complete Example
```python
from flask import Flask
from utils.api_docs import setup_api_documentation
from utils.tls_config import setup_tls
from utils.distributed_tracing import setup_distributed_tracing
from utils.circuit_breaker import circuit_breaker

app = Flask(__name__)
setup_api_documentation(app)
setup_tls(app)
setup_distributed_tracing(app)

@app.route('/api/data')
@circuit_breaker("external_api")
def get_data():
    return {"data": "value"}

if __name__ == '__main__':
    app.run()
```

---

**Total Features:** 9 ✅  
**Status:** Production Ready 🚀  
**Version:** 2.0.0 Enterprise
