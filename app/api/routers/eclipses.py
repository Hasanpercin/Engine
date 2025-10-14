# app/api/routers/eclipses.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

import os

# --- Swiss Ephemeris yüklemesi ---
try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # bazı ortamlarda bu isimle geliyor

# Ephemeris path
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

IFL = swe.FLG_SWIEPH  # yeterli; hız gerekmiyor

# --- Pydantic modelleri ---

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
    def _check_order(self):
        try:
            _ = swe.julday(self.start_year, self.start_month, self.start_day, 0.0, swe.GREG_CAL)
            _ = swe.julday(self.end_year, self.end_month, self.end_day, 0.0, swe.GREG_CAL)
        except Exception as e:
            raise ValueError(f"Invalid date: {e}")
        jd_start = swe.julday(self.start_year, self.start_month, self.start_day, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(self.end_year, self.end_month, self.end_day, 0.0, swe.GREG_CAL)
        if jd_end < jd_start:
            raise ValueError("end date must be >= start date")
        return self


class EclipseOut(BaseModel):
    kind: Literal["solar", "lunar"]
    type: Literal["partial", "total", "annular", "annular-total", "penumbral"]
    max_ts: str
    jd_max: float
    # Opsiyonel debug alanları
    retflag: Optional[int] = None
    api: Optional[str] = None


class RangeOut(BaseModel):
    count: int
    items: list[EclipseOut]


# --- Yardımcılar ---

def _ts(jd_ut: float) -> str:
    y, m, d, f = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(f * 24)
    mm = int((f * 24 - hh) * 60)
    ss = int(round((((f * 24) - hh) * 60 - mm) * 60))
    dt = datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)
    return dt.isoformat()

def _classify_solar(jd_max: float, retflag: int) -> str:
    """
    Swiss Ephemeris bazı durumlarda global aramada (when_glob) noncentral olaylar için
    annular/annular-total bitlerini set edebiliyor. Küresel görünürlük için:
    - Eğer central path yoksa → partial
    - Noncentral ise → partial
    - Aksi halde retflag’e göre total / annular / annular-total
    """
    try:
        # where() → central path bilgisi. partial-only olaylarda CENTRAL/NONCENTRAL set olmaz.
        geopos = [0.0, 0.0, 0.0]
        attr = [0.0] * 20
        wflag = swe.sol_eclipse_where(jd_max, IFL, geopos, attr)
        has_central = bool(wflag & (swe.SE_ECL_CENTRAL | swe.SE_ECL_NONCENTRAL))
        if not has_central:
            return "partial"
        if wflag & swe.SE_ECL_NONCENTRAL:
            # Noncentral: Dünya üzerinde hiçbir yerde merkez çizgi yok → yalnızca partial gözlenir.
            return "partial"
    except Exception:
        # where() başarısızsa retflag'e düşeriz
        pass

    if retflag & getattr(swe, "SE_ECL_TOTAL", 1):
        return "total"
    if retflag & getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16):
        return "annular-total"
    if retflag & getattr(swe, "SE_ECL_ANNULAR", 2):
        return "annular"
    # SwissEph build'lerine göre partial biti 4
    return "partial"

def _classify_lunar(jd_max: float, retflag: int) -> str:
    """
    Ay tutulmasında küresel tip, umbral/penumbral büyüklüklerle kesin belirlenebilir:
      - umbral >= 1.0 → total
      - 0 < umbral < 1.0 → partial
      - umbral == 0 ve penumbral > 0 → penumbral
    """
    try:
        # jSwisseph dokümanında geopos istenir ama Ay tutulması için konum kritik değildir.
        geopos = [0.0, 0.0, 0.0]
        attr = [0.0] * 20
        _ = swe.lun_eclipse_how(jd_max, IFL, geopos, attr)
        umbral = float(attr[0])
        pen = float(attr[1])
        if umbral >= 0.999999:  # sayısal güvenlik
            return "total"
        if umbral > 0.0:
            return "partial"
        if pen > 0.0:
            return "penumbral"
    except Exception:
        # how() olmazsa retflag'e göre en iyi tahmin
        if retflag & getattr(swe, "SE_ECL_TOTAL", 1):
            return "total"
        if retflag & getattr(swe, "SE_ECL_PARTIAL", 4):
            return "partial"
        return "penumbral"
    # Güvenlik
    return "penumbral"

