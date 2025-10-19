# app/api/routers/natal.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.astro import to_jd, all_planets
from app.utils.rate_limit import plan_limiter

router = APIRouter(tags=["natal"])  # prefix main.py'de

class NatalRequest(BaseModel):
    year: int = Field(..., description="Yerel yıl")
    month: int = Field(..., description="Yerel ay (1-12)")
    day: int = Field(..., description="Yerel gün (1-31)")
    hour: int = Field(..., description="Yerel saat (0-23)")
    minute: int = Field(..., description="Yerel dakika (0-59)")
    tz_offset: float = Field(0.0, description="Yerel saat UTC ofseti (saat cinsinden, örn. +3.0)")

class Body(BaseModel):
    name: str = Field(..., description="Gezegen/ışık/hesaplanan gökcisminin adı")
    lon: float = Field(..., description="Ekliptik boylam (derece)")
    sign_index: int = Field(..., description="Burç indeksi (0=Koç, 1=Boğa, ... 11=Balık)")

class NatalResponse(BaseModel):
    ts_utc: str = Field(..., description="UTC zaman damgası (ISO8601)")
    bodies: List[Body] = Field(..., description="Temel gökcismi konumları")

@router.post(
    "/basic",
    operation_id="natal_basic",
    summary="Temel doğum haritası hesaplama",
    description=(
        "Yerel tarih/saat ve UTC ofseti verildiğinde, UTC'ye dönüştürüp gezegen/ışık boylamlarını "
        "ve burç indekslerini döndürür."
    ),
    response_model=NatalResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(plan_limiter("FREE"))],
)
async def basic(req: NatalRequest) -> NatalResponse:
    try:
        base_local = datetime(
            req.year, req.month, req.day, req.hour, req.minute,
            tzinfo=timezone(timedelta(hours=req.tz_offset))
        )
        dt_utc = base_local.astimezone(timezone.utc)
        jd = to_jd(dt_utc)
        pos = all_planets(jd)
        bodies = [
            Body(name=k, lon=v[0], sign_index=int(v[0] // 30))
            for k, v in pos.items()
        ]
        return NatalResponse(ts_utc=dt_utc.isoformat(), bodies=bodies)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
