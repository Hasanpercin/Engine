"""
Secondary progressions and solar arc directions
Complete implementation of progressed chart calculations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from kerykeion import AstrologicalSubject
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def calculate_secondary_progressions(
    birth_data: Dict[str, Any],
    progression_date: date,
    include_aspects: bool = True
) -> Dict[str, Any]:
    """
    Calculate secondary progressions
    
    Secondary progressions: One day after birth = one year of life
    Example: Day 30 after birth = Age 30
    
    Args:
        birth_data: Birth data dictionary
        progression_date: Date to progress to
        include_aspects: Whether to calculate progressed-to-natal aspects
        
    Returns:
        Complete progressed chart data
    """
    try:
        birth_date = birth_data['birth_date']
        
        # Calculate progression: 1 day = 1 year
        age_in_years = (progression_date - birth_date.date()).days / 365.25
        days_to_add = int(age_in_years)
        
        # Progressed date = birth_date + days_to_add
        progressed_date = birth_date + timedelta(days=days_to_add)
        
        logger.info(
            f"Calculating secondary progressions for age {age_in_years:.1f} "
            f"(progressed date: {progressed_date.date()})"
        )
        
        # Create progressed chart
        progressed_chart = AstrologicalSubject(
            name=f"{birth_data['name']} - Progressed",
            year=progressed_date.year,
            month=progressed_date.month,
            day=progressed_date.day,
            hour=progressed_date.hour,
            minute=progressed_date.minute,
            city=birth_data['birth_place'],
            nation=birth_data.get('nation', 'TR'),
            lat=birth_data['latitude'],
            lng=birth_data['longitude'],
            tz_str=birth_data['timezone']
        )
        
        # Extract progressed planets
        progressed_planets = extract_progressed_planets(progressed_chart)
        
        # Calculate progressed houses (use current location, not birth location)
        # Note: Some astrologers use progressed MC, others use current MC
        progressed_houses = extract_houses(progressed_chart)
        
        result = {
            'birth_date': birth_date.date().isoformat(),
            'progression_date': progression_date.isoformat(),
            'age': round(age_in_years, 2),
            'progressed_date': progressed_date.date().isoformat(),
            'progressed_planets': progressed_planets,
            'progressed_houses': progressed_houses,
            'method': 'secondary_progressions',
            'calculation_note': 'One day after birth equals one year of life'
        }
        
        # Calculate progressed to natal aspects
        if include_aspects:
            natal_chart = AstrologicalSubject(
                name=birth_data['name'],
                year=birth_date.year,
                month=birth_date.month,
                day=birth_date.day,
                hour=birth_date.hour,
                minute=birth_date.minute,
                city=birth_data['birth_place'],
                nation=birth_data.get('nation', 'TR'),
                lat=birth_data['latitude'],
                lng=birth_data['longitude'],
                tz_str=birth_data['timezone']
            )
            
            natal_planets = extract_progressed_planets(natal_chart)
            prog_to_natal_aspects = calculate_progressed_to_natal_aspects(
                progressed_planets,
                natal_planets
            )
            result['progressed_to_natal_aspects'] = prog_to_natal_aspects
        
        # Identify significant progressions
        result['significant_progressions'] = identify_significant_progressions(
            progressed_planets,
            progressed_houses,
            age_in_years
        )
        
        # Generate interpretation
        result['interpretation'] = generate_progressions_interpretation(
            progressed_planets,
            age_in_years,
            result.get('significant_progressions', [])
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating secondary progressions: {str(e)}")
        raise


def calculate_solar_arc_directions(
    birth_data: Dict[str, Any],
    target_date: date
) -> Dict[str, Any]:
    """
    Calculate solar arc directions
    
    Solar arc: Move all planets by the Sun's secondary progression amount
    Simpler than secondary progressions, moves everything uniformly
    
    Args:
        birth_data: Birth data dictionary
        target_date: Date to calculate solar arcs for
        
    Returns:
        Solar arc directed chart
    """
    try:
        birth_date = birth_data['birth_date']
        age_in_years = (target_date - birth_date.date()).days / 365.25
        
        logger.info(f"Calculating solar arc directions for age {age_in_years:.1f}")
        
        # Calculate progressed Sun position
        days_to_add = int(age_in_years)
        progressed_date = birth_date + timedelta(days=days_to_add)
        
        # Get natal Sun position
        natal_chart = AstrologicalSubject(
            name=birth_data['name'],
            year=birth_date.year,
            month=birth_date.month,
            day=birth_date.day,
            hour=birth_date.hour,
            minute=birth_date.minute,
            city=birth_data['birth_place'],
            nation=birth_data.get('nation', 'TR'),
            lat=birth_data['latitude'],
            lng=birth_data['longitude'],
            tz_str=birth_data['timezone']
        )
        
        natal_sun_lon = natal_chart.sun['position']
        
        # Get progressed Sun position
        prog_jd = swe.julday(
            progressed_date.year,
            progressed_date.month,
            progressed_date.day,
            progressed_date.hour + progressed_date.minute / 60.0
        )
        prog_sun_pos, _ = swe.calc_ut(prog_jd, swe.SUN)
        prog_sun_lon = prog_sun_pos[0]
        
        # Solar arc = difference between natal and progressed Sun
        solar_arc = (prog_sun_lon - natal_sun_lon) % 360
        
        logger.info(f"Solar arc for age {age_in_years:.1f}: {solar_arc:.2f}°")
        
        # Apply solar arc to all natal planets
        natal_planets = extract_progressed_planets(natal_chart)
        solar_arc_planets = {}
        
        for planet_name, planet_data in natal_planets.items():
            natal_lon = planet_data['longitude']
            arc_lon = (natal_lon + solar_arc) % 360
            
            # Determine sign
            arc_sign = get_sign_from_longitude(arc_lon)
            
            solar_arc_planets[planet_name] = {
                'natal_longitude': natal_lon,
                'solar_arc_longitude': arc_lon,
                'solar_arc_sign': arc_sign,
                'arc_amount': solar_arc,
                'natal_sign': planet_data['sign']
            }
        
        return {
            'birth_date': birth_date.date().isoformat(),
            'target_date': target_date.isoformat(),
            'age': round(age_in_years, 2),
            'solar_arc_amount': round(solar_arc, 2),
            'solar_arc_planets': solar_arc_planets,
            'method': 'solar_arc_directions',
            'interpretation': generate_solar_arc_interpretation(
                solar_arc_planets,
                solar_arc,
                age_in_years
            )
        }
        
    except Exception as e:
        logger.error(f"Error calculating solar arc directions: {str(e)}")
        raise


def track_progressed_moon_phases(
    birth_data: Dict[str, Any],
    start_age: int,
    end_age: int
) -> List[Dict[str, Any]]:
    """
    Track progressed Moon phases through age range
    
    Progressed Moon cycle: ~27-30 years to complete zodiac
    New Moon every ~27-28 years is significant
    
    Args:
        birth_data: Birth data
        start_age: Starting age
        end_age: Ending age
        
    Returns:
        List of progressed Moon phase changes
    """
    try:
        phases = []
        birth_date = birth_data['birth_date']
        
        for age in range(start_age, end_age + 1):
            progression_date = birth_date.date() + timedelta(days=age * 365.25)
            
            prog_data = calculate_secondary_progressions(
                birth_data,
                progression_date,
                include_aspects=False
            )
            
            prog_sun = prog_data['progressed_planets']['sun']['longitude']
            prog_moon = prog_data['progressed_planets']['moon']['longitude']
            
            # Calculate phase angle
            phase_angle = (prog_moon - prog_sun) % 360
            
            # Determine phase
            phase_name = get_moon_phase_name(phase_angle)
            
            phases.append({
                'age': age,
                'date': progression_date.isoformat(),
                'phase_angle': round(phase_angle, 2),
                'phase_name': phase_name,
                'progressed_moon_sign': prog_data['progressed_planets']['moon']['sign']
            })
        
        # Identify phase changes
        phase_changes = []
        for i in range(1, len(phases)):
            if phases[i]['phase_name'] != phases[i-1]['phase_name']:
                phase_changes.append({
                    'age': phases[i]['age'],
                    'from_phase': phases[i-1]['phase_name'],
                    'to_phase': phases[i]['phase_name'],
                    'significance': get_phase_change_significance(
                        phases[i-1]['phase_name'],
                        phases[i]['phase_name']
                    )
                })
        
        return {
            'all_phases': phases,
            'phase_changes': phase_changes,
            'current_phase': phases[-1] if phases else None
        }
        
    except Exception as e:
        logger.error(f"Error tracking progressed Moon phases: {str(e)}")
        return {'all_phases': [], 'phase_changes': [], 'current_phase': None}


def calculate_progressed_to_natal_aspects(
    progressed_planets: Dict[str, Any],
    natal_planets: Dict[str, Any],
    orb: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between progressed and natal planets
    
    Progressed-to-natal aspects are significant life events
    
    Args:
        progressed_planets: Progressed planet positions
        natal_planets: Natal planet positions
        orb: Aspect orb in degrees
        
    Returns:
        List of progressed-to-natal aspects
    """
    aspects = []
    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for prog_name, prog_data in progressed_planets.items():
        prog_lon = prog_data['longitude']
        
        for natal_name, natal_data in natal_planets.items():
            natal_lon = natal_data['longitude']
            
            # Calculate angle between planets
            angle = abs((prog_lon - natal_lon + 180) % 360 - 180)
            
            # Check each aspect type
            for aspect_name, aspect_angle in aspect_angles.items():
                diff = abs(angle - aspect_angle)
                
                if diff <= orb:
                    aspects.append({
                        'progressed_planet': prog_name,
                        'natal_planet': natal_name,
                        'aspect': aspect_name,
                        'orb': round(diff, 2),
                        'exact': diff < 0.5,
                        'interpretation': get_progressed_aspect_interpretation(
                            prog_name,
                            natal_name,
                            aspect_name
                        )
                    })
    
    # Sort by orb (most exact first)
    aspects.sort(key=lambda x: x['orb'])
    
    return aspects


