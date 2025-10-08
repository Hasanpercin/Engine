"""
Transit calculations - COMPLETE VERSION
Tracks planetary movements and their aspects to natal chart
"""

from kerykeion import AstrologicalSubject
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def calculate_daily_transits(
    natal_data: Dict[str, Any],
    transit_date: date,
    location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate daily transits with aspects to natal chart
    
    Args:
        natal_data: Birth data with planets and houses
        transit_date: Date for transit calculation
        location: Optional location (defaults to birth location)
        
    Returns:
        Transit data with aspects to natal chart
    """
    try:
        logger.info(f"Calculating transits for {transit_date}")
        
        # Use birth location if not specified
        if location is None:
            location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'nation': natal_data.get('nation', 'TR'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Create transit chart
        transit_subject = AstrologicalSubject(
            name=f"Transit {transit_date.isoformat()}",
            year=transit_date.year,
            month=transit_date.month,
            day=transit_date.day,
            hour=12,
            minute=0,
            city=location.get('city', 'Istanbul'),
            nation=location.get('nation', 'TR'),
            lat=location.get('latitude', 41.0082),
            lng=location.get('longitude', 28.9784),
            tz_str=location.get('timezone', 'Europe/Istanbul')
        )
        
        # Extract transiting planets
        transiting_planets = extract_transiting_planets(transit_subject)
        
        # Extract natal planets from natal_data
        natal_planets = natal_data.get('planets', {})
        natal_houses = natal_data.get('houses', {})
        
        # Calculate aspects to natal chart
        transit_aspects = calculate_transit_aspects(
            transiting_planets,
            natal_planets
        )
        
        # Determine house positions for transiting planets
        transit_houses = calculate_transit_house_positions(
            transiting_planets,
            natal_houses
        )
        
        # Identify significant transits
        significant_transits = identify_significant_transits(
            transit_aspects,
            transit_houses
        )
        
        # Generate interpretations
        interpretations = generate_transit_interpretations(
            significant_transits,
            transit_aspects
        )
        
        return {
            'date': transit_date.isoformat(),
            'transiting_planets': transiting_planets,
            'transit_houses': transit_houses,
            'aspects_to_natal': transit_aspects,
            'significant_transits': significant_transits,
            'interpretations': interpretations,
            'summary': generate_daily_summary(significant_transits)
        }
        
    except Exception as e:
        logger.error(f"Transit calculation failed: {str(e)}")
        raise


def calculate_monthly_transits(
    natal_data: Dict[str, Any],
    year: int,
    month: int,
    location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate transits for an entire month
    
    Returns:
        Monthly transit overview with daily breakdowns
    """
    try:
        logger.info(f"Calculating monthly transits for {year}-{month:02d}")
        
        # Determine number of days in month
        if month == 12:
            last_day = 31
        else:
            next_month = date(year, month + 1, 1)
            last_day = (next_month - timedelta(days=1)).day
        
        # Calculate transits for each day
        daily_transits = []
        for day in range(1, last_day + 1):
            transit_date = date(year, month, day)
            day_transits = calculate_daily_transits(
                natal_data,
                transit_date,
                location
            )
            daily_transits.append(day_transits)
        
        # Identify month themes
        month_themes = identify_monthly_themes(daily_transits)
        
        # Find peak days
        peak_days = find_peak_transit_days(daily_transits)
        
        return {
            'year': year,
            'month': month,
            'daily_transits': daily_transits,
            'monthly_themes': month_themes,
            'peak_days': peak_days,
            'summary': generate_monthly_summary(month_themes, peak_days)
        }
        
    except Exception as e:
        logger.error(f"Monthly transit calculation failed: {str(e)}")
        raise


def extract_transiting_planets(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract transiting planet positions"""
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
                'degree': planet_obj['position'] % 30,
                'retrograde': planet_obj.get('retrograde', False),
                'speed': planet_obj.get('speed', 0)
            }
    
    return planets


def calculate_transit_aspects(
    transiting_planets: Dict[str, Any],
    natal_planets: Dict[str, Any],
    orb: float = 8.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between transiting and natal planets
    
    Args:
        transiting_planets: Current transiting positions
        natal_planets: Natal planet positions
        orb: Aspect orb in degrees
        
    Returns:
        List of transit aspects
    """
    aspects = []
    
    # Major aspects
    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for transit_name, transit_data in transiting_planets.items():
        transit_lon = transit_data['longitude']
        
        for natal_name, natal_data in natal_planets.items():
            natal_lon = natal_data.get('longitude', 0)
            
            # Calculate angle between planets
            angle = abs(transit_lon - natal_lon)
            if angle > 180:
                angle = 360 - angle
            
            # Check for aspects
            for aspect_name, aspect_angle in aspect_angles.items():
                diff = abs(angle - aspect_angle)
                
                if diff <= orb:
                    aspects.append({
                        'transiting_planet': transit_name,
                        'natal_planet': natal_name,
                        'aspect': aspect_name,
                        'orb': round(diff, 2),
                        'exact': diff < 1.0,
                        'transiting_sign': transit_data['sign'],
                        'natal_sign': natal_data.get('sign', 'Unknown'),
                        'description': f"{transit_name.title()} {aspect_name} Natal {natal_name.title()}"
                    })
    
    return sorted(aspects, key=lambda x: x['orb'])


def calculate_transit_house_positions(
    transiting_planets: Dict[str, Any],
    natal_houses: Dict[str, Any]
) -> Dict[str, int]:
    """
    Determine which natal house each transiting planet is in
    
    Returns:
        Dict mapping planet names to house numbers
    """
    transit_houses = {}
    
    for planet_name, planet_data in transiting_planets.items():
        planet_lon = planet_data['longitude']
        
        # Find which house this planet is in
        house_num = determine_house(planet_lon, natal_houses)
        transit_houses[planet_name] = house_num
    
    return transit_houses


def determine_house(longitude: float, houses: Dict[str, Any]) -> int:
    """Determine which house a longitude falls in"""
    # Simplified house calculation
    # In reality, should use proper house cusp calculations
    
    for house_num in range(1, 13):
        house_data = houses.get(str(house_num), {})
        next_house = houses.get(str((house_num % 12) + 1), {})
        
        cusp = house_data.get('cusp', 0)
        next_cusp = next_house.get('cusp', 0)
        
        if next_cusp < cusp:  # House crosses 0° Aries
            if longitude >= cusp or longitude < next_cusp:
                return house_num
        else:
            if cusp <= longitude < next_cusp:
                return house_num
    
    return 1  # Default to 1st house


def identify_significant_transits(
    aspects: List[Dict[str, Any]],
    transit_houses: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Identify the most significant transits
    
    Criteria:
    - Exact aspects (orb < 1°)
    - Outer planet transits (Jupiter, Saturn, Uranus, Neptune, Pluto)
    - Angular house transits (1, 4, 7, 10)
    - Multiple aspects to same planet
    """
    significant = []
    
    # Outer planets
    outer_planets = ['jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    
    # Angular houses
    angular_houses = [1, 4, 7, 10]
    
    # Check aspects
    for aspect in aspects:
        transit_planet = aspect['transiting_planet']
        significance_score = 0
        reasons = []
        
        # Exact aspect
        if aspect['exact']:
            significance_score += 3
            reasons.append('Exact aspect')
        
        # Outer planet
        if transit_planet in outer_planets:
            significance_score += 2
            reasons.append(f'{transit_planet.title()} transit')
        
        # Challenging aspect
        if aspect['aspect'] in ['square', 'opposition']:
            significance_score += 1
            reasons.append(f'{aspect["aspect"].title()} aspect')
        
        # Harmonious aspect
        if aspect['aspect'] in ['trine', 'sextile']:
            significance_score += 1
            reasons.append(f'{aspect["aspect"].title()} aspect')
        
        if significance_score >= 2:
            significant.append({
                **aspect,
                'significance_score': significance_score,
                'reasons': reasons
            })
    
    # Check house positions
    for planet, house in transit_houses.items():
        if house in angular_houses and planet in outer_planets:
            significant.append({
                'type': 'house_transit',
                'planet': planet,
                'house': house,
                'significance_score': 2,
                'reasons': [f'{planet.title()} in {house}th house']
            })
    
    return sorted(significant, key=lambda x: x['significance_score'], reverse=True)


def generate_transit_interpretations(
    significant_transits: List[Dict[str, Any]],
    all_aspects: List[Dict[str, Any]]
) -> List[str]:
    """Generate human-readable interpretations"""
    interpretations = []
    
    for transit in significant_transits[:5]:  # Top 5 most significant
        if transit.get('type') == 'house_transit':
            interpretation = interpret_house_transit(transit)
        else:
            interpretation = interpret_aspect_transit(transit)
        
        if interpretation:
            interpretations.append(interpretation)
    
    return interpretations


def interpret_aspect_transit(aspect: Dict[str, Any]) -> str:
    """Interpret a transit aspect"""
    transit_planet = aspect['transiting_planet'].title()
    natal_planet = aspect['natal_planet'].title()
    aspect_type = aspect['aspect']
    
    templates = {
        'conjunction': f"{transit_planet} conjunct {natal_planet}: Fusion of energies, new beginnings",
        'sextile': f"{transit_planet} sextile {natal_planet}: Opportunities, easy flow",
        'square': f"{transit_planet} square {natal_planet}: Tension, growth through challenge",
        'trine': f"{transit_planet} trine {natal_planet}: Harmony, natural talents flow",
        'opposition': f"{transit_planet} opposite {natal_planet}: Awareness, balancing act"
    }
    
    return templates.get(aspect_type, f"{transit_planet} {aspect_type} {natal_planet}")


def interpret_house_transit(transit: Dict[str, Any]) -> str:
    """Interpret a house transit"""
    planet = transit['planet'].title()
    house = transit['house']
    
    house_meanings = {
        1: "Self, identity, appearance",
        2: "Resources, values, self-worth",
        3: "Communication, siblings, short trips",
        4: "Home, family, roots",
        5: "Creativity, romance, children",
        6: "Work, health, daily routines",
        7: "Partnerships, relationships, others",
        8: "Transformation, shared resources, intimacy",
        9: "Philosophy, travel, higher learning",
        10: "Career, public life, reputation",
        11: "Friends, groups, aspirations",
        12: "Spirituality, unconscious, solitude"
    }
    
    return f"{planet} transiting {house}th house: Focus on {house_meanings.get(house, 'life themes')}"


def generate_daily_summary(significant_transits: List[Dict[str, Any]]) -> str:
    """Generate a brief daily summary"""
    if not significant_transits:
        return "Quiet day astrologically - focus on routine matters"
    
    top_transit = significant_transits[0]
    
    if top_transit.get('type') == 'house_transit':
        return f"Key focus: {top_transit['planet'].title()} energy in {top_transit['house']}th house"
    else:
        return f"Key aspect: {top_transit['description']}"


def identify_monthly_themes(daily_transits: List[Dict[str, Any]]) -> List[str]:
    """Identify recurring themes throughout the month"""
    themes = []
    
    # Count planet/house combinations
    house_counts = {}
    aspect_counts = {}
    
    for day in daily_transits:
        for transit in day.get('significant_transits', []):
            if transit.get('type') == 'house_transit':
                key = f"{transit['planet']}_house_{transit['house']}"
                house_counts[key] = house_counts.get(key, 0) + 1
            else:
                key = f"{transit['transiting_planet']}_{transit['aspect']}_{transit['natal_planet']}"
                aspect_counts[key] = aspect_counts.get(key, 0) + 1
    
    # Find recurring patterns
    for key, count in house_counts.items():
        if count >= 7:  # Present for at least a week
            themes.append(f"Extended {key.replace('_', ' ')} influence")
    
    return themes


def find_peak_transit_days(daily_transits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find days with most significant activity"""
    peak_days = []
    
    for day in daily_transits:
        significant = day.get('significant_transits', [])
        if len(significant) >= 3:  # 3+ significant transits
            total_score = sum(t.get('significance_score', 0) for t in significant)
            peak_days.append({
                'date': day['date'],
                'transit_count': len(significant),
                'total_score': total_score,
                'summary': day['summary']
            })
    
    return sorted(peak_days, key=lambda x: x['total_score'], reverse=True)[:5]


def generate_monthly_summary(
    themes: List[str],
    peak_days: List[Dict[str, Any]]
) -> str:
    """Generate monthly overview"""
    summary = "Monthly Transit Overview:\n\n"
    
    if themes:
        summary += "Key Themes:\n"
        for theme in themes:
            summary += f"• {theme}\n"
        summary += "\n"
    
    if peak_days:
        summary += "Peak Activity Days:\n"
        for peak in peak_days[:3]:
            summary += f"• {peak['date']}: {peak['summary']}\n"
    
    return summary


def calculate_aspect(lon1: float, lon2: float, orb: float = 8.0) -> Optional[Tuple[str, float]]:
    """
    Calculate aspect between two longitude positions
    
    Returns:
        (aspect_name, orb) or None if no aspect
    """
    angle = abs(lon1 - lon2)
    if angle > 180:
        angle = 360 - angle
    
    aspects = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for aspect_name, aspect_angle in aspects.items():
        diff = abs(angle - aspect_angle)
        if diff <= orb:
            return (aspect_name, diff)
    
    return None


# Example usage
if __name__ == "__main__":
    # Sample natal data
    natal_data = {
        'planets': {
            'sun': {'longitude': 120.5, 'sign': 'Leo'},
            'moon': {'longitude': 45.2, 'sign': 'Taurus'},
            'mercury': {'longitude': 110.8, 'sign': 'Cancer'}
        },
        'houses': {
            '1': {'cusp': 0},
            '2': {'cusp': 30},
            # ... etc
        }
    }
    
    # Calculate today's transits
    today = date.today()
    transits = calculate_daily_transits(natal_data, today)
    
    print(f"Transits for {today}:")
    print(f"Significant transits: {len(transits['significant_transits'])}")
    print(f"Summary: {transits['summary']}")
