# app/api/routers/eclipses.py
from __future__ import annotations

from typing import List, Tuple, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

try:
    import swisseph as swe  # pyswisseph
except Exception:
    import pyswisseph as swe

router = APIRouter()

# ---------- Schemas ----------

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
    kind: str                 # "solar" | "lunar"
    type: str                 # solar: total/annular/partial ; lunar: total/partial/penumbral
    max_ts: str               # ISO UTC
    jd_max: float
    retflag: Optional[int] = None  # debug için
    api: Optional[str] = None      # debug için


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
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}+00:00"


# pyswisseph sürümleri dönüş sırasını değiştirebiliyor
def _normalize_when_ret(ret: Tuple) -> Tuple[int, List[float]]:
    a, b = ret[0], ret[1]
    if isinstance(a, int):
        return a, list(b)     # (retflag, tret[])
    else:
        return int(b), list(a)  # (tret[], retflag)


def _solar_type_from_flag(retflag: int) -> str:
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", 2)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 4)  # ← DOĞRU değer
    ECL_NONCENTRAL = getattr(swe, "SE_ECL_NONCENTRAL", 64)
    ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16)

    # Non-central olayları kullanıcıya partial olarak raporla
    if retflag & ECL_NONCENTRAL:
        return "partial"
    if retflag & ECL_TOTAL:
        return "total"
    if retflag & (ECL_ANNULAR | ECL_ANNULAR_TOTAL):
        return "annular"
    if retflag & ECL_PARTIAL:
        return "partial"
    return "partial"


def _lunar_type_from_flag(retflag: int) -> str:
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
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", 2)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 4)        # ← DOĞRU değer
    ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", 16)
    ecl_all = ECL_TOTAL | ECL_ANNULAR | ECL_ANNULAR_TOTAL | ECL_PARTIAL

    last_exc = None
    for args in [
        (jd_start, iflag, ecl_all, 0),
        (jd_start, iflag, ecl_all),
        (jd_start, iflag),
        (jd_start,)
    ]:
        try:
            ret = swe.sol_eclipse_when_glob(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e
    raise RuntimeError(f"sol_eclipse_when_glob failed: {last_exc}")


def _call_lun_when_glob(jd_start: float, iflag: int) -> Tuple[int, List[float]]:
    ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", 1)
    ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", 2)
    ECL_PENUMBRAL = getattr(swe, "SE_ECL_PENUMBRAL", 4)
    ecl_all = ECL_TOTAL | ECL_PARTIAL | ECL_PENUMBRAL

    last_exc = None
    for args in [(jd_start, iflag, ecl_all, 0), (jd_start, iflag, ecl_all), (jd_start, iflag)]:
        try:
            fn = getattr(swe, "lun_eclipse_when_glob")
            ret = fn(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e
    for args in [(jd_start, iflag, ecl_all, 0), (jd_start, iflag, ecl_all), (jd_start, iflag), (jd_start,)]:
        try:
            fn = getattr(swe, "lun_eclipse_when")
            ret = fn(*args)
            return _normalize_when_ret(ret)
        except Exception as e:
            last_exc = e
    raise RuntimeError(f"lun_eclipse_when(_glob) failed: {last_exc}")


# ---------- Routes ----------
# NOT: burada '/eclipses' yok; main.py prefix ekliyor.

@router.post("/solar/range", response_model=EclipseRangeResp)
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
            jd += 10
            continue

        # >>> aralık filtresi: aralığın dışındaysa ekleme ve bitir
        if jd_max > jd_end:
            break

        etype = _solar_type_from_flag(retflag)
        items.append(
            EclipseItem(
                kind="solar",
                type=etype,
                max_ts=_revjul_ts(jd_max),
                jd_max=jd_max,
                retflag=retflag if req.debug else None,
                api="sol_glob",
            )
        )
        jd = jd_max + 1.0

    return EclipseRangeResp(count=len(items), items=items)


@router.post("/lunar/range", response_model=EclipseRangeResp)
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
            retflag, tret = _call_lun_when_glob(jd, iflag)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lunar eclipse search failed: {e}")

        jd_max = float(tret[0])
        if jd_max <= 0:
            jd += 10
            continue

        # >>> aralık filtresi
        if jd_max > jd_end:
            break

        ltype = _lunar_type_from_flag(retflag)
        items.append(
            EclipseItem(
                kind="lunar",
                type=ltype,
                max_ts=_revjul_ts(jd_max),
                jd_max=jd_max,
                retflag=retflag if req.debug else None,
                api="lun_when",
            )
        )
        jd = jd_max + 1.0

    return EclipseRangeResp(count=len(items), items=items)
