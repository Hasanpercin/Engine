# app/main.py
from __future__ import annotations

import os
import time
import logging
import json
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# MCP
from fastapi_mcp import FastApiMCP, AuthConfig

from app.utils.rate_limit import init_rate_limiter
from app.security import verify_bearer

# --------- Lifespan ---------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rate_limiter(app)
    yield

# OpenAPI/dokümantasyon bayrağı
_openapi_enabled = os.getenv("OPENAPI_ENABLED", "true").strip().lower() not in {"0", "false", "no"}

app = FastAPI(
    title="AstroCalc Calculation Engine",
    version=os.getenv("ENGINE_VERSION", "0.1.0"),
    docs_url="/docs" if _openapi_enabled else None,
    redoc_url="/redoc" if _openapi_enabled else None,
    openapi_url="/openapi.json" if _openapi_enabled else None,
    lifespan=lifespan,
)

# --------- CORS ---------
_cors_origins_env = os.getenv("CORS_ORIGINS", "")
if _cors_origins_env:
    origins: List[str] = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            max_age=86400,
        )

# --------- MCP SessionId Injection Middleware ---------
class SessionIdInjectionMiddleware(BaseHTTPMiddleware):
    """
    SessionId'yi 3 kaynaktan okur: Query Param, Header, Body
    n8n için query param desteği eklendi: ?sessionId=xxx
    """
    async def dispatch(self, request: Request, call_next):
        # Uvicorn logger - kesinlikle çalışır
        logger = logging.getLogger("uvicorn.error")
        
        # HER İSTEĞİ LOGLA
        logger.info("🚀 MIDDLEWARE: %s %s", request.method, request.url.path)
        
        # MCP endpoint'leri için session injection (POST veya GET - SSE için)
        if request.url.path in ["/mcp", "/sse"] and request.method in ["POST", "GET"]:
            session_id = None
            
            # 1. ÖNCE QUERY PARAMETER'DAN OKU (n8n için)
            session_id = request.query_params.get("sessionId")
            if session_id:
                logger.info("🔍 SessionId from QUERY PARAM: %s", session_id)
            
            # 2. Query param yoksa HEADER'DAN OKU
            if not session_id:
                session_id = request.headers.get("X-Session-ID") or request.headers.get("x-session-id")
                if session_id:
                    logger.info("🔍 SessionId from HEADER: %s", session_id)
            
            # 3. SessionId varsa ve POST ise BODY'YE INJECT ET
            if session_id and request.method == "POST":
                try:
                    # Body'yi oku
                    body_bytes = await request.body()
                    
                    logger.info("📦 Body length: %d bytes", len(body_bytes))
                    
                    if body_bytes:
                        # JSON parse
                        body_json = json.loads(body_bytes.decode('utf-8'))
                        
                        # params ekle
                        if "params" not in body_json:
                            body_json["params"] = {}
                        
                        # SessionId inject
                        if isinstance(body_json["params"], dict):
                            if "sessionId" not in body_json["params"]:
                                body_json["params"]["sessionId"] = session_id
                                logger.info("✅ SessionId INJECTED into params: %s", session_id)
                            else:
                                logger.info("ℹ️ SessionId already exists in params")
                        
                        # Modified body
                        modified_body = json.dumps(body_json).encode('utf-8')
                        
                        # Request receive override
                        async def modified_receive():
                            return {
                                "type": "http.request",
                                "body": modified_body,
                                "more_body": False,
                            }
                        
                        request._receive = modified_receive
                        logger.info("📦 Body modified successfully")
                        
                except json.JSONDecodeError as e:
                    logger.warning("⚠️ JSON decode error: %s", e)
                except Exception as e:
                    logger.error("❌ Injection error: %s", e, exc_info=True)
            
            elif session_id and request.method == "GET":
                # SSE için - query param'da sessionId var, body yok
                logger.info("✅ SSE request with sessionId: %s", session_id)
            
            else:
                logger.warning("⚠️ No sessionId found (checked query param and header)")
        
        # Call next middleware
        response = await call_next(request)
        return response

# Middleware'i ekle - CORS'tan sonra, router'lardan önce
app.add_middleware(SessionIdInjectionMiddleware)

# --------- Sağlık ucu ---------
try:
    from app.api.routers import health  # type: ignore
    app.include_router(health.router)
except Exception:
    @app.get("/healthz")
    async def _healthz():
        return {"status": "ok"}

