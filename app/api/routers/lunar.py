# app/api/routers/lunar.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

# Rate limit (FREE plan)
from app.utils.rate_limit import plan_limiter

# Swiss Ephemeris
try:
    import swisseph as swe
except Exception:  # bazı ortamlar pyswisseph olarak expose eder
    import pyswisseph as swe  # type: ignore

# ---- Ay fazı hesaplayıcısı: önce lunar_phases.py, yoksa electional.lunar_phase
try:
    from app.calculators.lunar_phases import lunar_phase as _lunar_phase
except Exception:
    from app.calculators.electional import lunar_phase as _lunar_phase  # fallback

router = APIRouter(tags=["lunar"])  # prefix main.py'de verilecek

def _to_jd(dt_utc: datetime) -> float:
    """UTC datetime -> Julian Day (UT)"""
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

# ---------- MODELLER ----------
class PhaseRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0

class PhaseResponse(BaseModel):
    ts: str
    elongation: float
    waxing: bool
    phase: str

@router.post(
    "/phase",
    response_model=PhaseResponse,
    dependencies=[Depends(plan_limiter("FREE"))],
)
async def phase(req: PhaseRequest) -> Dict[str, Any]:
    """Tek zaman için Ay fazı bilgisi."""
    try:
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        dt = base + timedelta(hours=req.hour, minutes=req.minute)
        ph = _lunar_phase(_to_jd(dt))
        return {"ts": dt.isoformat(), **ph}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class CalendarRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    days: int = Field(30, ge=1, le=62)
    step_minutes: int = Field(60, ge=15, le=720)

class CalendarItem(BaseModel):
    ts: str
    phase: str
    elongation: float
    waxing: bool

class CalendarResponse(BaseModel):
    count: int
    items: List[CalendarItem]

@router.post(
    "/calendar",
    response_model=CalendarResponse,
    dependencies=[Depends(plan_limiter("FREE"))],
)
async def calendar(req: CalendarRequest) -> Dict[str, Any]:
    """Belirli bir aralıkta periyodik zamanlarda Ay fazı listesi."""
    try:
        start = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc) + \
                timedelta(hours=req.hour, minutes=req.minute)
        end = start + timedelta(days=req.days)
        step = timedelta(minutes=int(req.step_minutes))
        items: List[Dict[str, Any]] = []
        cur = start
        while cur <= end:
            ph = _lunar_phase(_to_jd(cur))
            items.append({"ts": cur.isoformat(), **ph})
            cur += step
        return {"count": len(items), "items": items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class ManifestationRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    window_days: int = Field(3, ge=1, le=10, description="Merkezde Yeni/Dolunay ± gün sayısı")

class ManifestationResponse(BaseModel):
    center_ts: str
    kind: str
    window: List[str]

@router.post(
    "/manifestation",
    response_model=ManifestationResponse,
    dependencies=[Depends(plan_limiter("FREE"))],
)
async def manifestation(req: ManifestationRequest) -> Dict[str, Any]:
    """Verilen tarihe en yakın Yeni Ay/Dolunay'ı bulup +/- window_days aralığını döndürür (basit tarama yaklaşımı)."""
    try:
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc) + \
               timedelta(hours=req.hour, minutes=req.minute)
        best_dt = None; best_kind = None; best_err = 1e9
        for d in range(-15, 16):
            dt = base + timedelta(days=d)
            ph = _lunar_phase(_to_jd(dt))
            if ph["phase"] in ("New Moon", "Full Moon"):
                target = 0 if ph["phase"] == "New Moon" else 180
                err = abs(ph["elongation"] - target)
                if err < best_err:
                    best_err = err; best_dt = dt; best_kind = ph["phase"]
        if best_dt is None:
            best_dt, best_kind = base, "Unknown"
        window = [(best_dt + timedelta(days=off)).isoformat()
                  for off in range(-req.window_days, req.window_days + 1)]
        return {"center_ts": best_dt.isoformat(), "kind": best_kind, "window": window}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
