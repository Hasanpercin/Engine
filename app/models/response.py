from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ElectionalSlot(BaseModel):
    start: datetime
    end: datetime
    score: float
    reasons: List[str]

class ElectionalSearchResponse(BaseModel):
    slots: List[ElectionalSlot]
