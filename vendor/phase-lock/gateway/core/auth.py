import hmac

from fastapi import Header, HTTPException

from gateway.core.config import load_settings


def api_key_matches(provided: str | None, expected: str) -> bool:
    if provided is None:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = load_settings()
    if settings.api_key is None:
        # Fail closed: an unset key must not silently open the gateway.
        if settings.allow_insecure_no_auth:
            return
        raise HTTPException(
            status_code=503,
            detail="GATEWAY_API_KEY is not configured. Set it, or set ALLOW_INSECURE_NO_AUTH=true for local development only.",
        )
    if not api_key_matches(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
