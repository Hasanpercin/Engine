from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field, conint
import swisseph as swe

router = APIRouter(prefix="/eclipses", tags=["eclipses"])

# --------- Models ---------
class RangeRequest(BaseModel):
    start_year: int
    start_month: conint(ge=1, le=12)
    start_day: conint(ge=1, le=31)
    end_year: int
    end_month: conint(ge=1, le=12)
    end_day: conint(ge=1, le=31)
    max_events: conint(gt=0, le=50) = Field(default=10, description="Upper bound to avoid runaway loops")
    debug: bool = False


# --------- Helpers ---------
def _jd_utc(y: int, m: int, d: int) -> float:
    # SwissEph julday default: UT
    return swe.julday(y, m, d)

def _jd_to_iso(jd: float) -> str:
    y, m, d, ut = swe.revjul(jd)  # ut in fractional day
    hh = int(ut * 24)
    mm = int((ut * 24 - hh) * 60)
    ss = int(round((((ut * 24 - hh) * 60) - mm) * 60))
    # normalize seconds (e.g., 60 -> carry to minute)
    if ss == 60:
        ss = 0
        mm += 1
    if mm == 60:
        mm = 0
        hh += 1
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}Z"

def _rf_names(retflag: int) -> list[str]:
    names = []
    bits = [
        ("SE_ECL_TOTAL", swe.SE_ECL_TOTAL),
        ("SE_ECL_ANNULAR", swe.SE_ECL_ANNULAR),
        ("SE_ECL_PARTIAL", swe.SE_ECL_PARTIAL),
        ("SE_ECL_ANNULAR_TOTAL", getattr(swe, "SE_ECL_ANNULAR_TOTAL", 32)),
        ("SE_ECL_PENUMBRAL", getattr(swe, "SE_ECL_PENUMBRAL", 0)),
        ("SE_ECL_CENTRAL", getattr(swe, "SE_ECL_CENTRAL", 1)),
        ("SE_ECL_NONCENTRAL", getattr(swe, "SE_ECL_NONCENTRAL", 2)),
    ]
    for name, bit in bits:
        if bit and (retflag & bit):
            names.append(name)
    return names

def _classify_solar(retflag: int) -> dict:
    # Type
    if retflag & getattr(swe, "SE_ECL_ANNULAR_TOTAL", 32):
        etype = "hybrid"           # annular-total
    elif retflag & swe.SE_ECL_TOTAL:
        etype = "total"
    elif retflag & swe.SE_ECL_ANNULAR:
        etype = "annular"
    elif retflag & swe.SE_ECL_PARTIAL:
        etype = "partial"
    else:
        etype = "unknown"
    # Centrality (NONCENTRAL set ise central=False)
    noncentral = bool(retflag & getattr(swe, "SE_ECL_NONCENTRAL", 2))
    central = not noncentral
    return {"type": etype, "central": central}

def _classify_lunar(retflag: int) -> dict:
    if retflag & swe.SE_ECL_TOTAL:
        etype = "total"
    elif retflag & swe.SE_ECL_PARTIAL:
        etype = "partial"
    elif retflag & getattr(swe, "SE_ECL_PENUMBRAL", 0):
        etype = "penumbral"
    else:
        etype = "unknown"
    return {"type": etype}

def _validate_period(start_jd: float, end_jd: float):
    if end_jd < start_jd:
        raise ValueError("end date must be >= start date")


# --------- Routes ---------
@router.post("/solar/range")
def solar_range(req: RangeRequest):
    start_jd = _jd_utc(req.start_year, req.start_month, req.start_day)
    end_jd = _jd_utc(req.end_year, req.end_month, req.end_day)
    _validate_period(start_jd, end_jd)

    items = []
    jd = start_jd
    # ifltype=0 → any type; backward=False
    while jd <= end_jd and len(items) < req.max_events:
        retflag, tret = swe.sol_eclipse_when_glob(jd, 0, False)
        max_jd = tret[0]
        if max_jd <= 0:
            break
        if max_jd > end_jd:
            break

        classification = _classify_solar(retflag)
        item = {
            "max_time_utc": _jd_to_iso(max_jd),
            "retflag": retflag,
            "classification": classification,
        }
        if req.debug:
            item["retflag_names"] = _rf_names(retflag)
            item["api"] = "sol_eclipse_when_glob"

        items.append(item)
        # ileri al: aynı olayı tekrar yakalamamak için 1 gün marj
        jd = max_jd + 1.0

    return {"count": len(items), "items": items}


@router.post("/lunar/range")
def lunar_range(req: RangeRequest):
    start_jd = _jd_utc(req.start_year, req.start_month, req.start_day)
    end_jd = _jd_utc(req.end_year, req.end_month, req.end_day)
    _validate_period(start_jd, end_jd)

    items = []
    jd = start_jd
    # ifltype=0 → any lunar eclipse
    while jd <= end_jd and len(items) < req.max_events:
        retflag, tret = swe.lun_eclipse_when(jd, 0, False)
        max_jd = tret[0]
        if max_jd <= 0:
            break
        if max_jd > end_jd:
            break

        classification = _classify_lunar(retflag)
        item = {
            "max_time_utc": _jd_to_iso(max_jd),
            "retflag": retflag,
            "classification": classification,
        }
        if req.debug:
            item["retflag_names"] = _rf_names(retflag)
            item["api"] = "lun_eclipse_when"

        items.append(item)
        jd = max_jd + 1.0

    return {"count": len(items), "items": items}
