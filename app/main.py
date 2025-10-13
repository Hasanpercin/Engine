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

# Lunar
try:
    from app.api.routers import lunar  # type: ignore
    app.include_router(lunar.router, prefix="/lunar", tags=["lunar"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Lunar router DISABLED: %s", e)

# Eclipses
try:
    from app.api.routers import eclipses  # type: ignore
    app.include_router(eclipses.router, prefix="/eclipses", tags=["eclipses"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Eclipses router DISABLED: %s", e)

# Synastry
try:
    from app.api.routers import synastry  # type: ignore
    app.include_router(synastry.router, prefix="/synastry", tags=["synastry"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Synastry router DISABLED: %s", e)

# Composite & Davison  (prefix VERME!)
try:
    from app.api.routers import composite  # type: ignore
    app.include_router(composite.router, tags=["composite"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Composite router DISABLED: %s", e)

# Returns
try:
    from app.api.routers import returns  # type: ignore
    app.include_router(returns.router, prefix="/returns", tags=["returns"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Returns router DISABLED: %s", e)

# Profections
try:
    from app.api.routers import profections  # type: ignore
    app.include_router(profections.router, prefix="/profections", tags=["profections"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Profections router DISABLED: %s", e)

# Retrogrades
try:
    from app.api.routers import retrogrades  # type: ignore
    app.include_router(retrogrades.router, prefix="/retrogrades", tags=["retrogrades"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Retrogrades router DISABLED: %s", e)

# Progressions
try:
    from app.api.routers import progressions  # type: ignore
    app.include_router(progressions.router, prefix="/progressions", tags=["progressions"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Progressions router DISABLED: %s", e)

# Transits
try:
    from app.api.routers import transits  # type: ignore
    app.include_router(transits.router, prefix="/transits", tags=["transits"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Transits router DISABLED: %s", e)

# Natal
try:
    from app.api.routers import natal  # type: ignore
    app.include_router(natal.router, prefix="/natal", tags=["natal"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Natal router DISABLED: %s", e)

# Electional
try:
    from app.api.routers import electional  # type: ignore
    # electional.router içinde prefix tanımlı değil; burada veriyoruz
    app.include_router(electional.router, prefix="/electional", tags=["electional"])
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning("Electional router DISABLED: %s", e)
