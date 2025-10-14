# app/api/routers/eclipses.py
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

# --- Swiss Ephemeris ---
try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # bazı ortamlarda bu isimle gelir

swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))
IFL = swe.FLG_SWIEPH  # hız gerekmiyor

# ===================== Pydantic I/O Modelleri =====================

class DateRangeIn(BaseModel):
    start_year: int = Field(..., ge=1, le=9999)
    start_month: int = Field(..., ge=1, le=12)
    start_day: int = Field(..., ge=1, le=31)
    end_year: int = Field(..., ge=1, le=9999)
    end_month: int = Field(..., ge=1, le=12)
    end_day: int = Field(..., ge=1, le=31)
    max_events: int = Field(10, ge=1, le=50)
    debug: bool = False

    @model_validator(mode="after")
    def _check_range(self):
        try:
            jd_start = swe.julday(self.start_year, self.start_month, self.start_day, 0.0, swe.GREG_CAL)
            jd_end = swe.julday(self.end_year, self.end_month, self.end_day, 0.0, swe.GREG_CAL)
        except Exception as e:
            raise ValueError(f"Invalid date: {e}")
        if jd_end < jd_start:
            raise ValueError("end date must be >= start date")
        return self


class EclipseOut(BaseModel):
    kind: Literal["solar", "lunar"]
    type: Literal["partial", "total", "annular", "annular-total", "penumbral"]
    max_ts: str
    jd_max: float
    # debug alanları (isteğe bağlı)
    retflag: Optional[int] = None
    api: Optional[str] = None


class RangeOut(BaseModel):
    count: int
    items: list[EclipseOut]

# ===================== Yardımcılar =====================

def _ts_from_jd(jd_ut: float) -> str:
    y, m, d, f = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(f * 24)
    mm = int((f * 24 - hh) * 60)
    ss = int(round((((f * 24) - hh) * 60 - mm) * 60))
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc).isoformat()

def _safe_sol_where_is_central(jd_max: float) -> tuple[bool, bool]:
    """(has_any_central_flag, is_noncentral). Hata olursa (False, False)."""
    try:
        geopos = [0.0, 0.0, 0.0]
        attr = [0.0] * 20
        wflag = int(swe.sol_eclipse_where(jd_max, IFL, geopos, attr))
        has_central = bool(wflag & (getattr(swe, "SE_ECL_CENTRAL", 32) | getattr(swe, "SE_ECL_NONCENTRAL", 64)))
        is_noncentral = bool(wflag & getattr(swe, "SE_ECL_NONCENTRAL", 64))
        return has_central, is_noncentral
    except Exception:
        return (False, False)

def _classify_solar(jd_max: float, retflag: int) -> str:
    """
    Küresel tip:
      - Central path yoksa → partial
      - Noncentral ise → partial
      - Aksi halde retflag'e göre: total / annular-total / annular / partial
    """
    has_central, is_noncentral = _safe_sol_where_is_central(jd_max)
    if has_central and is_noncentral:
        return "partial"
    if not has_central:
        return "partial"
    if retflag & getattr(swe, "SE_ECL_TOTAL", 1):
        return "total"
    if retflag & getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16):
        return "annular-total"
    if retflag & getattr(swe, "SE_ECL_ANNULAR", 2):
        return "annular"
    return "partial"

def _classify_lunar(jd_max: float, retflag: int) -> str:
    """
    Ay tutulması tipleri büyüklüklerle kesin:
      umbral >= 1.0 → total
      0 < umbral < 1.0 → partial
      umbral == 0 ve penumbral > 0 → penumbral
    """
    try:
        geopos = [0.0, 0.0, 0.0]
        attr = [0.0] * 20
        _ = swe.lun_eclipse_how(jd_max, IFL, geopos, attr)
        umbral = float(attr[0])
        pen = float(attr[1])
        if umbral >= 0.999999:
            return "total"
        if umbral > 0.0:
            return "partial"
        if pen > 0.0:
            return "penumbral"
    except Exception:
        # how() başarısızsa retflag en iyi tahmindir
        if retflag & getattr(swe, "SE_ECL_TOTAL", 1):
            return "total"
        if retflag & getattr(swe, "SE_ECL_PARTIAL", 4):
            return "partial"
        return "penumbral"
    return "penumbral"