def _search_solar(jd_start: float, jd_end: float, max_events: int, debug: bool) -> list[EclipseOut]:
    out: list[EclipseOut] = []
    jd = jd_start
    # Türkçe: herhangi bir tip + noncentral’ı da ara
    ifltype = (
        swe.SE_ECL_TOTAL
        | swe.SE_ECL_ANNULAR
        | swe.SE_ECL_ANNULAR_TOTAL
        | swe.SE_ECL_PARTIAL
        | swe.SE_ECL_NONCENTRAL
    )
    backward = 0
    safety = 0
    while jd <= jd_end and len(out) < max_events and safety < 200:
        safety += 1
        try:
            tret, rflag = swe.sol_eclipse_when_glob(jd, ifltype, IFL, backward)
            jd_max = float(tret[0])
            if jd_max == 0 or jd_max < jd or jd_max > jd_end:
                # bir sonraki gün(e) atla
                jd += 1.0
                continue
            typ = _classify_solar(jd_max, int(rflag))
            out.append(EclipseOut(
                kind="solar",
                type=typ,
                max_ts=_ts(jd_max),
                jd_max=jd_max,
                retflag=int(rflag) if debug else None,
                api="sol_glob" if debug else None,
            ))
            # sonraki arama için küçük bir ilerleme: maksimum anın biraz ilerisinden devam
            jd = jd_max + 0.1
        except Exception as e:
            # Bir şey ters giderse bir gün atlayalım
            if debug and len(out) < max_events:
                # en azından denemeye devam edelim
                pass
            jd += 1.0
    return out

def _search_lunar(jd_start: float, jd_end: float, max_events: int, debug: bool) -> list[EclipseOut]:
    out: list[EclipseOut] = []
    jd = jd_start
    ifltype = swe.SE_ECL_TOTAL | swe.SE_ECL_PARTIAL | swe.SE_ECL_PENUMBRAL
    backward = 0
    safety = 0
    while jd <= jd_end and len(out) < max_events and safety < 200:
        safety += 1
        try:
            tret, rflag = swe.lun_eclipse_when(jd, ifltype, IFL, backward)
            jd_max = float(tret[0])
            if jd_max == 0 or jd_max < jd or jd_max > jd_end:
                jd += 1.0
                continue
            typ = _classify_lunar(jd_max, int(rflag))
            out.append(EclipseOut(
                kind="lunar",
                type=typ,
                max_ts=_ts(jd_max),
                jd_max=jd_max,
                retflag=int(rflag) if debug else None,
                api="lun_when" if debug else None,
            ))
            jd = jd_max + 0.1
        except Exception:
            jd += 1.0
    return out

# --- Router ---

router = APIRouter()

@router.post("/solar/range", response_model=RangeOut)
def solar_range(inp: DateRangeIn) -> RangeOut:
    try:
        jd_start = swe.julday(inp.start_year, inp.start_month, inp.start_day, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(inp.end_year, inp.end_month, inp.end_day, 0.0, swe.GREG_CAL)
        items = _search_solar(jd_start, jd_end, inp.max_events, inp.debug)
        return RangeOut(count=len(items), items=items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solar eclipse search failed: {e}")

@router.post("/lunar/range", response_model=RangeOut)
def lunar_range(inp: DateRangeIn) -> RangeOut:
    try:
        jd_start = swe.julday(inp.start_year, inp.start_month, inp.start_day, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(inp.end_year, inp.end_month, inp.end_day, 0.0, swe.GREG_CAL)
        items = _search_lunar(jd_start, jd_end, inp.max_events, inp.debug)
        return RangeOut(count=len(items), items=items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")
