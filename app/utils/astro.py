# app/utils/astro.py
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, Tuple

# Swiss Ephemeris (bazı ortamlarda pyswisseph adıyla gelir)
try:
    import swisseph as swe
except Exception:  # pragma: no cover
    import pyswisseph as swe  # type: ignore

# Ephemeris yolu (Docker'da /app/ephe)
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# Kullanacağımız gezegenler
PLANET_IDS: Dict[str, int] = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
}

def to_jd(dt_utc: datetime) -> float:
    """UTC datetime -> Julian Day (UT)."""
    dt_utc = dt_utc.astimezone(timezone.utc)
    hourf = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hourf, swe.GREG_CAL)

def planet_lon_speed(jd_ut: float, pid: int) -> Tuple[float, float]:
    """Gezegen ekliptik boylamı ve hız (deg/day)."""
    xx, _ = swe.calc_ut(jd_ut, pid, _SWE_FLAGS)
    lon = xx[0] % 360.0
    lon_speed = xx[3]
    return lon, lon_speed

def all_planets(jd_ut: float) -> Dict[str, Tuple[float, float]]:
    """Tüm gezegenler için (lon, speed) sözlüğü."""
    return {name: planet_lon_speed(jd_ut, pid) for name, pid in PLANET_IDS.items()}

def angle_norm(a: float) -> float:
    return a % 360.0

def angle_diff(a: float, b: float) -> float:
    """İki açı arasındaki en küçük fark [0,180]."""
    d = abs(angle_norm(a - b))
    return d if d <= 180.0 else 360.0 - d
