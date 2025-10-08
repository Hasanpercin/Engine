from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BirthData(BaseModel):
    date: datetime
    lat: float
    lon: float
    tz: float = Field(..., description="Timezone offset hours (e.g., +3 for Europe/Istanbul)")

class ElectionalSearchRequest(BaseModel):
    start: datetime
    end: datetime
    lat: float
    lon: float
    event_type: str = "generic"
    step_minutes: int = 15
    avoid_merc_rx: bool = True
    avoid_moon_voc: bool = True
    top_n: int = 10
