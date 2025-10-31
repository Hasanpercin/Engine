# app/api/routers/natal.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.astro import to_jd, all_planets, calculate_chart_points
from app.utils.rate_limit import plan_limiter

router = APIRouter(tags=["natal"])  # prefix main.py'de


class NatalRequest(BaseModel):
    year: int = Field(..., description="Yerel yıl")
    month: int = Field(..., description="Yerel ay (1-12)")
    day: int = Field(..., description="Yerel gün (1-31)")
    hour: int = Field(..., description="Yerel saat (0-23)")
    minute: int = Field(..., description="Yerel dakika (0-59)")
    tz_offset: float = Field(0.0, description="Yerel saat UTC ofseti (saat cinsinden, örn. +3.0)")
    
    # YENİ - Opsiyonel koordinatlar
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Doğum yeri enlemi (derece)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Doğum yeri boylamı (derece)")
    house_system: Optional[str] = Field("P", description="Ev sistemi: P=Placidus, K=Koch, W=Whole, E=Equal")


class Body(BaseModel):
    name: str = Field(..., description="Gezegen/ışık/hesaplanan gökcisminin adı")
    lon: float = Field(..., description="Ekliptik boylam (derece)")
    sign_index: int = Field(..., description="Burç indeksi (0=Koç, 1=Boğa, ... 11=Balık)")
    speed: Optional[float] = Field(None, description="Günlük hız (derece/gün)")


class ChartPoint(BaseModel):
    """Ascendant, MC, Vertex gibi özel noktalar için"""
    degree: float = Field(..., description="Derece (0-360)")
    sign: str = Field(..., description="Burç adı")
    sign_index: int = Field(..., description="Burç indeksi (0-11)")
    degree_in_sign: float = Field(..., description="Burç içindeki derece (0-30)")


class House(BaseModel):
    number: int = Field(..., description="Ev numarası (1-12)")
    degree: float = Field(..., description="Ev cusp derecesi (0-360)")
    sign: str = Field(..., description="Ev cusp burcu")
    sign_index: int = Field(..., description="Burç indeksi (0-11)")
    degree_in_sign: float = Field(..., description="Burç içindeki derece (0-30)")


class NatalResponse(BaseModel):
    ts_utc: str = Field(..., description="UTC zaman damgası (ISO8601)")
    bodies: List[Body] = Field(..., description="Temel gökcismi konumları")
    
    # YENİ - Opsiyonel chart points ve houses
    ascendant: Optional[ChartPoint] = Field(None, description="Yükselen burç (latitude/longitude verildiğinde)")
    mc: Optional[ChartPoint] = Field(None, description="Gökyüzü ortası/MC (latitude/longitude verildiğinde)")
    vertex: Optional[ChartPoint] = Field(None, description="Vertex noktası (latitude/longitude verildiğinde)")
    houses: Optional[List[House]] = Field(None, description="12 ev pozisyonu (latitude/longitude verildiğinde)")


@router.post(
    "/basic",
    operation_id="natal_basic",
    summary="Temel doğum haritası hesaplama",
    description=(
        "Yerel tarih/saat ve UTC ofseti verildiğinde, UTC'ye dönüştürüp gezegen/ışık boylamlarını "
        "ve burç indekslerini döndürür. Latitude/longitude verildiğinde ascendant, MC, vertex ve "
        "houses de hesaplanır."
    ),
    response_model=NatalResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(plan_limiter("FREE"))],
)
async def basic(req: NatalRequest) -> NatalResponse:
    try:
        # UTC'ye dönüştür
        base_local = datetime(
            req.year, req.month, req.day, req.hour, req.minute,
            tzinfo=timezone(timedelta(hours=req.tz_offset))
        )
        dt_utc = base_local.astimezone(timezone.utc)
        jd = to_jd(dt_utc)
        
        # Gezegen pozisyonları (hız bilgisi dahil)
        pos = all_planets(jd)
        bodies = [
            Body(
                name=k,
                lon=v[0],
                sign_index=int(v[0] // 30),
                speed=v[1]  # Günlük hız
            )
            for k, v in pos.items()
        ]
        
        # Chart points ve Houses (koordinatlar varsa)
        ascendant_data = None
        mc_data = None
        vertex_data = None
        houses_data = None
        
        if req.latitude is not None and req.longitude is not None:
            chart_data = calculate_chart_points(
                jd, 
                req.latitude, 
                req.longitude,
                req.house_system or 'P'
            )
            
            ascendant_data = ChartPoint(**chart_data["ascendant"])
            mc_data = ChartPoint(**chart_data["mc"])
            vertex_data = ChartPoint(**chart_data["vertex"])
            houses_data = [House(**h) for h in chart_data["houses"]]
        
        return NatalResponse(
            ts_utc=dt_utc.isoformat(),
            bodies=bodies,
            ascendant=ascendant_data,
            mc=mc_data,
            vertex=vertex_data,
            houses=houses_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