def identify_significant_progressions(
    progressed_planets: Dict[str, Any],
    progressed_houses: Dict[str, Any],
    age: float
) -> List[Dict[str, Any]]:
    """
    Identify significant progressed events
    
    - Progressed planet changing signs
    - Progressed planet changing houses
    - Progressed Moon phases
    - Progressed angles changing signs
    
    Args:
        progressed_planets: Progressed planets
        progressed_houses: Progressed houses
        age: Current age
        
    Returns:
        List of significant progressions
    """
    significant = []
    
    # Check progressed Moon (moves fastest, ~1° per month = 1 sign every 2.5 years)
    prog_moon = progressed_planets.get('moon', {})
    prog_moon_sign = prog_moon.get('sign')
    prog_moon_degree = prog_moon.get('longitude', 0) % 30
    
    # Check if Moon is at critical degrees (0°, 15°, 29°)
    if prog_moon_degree < 1 or prog_moon_degree > 29:
        significant.append({
            'type': 'progressed_moon_sign_change',
            'planet': 'moon',
            'event': f'Progressed Moon entering/leaving {prog_moon_sign}',
            'significance': 'Major emotional shift, new 2.5-year chapter',
            'age': age
        })
    
    # Check progressed Sun (moves ~1° per year)
    prog_sun = progressed_planets.get('sun', {})
    prog_sun_degree = prog_sun.get('longitude', 0) % 30
    
    if prog_sun_degree < 1:
        significant.append({
            'type': 'progressed_sun_sign_change',
            'planet': 'sun',
            'event': f'Progressed Sun entering {prog_sun.get("sign")}',
            'significance': 'Major identity shift, new 30-year life chapter',
            'age': age
        })
    
    # Progressed New Moon (happens ~every 27-29 years)
    prog_sun_lon = prog_sun.get('longitude', 0)
    prog_moon_lon = prog_moon.get('longitude', 0)
    sun_moon_angle = abs((prog_moon_lon - prog_sun_lon) % 360)
    
    if sun_moon_angle < 3:  # Within 3° of New Moon
        significant.append({
            'type': 'progressed_new_moon',
            'event': 'Progressed New Moon',
            'significance': 'Major new beginning, ~27-29 year life cycle starting',
            'age': age
        })
    
    return significant


