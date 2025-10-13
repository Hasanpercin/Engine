# app/api/routers/synastry.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter
from app.utils.astro import to_jd, all_planets, angle_diff
from app.calculators.electional import MAJOR_ASPECTS, DEFAULT_ORBS

router = APIRouter(tags=["synastry"])

PLANET_LIST = ["sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto"]

class Natal(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int
    tz_offset: float = 0.0

class SynastryRequest(BaseModel):
    a: Natal
    b: Natal
    orb_overrides: Dict[str, float] | None = Field(default=None, description="örn: {'conjunction':8,'trine':6}")

class AspectItem(BaseModel):
    a_body: str
    b_body: str
    aspect: str
    delta: float     # |lonA - lonB| min (deg)
    orb: float       # izin verilen orb
    tightness: float # (orb - |delta - exact|), büyük = daha sıkı

class SynastryResponse(BaseModel):
    count: int
    items: List[AspectItem]

def _natal_dt(n: Natal) -> datetime:
    local = datetime(n.year, n.month, n.day, n.hour, n.minute,
                     tzinfo=timezone(timedelta(hours=n.tz_offset)))
    return local.astimezone(timezone.utc)

@router.post("/aspects", response_model=SynastryResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def aspects(req: SynastryRequest) -> Dict[str, Any]:
    try:
        jd_a = to_jd(_natal_dt(req.a))
        jd_b = to_jd(_natal_dt(req.b))
        pos_a = all_planets(jd_a)
        pos_b = all_planets(jd_b)

        orb_tbl = dict(DEFAULT_ORBS)
        if req.orb_overrides:
            for k, v in req.orb_overrides.items():
                if k in MAJOR_ASPECTS and v > 0:
                    orb_tbl[k] = float(v)

        items: List[Dict[str, Any]] = []
        for pa in PLANET_LIST:
            for pb in PLANET_LIST:
                da = pos_a[pa][0]; db = pos_b[pb][0]
                d = angle_diff(da, db)
                found = None
                diff_from_exact = None
                used_orb = None
                for asp, exact in MAJOR_ASPECTS.items():
                    orb = float(orb_tbl.get(asp, 6))
                    if abs(d - exact) <= orb:
                        found = asp
                        diff_from_exact = abs(d - exact)
                        used_orb = orb
                        break
                if found:
                    items.append({
                        "a_body": pa, "b_body": pb, "aspect": found,
                        "delta": d, "orb": used_orb,
                        "tightness": (used_orb - diff_from_exact) if used_orb is not None else 0.0,
                    })
        # sıkıdan gevşeğe sırala
        items.sort(key=lambda x: (-x["tightness"], x["aspect"]))
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Synastry error: {e}")