# ===================== Arama Motorları =====================

def _search_solar(jd_start: float, jd_end: float, max_events: int, debug: bool) -> list[EclipseOut]:
    out: list[EclipseOut] = []
    jd = jd_start
    ifltype = (
        getattr(swe, "SE_ECL_TOTAL", 1)
        | getattr(swe, "SE_ECL_ANNULAR", 2)
        | getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16)
        | getattr(swe, "SE_ECL_PARTIAL", 4)
        | getattr(swe, "SE_ECL_NONCENTRAL", 64)
    )
    backward = 0
    safety = 0
    while jd <= jd_end and len(out) < max_events and safety < 300:
        safety += 1
        try:
            tret, rflag = swe.sol_eclipse_when_glob(jd, ifltype, IFL, backward)
            jd_max = float(tret[0])
        except Exception:
            jd += 1.0
            continue

        if jd_max <= 0 or jd_max < jd or jd_max > jd_end:
            jd += 1.0
            continue

        try:
            typ = _classify_solar(jd_max, int(rflag))
        except Exception:
            typ = "partial"

        out.append(EclipseOut(
            kind="solar",
            type=typ,
            max_ts=_ts_from_jd(jd_max),
            jd_max=jd_max,
            retflag=int(rflag) if debug else None,
            api="sol_glob" if debug else None,
        ))
        jd = jd_max + 0.1  # bir sonraki olaya atla

    return out


def _search_lunar(jd_start: float, jd_end: float, max_events: int, debug: bool) -> list[EclipseOut]:
    out: list[EclipseOut] = []
    jd = jd_start
    ifltype = (
        getattr(swe, "SE_ECL_TOTAL", 1)
        | getattr(swe, "SE_ECL_PARTIAL", 4)
        | getattr(swe, "SE_ECL_PENUMBRAL", 8)
    )
    backward = 0
    safety = 0
    while jd <= jd_end and len(out) < max_events and safety < 300:
        safety += 1
        try:
            tret, rflag = swe.lun_eclipse_when(jd, ifltype, IFL, backward)
            jd_max = float(tret[0])
        except Exception:
            jd += 1.0
            continue

        if jd_max <= 0 or jd_max < jd or jd_max > jd_end:
            jd += 1.0
            continue

        try:
            typ = _classify_lunar(jd_max, int(rflag))
        except Exception:
            typ = "penumbral"

        out.append(EclipseOut(
            kind="lunar",
            type=typ,
            max_ts=_ts_from_jd(jd_max),
            jd_max=jd_max,
            retflag=int(rflag) if debug else None,
            api="lun_when" if debug else None,
        ))
        jd = jd_max + 0.1

    return out

# ===================== Router =====================

# DİKKAT: prefix YOK! (main.py zaten prefix="/eclipses" ile include ediyor)
router = APIRouter(tags=["eclipses"])

@router.post("/solar/range", response_model=RangeOut)
def solar_range(inp: DateRangeIn) -> RangeOut:
    jd_start = swe.julday(inp.start_year, inp.start_month, inp.start_day, 0.0, swe.GREG_CAL)
    jd_end = swe.julday(inp.end_year, inp.end_month, inp.end_day, 0.0, swe.GREG_CAL)
    items = _search_solar(jd_start, jd_end, inp.max_events, inp.debug)
    return RangeOut(count=len(items), items=items)

@router.post("/lunar/range", response_model=RangeOut)
def lunar_range(inp: DateRangeIn) -> RangeOut:
    jd_start = swe.julday(inp.start_year, inp.start_month, inp.start_day, 0.0, swe.GREG_CAL)
    jd_end = swe.julday(inp.end_year, inp.end_month, inp.end_day, 0.0, swe.GREG_CAL)
    items = _search_lunar(jd_start, jd_end, inp.max_events, inp.debug)
    return RangeOut(count=len(items), items=items)
