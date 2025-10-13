# app/utils/astro.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple

try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

# Ephemeris yolu
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

# Gezegen ID’leri
PLANETS = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
    "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN,
    "uranus": swe.URANUS, "neptune": swe.NEPTUNE, "pluto": swe.PLUTO
}

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# --- JD <-> ISO ---
def to_jd(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def jd_to_iso(jd: float) -> str:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    base = datetime(y, m, d, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(hours=hh, minutes=mm)).isoformat()

# --- Pozisyonlar ---
def planet_lon_speed(jd_utc: float, planet: int) -> Tuple[float, float]:
    xx, _ = swe.calc_ut(jd_utc, planet, _SWE_FLAGS)
    return xx[0] % 360.0, xx[3]

def all_planets(jd_utc: float) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    for name, pid in PLANETS.items():
        lon, spd = planet_lon_speed(jd_utc, pid)
        out[name] = (lon, spd)
    return out

def norm360(a: float) -> float:
    return a % 360.0

def angle_diff(a: float, b: float) -> float:
    d = abs(norm360(a - b))
    return d if d <= 180 else 360 - d
