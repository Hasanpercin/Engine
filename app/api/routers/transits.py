# app/api/routers/transits.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.astro import to_jd, all_planets, angle_diff
from app.calculators.electional import MAJOR_ASPECTS, DEFAULT_ORBS
from app.utils.rate_limit import plan_limiter

router = APIRouter(tags=["transits"])  # prefix main.py'de

def _energy_point(ts: datetime) -> Dict[str, int]:
    pos = all_planets(to_jd(ts))
    names = list(pos.keys())
    good = hard = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            da = pos[names[i]][0]; db = pos[names[j]][0]
            delta = angle_diff(da, db)
            for asp, ang in MAJOR_ASPECTS.items():
                orb = DEFAULT_ORBS.get(asp, 6)
                if abs(delta - ang) <= orb:
                    if asp in ("trine", "sextile"):
                        good += 1
                    elif asp in ("square", "opposition"):
                        hard += 1
                    break
    return {"good_aspects": good, "hard_aspects": hard}

class DailyRequest(BaseModel):
    year: int; month: int; day: int
    step_minutes: int = Field(120, ge=30, le=360)

class EnergyPoint(BaseModel):
    ts: str
    good_aspects: int
    hard_aspects: int

class DailyResponse(BaseModel):
    count: int
    items: List[EnergyPoint]

@router.post("/daily", response_model=DailyResponse, dependencies=[Depends(plan_limiter("FREE"))])
async def daily(req: DailyRequest) -> Dict[str, Any]:
    try:
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        end = base + timedelta(days=1)
        cur = base
        step = timedelta(minutes=int(req.step_minutes))
        out: List[Dict[str, Any]] = []
        while cur < end:
            e = _energy_point(cur)
            out.append({"ts": cur.isoformat(), **e})
            cur += step
        return {"count": len(out), "items": out}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class WeeklyRequest(BaseModel):
    year: int; month: int; day: int  # haftanın başlangıcı (UTC)
    step_hours: int = Field(6, ge=1, le=24)
    days: int = Field(7, ge=3, le=10)

class WeeklyItem(BaseModel):
    ts: str; good_aspects: int; hard_aspects: int

class WeeklyResponse(BaseModel):
    count: int; items: List[WeeklyItem]

@router.post("/weekly", response_model=WeeklyResponse, dependencies=[Depends(plan_limiter("FREE"))])
async def weekly(req: WeeklyRequest) -> Dict[str, Any]:
    try:
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        end = base + timedelta(days=int(req.days))
        cur = base
        step = timedelta(hours=int(req.step_hours))
        items: List[Dict[str, Any]] = []
        while cur < end:
            e = _energy_point(cur)
            items.append({"ts": cur.isoformat(), **e})
            cur += step
        return {"count": len(items), "items": items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
