# app/calculators/electional.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone
import math
import os

# Swiss Ephemeris: bazı ortamlarda "pyswisseph" adıyla gelir
try:
    import swisseph as swe
except Exception:
    import pyswisseph as swe  # type: ignore

# Ephemeris yolu (ENV > /app/ephe)
swe.set_ephe_path(os.getenv("SE_EPHE_PATH", "/app/ephe"))

# --------------------------------------------------------------------
# Sabitler
# --------------------------------------------------------------------
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

# Ekliptik + hız bayrakları (hız için FLG_SPEED şart)
_SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# --------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------
def _norm360(angle: float) -> float:
    return angle % 360.0

def _angle_diff(a: float, b: float) -> float:
    d = abs(_norm360(a - b))
    return d if d <= 180 else 360 - d

def _planet_lon_speed(jd_utc: float, planet: int) -> Tuple[float, float]:
    """
    Swiss Ephemeris'ten geosantrik ekliptik boylam (deg) ve boylam hızı (deg/gün).
    DÖNÜŞ: (xx, retflag); lon = xx[0], speed = xx[3]
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

# --------------------------------------------------------------------
# Çekirdek hesaplar
# --------------------------------------------------------------------
def lunar_phase(jd_utc: float) -> Dict[str, object]:
    lon_sun, _ = _planet_lon_speed(jd_utc, swe.SUN)
    lon_moon, _ = _planet_lon_speed(jd_utc, swe.MOON)
    elong = _norm360(lon_moon - lon_sun)
    waxing = elong < 180
    # ±10° toleransla faz sınıflama
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
        "mars": [3], "jupiter": [4], "saturn": [6]  # Satürn Terazi'de yücelir
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
    Majör açılar ve "applying" bilgisi.
    Dönüş: {(a,b): {"aspect": name, "delta": deg, "applying": bool}}
    """
    if orb_table is None:
        orb_table = DEFAULT_ORBS

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
                # basit applying tanımı: relatif hız ve fark yönü
                applying = (spd_a - spd_b) * ((lon_b - lon_a + 360) % 360) > 0
                results[(a, b)] = {"aspect": found, "delta": delta, "applying": applying}
    return results

def moon_void_of_course(jd_start_utc: float, step_minutes: int = 15) -> Tuple[bool, float, float]:
    """
    Strict VoC: Mevcut burçta Ay'ın yaptığı SON majör açıdan, bir SONRAKİ burç girişine kadar.
    Dönüş: (is_voc_now, jd_voc_start, jd_sign_change)
    """
    step_minutes = int(step_minutes)
    if step_minutes <= 0:
        raise ValueError("step_minutes must be > 0")

    start_sign = _moon_sign(jd_start_utc)
    jd = jd_start_utc
    last_aspect_jd = None

    # Güvenlik: uzun taramalarda sonsuz döngü engeli (yaklaşık bir sinodik ay)
    max_iters = int((29.5 * 24 * 60) // step_minutes) + 5
    it = 0
    while _moon_sign(jd) == start_sign and it < max_iters:
        asps = aspects_matrix(jd)
        moon_pairs = [k for k in asps.keys() if "moon" in k]
        if moon_pairs:
            last_aspect_jd = jd
        jd += step_minutes / (24 * 60)
        it += 1

    jd_sign_change = jd
    jd_voc_start = jd_start_utc if last_aspect_jd is None else last_aspect_jd
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

def search_electional_windows(
    jd_start: float,
    jd_end: float,
    lat: float,
    lon: float,
    step_minutes: int = 15,
    avoid_merc_rx: bool = True,
    avoid_moon_voc: bool = True,
) -> List[ElectionalScore]:
    """
    [jd_start .. jd_end] aralığını "inclusive" biçimde tarar; her örnek nokta için
    faz/asalet/açı/retro/VoC kriterlerine göre skor üretir ve en iyi 50 sonucu döndürür.
    Not: lat/lon şu an kullanılmıyor; imzada tutuldu.
    """
    step_minutes = int(step_minutes)
    if step_minutes <= 0:
        raise ValueError("step_minutes must be > 0")
    if jd_end < jd_start:
        raise ValueError("jd_end must be >= jd_start")

    # Inclusive adımlama: başlangıç + her adım + (mümkünse) bitiş noktasını kapsar
    total_min = int(round((jd_end - jd_start) * 24 * 60))
    steps = total_min // step_minutes  # 2h/30m -> 120//30 = 4 → range(5) ile 5 nokta

    out: List[ElectionalScore] = []
    for i in range(steps + 1):
        jd = jd_start + (i * step_minutes) / (24 * 60)

        reasons: List[str] = []
        score = 0.0

        # Faz
        phase = lunar_phase(jd)
        if phase["phase"] in {"New Moon", "First Quarter", "Full Moon", "Last Quarter"}:
            score += 1.0
            reasons.append(f"phase={phase['phase']}")

        # Dignities: Moon & Venus örneği
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

        # Açı matrisi: trine/sextile ve içinde venus/jupiter olan çiftler
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

    out_sorted = sorted(out, key=lambda x: -x.score)
    return out_sorted[:50]