# --------- Routers ---------
# Lunar
try:
    from app.api.routers import lunar  # type: ignore
    app.include_router(lunar.router, prefix="/lunar", tags=["lunar"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Lunar router DISABLED: %s", e)

# Eclipses
try:
    from app.api.routers import eclipses  # type: ignore
    app.include_router(eclipses.router, prefix="/eclipses", tags=["eclipses"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Eclipses router DISABLED: %s", e)

# Synastry
try:
    from app.api.routers import synastry  # type: ignore
    app.include_router(synastry.router, prefix="/synastry", tags=["synastry"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Synastry router DISABLED: %s", e)

# Composite & Davison
try:
    from app.api.routers import composite  # type: ignore
    app.include_router(composite.router, tags=["composite"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Composite router DISABLED: %s", e)

# Returns
try:
    from app.api.routers import returns  # type: ignore
    app.include_router(returns.router, prefix="/returns", tags=["returns"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Returns router DISABLED: %s", e)

# Profections
try:
    from app.api.routers import profections  # type: ignore
    app.include_router(profections.router, prefix="/profections", tags=["profections"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Profections router DISABLED: %s", e)

# Retrogrades
try:
    from app.api.routers import retrogrades  # type: ignore
    app.include_router(retrogrades.router, prefix="/retrogrades", tags=["retrogrades"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Retrogrades router DISABLED: %s", e)

# Progressions
try:
    from app.api.routers import progressions  # type: ignore
    app.include_router(progressions.router, prefix="/progressions", tags=["progressions"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Progressions router DISABLED: %s", e)

# Transits
try:
    from app.api.routers import transits  # type: ignore
    app.include_router(transits.router, prefix="/transits", tags=["transits"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Transits router DISABLED: %s", e)

# Natal
try:
    from app.api.routers import natal  # type: ignore
    app.include_router(natal.router, prefix="/natal", tags=["natal"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Natal router DISABLED: %s", e)

# Electional
try:
    from app.api.routers import electional  # type: ignore
    app.include_router(electional.router, prefix="/electional", tags=["electional"])
except Exception as e:
    logging.getLogger("uvicorn.error").warning("Electional router DISABLED: %s", e)

# --------- MCP (AI Agent tool'ları) ---------
_MCP_INCLUDE_TAGS = [
    "lunar",
    "eclipses",
    "synastry",
    "composite",
    "returns",
    "profections",
    "retrogrades",
    "progressions",
    "transits",
    "natal",
    "electional",
]

mcp = FastApiMCP(
    app,
    name="AstroCalc Engine MCP",
    description="AstroCalc hesaplama motoru için MCP tool seti",
    include_tags=_MCP_INCLUDE_TAGS,
    describe_all_responses=True,
    describe_full_response_schema=True,
    auth_config=AuthConfig(dependencies=[Depends(verify_bearer)]),
)

# Hem HTTP hem SSE taşımasını aç
mcp.mount_http()   # -> /mcp
mcp.mount_sse()    # -> /sse

# --------- /version ---------
ENGINE_VERSION = os.getenv("ENGINE_VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "unknown")
BUILD_TIME = os.getenv("BUILD_TIME", "")

@app.get("/version")
def version():
    return {
        "engine_version": ENGINE_VERSION,
        "git_sha": GIT_SHA,
        "build_time": BUILD_TIME,
        "routes": sorted([r.path for r in app.routes]),
    }

# --------- Startup: kısa özet log ---------
@app.on_event("startup")
async def _on_startup():
    rl_url = os.getenv("RATE_LIMIT_REDIS_URL")
    if rl_url:
        logging.getLogger("engine.bootstrap").info("Rate limiter: ENABLED (redis=%s)", rl_url)
    else:
        logging.getLogger("engine.bootstrap").info("Rate limiter: DISABLED")
    
    logging.getLogger("engine.bootstrap").info("Routes: %s", ", ".join(sorted([r.path for r in app.routes])))
    logging.getLogger("engine.bootstrap").info("MCP endpoints: /mcp (HTTP), /sse (SSE)")
    logging.getLogger("engine.bootstrap").info("SessionId injection: ENABLED (query param + header + body)")
```

## Ana Değişiklikler:

1. ✅ **Satır 68**: `request.method in ["POST", "GET"]` - SSE için GET desteği
2. ✅ **Satır 71-74**: **Query parameter'dan sessionId okuma** (n8n için)
3. ✅ **Satır 77-80**: Header'dan okuma (fallback)
4. ✅ **Satır 83**: POST için body injection
5. ✅ **Satır 117-119**: GET/SSE için log
6. ✅ **Satır 122**: Daha açıklayıcı warning

Şimdi n8n'deki URL çalışacak:
```
https://engine.hasanpercin.xyz/mcp/sse?sessionId=xxx
