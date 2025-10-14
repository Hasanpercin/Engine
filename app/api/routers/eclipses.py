# app/api/routers/eclipses.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

try:
    import swisseph as swe  # pyswisseph
except Exception:
    import pyswisseph as swe  # bazı ortamlarda böyle adlandırılıyor

router = APIRouter()

# ---------- Pydantic Schemas ----------

class _RangeBase(BaseModel):
    start_year: int
    start_month: int
    start_day: int
    end_year: int
    end_month: int
    end_day: int
    max_events: int = Field(default=10, ge=1, le=50)
    debug: bool = False

    @validator("start_month", "end_month")
    def _m_ok(cls, v):
        if not (1 <= v <= 12):
            raise ValueError("Month must be 1..12")
        return v

    @validator("start_day", "end_day")
    def _d_ok(cls, v):
        if not (1 <= v <= 31):
            raise ValueError("Day must be 1..31")
        return v


class SolarRangeReq(_RangeBase):
    pass


class LunarRangeReq(_RangeBase):
    pass


class EclipseItem(BaseModel):
    kind: str  # "solar" | "lunar"
    type: str  # solar: total/annular/partial ; lunar: total/partial/penumbral
    max_ts: str
    jd_max: float
    # debug alanları (isteğe bağlı)
    retflag: Optional[int] = None
    api: Optional[str] = None


class EclipseRangeResp(BaseModel):
    count: int
    items: List[EclipseItem]


# ---------- Helpers ----------

def _jd(y: int, m: int, d: int, hour_ut: float = 0.0) -> float:
    return swe.julday(y, m, d, hour_ut, swe.GREG_CAL)


def _revjul_ts(jd_ut: float) -> str:
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(h)
    mm = int((h - hh) * 60 + 1e-9)
    ss = int(round((((h - hh) * 60) - mm) * 60))
    # ISO-like UTC
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}+00:00"


# Pyswisseph'in farklı sürümlerinde return sırası değişebiliyor:
# Bazısında (retflag, tret), bazısında (tret, retflag) dönebiliyor.
def _normalize_when_ret(ret: Tuple) -> Tuple[int, List[float]]:
    # 'tret' tipik olarak en az 10 elemanlı float listesi/dizisi oluyor.
    a, b = ret[0], ret[1]
    if isinstance(a, int):
        # (retflag, tret)
        return a, list(b)
    else:
        # (tret, retflag)
        return int(b), list(a)


def _solar_type_from_flag(retflag: int) -> str:
    # Swiss Ephemeris bayrakları:
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", 2)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 32)
    ECL_NONCENTRAL = getattr(swe, "SE_ECL_NONCENTRAL", 64)
    # ANNULAR_TOTAL (hibrit) bazı sürümlerde mevcut:
    ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16)

    # NONCENTRAL varsa siz “partial” demek istiyorsunuz:
    if retflag & ECL_NONCENTRAL:
        return "partial"

    if retflag & ECL_TOTAL:
        # Hibriti total gibi ele almak isterseniz:
        if retflag & ECL_ANNULAR_TOTAL:
            return "total"
        return "total"
    if retflag & ECL_ANNULAR or retflag & ECL_ANNULAR_TOTAL:
        return "annular"
    if retflag & ECL_PARTIAL:
        return "partial"
    # Fallback
    return "partial"


def _lunar_type_from_flag(retflag: int) -> str:
    # Lunar için tipik bitler:
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 2)
    ECL_PENUMBRAL = getattr(swe, "SE_ECL_PENUMBRAL", 4)

    if retflag & ECL_TOTAL:
        return "total"
    if retflag & ECL_PARTIAL:
        return "partial"
    if retflag & ECL_PENUMBRAL:
        return "penumbral"
    return "penumbral"


