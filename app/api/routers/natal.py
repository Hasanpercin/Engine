# app/api/routers/natal.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.astro import to_jd, all_planets
from app.utils.rate_limit import plan_limiter

router = APIRouter(tags=["natal"])  # prefix main.py'de

class NatalRequest(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int
    tz_offset: float = Field(0.0, description="Yerel saat UTC ofseti (saat cinsinden, örn. +3.0)")

class Body(BaseModel):
    name: str; lon: float; sign_index: int

class NatalResponse(BaseModel):
    ts_utc: str; bodies: List[Body]

@router.post("/basic", response_model=NatalResponse, dependencies=[Depends(plan_limiter("FREE"))])
async def basic(req: NatalRequest) -> Dict[str, Any]:
    try:
        base_local = datetime(req.year, req.month, req.day, req.hour, req.minute,
                              tzinfo=timezone(timedelta(hours=req.tz_offset)))
        dt_utc = base_local.astimezone(timezone.utc)
        jd = to_jd(dt_utc)
        pos = all_planets(jd)
        bodies = [{"name": k, "lon": v[0], "sign_index": int(v[0] // 30)} for k, v in pos.items()]
        return {"ts_utc": dt_utc.isoformat(), "bodies": bodies}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
