# app/api/routers/eclipses.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional

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

# Tür eşleştirme modu:
# - simple: "partial" öncelikli (pratik katalog uyumu için)
# - strict: "total" > "hybrid" > "annular" > "partial" (kitabi sıra)
ECL_CLASS_MODE = os.getenv("ECL_CLASS_MODE", "simple").strip().lower()

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

# Sıralama profilleri
_SOLAR_ORDER_SIMPLE  = [("partial", ECL_PARTIAL), ("total", ECL_TOTAL),
                        ("hybrid", ECL_ANNULAR_TOTAL), ("annular", ECL_ANNULAR)]
_SOLAR_ORDER_STRICT  = [("total", ECL_TOTAL), ("hybrid", ECL_ANNULAR_TOTAL),
                        ("annular", ECL_ANNULAR), ("partial", ECL_PARTIAL)]

_LUNAR_ORDER_SIMPLE  = [("partial", ECL_PARTIAL), ("total", ECL_TOTAL), ("penumbral", ECL_PENUMBRAL)]
_LUNAR_ORDER_STRICT  = [("total", ECL_TOTAL), ("partial", ECL_PARTIAL), ("penumbral", ECL_PENUMBRAL)]

def _pick_type(retflag: int, order: List[Tuple[str, int]]) -> str:
    try:
        for name, mask in order:
            if retflag & mask:
                return name
    except Exception:
        pass
    return "unknown"

def _sol_type_name(retflag: int) -> str:
    order = _SOLAR_ORDER_STRICT if ECL_CLASS_MODE == "strict" else _SOLAR_ORDER_SIMPLE
    return _pick_type(retflag, order)

def _lun_type_name(retflag: int) -> str:
    order = _LUNAR_ORDER_STRICT if ECL_CLASS_MODE == "strict" else _LUNAR_ORDER_SIMPLE
    return _pick_type(retflag, order)

def _normalize_ecl_result(out: Any) -> Tuple[int, List[float], Optional[List[float]]]:
    """
    pyswisseph uyumluluğu:
    - (retflag, tret, attr, serr)
    - (tret, retflag)
    - (retflag, tret)
    Edge: yalnız tret listesi/tuple'ı dönebilir (retflag yok) → retflag=0
    Döndürür: (retflag, tret_list, attr_list | None)
    """
    if isinstance(out, tuple):
        if len(out) == 4:
            retflag, tret, attr, _serr = out
            return int(retflag), list(tret), list(attr)
        if len(out) == 2:
            a, b = out
            if isinstance(a, (list, tuple)):
                # (tret, retflag)
                return int(b), list(a), None
            # (retflag, tret)
            return int(a), list(b), None
    if isinstance(out, (list, tuple)) and len(out) >= 1:
        return 0, list(out), None
    raise TypeError(
        f"Unexpected eclipse result shape: {type(out)} "
        f"len={len(out) if hasattr(out,'__len__') else 'n/a'}"
    )

def _call_sol_glob(jd: float, ifl: int) -> Tuple[int, List[float], Optional[List[float]], str]:
    # Farklı imza varyantlarını sırayla dene
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.sol_eclipse_when_glob(*args)  # type: ignore[misc]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "sol_glob"
        except Exception:
            continue
    # Olmadıysa boş dön
    return 0, [], None, "sol_glob"

def _call_lun_any(jd: float, ifl: int) -> Tuple[int, List[float], Optional[List[float]], str]:
    # 1) glob
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when_glob(*args)  # type: ignore[misc]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "lun_glob"
        except Exception:
            continue
    # 2) fallback: non-glob
    for args in ((jd, ifl, 0), (jd, ifl), (jd,)):
        try:
            out = swe.lun_eclipse_when(*args)  # type: ignore[misc]
            ret, tret, attr = _normalize_ecl_result(out)
            return ret, tret, attr, "lun_when"
        except Exception:
            continue
    return 0, [], None, "lun_none"

# ---------- Models ----------
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
    kind: str              # "solar" | "lunar"
    type: str              # "total" | "annular" | "hybrid" | "partial" | "penumbral" | "unknown"
    max_ts: str            # ISO 8601 UTC
    jd_max: float
    # debug opsiyonel alanlar:
    retflag: Optional[int] = None
    api: Optional[str] = None
    attrs: Optional[List[float]] = None

class RangeResponse(BaseModel):
    count: int
    items: List[EclipseItem]

# ---------- Endpoints ----------
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
                # olası yerinde sayma için güvenli sıçrama
                jd = jd + 25.0
                continue

            item: Dict[str, Any] = {
                "kind": "solar",
                "type": _sol_type_name(int(retflag)),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            }
            if req.debug:
                item.update({"retflag": int(retflag), "api": api, "attrs": attr})
            items.append(item)

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
            retflag, tret, attr, api = _call_lun_any(jd, ifl)
            if not tret:
                break
            jd_max = float(tret[0])
            if jd_max > jd_end:
                break
            if jd_max <= jd:
                jd = jd + 25.0
                continue

            item: Dict[str, Any] = {
                "kind": "lunar",
                "type": _lun_type_name(int(retflag)),
                "max_ts": _jd_to_iso(jd_max),
                "jd_max": jd_max,
            }
            if req.debug:
                item.update({"retflag": int(retflag), "api": api, "attrs": attr})
            items.append(item)

            if len(items) >= req.max_events:
                break
            jd = max(jd_max + 1.0, jd + 25.0)

        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")
