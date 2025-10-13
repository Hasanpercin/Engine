# app/api/routers/eclipses.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.utils.rate_limit import plan_limiter

try:
    import swisseph as swe
except Exception:  # pragma: no cover
    import pyswisseph as swe  # type: ignore

swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

router = APIRouter(tags=["eclipses"])

# ---------- helpers ----------
def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def _jd_to_iso(jd: float) -> str:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(hours=hh, minutes=mm)).isoformat()

def _sol_type_name(retflag: int) -> str:
    if retflag & swe.SE_ECL_TOTAL: return "total"
    if retflag & swe.SE_ECL_ANNULAR_TOTAL: return "hybrid"
    if retflag & swe.SE_ECL_ANNULAR: return "annular"
    if retflag & swe.SE_ECL_PARTIAL: return "partial"
    return "unknown"

def _lun_type_name(retflag: int) -> str:
    if retflag & swe.SE_ECL_TOTAL: return "total"
    if retflag & swe.SE_ECL_PARTIAL: return "partial"
    if retflag & swe.SE_ECL_PENUMBRAL: return "penumbral"
    return "unknown"

def _normalize_ecl_result(out: Any) -> Tuple[int, List[float]]:
    """
    Çeşitli pyswisseph sürümlerine uyum:
    - (retflag, tret, attr, serr)
    - (tret, retflag)
    - (retflag, tret)
    """
    if isinstance(out, tuple):
        if len(out) == 4:
            retflag, tret, _, _ = out
            return int(retflag), list(tret)
        if len(out) == 2:
            a, b = out
            # a list/tuple ise tret odur; değilse terse çevir
            if isinstance(a, (list, tuple)):
                return int(b), list(a)
            else:
                return int(a), list(b)
    raise TypeError(f"Unexpected eclipse result shape: {type(out)} len={len(out) if hasattr(out,'__len__') else 'n/a'}")

def _call_sol_glob(jd: float, ifl: int) -> Tuple[int, List[float]]:
    # Sırayla farklı imzaları dene
    for args in [(jd, ifl, 0), (jd, ifl)]:
        try:
            out = swe.sol_eclipse_when_glob(*args)  # type: ignore[misc]
            return _normalize_ecl_result(out)
        except Exception:
            continue
    # Bazı çok eski sürümler parametresiz sadece (jd) kabul edebilir
    out = swe.sol_eclipse_when_glob(jd)  # type: ignore[misc]
    return _normalize_ecl_result(out)

def _call_lun_glob(jd: float, ifl: int) -> Tuple[int, List[float]]:
    for args in [(jd, ifl, 0), (jd, ifl)]:
        try:
            out = swe.lun_eclipse_when_glob(*args)  # type: ignore[misc]
            return _normalize_ecl_result(out)
        except Exception:
            continue
    out = swe.lun_eclipse_when_glob(jd)  # type: ignore[misc]
    return _normalize_ecl_result(out)

# ---------- models ----------
class RangeRequest(BaseModel):
    start_year: int; start_month: int; start_day: int
    end_year: int; end_month: int; end_day: int
    max_events: int = Field(20, ge=1, le=200)

class EclipseItem(BaseModel):
    kind: str
    type: str
    max_ts: str
    jd_max: float

class RangeResponse(BaseModel):
    count: int
    items: List[EclipseItem]

# ---------- endpoints ----------
@router.post("/solar/range", response_model=RangeResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def solar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = swe.FLG_SWIEPH

        while True:
            retflag, tret = _call_sol_glob(jd, ifl)
            if not retflag:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            items.append({
                "kind": "solar",
                "type": _sol_type_name(retflag),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            })
            if len(items) >= req.max_events:
                break
            jd = jd_max + 1.0
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solar eclipse search failed: {e}")

@router.post("/lunar/range", response_model=RangeResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def lunar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = swe.FLG_SWIEPH

        while True:
            retflag, tret = _call_lun_glob(jd, ifl)
            if not retflag:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            items.append({
                "kind": "lunar",
                "type": _lun_type_name(retflag),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            })
            if len(items) >= req.max_events:
                break
            jd = jd_max + 1.0
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")