# Helper functions

def extract_progressed_planets(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract planet positions from progressed chart"""
    planets = {}
    planet_list = [
        'sun', 'moon', 'mercury', 'venus', 'mars',
        'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
    ]
    
    for planet_name in planet_list:
        planet_obj = getattr(chart, planet_name, None)
        if planet_obj:
            planets[planet_name] = {
                'longitude': planet_obj['position'],
                'sign': planet_obj['sign'],
                'house': planet_obj.get('house', 'Unknown'),
                'retrograde': planet_obj.get('retrograde', False)
            }
    
    return planets


def extract_houses(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract house cusps"""
    houses = {}
    
    for i in range(1, 13):
        house_obj = getattr(chart, f'house{i}', None)
        if house_obj:
            houses[str(i)] = {
                'cusp': house_obj['position'],
                'sign': house_obj['sign']
            }
    
    return houses


def get_sign_from_longitude(longitude: float) -> str:
    """Convert longitude to zodiac sign"""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30)
    return signs[sign_index % 12]


def get_moon_phase_name(phase_angle: float) -> str:
    """Get Moon phase name from angle"""
    if phase_angle < 45:
        return "New Moon"
    elif phase_angle < 90:
        return "Crescent"
    elif phase_angle < 135:
        return "First Quarter"
    elif phase_angle < 180:
        return "Gibbous"
    elif phase_angle < 225:
        return "Full Moon"
    elif phase_angle < 270:
        return "Disseminating"
    elif phase_angle < 315:
        return "Last Quarter"
    else:
        return "Balsamic"


