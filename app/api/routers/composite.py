# app/api/routers/composite.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter
from app.utils.astro import to_jd, all_planets

router = APIRouter(tags=["composite"])

PLANET_LIST = ["sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto"]

class Natal(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int
    tz_offset: float = 0.0

class CompositeRequest(BaseModel):
    a: Natal
    b: Natal

class Body(BaseModel):
    name: str; lon: float

class CompositeResponse(BaseModel):
    method: str
    bodies: List[Body]

def _natal_dt(n: Natal) -> datetime:
    local = datetime(n.year, n.month, n.day, n.hour, n.minute,
                     tzinfo=timezone(timedelta(hours=n.tz_offset)))
    return local.astimezone(timezone.utc)

def _circ_mid(a: float, b: float) -> float:
    """
    Dairesel orta nokta: kısa yay üzerinden ortalama.
    """
    # normalize
    a %= 360.0; b %= 360.0
    diff = ((b - a + 540.0) % 360.0) - 180.0  # signed shortest
    return (a + diff / 2.0) % 360.0

@router.post("/composite/planets", response_model=CompositeResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def composite_planets(req: CompositeRequest) -> Dict[str, Any]:
    try:
        jd_a = to_jd(_natal_dt(req.a))
        jd_b = to_jd(_natal_dt(req.b))
        pos_a = all_planets(jd_a)
        pos_b = all_planets(jd_b)

        bodies = []
        for p in PLANET_LIST:
            mid = _circ_mid(pos_a[p][0], pos_b[p][0])
            bodies.append({"name": p, "lon": mid})
        return {"method": "composite-midpoint", "bodies": bodies}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Composite error: {e}")

class DavisonRequest(BaseModel):
    a: Natal
    b: Natal

class DavisonResponse(BaseModel):
    ts_utc: str
    bodies: List[Body]

@router.post("/davison/planets", response_model=DavisonResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def davison_planets(req: DavisonRequest) -> Dict[str, Any]:
    """
    Davison: iki doğum zamanının tam ortası (UTC) için gerçek gezegen konumları.
    (Şimdilik yer bilgisi gerektirmeyen, gezegen boylamları.)
    """
    try:
        dt_a = _natal_dt(req.a)
        dt_b = _natal_dt(req.b)
        # midpoint in time (UTC)
        mid_ts = dt_a + (dt_b - dt_a) / 2
        jd_mid = to_jd(mid_ts)
        pos = all_planets(jd_mid)
        bodies = [{"name": k, "lon": v[0]} for k, v in pos.items() if k in PLANET_LIST]
        return {"ts_utc": mid_ts.isoformat(), "bodies": bodies}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Davison error: {e}")
