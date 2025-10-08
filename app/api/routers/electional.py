from fastapi import APIRouter, Depends
from app.models.request import ElectionalSearchRequest
from app.models.response import ElectionalSearchResponse, ElectionalSlot
from app.utils.auth import api_key_auth
from app.utils.rate_limit import plan_limiter
from datetime import timezone, datetime
from typing import List
from app.calculators.electional import search_electional_windows
import swisseph as swe

router = APIRouter(prefix="/electional", tags=["electional"])

@router.post("/search", response_model=ElectionalSearchResponse,
             dependencies=[Depends(api_key_auth)])
async def search(req: ElectionalSearchRequest, plan: str = Depends(api_key_auth)):
    # Rate limit per plan
    limiter = plan_limiter(plan)  # noqa: F841 (declared but not used - still initializes limiter)
    jd_start = swe.julday(req.start.year, req.start.month, req.start.day,
                          req.start.hour + req.start.minute/60.0)
    jd_end = swe.julday(req.end.year, req.end.month, req.end.day,
                        req.end.hour + req.end.minute/60.0)
    scores = search_electional_windows(jd_start, jd_end, req.lat, req.lon,
                                       step_minutes=req.step_minutes,
                                       avoid_merc_rx=req.avoid_merc_rx,
                                       avoid_moon_voc=req.avoid_moon_voc)
    slots: List[ElectionalSlot] = []
    for sc in scores[:req.top_n]:
        # back-convert JD to datetime (UTC) for output
        jd = sc.jd
        y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
        hour = int(h)
        minute = int(round((h - hour) * 60))
        dt = datetime(y, m, d, hour, minute, tzinfo=timezone.utc)
        slots.append(ElectionalSlot(start=dt, end=dt, score=sc.score, reasons=sc.reasons))
    return ElectionalSearchResponse(slots=slots)
