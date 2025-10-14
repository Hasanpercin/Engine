# app/api/routers/eclipses.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.utils.rate_limit import plan_limiter

# Swiss Ephemeris
try:
    import swisseph as swe  # type: ignore
except Exception:  # pragma: no cover
    import pyswisseph as swe  # type: ignore

swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))
router = APIRouter(tags=["eclipses"])

# ---------- helpers ----------
def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def _jd_to_iso(jd: float) -> str:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    total_seconds = int(round(h * 3600))
    return (base + timedelta(seconds=total_seconds)).isoformat()

# SwissEph flag sabitleri (doğru fallback değerlerle)
ECL_CENTRAL        = getattr(swe, "SE_ECL_CENTRAL",         1)
ECL_NONCENTRAL     = getattr(swe, "SE_ECL_NONCENTRAL",      2)
ECL_TOTAL          = getattr(swe, "SE_ECL_TOTAL",           4)
ECL_ANNULAR        = getattr(swe, "SE_ECL_ANNULAR",         8)
ECL_PARTIAL        = getattr(swe, "SE_ECL_PARTIAL",        16)
ECL_ANNULAR_TOTAL  = getattr(swe, "SE_ECL_ANNULAR_TOTAL",  32)
ECL_PENUMBRAL      = getattr(swe, "SE_ECL_PENUMBRAL",      64)

def _normalize_ecl_result(out: Any) -> Tuple[int, List[float], Optional[List[float]]]:
    """
    Dönüş imzalarını normalize et:
      - (retflag, tret, attr, serr)
      - (tret, retflag)
      - (retflag, tret)
      - yalnız tret
    Döndür: (retflag, list(tret), list(attr)|None)
    """
    if isinstance(out, tuple):
        if len(out) == 4:
            retflag, tret, attr, _ = out
            return int(retflag), list(tret), list(attr)
        if len(out) == 2:
            a, b = out
            if isinstance(a, (list, tuple)):
                return int(b), list(a), None
            return int(a), list(b), None
    if isinstance(out, (list, tuple)) and len(out) >= 1:
        return 0, list(out), None
    raise TypeError(f"Unexpected eclipse result shape: {type(out)}")

def _call_sol_glob(jd: float, ifl: int) -> Tuple[int, List[float], Optional[List[float]], str]:
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.sol_eclipse_when_glob(*args)  # type: ignore[misc]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "sol_glob"
        except Exception:
            continue
    return 0, [], None, "sol_glob"

def _call_lun_glob_or_when(jd: float, ifl: int) -> Tuple[int, List[float], Optional[List[float]], str]:
    # Bazı build'larda lun_eclipse_when_glob yok; varsa önce onu deneriz
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when_glob(*args)  # type: ignore[attr-defined]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "lun_glob"
        except Exception:
            continue
    # Standart global arama (lokasyon gerektirmez)
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when(*args)  # type: ignore[misc]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "lun_when"
        except Exception:
            continue
    return 0, [], None, "lun_none"

def _sol_how_at(jd: float, ifl: int) -> Tuple[Optional[int], Optional[List[float]]]:
    """
    Solar tip teyidi: jd_max anında 'how'.
    İmza: (tjd_ut, ifl, geopos[lon,lat,alt], atpress, attemp)
    """
    for args in (
        (jd, ifl, (0.0, 0.0, 0.0), 0.0, 0.0),
        (jd, ifl, [0.0, 0.0, 0.0], 0.0, 0.0),
    ):
        try:
            out = swe.sol_eclipse_how(*args)  # type: ignore[misc]
            if isinstance(out, tuple) and len(out) >= 2:
                retflag, attr = out[0], out[1]
                return int(retflag), list(attr) if isinstance(attr, (list, tuple)) else None
        except Exception:
            continue
    return None, None

