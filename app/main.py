# app/main.py
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.rate_limit import init_rate_limiter

# --------- Lifespan ---------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Rate limiter'ı başlat (fail-open; Redis yoksa servis yine ayakta kalır)
    await init_rate_limiter(app)
    yield
    # (Gerekirse kapanışta kaynakları temizleyebilirsin)

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

# --------- CORS (opsiyonel) ---------
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

# --------- Routers ---------
# Sağlık ucu mutlaka mevcut olsun:
try:
    from app.api.routers import health  # type: ignore
    app.include_router(health.router)
except Exception:
    @app.get("/healthz")
    async def _healthz():
        return {"status": "ok"}

# Diğer router örneği: electional
try:
    from app.api.routers import electional  # type: ignore
    app.include_router(electional.router, prefix="/electional", tags=["electional"])
except Exception:
    # Router yoksa servis yine ayağa kalksın; sağlık ucu yeter.
    pass