def get_phase_change_significance(from_phase: str, to_phase: str) -> str:
    """Get significance of progressed Moon phase change"""
    phase_meanings = {
        'New Moon': 'New beginnings, planting seeds',
        'Crescent': 'Growth, emergence',
        'First Quarter': 'Crisis of action, decision time',
        'Gibbous': 'Development, refinement',
        'Full Moon': 'Culmination, achievement, illumination',
        'Disseminating': 'Sharing, teaching',
        'Last Quarter': 'Crisis of consciousness, letting go',
        'Balsamic': 'Release, preparation for new cycle'
    }
    
    return f"Entering {to_phase} phase: {phase_meanings.get(to_phase, 'Phase shift')}"


def get_progressed_aspect_interpretation(
    prog_planet: str,
    natal_planet: str,
    aspect: str
) -> str:
    """Get interpretation for progressed-to-natal aspect"""
    
    # Simplified interpretation
    harmonious = aspect in ['conjunction', 'sextile', 'trine']
    challenging = aspect in ['square', 'opposition']
    
    if harmonious:
        return (
            f"Progressed {prog_planet.title()} {aspect} natal {natal_planet.title()}: "
            f"Harmonious development of {prog_planet} themes in relation to natal {natal_planet}."
        )
    elif challenging:
        return (
            f"Progressed {prog_planet.title()} {aspect} natal {natal_planet.title()}: "
            f"Dynamic tension requiring growth in {prog_planet} expression "
            f"relative to natal {natal_planet}."
        )
    else:
        return f"Progressed {prog_planet.title()} {aspect} natal {natal_planet.title()}"


def generate_progressions_interpretation(
    progressed_planets: Dict[str, Any],
    age: float,
    significant_progressions: List[Dict[str, Any]]
) -> str:
    """Generate interpretation for progressions"""
    
    parts = []
    
    parts.append(f"SECONDARY PROGRESSIONS AT AGE {age:.1f}\n\n")
    
    # Progressed Sun
    prog_sun = progressed_planets.get('sun', {})
    parts.append(
        f"Progressed Sun in {prog_sun.get('sign', 'Unknown')}: "
        f"Your evolving identity and life direction now express through "
        f"{prog_sun.get('sign', 'Unknown')} qualities.\n\n"
    )
    
    # Progressed Moon
    prog_moon = progressed_planets.get('moon', {})
    parts.append(
        f"Progressed Moon in {prog_moon.get('sign', 'Unknown')}: "
        f"Your emotional focus for the next 2-3 years is colored by "
        f"{prog_moon.get('sign', 'Unknown')} themes.\n\n"
    )
    
    # Significant events
    if significant_progressions:
        parts.append("SIGNIFICANT PROGRESSIONS:\n")
        for sig in significant_progressions[:3]:
            parts.append(f"• {sig['event']}: {sig['significance']}\n")
    
    return ''.join(parts)


def generate_solar_arc_interpretation(
    solar_arc_planets: Dict[str, Any],
    solar_arc: float,
    age: float
) -> str:
    """Generate interpretation for solar arcs"""
    
    parts = []
    
    parts.append(f"SOLAR ARC DIRECTIONS AT AGE {age:.1f}\n\n")
    parts.append(f"Solar Arc Amount: {solar_arc:.2f}°\n\n")
    parts.append(
        "Solar arc directions show the timing of natal potential unfolding. "
        "When a solar arc planet aspects a natal planet or angle, "
        "significant life events occur.\n\n"
    )
    
    # List any planets that changed signs
    sign_changes = []
    for planet_name, planet_data in solar_arc_planets.items():
        if planet_data['natal_sign'] != planet_data['solar_arc_sign']:
            sign_changes.append(
                f"• {planet_name.title()} moved from "
                f"{planet_data['natal_sign']} to {planet_data['solar_arc_sign']}"
            )
    
    if sign_changes:
        parts.append("SOLAR ARC SIGN CHANGES:\n")
        parts.extend(sign_changes)
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    example_birth_data = {
        'name': 'Example Person',
        'birth_date': datetime(1990, 6, 15, 14, 30),
        'birth_place': 'Istanbul',
        'nation': 'TR',
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timezone': 'Europe/Istanbul'
    }
    
    # Calculate progressions for age 34
    progression_date = date(2024, 6, 15)
    
    progressions = calculate_secondary_progressions(
        example_birth_data,
        progression_date
    )
    
    print("Secondary Progressions:")
    print(f"Age: {progressions['age']}")
    print(f"Progressed Sun: {progressions['progressed_planets']['sun']['sign']}")
    print(f"Progressed Moon: {progressions['progressed_planets']['moon']['sign']}")
    
    # Solar arc
    solar_arc = calculate_solar_arc_directions(
        example_birth_data,
        progression_date
    )
    
    print(f"\nSolar Arc Amount: {solar_arc['solar_arc_amount']}°")