def _lun_how_at(jd: float, ifl: int) -> Tuple[Optional[int], Optional[List[float]]]:
    """
    Lunar tip teyidi: jd_max anında 'how'.
    İmza: (tjd_ut, ifl, geopos[lon,lat,alt], atpress, attemp)
    """
    for args in (
        (jd, ifl, (0.0, 0.0, 0.0), 0.0, 0.0),
        (jd, ifl, [0.0, 0.0, 0.0], 0.0, 0.0),
    ):
        try:
            out = swe.lun_eclipse_how(*args)  # type: ignore[misc]
            if isinstance(out, tuple) and len(out) >= 2:
                retflag, attr = out[0], out[1]
                return int(retflag), list(attr) if isinstance(attr, (list, tuple)) else None
        except Exception:
            continue
    return None, None

def _classify_solar(retflag: int) -> str:
    # Tip = hybrid > total > annular > partial  (merkezlilik ayrı)
    if retflag & ECL_ANNULAR_TOTAL:
        return "hybrid"
    if retflag & ECL_TOTAL:
        return "total"
    if retflag & ECL_ANNULAR:
        return "annular"
    if retflag & ECL_PARTIAL:
        return "partial"
    return "unknown"

def _solar_centrality(retflag: int) -> Optional[str]:
    if retflag & ECL_CENTRAL:
        return "central"
    if retflag & ECL_NONCENTRAL:
        return "noncentral"
    return None

def _classify_lunar(retflag: int) -> str:
    # Lunar: total > partial > penumbral
    if retflag & ECL_TOTAL:
        return "total"
    if retflag & ECL_PARTIAL:
        return "partial"
    if retflag & ECL_PENUMBRAL:
        return "penumbral"
    return "unknown"

# ---------- models ----------
class RangeRequest(BaseModel):
    start_year: int
    start_month: int
    start_day: int
    end_year: int
    end_month: int
    end_day: int
    max_events: int = Field(20, ge=1, le=200)
    debug: bool = False

class EclipseItem(BaseModel):
    kind: str
    type: str
    max_ts: str
    jd_max: float
    retflag: Optional[int] = None
    api: Optional[str] = None
    attrs: Optional[List[float]] = None
    centrality: Optional[str] = None

class RangeResponse(BaseModel):
    count: int
    items: List[EclipseItem]

# ---------- endpoints ----------
@router.post(
    "/solar/range",
    response_model=RangeResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(plan_limiter("PRO"))],
)
async def solar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = getattr(swe, "FLG_SWIEPH", 2)

        while True:
            retflag, tret, attr, api = _call_sol_glob(jd, ifl)
            if not tret:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            if jd_max <= jd:
                jd = jd + 25.0
                continue

            # jd_max’te tip teyidi
            ret2, attr2 = _sol_how_at(jd_max, ifl)
            use_ret = int(ret2) if ret2 is not None else int(retflag)

            item: Dict[str, Any] = {
                "kind": "solar",
                "type": _classify_solar(use_ret),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            }
            if req.debug:
                item.update({
                    "retflag": use_ret,
                    "api": api,
                    "centrality": _solar_centrality(retflag),  # merkezlilik 'when_glob' retflag'ından
                    "attrs": attr2 if attr2 is not None else attr
                })
            items.append(item)

            if len(items) >= req.max_events:
                break
            jd = max(jd_max + 1.0, jd + 25.0)

        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solar eclipse search failed: {e}")

@router.post(
    "/lunar/range",
    response_model=RangeResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(plan_limiter("PRO"))],
)
async def lunar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = getattr(swe, "FLG_SWIEPH", 2)

        while True:
            retflag, tret, attr, api = _call_lun_glob_or_when(jd, ifl)
            if not tret:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            if jd_max <= jd:
                jd = jd + 25.0
                continue

            # jd_max’te tip teyidi
            ret2, attr2 = _lun_how_at(jd_max, ifl)
            use_ret = int(ret2) if ret2 is not None else int(retflag)

            item: Dict[str, Any] = {
                "kind": "lunar",
                "type": _classify_lunar(use_ret),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            }
            if req.debug:
                item.update({
                    "retflag": use_ret,
                    "api": api,
                    "attrs": attr2 if attr2 is not None else attr
                })
            items.append(item)

            if len(items) >= req.max_events:
                break
            jd = max(jd_max + 1.0, jd + 25.0)

        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")
