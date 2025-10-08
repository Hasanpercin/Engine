from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone
import math
import os

try:
    import swisseph as swe  # pyswisseph package
except Exception:
    import pyswisseph as swe  # some envs expose as pyswisseph

# --- Constants ---
MAJOR_ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}
DEFAULT_ORBS = {
    "conjunction": 8,
    "opposition": 8,
    "trine": 7,
    "square": 6,
    "sextile": 5,
}

LUMINARIES = {"sun", "moon"}

PLANETS = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
    "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN,
    "uranus": swe.URANUS, "neptune": swe.NEPTUNE, "pluto": swe.PLUTO
}

# --- Utilities ---
def _norm360(angle: float) -> float:
    return angle % 360.0

def _angle_diff(a: float, b: float) -> float:
    d = abs(_norm360(a - b))
    return d if d <= 180 else 360 - d

def _planet_lon_speed(jd_utc: float, planet: int) -> Tuple[float, float]:
    lon, lat, dist, lon_speed = swe.calc_ut(jd_utc, planet, swe.FLG_EQUATORIAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
    # Equatorial returns RA; better use ECLIPTIC
    lon, lat, dist, lon_speed = swe.calc_ut(jd_utc, planet, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return lon, lon_speed

def _moon_sign(jd_utc: float) -> int:
    lon, _ = _planet_lon_speed(jd_utc, swe.MOON)
    return int(lon // 30)

def _is_mercury_rx(jd_utc: float) -> bool:
    _, spd = _planet_lon_speed(jd_utc, swe.MERCURY)
    return spd < 0

# --- Core calculations ---
def lunar_phase(jd_utc: float) -> Dict[str, object]:
    lon_sun, _ = _planet_lon_speed(jd_utc, swe.SUN)
    lon_moon, _ = _planet_lon_speed(jd_utc, swe.MOON)
    elong = _norm360(lon_moon - lon_sun)
    waxing = elong < 180
    # classify
    if _angle_diff(elong, 0) <= 10:
        name = "New Moon"
    elif _angle_diff(elong, 90) <= 10 and waxing:
        name = "First Quarter"
    elif _angle_diff(elong, 180) <= 10:
        name = "Full Moon"
    elif _angle_diff(elong, 270) <= 10 and not waxing:
        name = "Last Quarter"
    else:
        name = "Waxing" if waxing else "Waning"
    return {"elongation": elong, "waxing": waxing, "phase": name}

def essential_dignities(sign_index: int, planet_name: str) -> Dict[str, bool]:
    # Minimal table: domicile/exaltation/detriment/fall
    domicile = {
        "sun": [4], "moon": [3], "mercury": [2,5], "venus": [1,6],
        "mars": [0,7], "jupiter": [8,11], "saturn": [9,10]
    }
    exaltation = {
        "sun": [0], "moon": [1], "mercury": [6], "venus": [11],
        "mars": [3], "jupiter": [4], "saturn": [6]  # Saturn exalt in Libra (sign 6)
    }
    di = domicile.get(planet_name, [])
    ex = exaltation.get(planet_name, [])
    detr = [(s+6) % 12 for s in di]
    fall = [(s+6) % 12 for s in ex]
    return {
        "domicile": sign_index in di,
        "exaltation": sign_index in ex,
        "detriment": sign_index in detr,
        "fall": sign_index in fall,
    }

def aspects_matrix(jd_utc: float, orb_table: Dict[str, int] | None = None) -> Dict[Tuple[str,str], Dict]:
    if orb_table is None:
        orb_table = DEFAULT_ORBS
    # compute longitudes & speeds
    pos = {}
    for name, pid in PLANETS.items():
        lon, spd = _planet_lon_speed(jd_utc, pid)
        pos[name] = (lon, spd)

    results = {}
    names = list(pos.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            lon_a, spd_a = pos[a]; lon_b, spd_b = pos[b]
            delta = _angle_diff(lon_a, lon_b)
            found = None
            for asp_name, asp_angle in MAJOR_ASPECTS.items():
                orb = orb_table.get(asp_name, 6)
                if abs(delta - asp_angle) <= orb:
                    found = asp_name
                    break
            if found:
                applying = (spd_a - spd_b) * ((lon_b - lon_a + 360) % 360) > 0
                results[(a,b)] = {
                    "aspect": found, "delta": delta, "applying": applying
                }
    return results

def moon_void_of_course(jd_start_utc: float, step_minutes: int = 15) -> Tuple[bool, float, float]:
    """Return (is_voc_now, jd_voc_start, jd_sign_change)
    Strict VoC: from Moon's last major aspect in current sign until next sign ingress.
    """
    # find current sign
    start_sign = _moon_sign(jd_start_utc)
    jd = jd_start_utc
    last_aspect_jd = None
    # scan forward until sign change; track last major aspect exactness window
    while _moon_sign(jd) == start_sign:
        asps = aspects_matrix(jd)
        # remove aspects with Moon? We consider aspects the Moon makes to planets (excluding nodes etc.)
        moon_pairs = [k for k in asps.keys() if "moon" in k]
        if moon_pairs:
            last_aspect_jd = jd
        jd += step_minutes / (24*60)
    jd_sign_change = jd
    if last_aspect_jd is None:
        # no aspect in this sign at all -> VoC from sign entry; approximate as start
        jd_voc_start = jd_start_utc
    else:
        jd_voc_start = last_aspect_jd
    is_voc_now = jd_start_utc >= jd_voc_start and jd_start_utc < jd_sign_change
    return is_voc_now, jd_voc_start, jd_sign_change

def part_of_fortune(jd_utc: float, is_day_chart: bool, asc_lon: float, sun_lon: float, moon_lon: float) -> float:
    if is_day_chart:
        pof = asc_lon + (moon_lon - sun_lon)
    else:
        pof = asc_lon + (sun_lon - moon_lon)
    return _norm360(pof)

@dataclass
class ElectionalScore:
    jd: float
    score: float
    reasons: List[str]

def search_electional_windows(jd_start: float, jd_end: float, lat: float, lon: float,
                              step_minutes: int = 15,
                              avoid_merc_rx: bool = True, avoid_moon_voc: bool = True) -> List[ElectionalScore]:
    jd = jd_start
    out: List[ElectionalScore] = []
    while jd <= jd_end:
        reasons = []
        score = 0.0

        # Moon phase basic scoring
        phase = lunar_phase(jd)
        if phase["phase"] in {"New Moon", "First Quarter", "Full Moon", "Last Quarter"}:
            score += 1.0
            reasons.append(f"phase={phase['phase']}")

        # Dignities: simple check for Moon & Venus
        moon_lon, _ = _planet_lon_speed(jd, swe.MOON)
        venus_lon, _ = _planet_lon_speed(jd, swe.VENUS)
        moon_sign = int(moon_lon // 30)
        venus_sign = int(venus_lon // 30)
        moon_dig = essential_dignities(moon_sign, "moon")
        ven_dig = essential_dignities(venus_sign, "venus")
        if moon_dig["domicile"] or moon_dig["exaltation"]:
            score += 1.0; reasons.append("moon_dignified")
        if ven_dig["domicile"] or ven_dig["exaltation"]:
            score += 1.0; reasons.append("venus_dignified")

        # Aspects: check Venus/Jupiter trines/sextiles to ASC rulers would be ideal (simplified here)
        asps = aspects_matrix(jd)
        good = 0
        for (a,b), data in asps.items():
            if data["aspect"] in {"trine", "sextile"} and any(x in (a,b) for x in ("venus","jupiter")):
                good += 1
        score += 0.5 * good
        if good:
            reasons.append(f"good_aspects={good}")

        # Penalties
        if avoid_merc_rx and _is_mercury_rx(jd):
            score -= 2.0; reasons.append("mercury_rx")
        if avoid_moon_voc:
            is_voc, voc_start, voc_end = moon_void_of_course(jd, step_minutes=step_minutes)
            if is_voc:
                score -= 3.0; reasons.append("moon_voc")

        out.append(ElectionalScore(jd, score, reasons))
        jd += step_minutes / (24*60)

    # Aggregate contiguous high-score regions into windows
    out_sorted = sorted(out, key=lambda x: -x.score)
    return out_sorted[:50]
