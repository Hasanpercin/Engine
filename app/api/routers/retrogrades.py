# app/api/routers/retrogrades.py
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

router = APIRouter(tags=["retrogrades"])

_PLANETS = [
    ("mercury", swe.MERCURY), ("venus", swe.VENUS), ("mars", swe.MARS),
    ("jupiter", swe.JUPITER), ("saturn", swe.SATURN), ("uranus", swe.URANUS),
    ("neptune", swe.NEPTUNE), ("pluto", swe.PLUTO)
]

def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

def _speed(jd: float, pid: int) -> float:
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[3]

class CurrentRequest(BaseModel):
    year: int; month: int; day: int; hour: int = 0; minute: int = 0

class CurrentResponse(BaseModel):
    ts: str
    retrogrades: Dict[str, bool]

@router.post("/current", response_model=CurrentResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def current(req: CurrentRequest) -> Dict[str, Any]:
    try:
        dt = datetime(req.year, req.month, req.day, req.hour, req.minute, tzinfo=timezone.utc)
        jd = _to_jd(dt)
        out = {name: (_speed(jd, pid) < 0) for name, pid in _PLANETS}
        return {"ts": dt.isoformat(), "retrogrades": out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class RangeRequest(BaseModel):
    start_year: int; start_month: int; start_day: int
    end_year: int; end_month: int; end_day: int
    step_hours: int = Field(12, ge=1, le=48)

class Interval(BaseModel):
    planet: str
    start_ts: str
    end_ts: str

class RangeResponse(BaseModel):
    count: int
    items: List[Interval]

@router.post("/range", response_model=RangeResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def range_(req: RangeRequest) -> Dict[str, Any]:
    try:
        start = datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc)
        end = datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc)
        step = timedelta(hours=int(req.step_hours))

        items: List[Dict[str, Any]] = []
        for name, pid in _PLANETS:
            cur = start
            in_rx = None
            int_start = None
            while cur <= end:
                jd = _to_jd(cur)
                rx = _speed(jd, pid) < 0
                if in_rx is None:
                    in_rx = rx
                    if rx: int_start = cur
                elif in_rx != rx:
                    # transition
                    if rx:
                        # direct -> retro start
                        int_start = cur
                    else:
                        # retro -> direct end
                        if int_start is not None:
                            items.append({"planet": name, "start_ts": int_start.isoformat(), "end_ts": cur.isoformat()})
                            int_start = None
                    in_rx = rx
                cur += step
            # if ends in retro
            if in_rx and int_start is not None:
                items.append({"planet": name, "start_ts": int_start.isoformat(), "end_ts": end.isoformat()})
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
