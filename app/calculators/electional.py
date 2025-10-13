# app/calculators/electional.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone
import math
import os

# Swiss Ephemeris import (pyswisseph alias'ı olan ortamlara uyumlu)
try:
    import swisseph as swe  # pyswisseph package
except Exception:
    import pyswisseph as swe  # some envs expose as pyswisseph

# --- Ephemeris path (prod'da mutlaka set edilsin) ---
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

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

# Bayraklar: Ekliptik koordinatlar + hız
_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED  # Ecliptic (default) + speed


# --- Utilities ---
def _norm360(angle: float) -> float:
    return angle % 360.0

def _angle_diff(a: float, b: float) -> float:
    d = abs(_norm360(a - b))
    return d if d <= 180 else 360 - d

def _planet_lon_speed(jd_utc: float, planet: int) -> Tuple[float, float]:
    """
    Swiss Ephemeris'ten geosantrik ekliptik boylam (deg) ve boylam hızı (deg/gün) döndürür.
    DİKKAT: calc_ut dönüşü (xx, retflag) şeklindedir; hız xx[3]'tedir.
    """
    xx, retflag = swe.calc_ut(jd_utc, planet, _SWE_FLAGS)
    lon = xx[0] % 360.0
    lon_speed = xx[3]
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
    # sınıflandırma (±10° tolerans)
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
    # Minimal tablo: domicile/exaltation/detriment/fall
    domicile = {
        "sun": [4], "moon": [3], "mercury": [2, 5], "venus": [1, 6],
        "mars": [0, 7], "jupiter": [8, 11], "saturn": [9, 10]
    }
    exaltation = {
        "sun": [0], "moon": [1], "mercury": [6], "venus": [11],
        "mars": [3], "jupiter": [4], "saturn": [6]  # Saturn exalt in Libra (sign 6)
    }
    di = domicile.get(planet_name, [])
    ex = exaltation.get(planet_name, [])
    detr = [(s + 6) % 12 for s in di]
    fall = [(s + 6) % 12 for s in ex]
    return {
        "domicile": sign_index in di,
        "exaltation": sign_index in ex,
        "detriment": sign_index in detr,
        "fall": sign_index in fall,
    }

def aspects_matrix(jd_utc: float, orb_table: Dict[str, int] | None = None) -> Dict[Tuple[str, str], Dict]:
    """
    Ana gezegenler arası majör açılar (orb toleranslarıyla) ve 'applying' bilgisi.
    Dönen sözlük: {(a,b): {"aspect": name, "delta": deg, "applying": bool}}
    """
    if orb_table is None:
        orb_table = DEFAULT_ORBS
    # longitudes & speeds
    pos: Dict[str, Tuple[float, float]] = {}
    for name, pid in PLANETS.items():
        lon, spd = _planet_lon_speed(jd_utc, pid)
        pos[name] = (lon, spd)

    results: Dict[Tuple[str, str], Dict] = {}
    names = list(pos.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            lon_a, spd_a = pos[a]
            lon_b, spd_b = pos[b]
            delta = _angle_diff(lon_a, lon_b)
            found = None
            for asp_name, asp_angle in MAJOR_ASPECTS.items():
                orb = orb_table.get(asp_name, 6)
                if abs(delta - asp_angle) <= orb:
                    found = asp_name
                    break
            if found:
                # Basit applying tanımı: relatif hız ve fark yönü
                applying = (spd_a - spd_b) * ((lon_b - lon_a + 360) % 360) > 0
                results[(a, b)] = {
                    "aspect": found, "delta": delta, "applying": applying
                }
    return results

def moon_void_of_course(jd_start_utc: float, step_minutes: int = 15) -> Tuple[bool, float, float]:
    """
    Return (is_voc_now, jd_voc_start, jd_sign_change)
    Strict VoC: Mevcut burçta Ay'ın yaptığı SON majör açıdan, bir SONRAKİ burç girişine kadar.
    """
    step_minutes = int(step_minutes)
    if step_minutes <= 0:
        raise ValueError("step_minutes must be > 0")

    # mevcut burç
    start_sign = _moon_sign(jd_start_utc)
    jd = jd_start_utc
    last_aspect_jd = None

    # burç değişimine dek tarama; son majör açı zamanını takip et
    # (sonsuz döngüye girmemek için kaba bir güvenlik sınırı)
    max_iters = int((29.5 * 24 * 60) // step_minutes) + 5  # bir sinodik ayı aşmasın
    it = 0
    while _moon_sign(jd) == start_sign and it < max_iters:
        asps = aspects_matrix(jd)
        # Ay'ın yaptığı majör açılar?
        moon_pairs = [k for k in asps.keys() if "moon" in k]
        if moon_pairs:
            last_aspect_jd = jd
        jd += step_minutes / (24 * 60)
        it += 1

    jd_sign_change = jd
    if last_aspect_jd is None:
        # Bu burçta hiç açı yoksa -> VoC burca girişten itibaren kabul; approx: start
        jd_voc_start = jd_start_utc
    else:
        jd_voc_start = last_aspect_jd

    is_voc_now = (jd_start_utc >= jd_voc_start) and (jd_start_utc < jd_sign_change)
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
    """
    JD aralığında (jd_start..jd_end) belirli adım ile tarama yapar ve
    puanlanmış zaman noktalarını döndürür (en iyi 50).
    Not: parametrelerdeki lat/lon şimdilik kullanılmıyor; imzada tutuldu.
    """
    step_minutes = int(step_minutes)
    if step_minutes <= 0:
        raise ValueError("step_minutes must be > 0")
    if jd_end < jd_start:
        raise ValueError("jd_end must be >= jd_start")

    jd = jd_start
    out: List[ElectionalScore] = []

    while jd <= jd_end:
        reasons: List[str] = []
        score = 0.0

        # Moon phase basic scoring
        phase = lunar_phase(jd)
        if phase["phase"] in {"New Moon", "First Quarter", "Full Moon", "Last Quarter"}:
            score += 1.0
            reasons.append(f"phase={phase['phase']}")

        # Essential dignities (Moon & Venus örneği)
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

        # Aspects: basit iyi açı sayımı (trine/sextile & venus/jupiter içeren çiftler)
        asps = aspects_matrix(jd)
        good = 0
        for (a, b), data in asps.items():
            if data["aspect"] in {"trine", "sextile"} and any(x in (a, b) for x in ("venus", "jupiter")):
                good += 1
        score += 0.5 * good
        if good:
            reasons.append(f"good_aspects={good}")

        # Cezalar
        if avoid_merc_rx and _is_mercury_rx(jd):
            score -= 2.0; reasons.append("mercury_rx")
        if avoid_moon_voc:
            is_voc, voc_start, voc_end = moon_void_of_course(jd, step_minutes=step_minutes)
            if is_voc:
                score -= 3.0; reasons.append("moon_voc")

        out.append(ElectionalScore(jd, score, reasons))
        jd += step_minutes / (24 * 60)

    # En iyi 50 sonucu döndür
    out_sorted = sorted(out, key=lambda x: -x.score)
    return out_sorted[:50]
