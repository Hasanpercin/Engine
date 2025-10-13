# app/api/routers/profections.py
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.rate_limit import plan_limiter

# Swiss Ephemeris
try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

# Ephemeris yolu; houses() tipik olarak dosya istemez ama calc çağrıları için iyi olur
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

router = APIRouter(tags=["profections"])

def _to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

# ---- ÖNEMLİ DÜZELTME: flags'li houses_ex yerine DİREKT houses() kullanıyoruz
def _asc_lon(jd: float, lat: float, lon: float, hsys: str = "P") -> float:
    # Girdi kontrolü (daha açıklayıcı 400 için)
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of range: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of range: {lon}")
    # Swiss: east-positive longitude; Türkiye için lon>0 doğru
    cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    return float(ascmc[0] % 360.0)  # ASC

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
    for_date_year: int = Field(..., description="Hangi UTC yılı için profeksiyon")
    house_system: str = Field("P", min_length=1, max_length=1,
                              description="Ev sistemi (tek harf): P=Placidus, K=Koch, O=Porphyry, W=Whole, vb.")

class AnnualProfectionResponse(BaseModel):
    ts_utc: str
    age: int
    profected_house_index: int
    profected_sign_index: int
    profected_ruler: str
    asc_sign_index: int
    asc_lon: float
    house_system: str

@router.post("/annual", response_model=AnnualProfectionResponse, dependencies=[Depends(plan_limiter("PRO"))])
async def annual(req: AnnualProfectionRequest) -> Dict[str, Any]:
    try:
        n = req.natal
        local = datetime(n.year, n.month, n.day, n.hour, n.minute,
                         tzinfo=timezone(timedelta(hours=n.tz_offset)))
        natal_utc = local.astimezone(timezone.utc)

        # Yaş ~ hedef yılın 1 Ocak UTC itibarıyla
        age = req.for_date_year - natal_utc.year

        jd_natal = _to_jd(natal_utc)
        asc = _asc_lon(jd_natal, float(n.lat), float(n.lon), req.house_system)
        asc_sign = int(asc // 30)

        prof_house = age % 12
        prof_sign = (asc_sign + prof_house) % 12
        ruler = _SIGN_RULER[prof_sign]

        ts = datetime(req.for_date_year, 1, 1, tzinfo=timezone.utc)
        return {
            "ts_utc": ts.isoformat(),
            "age": int(age),
            "profected_house_index": int(prof_house),
            "profected_sign_index": int(prof_sign),
            "profected_ruler": ruler,
            "asc_sign_index": int(asc_sign),
            "asc_lon": float(asc),
            "house_system": req.house_system,
        }
    except ValueError as e:
        # Giriş doğrulama veya houses hesap hataları
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Beklenmedik durumlar
        raise HTTPException(status_code=400, detail=f"Profections error: {e}")