def _call_sol_when_glob(jd_start: float, iflag: int) -> Tuple[int, List[float]]:
    # ecltype: ALL types (total + annular + annular-total + partial)
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", 2)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 32)
    ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16)
    ecl_all = ECL_TOTAL | ECL_ANNULAR | ECL_ANNULAR_TOTAL | ECL_PARTIAL

    # Çeşitli wrapper’lar için emniyetli denemeler:
    candidates = [
        (jd_start, iflag, ecl_all, 0),   # backward=0
        (jd_start, iflag, ecl_all),      # eski imzalar
        (jd_start, iflag),
        (jd_start,)
    ]
    last_exc = None
    for args in candidates:
        try:
            ret = swe.sol_eclipse_when_glob(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e
            continue
    raise RuntimeError(f"sol_eclipse_when_glob failed: {last_exc}")


def _call_lun_when_glob(jd_start: float, iflag: int) -> Tuple[int, List[float]]:
    # ecltype: ALL types (total + partial + penumbral)
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 2)
    ECL_PENUMBRAL = getattr(swe, "SE_ECL_PENUMBRAL", 4)
    ecl_all = ECL_TOTAL | ECL_PARTIAL | ECL_PENUMBRAL

    # Bazı pyswisseph paketlerinde global fonksiyon adı 'lun_eclipse_when' ( *_glob olmadan)
    # Bu yüzden iki varyantı da güvenli biçimde deniyoruz.
    last_exc = None

    # 1) *_when_glob
    for args in [(jd_start, iflag, ecl_all, 0), (jd_start, iflag, ecl_all), (jd_start, iflag)]:
        try:
            fn = getattr(swe, "lun_eclipse_when_glob")
            ret = fn(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e

    # 2) *_when (global davranan wrapper)
    for args in [(jd_start, iflag, ecl_all, 0), (jd_start, iflag, ecl_all), (jd_start, iflag), (jd_start,)]:
        try:
            fn = getattr(swe, "lun_eclipse_when")
            ret = fn(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e

    raise RuntimeError(f"lun_eclipse_when(_glob) failed: {last_exc}")


# ---------- Routes ----------

@router.post("/eclipses/solar/range", response_model=EclipseRangeResp)
def solar_range(req: SolarRangeReq) -> EclipseRangeResp:
    jd = _jd(req.start_year, req.start_month, req.start_day)
    jd_end = _jd(req.end_year, req.end_month, req.end_day)
    if jd_end <= jd:
        raise HTTPException(status_code=400, detail="Invalid date range")

    iflag = getattr(swe, "FLG_SWIEPH", getattr(swe, "SEFLG_SWIEPH", 2))

    items: List[EclipseItem] = []
    guard = 0
    while jd < jd_end and len(items) < req.max_events and guard < 200:
        guard += 1
        try:
            retflag, tret = _call_sol_when_glob(jd, iflag)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Solar eclipse search failed: {e}")

        jd_max = float(tret[0])
        if jd_max <= 0:
            # Güvenlik: bazen 0 dönebiliyor → aramayı biraz ileri al
            jd += 10
            continue

        etype = _solar_type_from_flag(retflag)
        item = EclipseItem(
            kind="solar",
            type=etype,
            max_ts=_revjul_ts(jd_max),
            jd_max=jd_max,
            retflag=retflag if req.debug else None,
            api="sol_glob",
        )
        items.append(item)

        # Bir sonrakini aramak için küçük bir sıçrama:
        jd = jd_max + 1.0

    return EclipseRangeResp(count=len(items), items=items)


@router.post("/eclipses/lunar/range", response_model=EclipseRangeResp)
def lunar_range(req: LunarRangeReq) -> EclipseRangeResp:
    jd = _jd(req.start_year, req.start_month, req.start_day)
    jd_end = _jd(req.end_year, req.end_month, req.end_day)
    if jd_end <= jd:
        raise HTTPException(status_code=400, detail="Invalid date range")

    iflag = getattr(swe, "FLG_SWIEPH", getattr(swe, "SEFLG_SWIEPH", 2))

    items: List[EclipseItem] = []
    guard = 0
    while jd < jd_end and len(items) < req.max_events and guard < 200:
        guard += 1
        try:
            # ÖNEMLİ: Global arama + tüm tipler (total/partial/penumbral)
            retflag, tret = _call_lun_when_glob(jd, iflag)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")

        jd_max = float(tret[0])
        if jd_max <= 0:
            jd += 10
            continue

        ltype = _lunar_type_from_flag(retflag)
        item = EclipseItem(
            kind="lunar",
            type=ltype,
            max_ts=_revjul_ts(jd_max),
            jd_max=jd_max,
            retflag=retflag if req.debug else None,
            api="lun_when_glob",  # veya 'lun_when' – hangisi başarılı olduysa mantıksal olarak aynı
        )
        items.append(item)

        jd = jd_max + 1.0

    return EclipseRangeResp(count=len(items), items=items)
