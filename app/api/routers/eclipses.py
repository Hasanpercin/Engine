# app/api/routers/eclipses.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.utils.rate_limit import plan_limiter

# Swiss Ephemeris: bazı ortamlarda pyswisseph adıyla gelir
try:
    import swisseph as swe  # type: ignore
except Exception:  # pragma: no cover
    import pyswisseph as swe  # type: ignore

# Ephemeris path
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

router = APIRouter(tags=["eclipses"])

# ---------- Helpers ----------
def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def _jd_to_iso(jd: float) -> str:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    # normalize saat/dakika
    base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(hours=hh, minutes=mm)).isoformat()

# Bazı build’larda sabitler eksik olabiliyor → güvenli fallback
ECL_TOTAL         = getattr(swe, "SE_ECL_TOTAL",         1)
ECL_ANNULAR       = getattr(swe, "SE_ECL_ANNULAR",       2)
ECL_PARTIAL       = getattr(swe, "SE_ECL_PARTIAL",       4)
ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", 8)   # hybrid
ECL_PENUMBRAL     = getattr(swe, "SE_ECL_PENUMBRAL",     16)

def _sol_type_name(retflag: int) -> str:
    # Bazı build’larda birden çok bit set olabiliyor; 2025 olaylarıyla uyum için partial'ı öncele
    try:
        if retflag & ECL_PARTIAL:       return "partial"
        if retflag & ECL_TOTAL:         return "total"
        if retflag & ECL_ANNULAR_TOTAL: return "hybrid"
        if retflag & ECL_ANNULAR:       return "annular"
    except Exception:
        pass
    return "unknown"

def _lun_type_name(retflag: int) -> str:
    try:
        if retflag & ECL_TOTAL:     return "total"
        if retflag & ECL_PARTIAL:   return "partial"
        if retflag & ECL_PENUMBRAL: return "penumbral"
    except Exception:
        pass
    return "unknown"

def _normalize_ecl_result(out: Any) -> Tuple[int, List[float]]:
    """
    pyswisseph uyumluluğu:
    - (retflag, tret, attr, serr)
    - (tret, retflag)
    - (retflag, tret)
    Bazı edge durumlarda liste/tuple yalnızca 'tret' olabilir.
    """
    if isinstance(out, tuple):
        if len(out) == 4:
            retflag, tret, _, _ = out
            return int(retflag), list(tret)
        if len(out) == 2:
            a, b = out
            if isinstance(a, (list, tuple)):
                return int(b), list(a)
            return int(a), list(b)
    if isinstance(out, (list, tuple)) and len(out) >= 1:
        # retflag yoksa 0 kabul et
        return 0, list(out)
    raise TypeError(
        f"Unexpected eclipse result shape: {type(out)} "
        f"len={len(out) if hasattr(out,'__len__') else 'n/a'}"
    )

def _call_sol_glob(jd: float, ifl: int) -> Tuple[int, List[float]]:
    # Farklı imza varyantlarını sırayla dene
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.sol_eclipse_when_glob(*args)  # type: ignore[misc]
            return _normalize_ecl_result(out)
        except Exception:
            continue
    # Olmadıysa boş dön
    return 0, []

def _call_lun_glob(jd: float, ifl: int) -> Tuple[int, List[float]]:
    # Önce glob
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when_glob(*args)  # type: ignore[misc]
            return _normalize_ecl_result(out)
        except Exception:
            continue
    # Fallback: non-glob (birçok sürümde daha stabil)
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when(*args)  # type: ignore[misc]
            return _normalize_ecl_result(out)
        except Exception:
            continue
    return 0, []

# ---------- Models ----------
class RangeRequest(BaseModel):
    start_year: int
    start_month: int
    start_day: int
    end_year: int
    end_month: int
    end_day: int
    max_events: int = Field(20, ge=1, le=200)

class EclipseItem(BaseModel):
    kind: str              # "solar" | "lunar"
    type: str              # "total" | "annular" | "hybrid" | "partial" | "penumbral" | "unknown"
    max_ts: str            # ISO 8601 UTC
    jd_max: float

class RangeResponse(BaseModel):
    count: int
    items: List[EclipseItem]

# ---------- Endpoints ----------
@router.post(
    "/solar/range",
    response_model=RangeResponse,
    dependencies=[Depends(plan_limiter("PRO"))],
)
async def solar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = getattr(swe, "FLG_SWIEPH", 2)

        while True:
            retflag, tret = _call_sol_glob(jd, ifl)
            if not tret:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            if jd_max <= jd:
                # olası yerinde sayma için güvenli sıçrama
                jd = jd + 25.0
                continue

            items.append({
                "kind": "solar",
                "type": _sol_type_name(int(retflag)),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            })
            if len(items) >= req.max_events:
                break
            # sonraki olaya atla (yerinde saymayı önlemek için max ile)
            jd = max(jd_max + 1.0, jd + 25.0)

        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solar eclipse search failed: {e}")

@router.post(
    "/lunar/range",
    response_model=RangeResponse,
    dependencies=[Depends(plan_limiter("PRO"))],
)
async def lunar_range(req: RangeRequest) -> Dict[str, Any]:
    try:
        jd = _to_jd(datetime(req.start_year, req.start_month, req.start_day, tzinfo=timezone.utc))
        jd_end = _to_jd(datetime(req.end_year, req.end_month, req.end_day, tzinfo=timezone.utc))
        items: List[Dict[str, Any]] = []
        ifl = getattr(swe, "FLG_SWIEPH", 2)

        while True:
            retflag, tret = _call_lun_glob(jd, ifl)
            if not tret:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            if jd_max <= jd:
                jd = jd + 25.0
                continue

            items.append({
                "kind": "lunar",
                "type": _lun_type_name(int(retflag)),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            })
            if len(items) >= req.max_events:
                break
            jd = max(jd_max + 1.0, jd + 25.0)

        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")
