import os
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

FREE_HOURLY_LIMIT = int(os.getenv("FREE_HOURLY_LIMIT", "100"))
PRO_HOURLY_LIMIT = int(os.getenv("PRO_HOURLY_LIMIT", "2000"))

async def init_rate_limiter(app: FastAPI):
    r = await redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

def plan_limiter(plan: str):
    # plan: "free" or "pro"
    limit = FREE_HOURLY_LIMIT if plan.lower() == "free" else PRO_HOURLY_LIMIT
    return RateLimiter(times=limit, seconds=3600)
