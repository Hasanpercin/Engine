# app/api/routers/returns.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter

# Swiss Ephemeris (bazı ortamlarda pyswisseph adıyla gelir)
try:
    import swisseph as swe
except Exception:  # pragma: no cover
    import pyswisseph as swe  # type: ignore

router = APIRouter(tags=["returns"])

# ---- Yardımcılar ------------------------------------------------------------

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

def _to_jd(dt_utc: datetime) -> float:
    """UTC datetime -> Julian Day (UT)."""
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def _planet_lon(jd: float, pid: int) -> float:
    """Gezegen ekliptik boylamı [0,360)."""
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[0] % 360.0

def _ang_diff_signed(a: float, b: float) -> float:
    """En kısa işaretli fark a-b in (-180,180]."""
    return ((a - b + 540.0) % 360.0) - 180.0

def _revjul_iso(jd: float) -> str:
    """JD -> ISO8601 (UTC). minute=60/hh overflow gibi durumlar için base+timedelta kullanır."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(hours=hh, minutes=mm)).isoformat()

def _find_return_time(target_lon: float, pid: int, jd_guess: float, days_window: int = 400) -> float:
    """
    jd_guess civarında, gezegen boylamının target_lon olduğu anı bul.
    Strateji:
      1) 6 saatlik kaba tarama ile işaret değişimi/bracket yakala.
      2) Bisection ile ~saniye düzeyi hassasiyet.
    'days_window' toplam pencere (örn. 400 → ±200 gün).
    """
    step_hours = 6.0
    jd = jd_guess - (days_window / 2.0)
    end = jd_guess + (days_window / 2.0)

    last_diff: Optional[float] = None
    last_jd: Optional[float] = None

    while jd <= end:
        lon = _planet_lon(jd, pid)
        diff = _ang_diff_signed(lon, target_lon)

        if last_diff is not None:
            # tam isabet veya işaret değişimi (sıfır geçişi) yakalandı mı?
            if diff == 0.0:
                return jd
            if (diff > 0 and last_diff < 0) or (diff < 0 and last_diff > 0):
                # Bracket [last_jd, jd] aralığında çöz
                lo, hi = last_jd, jd
                for _ in range(40):  # ~ 2^40 rafine (fazlasıyla yeter)
                    mid = (lo + hi) / 2.0
                    dmid = _ang_diff_signed(_planet_lon(mid, pid), target_lon)
                    if dmid == 0.0:
                        return mid
                    dlo = _ang_diff_signed(_planet_lon(lo, pid), target_lon)
                    # işaret ayrımına göre aralığı daralt
                    if (dlo <= 0 < dmid) or (dmid <= 0 < dlo):
                        hi = mid
                    else:
                        lo = mid
                return (lo + hi) / 2.0

        last_diff = diff
        last_jd = jd
        jd += step_hours / 24.0

    raise ValueError("Return time not found within window; widen search or check inputs.")

def _dt_from_natal(local: "NatalInput") -> datetime:
    """Yerel doğum zamanı + tz_offset → UTC datetime."""
    base_local = datetime(
        local.year, local.month, local.day, local.hour, local.minute,
        tzinfo=timezone(timedelta(hours=local.tz_offset))
    )
    return base_local.astimezone(timezone.utc)

def _natal_body_lon(natal_utc: datetime, pid: int) -> float:
    """Doğumdaki gezegen boylamı."""
    jd = _to_jd(natal_utc)
    xx, _ = swe.calc_ut(jd, pid, _SWE_FLAGS)
    return xx[0] % 360.0

def _solar_guess_for_year(natal_utc: datetime, year: int) -> float:
    """
    Solar return için kaba tahmin: ilgili UTC yılında, doğum ay/gününe yakın bir zaman.
    (Ayı koru, gün 28'i geçmesin; zaman doğum saat/dakika.)
    """
    guess_dt = datetime(
        year, natal_utc.month, min(natal_utc.day, 28),
        natal_utc.hour, natal_utc.minute, tzinfo=timezone.utc
    )
    return _to_jd(guess_dt)

# Dönem yaklaşıkları (yıl cinsinden)
_APPROX_PERIOD_YEARS = {
    "moon": 0.0748,    # ~27.3 gün
    "saturn": 29.457,  # ~29.46 yıl
    "chiron": 50.0     # kaba yaklaşım
}

# ---- İstek/yanıt modelleri ---------------------------------------------------

class NatalInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz_offset: float = Field(0.0, description="Yerel saat UTC ofseti (saat cinsinden, örn. +3.0)")

class SolarReturnRequest(BaseModel):
    natal: NatalInput
    year: int = Field(..., description="Hangi UTC yılı için Solar Return")

class ReturnResponse(BaseModel):
    center_ts: str
    jd: float
    planet: str
    target_lon: float

class GenericReturnRequest(BaseModel):
    natal: NatalInput
    year: int
    body: str = Field(..., pattern="^(moon|saturn|chiron)$")
    # Opsiyonel: ± şu kadar yıl civarında ara (verilmezse gezegenin dönemine göre makul bir varsayılan kullanılır)
    search_years: float | None = Field(
        None,
        ge=0.5, le=60.0,
        description="Verilen yılın ± bu kadar yıl çevresinde dönüş ara (örn. 18)."
    )

# ---- Planet ID eşlemesi ------------------------------------------------------

_PID_MAP: Dict[str, int] = {"moon": swe.MOON, "saturn": swe.SATURN}
# Bazı build'larda Chiron olmayabilir
if hasattr(swe, "CHIRON"):
    _PID_MAP["chiron"] = getattr(swe, "CHIRON")

# ---- Endpoints ---------------------------------------------------------------

@router.post("/solar", response_model=ReturnResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def solar(req: SolarReturnRequest) -> Dict[str, Any]:
    """
    Solar Return: Güneş'in doğum boylamına tekrar geldiği an.
    """
    try:
        natal_utc = _dt_from_natal(req.natal)
        target_lon = _natal_body_lon(natal_utc, swe.SUN)
        jd_guess = _solar_guess_for_year(natal_utc, req.year)
        # Solar için ±200 gün pencere genelde yeterli
        jd_hit = _find_return_time(target_lon, swe.SUN, jd_guess, days_window=400)
        center_ts = _revjul_iso(jd_hit)
        return {"center_ts": center_ts, "jd": jd_hit, "planet": "sun", "target_lon": target_lon}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/body", response_model=ReturnResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def body_return(req: GenericReturnRequest) -> Dict[str, Any]:
    """
    Moon/Saturn/Chiron dönüşü: gezegenin doğum boylamına yeniden geldiği an.
    - year: aramayı merkezleyeceğimiz UTC yılı
    - search_years: verilirse ±search_years yıl civarında ara; verilmezse gezegen döneminin ~%60'ı kullanılır
    """
    try:
        if req.body not in _PID_MAP:
            raise HTTPException(status_code=400, detail=f"Unsupported body '{req.body}'.")

        pid = _PID_MAP[req.body]
        natal_utc = _dt_from_natal(req.natal)
        target_lon = _natal_body_lon(natal_utc, pid)

        # Varsayılan arama genişliği: gezegen dönemi * 0.6 (Saturn için ~±17-18 yıl)
        if req.search_years is not None:
            search_years = float(req.search_years)
        else:
            period = _APPROX_PERIOD_YEARS.get(req.body, 1.0)
            search_years = max(2.0, period * 0.6)

        # year civarı kaba tahmin
        jd_guess = _to_jd(datetime(
            req.year, natal_utc.month, min(natal_utc.day, 28),
            natal_utc.hour, natal_utc.minute, tzinfo=timezone.utc
        ))

        # Gün penceresi: ±search_years → total = 2*search_years
        days_window = int(2 * search_years * 365.25)

        jd_hit = _find_return_time(target_lon, pid, jd_guess, days_window=days_window)
        center_ts = _revjul_iso(jd_hit)
        return {"center_ts": center_ts, "jd": jd_hit, "planet": req.body, "target_lon": target_lon}

    except ValueError:
        # Daha açıklayıcı mesaj
        sy = req.search_years if req.search_years is not None else round(_APPROX_PERIOD_YEARS.get(req.body, 1.0) * 0.6, 2)
        raise HTTPException(
            status_code=404,
            detail=f"No {req.body} return found within ±{sy} years of {req.year}."
        )
