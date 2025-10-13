# app/api/routers/electional.py
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.calculators import electional as E
import swisseph as swe

# Rate-limit: plan bazlı dependency
from app.utils.rate_limit import plan_limiter

# Not: prefix burada YOK; main.py içinde include_router(..., prefix="/electional") var.
router = APIRouter(tags=["electional"])

# -----------------------------
# Request / Response Modelleri
# -----------------------------
class SearchRequest(BaseModel):
    """
    Seçimsel (electional) tarama isteği.
    Zaman UTC kabul edilir; normalize işlemi base+timedelta ile yapılır.
    """
    year: int
    month: int
    day: int
    hour: int
    minute: int

    # Varsayılanlar ve sınırlar (dokümantasyon için)
    duration_hours: int = Field(24, ge=1, le=168, description="Toplam tarama süresi (saat)")
    step_minutes: int = Field(15, ge=1, le=1440, description="Örnekleme adımı (dakika)")

    # Coğrafi parametreler ileride kullanılmak üzere imzada mevcut
    lat: float = 0.0
    lon: float = 0.0

    # Kurallar
    avoid_mercury_rx: bool = True
    avoid_moon_voc: bool = True


class SearchItem(BaseModel):
    jd: float
    ts: str
    score: float
    reasons: List[str]


class SearchResponse(BaseModel):
    start_ts: str
    end_ts: str
    jd_start: float
    jd_end: float
    step_minutes: int
    duration_hours: int
    count: int
    items: List[SearchItem]


# -----------------------------
# Yardımcılar
# -----------------------------
def _to_jd(dt_utc: datetime) -> float:
    """UTC datetime -> Julian Day"""
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)


def _jd_to_iso(jd: float) -> str:
    """Julian Day -> ISO8601 UTC"""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(hours=hh, minutes=mm)).isoformat()


# -----------------------------
# Route
# -----------------------------
@router.post(
    "/search",
    response_model=SearchResponse,
    dependencies=[Depends(plan_limiter("FREE"))],  # FREE plan için saatlik limit
)
async def search(req: SearchRequest) -> Dict[str, Any]:
    """
    Belirtilen UTC tarih/saatten başlayarak, duration_hours süresince
    step_minutes adımıyla örnekleyip seçimsel skorları döndürür.

    Notlar:
    - hour/minute değerleri base+timedelta ile normalize edilir (örn. minute=60 → +1 saat)
    - Swiss Ephemeris JD dönüşümleri calculators modülündedir.
    """
    try:
        # Tip ve pozitiflik kontrolleri
        step_minutes = int(req.step_minutes)
        duration_hours = int(req.duration_hours)
        if req.hour < 0 or req.minute < 0:
            raise ValueError("hour/minute must be >= 0")
        if step_minutes <= 0 or duration_hours <= 0:
            raise ValueError("step_minutes and duration_hours must be > 0")

        # Normalize: direkt datetime(y,m,d,hour,minute) kurmak yerine base+timedelta
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        start_dt = base + timedelta(hours=req.hour, minutes=req.minute)
        end_dt = start_dt + timedelta(hours=duration_hours)

        jd_start = _to_jd(start_dt)
        jd_end = _to_jd(end_dt)

        results = E.search_electional_windows(
            jd_start=jd_start,
            jd_end=jd_end,
            lat=req.lat,
            lon=req.lon,
            step_minutes=step_minutes,
            avoid_merc_rx=req.avoid_mercury_rx,
            avoid_moon_voc=req.avoid_moon_voc,
        )

        items: List[Dict[str, Any]] = []
        for r in results:
            items.append(
                {"jd": r.jd, "ts": _jd_to_iso(r.jd), "score": r.score, "reasons": r.reasons}
            )

        return {
            "start_ts": start_dt.isoformat(),
            "end_ts": end_dt.isoformat(),
            "jd_start": jd_start,
            "jd_end": jd_end,
            "step_minutes": step_minutes,
            "duration_hours": duration_hours,
            "count": len(items),
            "items": items,
        }

    except ValueError as e:
        # Girdi validasyon hataları 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Beklenmeyenler 500
        raise HTTPException(status_code=500, detail="internal error")
