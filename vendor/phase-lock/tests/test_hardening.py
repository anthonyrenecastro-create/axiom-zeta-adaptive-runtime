import dataclasses


def _payload(tenant_id="acme"):
    return {
        "tenant_id": tenant_id,
        "request_id": "req-h",
        "text": "example",
        "metric_window": [0.1] * 24,
        "metadata": {},
    }


def test_gateway_fails_closed_without_key(client, monkeypatch):
    monkeypatch.delenv("GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("ALLOW_INSECURE_NO_AUTH", "false")
    res = client.post("/v1/stabilize", json=_payload())
    assert res.status_code == 503


def test_wrong_key_rejected(client, monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "top-secret")
    assert client.post("/v1/stabilize", json=_payload(), headers={"X-API-Key": "nope"}).status_code == 401
    assert client.post("/v1/stabilize", json=_payload(), headers={"X-API-Key": "top-secret"}).status_code == 200


def test_tenant_limit_returns_429(client, app_modules):
    _, routes, _ = app_modules
    routes.service.settings = dataclasses.replace(routes.service.settings, max_tenants=1)
    assert client.post("/v1/stabilize", json=_payload("one")).status_code == 200
    assert client.post("/v1/stabilize", json=_payload("one")).status_code == 200
    assert client.post("/v1/stabilize", json=_payload("two")).status_code == 429


def test_baseline_reset_endpoint(client):
    assert client.post("/v1/baseline/reset", json={"tenant_id": "ghost"}).json()["reset"] is False
    client.post("/v1/stabilize", json=_payload("acme"))
    assert client.post("/v1/baseline/reset", json={"tenant_id": "acme"}).json()["reset"] is True
