# app/api/routers/returns.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter

try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

# --- Helpers ---
def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

def _planet_lon(jd: float, pid: int) -> float:
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[0] % 360.0

def _ang_diff_signed(a: float, b: float) -> float:
    """Return signed smallest difference a-b in (-180, 180]."""
    return ((a - b + 540.0) % 360.0) - 180.0

def _find_return_time(target_lon: float, pid: int, jd_guess: float, days_window: int = 400) -> float:
    """
    Find time near jd_guess where planet longitude equals target_lon (mod 360).
    Strategy: coarse scan in hours to bracket sign change, then bisection refine.
    """
    step_hours = 6.0
    jd = jd_guess - (days_window / 2)
    end = jd_guess + (days_window / 2)
    last_diff: Optional[float] = None
    last_jd: Optional[float] = None

    while jd <= end:
        lon = _planet_lon(jd, pid)
        diff = _ang_diff_signed(lon, target_lon)
        if last_diff is not None and diff == 0.0:
            return jd
        if last_diff is not None and (diff == 0 or (diff > 0 and last_diff < 0) or (diff < 0 and last_diff > 0)):
            # bracket [last_jd, jd]
            lo, hi = last_jd, jd
            # refine bisection to ~1 second precision
            for _ in range(40):
                mid = (lo + hi) / 2.0
                dmid = _ang_diff_signed(_planet_lon(mid, pid), target_lon)
                if dmid == 0:
                    return mid
                # choose side
                dlo = _ang_diff_signed(_planet_lon(lo, pid), target_lon)
                if (dlo <= 0 < dmid) or (dmid <= 0 < dlo):
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2.0
        last_diff = diff
        last_jd = jd
        jd += step_hours / 24.0

    raise ValueError("Return time not found within window — widen search or check inputs.")

# --- API ---
router = APIRouter(tags=["returns"])

class NatalInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz_offset: float = Field(0.0, description="Yerel saat UTC ofseti (saat)")

class SolarReturnRequest(BaseModel):
    natal: NatalInput
    year: int = Field(..., description="Hangi yılın Solar Return'ü (UTC yılı)")

class ReturnResponse(BaseModel):
    center_ts: str
    jd: float
    planet: str
    target_lon: float

def _natal_sun_lon(natal_utc: datetime) -> float:
    jd = _to_jd(natal_utc)
    xx, _ = swe.calc_ut(jd, swe.SUN, _SWE_FLAGS)
    return xx[0] % 360.0

def _natal_body_lon(natal_utc: datetime, pid: int) -> float:
    jd = _to_jd(natal_utc)
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[0] % 360.0

def _dt_from_natal(local: NatalInput) -> datetime:
    base_local = datetime(local.year, local.month, local.day, local.hour, local.minute,
                          tzinfo=timezone(timedelta(hours=local.tz_offset)))
    return base_local.astimezone(timezone.utc)

def _solar_guess_for_year(natal_utc: datetime, year: int) -> float:
    # Guess near user's birthday in given UTC year
    guess_dt = datetime(year, natal_utc.month, min(natal_utc.day, 28), natal_utc.hour, natal_utc.minute, tzinfo=timezone.utc)
    return _to_jd(guess_dt)

@router.post("/solar", response_model=ReturnResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def solar(req: SolarReturnRequest) -> Dict[str, Any]:
    try:
        natal_utc = _dt_from_natal(req.natal)
        target_lon = _natal_sun_lon(natal_utc)
        jd_guess = _solar_guess_for_year(natal_utc, req.year)
        jd_hit = _find_return_time(target_lon, swe.SUN, jd_guess, days_window=400)
        dt = swe.revjul(jd_hit, swe.GREG_CAL)
        y, m, d, h = dt
        hh = int(h); mm = int(round((h - hh) * 60))
        ts = datetime(y, m, d, 0, 0, tzinfo=timezone.utc) + timedelta(hours=hh, minutes=mm)
        return {"center_ts": ts.isoformat(), "jd": jd_hit, "planet": "sun", "target_lon": target_lon}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class GenericReturnRequest(BaseModel):
    natal: NatalInput
    year: int
    body: str = Field(..., pattern="^(moon|saturn|chiron)$")

_PID_MAP = {"moon": swe.MOON, "saturn": swe.SATURN}
# Chiron opsiyonel (ephemeris varsa)
if hasattr(swe, "CHIRON"):
    _PID_MAP["chiron"] = getattr(swe, "CHIRON")

@router.post("/body", response_model=ReturnResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def body_return(req: GenericReturnRequest) -> Dict[str, Any]:
    try:
        if req.body not in _PID_MAP:
            raise HTTPException(status_code=400, detail=f"Unsupported body '{req.body}'.")
        pid = _PID_MAP[req.body]
        natal_utc = _dt_from_natal(req.natal)
        target_lon = _natal_body_lon(natal_utc, pid)
        # Guess: same month/day UTC in target year
        jd_guess = _to_jd(datetime(req.year, natal_utc.month, min(natal_utc.day, 28),
                                   natal_utc.hour, natal_utc.minute, tzinfo=timezone.utc))
        jd_hit = _find_return_time(target_lon, pid, jd_guess, days_window=450)
        y, m, d, h = swe.revjul(jd_hit, swe.GREG_CAL)
        hh = int(h); mm = int(round((h - hh) * 60))
        ts = datetime(y, m, d, 0, 0, tzinfo=timezone.utc) + timedelta(hours=hh, minutes=mm)
        return {"center_ts": ts.isoformat(), "jd": jd_hit, "planet": req.body, "target_lon": target_lon}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
