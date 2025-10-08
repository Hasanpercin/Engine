# app/utils/rate_limit.py
"""
Rate limit altyapısı (fastapi-limiter + Redis).
- Fail-open: Redis'e bağlanılamazsa servis yine başlar, yalnızca rate limit devre dışı kalır.
- PLAN bazlı limit: FREE / PRO değerleri env'den okunur.
Kullanım (router'da):
    from fastapi import Depends
    from app.utils.rate_limit import plan_limiter

    @router.get("/something", dependencies=[Depends(plan_limiter("FREE"))])
    async def something(...): ...
"""

from __future__ import annotations
import os
import logging
from typing import Optional

try:
    import redis.asyncio as redis  # redis==5.x ile gelir
except Exception as e:  # pragma: no cover
    redis = None  # type: ignore

try:
    from fastapi_limiter import FastAPILimiter
    from fastapi_limiter.depends import RateLimiter
except Exception:  # pragma: no cover
    FastAPILimiter = None  # type: ignore

LOGGER = logging.getLogger("uvicorn.error")

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except Exception:
        return default

def is_rate_limit_disabled() -> bool:
    return _env_bool("RATE_LIMIT_DISABLED", False)

def _plan_limits(plan: str) -> tuple[int, int]:
    """Saatlik limitler: (times, seconds)"""
    plan_up = (plan or "FREE").upper()
    if plan_up == "PRO":
        times = _env_int("PRO_HOURLY_LIMIT", 2000)
    else:
        times = _env_int("FREE_HOURLY_LIMIT", 100)
    return times, 3600

async def init_rate_limiter(app: Optional["FastAPI"] = None) -> None:
    """
    Redis'e bağlanır ve FastAPILimiter'i initialize eder.
    'app' opsiyoneldir; verilirse app.state içine flag yazar.
    Fail-open: herhangi bir hata olursa yalnızca uyarı loglar, raise etmez.
    """
    # Rate limit tamamen kapatılmak istenirse bayrak:
    if is_rate_limit_disabled():
        LOGGER.warning("Rate limiter disabled via RATE_LIMIT_DISABLED=1")
        if app is not None:
            try:
                app.state.rate_limiter_enabled = False  # type: ignore[attr-defined]
            except Exception:
                pass
        return

    if FastAPILimiter is None or redis is None:
        LOGGER.warning("Rate limiter dependencies missing; continuing without limits.")
        if app is not None:
            try:
                app.state.rate_limiter_enabled = False  # type: ignore[attr-defined]
            except Exception:
                pass
        return

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)  # type: ignore
        await FastAPILimiter.init(r)  # type: ignore
        LOGGER.info("Rate limiter: ENABLED (redis=%s)", redis_url)
        if app is not None:
            try:
                app.state.rate_limiter_enabled = True  # type: ignore[attr-defined]
            except Exception:
                pass
    except Exception as e:
        LOGGER.warning("Rate limiter init failed: %s; continuing without limits.", e)
        if app is not None:
            try:
                app.state.rate_limiter_enabled = False  # type: ignore[attr-defined]
            except Exception:
                pass

def plan_limiter(plan: str = "FREE"):
    """
    Router'da dependency olarak kullan:
        dependencies=[Depends(plan_limiter("FREE"))]
    """
    # Eğer limiter hiç init edilmediyse de RateLimiter nesnesi oluşturmak güvenlidir;
    # fastapi-limiter, init edilmemişse limitsiz davranır.
    times, seconds = _plan_limits(plan)
    try:
        return RateLimiter(times=times, seconds=seconds)  # type: ignore
    except Exception:
        # fastapi_limiter yoksa hiçbir şey döndürme; FastAPI dependency listesinde None yoksayılır.
        return
