"""
Secondary Progressions and Solar Arc Directions - COMPLETE VERSION
Symbolic timing techniques: 1 day = 1 year
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from kerykeion import AstrologicalSubject
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def calculate_secondary_progressions(
    natal_data: Dict[str, Any],
    progressed_date: date,
    location: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate Secondary Progressions
    
    Method: 1 day after birth = 1 year of life
    
    Args:
        natal_data: Birth data
        progressed_date: Date to progress to
        location: Location (uses birth location by default)
        
    Returns:
        Progressed chart data
    """
    try:
        logger.info(f"Calculating secondary progressions for {progressed_date}")
        
        birth_date = natal_data['birth_date']
        birth_time = natal_data.get('birth_time', datetime.min.time())
        
        # Calculate age in years
        age = (progressed_date - birth_date).days / 365.25
        
        # Progress date: birth_date + age in days
        days_to_add = int(age)
        progressed_birth_date = birth_date + timedelta(days=days_to_add)
        
        # Use birth location if no location specified
        if location is None:
            location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Create progressed chart
        progressed_chart = AstrologicalSubject(
            name=f"Progressed {progressed_date.isoformat()}",
            year=progressed_birth_date.year,
            month=progressed_birth_date.month,
            day=progressed_birth_date.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            city=location['city'],
            lat=location['latitude'],
            lng=location['longitude'],
            tz_str=location['timezone']
        )
        
        # Extract progressed planets
        progressed_planets = extract_planets(progressed_chart)
        progressed_houses = extract_houses(progressed_chart)
        
        # Calculate progressed-to-natal aspects
        natal_planets = natal_data.get('planets', {})
        progressed_aspects = calculate_progressed_to_natal_aspects(
            progressed_planets,
            natal_planets
        )
        
        # Track progressed Moon (moves ~1° per month, through all signs in ~28 years)
        progressed_moon = progressed_planets.get('moon', {})
        progressed_moon_phase = calculate_progressed_moon_phase(
            progressed_planets.get('sun', {}).get('longitude', 0),
            progressed_moon.get('longitude', 0)
        )
        
        # Identify significant progressions
        significant_progressions = identify_significant_progressions(
            progressed_planets,
            natal_planets,
            progressed_aspects
        )
        
        # Generate interpretation
        interpretation = generate_progression_interpretation(
            progressed_date,
            age,
            progressed_moon,
            progressed_moon_phase,
            significant_progressions
        )
        
        return {
            'method': 'Secondary Progressions',
            'progressed_date': progressed_date.isoformat(),
            'age': round(age, 2),
            'progressed_birth_date': progressed_birth_date.isoformat(),
            'progressed_planets': progressed_planets,
            'progressed_houses': progressed_houses,
            'progressed_moon_phase': progressed_moon_phase,
            'progressed_to_natal_aspects': progressed_aspects,
            'significant_progressions': significant_progressions,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Secondary progressions calculation failed: {str(e)}")
        raise


def calculate_solar_arc_directions(
    natal_data: Dict[str, Any],
    target_date: date
) -> Dict[str, Any]:
    """
    Calculate Solar Arc Directions
    
    Method: Sun progresses ~1° per year, all planets move by the same amount
    
    Args:
        natal_data: Birth data
        target_date: Date to calculate for
        
    Returns:
        Solar arc directed chart
    """
    try:
        logger.info(f"Calculating solar arc directions for {target_date}")
        
        birth_date = natal_data['birth_date']
        
        # Calculate age in years
        age = (target_date - birth_date).days / 365.25
        
        # Solar arc rate: approximately 1° per year
        solar_arc = age * 0.9856  # More accurate: ~0.9856° per year
        
        # Get natal planets
        natal_planets = natal_data.get('planets', {})
        
        # Direct all planets by solar arc
        directed_planets = {}
        for planet_name, planet_data in natal_planets.items():
            natal_lon = planet_data.get('longitude', 0)
            directed_lon = (natal_lon + solar_arc) % 360
            
            directed_planets[planet_name] = {
                'natal_longitude': natal_lon,
                'directed_longitude': directed_lon,
                'solar_arc': round(solar_arc, 2),
                'sign': get_sign_from_longitude(directed_lon),
                'degree': directed_lon % 30
            }
        
        # Calculate directed-to-natal aspects
        directed_aspects = calculate_directed_to_natal_aspects(
            directed_planets,
            natal_planets,
            solar_arc
        )
        
        # Identify significant directions
        significant_directions = identify_significant_directions(directed_aspects)
        
        # Generate interpretation
        interpretation = generate_solar_arc_interpretation(
            target_date,
            age,
            solar_arc,
            significant_directions
        )
        
        return {
            'method': 'Solar Arc Directions',
            'target_date': target_date.isoformat(),
            'age': round(age, 2),
            'solar_arc': round(solar_arc, 2),
            'directed_planets': directed_planets,
            'directed_to_natal_aspects': directed_aspects,
            'significant_directions': significant_directions,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Solar arc directions calculation failed: {str(e)}")
        raise


def track_progressed_moon_phases(
    natal_data: Dict[str, Any],
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Track progressed Moon through phases over time
    
    Progressed Moon completes a cycle through all signs in ~28 years
    
    Args:
        natal_data: Birth data
        start_date: Start of tracking period
        end_date: End of tracking period
        
    Returns:
        List of progressed Moon positions and phases
    """
    moon_tracking = []
    
    # Check monthly
    current_date = start_date
    while current_date <= end_date:
        progressions = calculate_secondary_progressions(natal_data, current_date)
        
        progressed_moon = progressions['progressed_planets'].get('moon', {})
        moon_phase = progressions['progressed_moon_phase']
        
        moon_tracking.append({
            'date': current_date.isoformat(),
            'progressed_moon_sign': progressed_moon.get('sign', 'Unknown'),
            'progressed_moon_longitude': progressed_moon.get('longitude', 0),
            'moon_phase': moon_phase['phase_name'],
            'illumination': moon_phase['illumination']
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return moon_tracking


def calculate_progressed_to_natal_aspects(
    progressed_planets: Dict[str, Any],
    natal_planets: Dict[str, Any],
    orb: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between progressed and natal planets
    
    Progressed aspects use tight orbs (1°)
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
        prog_lon = prog_data.get('longitude', 0)
        
        for natal_name, natal_data in natal_planets.items():
            natal_lon = natal_data.get('longitude', 0)
            
            # Calculate angle
            angle = abs(prog_lon - natal_lon)
            if angle > 180:
                angle = 360 - angle
            
            # Check for aspects
            for aspect_name, aspect_angle in aspect_angles.items():
                diff = abs(angle - aspect_angle)
                
                if diff <= orb:
                    aspects.append({
                        'progressed_planet': prog_name,
                        'natal_planet': natal_name,
                        'aspect': aspect_name,
                        'orb': round(diff, 2),
                        'exact': diff < 0.1,
                        'description': f"Progressed {prog_name.title()} {aspect_name} Natal {natal_name.title()}"
                    })
    
    return sorted(aspects, key=lambda x: x['orb'])


def calculate_directed_to_natal_aspects(
    directed_planets: Dict[str, Any],
    natal_planets: Dict[str, Any],
    solar_arc: float
) -> List[Dict[str, Any]]:
    """Calculate aspects between solar arc directed and natal planets"""
    aspects = []
    
    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for dir_name, dir_data in directed_planets.items():
        dir_lon = dir_data.get('directed_longitude', 0)
        
        for natal_name, natal_data in natal_planets.items():
            natal_lon = natal_data.get('longitude', 0)
            
            angle = abs(dir_lon - natal_lon)
            if angle > 180:
                angle = 360 - angle
            
            for aspect_name, aspect_angle in aspect_angles.items():
                diff = abs(angle - aspect_angle)
                
                if diff <= 1.0:
                    aspects.append({
                        'directed_planet': dir_name,
                        'natal_planet': natal_name,
                        'aspect': aspect_name,
                        'orb': round(diff, 2),
                        'exact': diff < 0.1,
                        'solar_arc': round(solar_arc, 2),
                        'description': f"Directed {dir_name.title()} {aspect_name} Natal {natal_name.title()}"
                    })
    
    return sorted(aspects, key=lambda x: x['orb'])


def calculate_progressed_moon_phase(sun_lon: float, moon_lon: float) -> Dict[str, Any]:
    """Calculate progressed Moon phase"""
    phase_angle = (moon_lon - sun_lon) % 360
    
    if phase_angle < 45:
        phase = 'New Moon'
    elif phase_angle < 90:
        phase = 'Waxing Crescent'
    elif phase_angle < 135:
        phase = 'First Quarter'
    elif phase_angle < 180:
        phase = 'Waxing Gibbous'
    elif phase_angle < 225:
        phase = 'Full Moon'
    elif phase_angle < 270:
        phase = 'Waning Gibbous'
    elif phase_angle < 315:
        phase = 'Last Quarter'
    else:
        phase = 'Waning Crescent'
    
    illumination = 50 * (1 - abs(phase_angle - 180) / 180)
    
    return {
        'phase_name': phase,
        'phase_angle': round(phase_angle, 2),
        'illumination': round(illumination, 1)
    }


def identify_significant_progressions(
    progressed_planets: Dict[str, Any],
    natal_planets: Dict[str, Any],
    aspects: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Identify most significant progressions"""
    significant = []
    
    # Exact aspects are most significant
    exact_aspects = [a for a in aspects if a['exact']]
    
    for aspect in exact_aspects:
        significant.append({
            **aspect,
            'significance': 'high',
            'reason': 'Exact progression'
        })
    
    # Progressed Moon changing signs
    prog_moon = progressed_planets.get('moon', {})
    prog_moon_degree = prog_moon.get('degree', 0)
    
    if prog_moon_degree < 1:  # Just entered new sign
        significant.append({
            'type': 'moon_sign_change',
            'new_sign': prog_moon.get('sign', 'Unknown'),
            'significance': 'medium',
            'reason': 'Progressed Moon changing signs'
        })
    
    return significant


def identify_significant_directions(aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify most significant solar arc directions"""
    significant = []
    
    # Exact aspects
    exact = [a for a in aspects if a['exact']]
    
    for aspect in exact:
        significant.append({
            **aspect,
            'significance': 'high'
        })
    
    # Personal planets (Sun, Moon, Mercury, Venus, Mars) are more significant
    personal_planets = ['sun', 'moon', 'mercury', 'venus', 'mars']
    
    personal_aspects = [
        a for a in aspects 
        if a['directed_planet'] in personal_planets or a['natal_planet'] in personal_planets
    ]
    
    for aspect in personal_aspects[:5]:  # Top 5
        if aspect not in significant:
            significant.append({
                **aspect,
                'significance': 'medium'
            })
    
    return significant


def extract_planets(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract planet positions"""
    planets = {}
    planet_list = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']
    
    for planet_name in planet_list:
        planet_obj = getattr(chart, planet_name, None)
        if planet_obj:
            planets[planet_name] = {
                'longitude': planet_obj['position'],
                'sign': planet_obj['sign'],
                'degree': planet_obj['position'] % 30
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
    """Get zodiac sign from longitude"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]


def generate_progression_interpretation(
    progressed_date: date,
    age: float,
    progressed_moon: Dict[str, Any],
    moon_phase: Dict[str, Any],
    significant: List[Dict[str, Any]]
) -> str:
    """Generate progressions interpretation"""
    
    interpretation = f"# Secondary Progressions - {progressed_date.isoformat()}\n\n"
    interpretation += f"Age: {age:.1f} years\n\n"
    
    interpretation += f"## Progressed Moon\n"
    interpretation += f"Sign: {progressed_moon.get('sign', 'Unknown')}\n"
    interpretation += f"Phase: {moon_phase['phase_name']} ({moon_phase['illumination']:.1f}% illuminated)\n\n"
    
    if significant:
        interpretation += "## Significant Progressions:\n"
        for prog in significant[:5]:
            interpretation += f"- {prog.get('description', prog.get('reason', 'Progression'))}\n"
    
    return interpretation


def generate_solar_arc_interpretation(
    target_date: date,
    age: float,
    solar_arc: float,
    significant: List[Dict[str, Any]]
) -> str:
    """Generate solar arc interpretation"""
    
    interpretation = f"# Solar Arc Directions - {target_date.isoformat()}\n\n"
    interpretation += f"Age: {age:.1f} years\n"
    interpretation += f"Solar Arc: {solar_arc:.2f}°\n\n"
    
    if significant:
        interpretation += "## Significant Directions:\n"
        for direction in significant[:5]:
            interpretation += f"- {direction['description']}\n"
    
    return interpretation


# Example usage
if __name__ == "__main__":
    from datetime import date, time
    
    natal_data = {
        'birth_date': date(1990, 5, 15),
        'birth_time': time(14, 30),
        'latitude': 41.0082,
        'longitude': 28.9784,
        'planets': {
            'sun': {'longitude': 54.2, 'sign': 'Taurus'},
            'moon': {'longitude': 120.5, 'sign': 'Leo'},
            'mercury': {'longitude': 60.8, 'sign': 'Gemini'}
        }
    }
    
    target = date(2025, 10, 8)
    
    # Secondary Progressions
    progressions = calculate_secondary_progressions(natal_data, target)
    print(progressions['interpretation'])
    
    print("\n" + "="*50 + "\n")
    
    # Solar Arc Directions
    solar_arc = calculate_solar_arc_directions(natal_data, target)
    print(solar_arc['interpretation'])
