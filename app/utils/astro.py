# app/utils/astro.py
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, Tuple, Any

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


def calculate_chart_points(jd_ut: float, latitude: float, longitude: float, house_system: str = 'P') -> Dict[str, Any]:
    """
    Ascendant, MC ve 12 ev pozisyonlarını hesapla
    
    Args:
        jd_ut: Julian Day (UT)
        latitude: Enlem (derece)
        longitude: Boylam (derece)
        house_system: Ev sistemi ('P'=Placidus, 'K'=Koch, 'W'=Whole Sign, 'E'=Equal)
    
    Returns:
        {
            "ascendant": {"degree": 125.5, "sign": "Leo", "sign_index": 4, ...},
            "mc": {"degree": 45.2, "sign": "Taurus", "sign_index": 1, ...},
            "vertex": {"degree": 215.3, "sign": "Scorpio", "sign_index": 7, ...},
            "houses": [
                {"number": 1, "degree": 125.5, "sign": "Leo", ...},
                ...
            ]
        }
    """
    # Swiss Ephemeris house calculation
    houses, ascmc = swe.houses_ex(jd_ut, latitude, longitude, house_system.encode())
    
    # Burç isimleri
    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", 
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # ASCENDANT (ascmc[0]) - YÜKSELİ BURÇ
    asc_degree = ascmc[0]
    asc_sign_index = int(asc_degree // 30)
    ascendant = {
        "degree": asc_degree,
        "sign": sign_names[asc_sign_index],
        "sign_index": asc_sign_index,
        "degree_in_sign": asc_degree % 30
    }
    
    # MC / MIDHEAVEN (ascmc[1]) - GÖKYÜZÜ ORTASI
    mc_degree = ascmc[1]
    mc_sign_index = int(mc_degree // 30)
    mc = {
        "degree": mc_degree,
        "sign": sign_names[mc_sign_index],
        "sign_index": mc_sign_index,
        "degree_in_sign": mc_degree % 30
    }
    
    # VERTEX (ascmc[3]) - KADER NOKTASI
    vertex_degree = ascmc[3]
    vertex_sign_index = int(vertex_degree // 30)
    vertex = {
        "degree": vertex_degree,
        "sign": sign_names[vertex_sign_index],
        "sign_index": vertex_sign_index,
        "degree_in_sign": vertex_degree % 30
    }
    
    # 12 EV (houses[])
    houses_list = []
    for i in range(12):
        house_degree = houses[i]
        sign_index = int(house_degree // 30)
        houses_list.append({
            "number": i + 1,
            "degree": house_degree,
            "sign": sign_names[sign_index],
            "sign_index": sign_index,
            "degree_in_sign": house_degree % 30
        })
    
    return {
        "ascendant": ascendant,
        "mc": mc,
        "vertex": vertex,
        "houses": houses_list
    }
