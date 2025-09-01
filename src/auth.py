"""API Key Authentication for FreeRADIUS API."""

from fastapi import Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from src.settings import settings

# Create API key header checker
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(x_api_key: str = Depends(api_key_header)):
    """Verify the API key from the request header.
    
    Args:
        x_api_key: The API key from the header
        
    Raises:
        HTTPException: If API key authentication is enabled and the key is invalid or missing
    """
    # If API key authentication is not enabled, allow the request
    if not settings.api_key_enabled:
        return True
    
    # If API key is missing or doesn't match, deny access
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    
    return True