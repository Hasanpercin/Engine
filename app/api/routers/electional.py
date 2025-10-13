from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from app.calculators import electional as E

router = APIRouter(tags=["electional"])

class SearchRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    step_minutes: int = Field(..., ge=1, le=1440)
    duration_hours: int = Field(24, ge=1, le=168)  # varsayılan 24 saat tarama

    @validator("step_minutes", pre=True)
    def _force_int(cls, v):
        return int(v)

    @validator("hour", "minute")
    def _non_negative(cls, v):
        if v < 0:
            raise ValueError("hour/minute must be >= 0")
        return v

@router.post("/search")
def search(req: SearchRequest) -> Dict[str, Any]:
    """
    Seçim pencereleri taraması: start_ts = UTC (normalize) ve
    step_minutes aralığı ile duration_hours boyunca tarar.
    """
    try:
        # minute==60 / hour==24 gibi durumlarda hata vermemesi için baz+timedelta
        base = datetime(req.year, req.month, req.day, 0, 0, tzinfo=timezone.utc)
        start_ts = base + timedelta(hours=req.hour, minutes=req.minute)

        # Hesaplama motorunu çağır
        items = E.search_electional_windows(
            start_dt=start_ts,
            step_minutes=int(req.step_minutes),
            duration_hours=int(req.duration_hours),
        )

        return {
            "start_ts": start_ts.isoformat(),
            "step_minutes": int(req.step_minutes),
            "duration_hours": int(req.duration_hours),
            "count": len(items),
            "items": items,
        }

    except ValueError as e:
        # Kullanıcı girdisi kaynaklı problemler 400 olsun
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Beklenmeyen hatalar 500
        raise HTTPException(status_code=500, detail="internal error")
