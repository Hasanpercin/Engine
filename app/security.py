# app/security.py
import os
from fastapi import Header, HTTPException, status

# Örnek: MCP_TOKENS="tok_v2,tok_v1"
_TOKENS = {t.strip() for t in os.getenv("MCP_TOKENS", "").split(",") if t.strip()}

def verify_bearer(authorization: str | None = Header(None)):
    # Prod'da mutlaka token olmalı:
    if not _TOKENS:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth misconfigured"
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    if token not in _TOKENS:
        # Bilgi sızdırma yok; tek tip hata
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
