# app/api/routers/electional.py
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.calculators import electional as E
import swisseph as swe

router = APIRouter(tags=["electional"])

class SearchRequest(BaseModel):
    # Başlangıç anı (UTC'ye normalize edilecek)
    year: int
    month: int
    day: int
    hour: int
    minute: int

    # Tarama parametreleri
    duration_hours: int = Field(24, ge=1, le=168)
    step_minutes: int = Field(15, ge=1, le=1440)

    # (opsiyonel) lokasyon — şimdilik kullanılmıyor ama imzada dursun
    lat: float = 0.0
    lon: float = 0.0

    avoid_mercury_rx: bool = True
    avoid_moon_voc: bool = True

@router.post("/search")
def search(req: SearchRequest) -> Dict[str, Any]:
    """
    /electional/search
    - Başlangıç zamanı UTC normalize edilir (minute==60 / hour==24 vb. hatalara düşmez)
    - JD aralığı [jd_start, jd_end] olarak hesaplanır
    - `search_electional_windows` çağrılır ve sonuçlar JSON'a dönüştürülür
    """
    try:
        # tip güvenliği
        step_minutes = int(req.step_minutes)
        duration_hours = int(req.duration_hours)
        if req.hour < 0 or req.minute < 0:
            raise ValueError("hour/minute must be >= 0")
        if step_minutes <= 0 or duration_hours <= 0:
            raise ValueError("step_minutes and duration_hours must be > 0")

        # Normalize: base + timedelta (minute==60 / hour==24 gibi değerlerde güvenli)
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        start_dt = base + timedelta(hours=req.hour, minutes=req.minute)
        end_dt = start_dt + timedelta(hours=duration_hours)

        # JD dönüşümü
        def _to_jd(dt_utc: datetime) -> float:
            dt_utc = dt_utc.astimezone(timezone.utc)
            hourf = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
            return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

        jd_start = _to_jd(start_dt)
        jd_end = _to_jd(end_dt)

        # Motoru çağır
        results = E.search_electional_windows(
            jd_start=jd_start,
            jd_end=jd_end,
            lat=req.lat,
            lon=req.lon,
            step_minutes=step_minutes,
            avoid_merc_rx=req.avoid_mercury_rx,
            avoid_moon_voc=req.avoid_moon_voc,
        )

        # Dataclass -> dict; ayrıca okunabilirlik için ts alanı ekleyelim
        def _jd_to_iso(jd: float) -> str:
            # Julian Day -> datetime (UTC)
            y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
            hh = int(h)
            mm = int(round((h - hh) * 60))
            base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
            return (base + timedelta(hours=hh, minutes=mm)).isoformat()

        items: List[Dict[str, Any]] = []
        for r in results:
            rd = {"jd": r.jd, "ts": _jd_to_iso(r.jd), "score": r.score, "reasons": r.reasons}
            items.append(rd)

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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Gerçek hata detayını log'a yazıp istemciye genelleştirilmiş mesaj veriyoruz
        raise HTTPException(status_code=500, detail="internal error")
