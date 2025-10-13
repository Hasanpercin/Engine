# app/api/routers/profections.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter

try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

router = APIRouter(tags=["profections"])

def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

# Ascendant
def _asc_lon(jd: float, lat: float, lon: float, hsys: str = "P") -> float:
    # Swiss Ephemeris expects geographic longitude (east positive)
    # In many APIs east-positive is default; if your input is west-positive, invert here.
    cusps, ascmc = swe.houses_ex(jd, swe.FLG_SWIEPH, lat, lon, hsys)
    return ascmc[0] % 360.0  # ASC

_SIGN_RULER = {
    0: "mars", 1: "venus", 2: "mercury", 3: "moon", 4: "sun", 5: "mercury",
    6: "venus", 7: "mars", 8: "jupiter", 9: "saturn", 10: "saturn", 11: "jupiter"
}

class Natal(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int
    tz_offset: float = 0.0
    lat: float; lon: float  # degrees (N/E positive)

class AnnualProfectionRequest(BaseModel):
    natal: Natal
    for_date_year: int = Field(..., description="Hangi yıl için (UTC)")

class AnnualProfectionResponse(BaseModel):
    ts_utc: str
    age: int
    profected_house_index: int
    profected_sign_index: int
    profected_ruler: str
    asc_sign_index: int
    asc_lon: float

@router.post("/annual", response_model=AnnualProfectionResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def annual(req: AnnualProfectionRequest) -> Dict[str, Any]:
    try:
        n = req.natal
        local = datetime(n.year, n.month, n.day, n.hour, n.minute,
                         tzinfo=timezone(timedelta(hours=n.tz_offset)))
        natal_utc = local.astimezone(timezone.utc)
        # age at Jan 1 (UTC) of target year ~ approximation
        age = req.for_date_year - natal_utc.year
        jd_natal = _to_jd(natal_utc)
        asc = _asc_lon(jd_natal, n.lat, n.lon)
        asc_sign = int(asc // 30)
        prof_house = age % 12
        prof_sign = (asc_sign + prof_house) % 12
        ruler = _SIGN_RULER[prof_sign]
        ts = datetime(req.for_date_year, 1, 1, tzinfo=timezone.utc)
        return {
            "ts_utc": ts.isoformat(),
            "age": age,
            "profected_house_index": prof_house,
            "profected_sign_index": prof_sign,
            "profected_ruler": ruler,
            "asc_sign_index": asc_sign,
            "asc_lon": asc
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
