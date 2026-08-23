from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from config.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Middleware dependency that enforces API key authentication when CHRONOS_API_KEY is configured in .env.
    If CHRONOS_API_KEY is not set or empty, authentication is bypassed (Public mode).
    """
    expected_key = settings.CHRONOS_API_KEY
    
    # Bypass auth if no key is configured in server settings
    if not expected_key:
        return True

    if not api_key or api_key.strip() != expected_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing 'X-API-Key' header."
        )
    return True
