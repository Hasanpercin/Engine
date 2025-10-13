# app/api/routers/progressions.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter

try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

router = APIRouter(tags=["progressions"])

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def _planet_lon(jd: float, pid: int) -> float:
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[0] % 360.0

_PLANETS = [
    ("sun", swe.SUN), ("moon", swe.MOON), ("mercury", swe.MERCURY), ("venus", swe.VENUS),
    ("mars", swe.MARS), ("jupiter", swe.JUPITER), ("saturn", swe.SATURN),
    ("uranus", swe.URANUS), ("neptune", swe.NEPTUNE), ("pluto", swe.PLUTO),
]

class Natal(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int
    tz_offset: float = 0.0

class SecondaryRequest(BaseModel):
    natal: Natal
    for_year: int = Field(..., description="Progressed date: 1 gün = 1 yıl kuralına göre hedef yıl (UTC)")

class Body(BaseModel):
    name: str
    lon: float

class SecondaryResponse(BaseModel):
    ts_utc: str
    jd: float
    bodies: List[Body]

@router.post("/secondary", response_model=SecondaryResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def secondary(req: SecondaryRequest) -> Dict[str, Any]:
    try:
        n = req.natal
        local = datetime(n.year, n.month, n.day, n.hour, n.minute, tzinfo=timezone(timedelta(hours=n.tz_offset)))
        natal_utc = local.astimezone(timezone.utc)
        # 1 gün = 1 yıl
        years = req.for_year - natal_utc.year
        prog_dt = natal_utc + timedelta(days=years)  # basit kural
        jd = _to_jd(prog_dt)
        bodies = [{"name": name, "lon": _planet_lon(jd, pid)} for name, pid in _PLANETS]
        return {"ts_utc": prog_dt.isoformat(), "jd": jd, "bodies": bodies}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SolarArcRequest(BaseModel):
    natal: Natal
    for_year: int

class SolarArcResponse(BaseModel):
    ts_utc: str
    jd: float
    arc: float
    bodies: List[Body]

@router.post("/solar-arc", response_model=SolarArcResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def solar_arc(req: SolarArcRequest) -> Dict[str, Any]:
    try:
        n = req.natal
        local = datetime(n.year, n.month, n.day, n.hour, n.minute, tzinfo=timezone(timedelta(hours=n.tz_offset)))
        natal_utc = local.astimezone(timezone.utc)
        years = req.for_year - natal_utc.year
        # Secondary progressed Sun
        prog_dt = natal_utc + timedelta(days=years)
        jd_prog = _to_jd(prog_dt)
        sun_prog = _planet_lon(jd_prog, swe.SUN)
        # Natal positions
        jd_nat = _to_jd(natal_utc)
        sun_nat = _planet_lon(jd_nat, swe.SUN)
        arc = (sun_prog - sun_nat) % 360.0
        bodies = []
        for name, pid in _PLANETS:
            natal_lon = _planet_lon(jd_nat, pid)
            bodies.append({"name": name, "lon": (natal_lon + arc) % 360.0})
        return {"ts_utc": prog_dt.isoformat(), "jd": jd_prog, "arc": arc, "bodies": bodies}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
