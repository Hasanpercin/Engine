"""
Detailed retrograde calculations and analysis
Includes current retrogrades, upcoming retrogrades, and natal retrograde analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import swisseph as swe
from kerykeion import AstrologicalSubject
import logging

logger = logging.getLogger(__name__)


# Planet Swiss Ephemeris IDs
PLANET_IDS = {
    'mercury': swe.MERCURY,
    'venus': swe.VENUS,
    'mars': swe.MARS,
    'jupiter': swe.JUPITER,
    'saturn': swe.SATURN,
    'uranus': swe.URANUS,
    'neptune': swe.NEPTUNE,
    'pluto': swe.PLUTO
}

# Retrograde meanings by planet
RETROGRADE_MEANINGS = {
    'mercury': {
        'title': 'Mercury Retrograde',
        'themes': ['Communication', 'Technology', 'Travel', 'Contracts'],
        'advice': 'Double-check communications, backup data, avoid signing contracts',
        'frequency': '~3 times per year',
        'duration': '~3 weeks',
        'shadow_period': '2 weeks before and after'
    },
    'venus': {
        'title': 'Venus Retrograde',
        'themes': ['Relationships', 'Love', 'Money', 'Values', 'Beauty'],
        'advice': 'Review relationships, avoid major purchases, reflect on values',
        'frequency': '~18 months',
        'duration': '~6 weeks',
        'shadow_period': '2-3 weeks before and after'
    },
    'mars': {
        'title': 'Mars Retrograde',
        'themes': ['Action', 'Energy', 'Anger', 'Sexuality', 'Initiative'],
        'advice': 'Rethink strategies, manage anger, review fitness routines',
        'frequency': '~2 years',
        'duration': '~10 weeks',
        'shadow_period': '2-3 weeks before and after'
    },
    'jupiter': {
        'title': 'Jupiter Retrograde',
        'themes': ['Growth', 'Expansion', 'Philosophy', 'Higher Learning'],
        'advice': 'Review beliefs, reflect on growth, reassess goals',
        'frequency': 'Once per year',
        'duration': '~4 months',
        'shadow_period': '2-3 weeks before and after'
    },
    'saturn': {
        'title': 'Saturn Retrograde',
        'themes': ['Responsibility', 'Structure', 'Discipline', 'Authority'],
        'advice': 'Review commitments, reassess boundaries, work on self-discipline',
        'frequency': 'Once per year',
        'duration': '~4.5 months',
        'shadow_period': '2-3 weeks before and after'
    },
    'uranus': {
        'title': 'Uranus Retrograde',
        'themes': ['Revolution', 'Change', 'Innovation', 'Freedom'],
        'advice': 'Internal revolution, review need for freedom, unexpected insights',
        'frequency': 'Once per year',
        'duration': '~5 months',
        'shadow_period': '2-3 weeks before and after'
    },
    'neptune': {
        'title': 'Neptune Retrograde',
        'themes': ['Spirituality', 'Dreams', 'Illusions', 'Compassion'],
        'advice': 'Deepen spiritual practice, face illusions, review boundaries',
        'frequency': 'Once per year',
        'duration': '~5 months',
        'shadow_period': '2-3 weeks before and after'
    },
    'pluto': {
        'title': 'Pluto Retrograde',
        'themes': ['Transformation', 'Power', 'Control', 'Rebirth'],
        'advice': 'Deep psychological work, release control, embrace transformation',
        'frequency': 'Once per year',
        'duration': '~5-6 months',
        'shadow_period': '2-3 weeks before and after'
    }
}


def is_planet_retrograde(planet_id: int, julian_day: float) -> bool:
    """
    Check if a planet is retrograde at a given Julian Day
    
    Args:
        planet_id: Swiss Ephemeris planet ID
        julian_day: Julian Day number
        
    Returns:
        True if retrograde, False if direct
    """
    try:
        # Calculate planet position with speed
        pos, ret = swe.calc_ut(julian_day, planet_id, swe.FLG_SPEED)
        speed = pos[3]  # Longitude speed
        
        # Negative speed = retrograde
        return speed < 0
        
    except Exception as e:
        logger.error(f"Error checking retrograde status: {str(e)}")
        return False


def find_retrograde_periods(
    planet_name: str,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Find all retrograde periods for a planet within a date range
    
    Args:
        planet_name: Planet name (lowercase)
        start_date: Start of search period
        end_date: End of search period
        
    Returns:
        List of retrograde periods with start/end dates
    """
    try:
        planet_id = PLANET_IDS.get(planet_name.lower())
        if not planet_id:
            raise ValueError(f"Unknown planet: {planet_name}")
        
        periods = []
        current_date = start_date
        in_retrograde = False
        retrograde_start = None
        
        # Scan day by day
        while current_date <= end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
            is_retro = is_planet_retrograde(planet_id, jd)
            
            if is_retro and not in_retrograde:
                # Retrograde period starting
                retrograde_start = current_date
                in_retrograde = True
            elif not is_retro and in_retrograde:
                # Retrograde period ending
                periods.append({
                    'planet': planet_name,
                    'start_date': retrograde_start.isoformat(),
                    'end_date': current_date.isoformat(),
                    'duration_days': (current_date - retrograde_start).days
                })
                in_retrograde = False
                retrograde_start = None
            
            current_date += timedelta(days=1)
        
        # Handle ongoing retrograde at end of period
        if in_retrograde and retrograde_start:
            periods.append({
                'planet': planet_name,
                'start_date': retrograde_start.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - retrograde_start).days,
                'ongoing': True
            })
        
        return periods
        
    except Exception as e:
        logger.error(f"Error finding retrograde periods: {str(e)}")
        return []


def get_current_retrogrades(reference_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Get all planets currently in retrograde
    
    Args:
        reference_date: Date to check (default: today)
        
    Returns:
        List of currently retrograde planets with details
    """
    if not reference_date:
        reference_date = date.today()
    
    current_retrogrades = []
    
    for planet_name, planet_id in PLANET_IDS.items():
        jd = swe.julday(
            reference_date.year,
            reference_date.month,
            reference_date.day,
            12.0
        )
        
        if is_planet_retrograde(planet_id, jd):
            # Find when this retrograde started and will end
            periods = find_retrograde_periods(
                planet_name,
                reference_date - timedelta(days=200),  # Look back
                reference_date + timedelta(days=200)   # Look forward
            )
            
            # Find the period that includes reference_date
            current_period = None
            for period in periods:
                start = date.fromisoformat(period['start_date'])
                end = date.fromisoformat(period['end_date'])
                if start <= reference_date <= end:
                    current_period = period
                    break
            
            if current_period:
                meaning = RETROGRADE_MEANINGS[planet_name]
                current_retrogrades.append({
                    'planet': planet_name,
                    'start_date': current_period['start_date'],
                    'end_date': current_period['end_date'],
                    'days_remaining': (
                        date.fromisoformat(current_period['end_date']) - reference_date
                    ).days,
                    'meaning': meaning
                })
    
    return current_retrogrades


def get_upcoming_retrogrades(
    start_date: Optional[date] = None,
    months_ahead: int = 6
) -> List[Dict[str, Any]]:
    """
    Get upcoming retrograde periods for all planets
    
    Args:
        start_date: Start date (default: today)
        months_ahead: How many months to look ahead
        
    Returns:
        List of upcoming retrograde periods
    """
    if not start_date:
        start_date = date.today()
    
    end_date = start_date + timedelta(days=30 * months_ahead)
    
    all_upcoming = []
    
    for planet_name in PLANET_IDS.keys():
        periods = find_retrograde_periods(planet_name, start_date, end_date)
        
        for period in periods:
            meaning = RETROGRADE_MEANINGS[planet_name]
            
            # Calculate shadow periods
            start = date.fromisoformat(period['start_date'])
            end = date.fromisoformat(period['end_date'])
            pre_shadow = start - timedelta(days=14)
            post_shadow = end + timedelta(days=14)
            
            all_upcoming.append({
                'planet': planet_name,
                'retrograde_start': period['start_date'],
                'retrograde_end': period['end_date'],
                'duration_days': period['duration_days'],
                'pre_shadow_start': pre_shadow.isoformat(),
                'post_shadow_end': post_shadow.isoformat(),
                'meaning': meaning,
                'days_until_start': (start - start_date).days
            })
    
    # Sort by start date
    all_upcoming.sort(key=lambda x: x['retrograde_start'])
    
    return all_upcoming


def analyze_natal_retrogrades(natal_chart: AstrologicalSubject) -> Dict[str, Any]:
    """
    Analyze retrograde planets in natal chart
    
    Natal retrograde planets suggest internalized or karmic themes
    
    Args:
        natal_chart: Natal chart object
        
    Returns:
        Analysis of natal retrograde planets
    """
    try:
        retrograde_planets = []
        
        planet_list = [
            'mercury', 'venus', 'mars', 'jupiter', 
            'saturn', 'uranus', 'neptune', 'pluto'
        ]
        
        for planet_name in planet_list:
            planet_obj = getattr(natal_chart, planet_name, None)
            if planet_obj and planet_obj.get('retrograde', False):
                retrograde_planets.append({
                    'planet': planet_name,
                    'sign': planet_obj.get('sign'),
                    'house': planet_obj.get('house'),
                    'longitude': planet_obj.get('position'),
                    'interpretation': get_natal_retrograde_interpretation(
                        planet_name,
                        planet_obj.get('house')
                    )
                })
        
        # Calculate retrograde count significance
        retrograde_count = len(retrograde_planets)
        significance = get_retrograde_count_significance(retrograde_count)
        
        return {
            'retrograde_count': retrograde_count,
            'retrograde_planets': retrograde_planets,
            'significance': significance,
            'overall_interpretation': generate_natal_retrograde_overview(
                retrograde_planets, significance
            )
        }
        
    except Exception as e:
        logger.error(f"Error analyzing natal retrogrades: {str(e)}")
        raise


def get_natal_retrograde_interpretation(planet_name: str, house: int) -> str:
    """Get interpretation for a natal retrograde planet"""
    
    interpretations = {
        'mercury': (
            f"Natal Mercury retrograde in house {house} suggests internalized "
            "communication. You may think deeply before speaking, have a unique "
            "learning style, or need to revisit educational themes."
        ),
        'venus': (
            f"Natal Venus retrograde in house {house} indicates internalized "
            "values and love. You may have unique relationship patterns, need to "
            "rediscover self-worth, or have karmic relationship lessons."
        ),
        'mars': (
            f"Natal Mars retrograde in house {house} suggests internalized action. "
            "You may have passive-aggressive tendencies, need to learn healthy "
            "anger expression, or have unique ways of pursuing desires."
        ),
        'jupiter': (
            f"Natal Jupiter retrograde in house {house} indicates internal growth. "
            "You develop your own philosophy, may question authority, and find "
            "expansion through introspection rather than external adventures."
        ),
        'saturn': (
            f"Natal Saturn retrograde in house {house} suggests karmic lessons "
            "around responsibility. You may have internalized authority issues, "
            "need to develop self-discipline, or work through past-life themes."
        ),
        'uranus': (
            f"Natal Uranus retrograde in house {house} indicates internalized "
            "rebellion. Your revolutionary nature is more internal, leading to "
            "unique insights and sudden inner revelations."
        ),
        'neptune': (
            f"Natal Neptune retrograde in house {house} suggests internalized "
            "spirituality. You have a unique spiritual path, may see through "
            "illusions easily, and develop deep compassion through introspection."
        ),
        'pluto': (
            f"Natal Pluto retrograde in house {house} indicates internalized "
            "power and transformation. You undergo deep psychological processes "
            "and have intense inner transformations."
        )
    }
    
    return interpretations.get(planet_name, "Natal retrograde planet.")


def get_retrograde_count_significance(count: int) -> Dict[str, Any]:
    """Interpret the significance of having multiple natal retrogrades"""
    
    if count == 0:
        return {
            'level': 'none',
            'meaning': 'No natal retrogrades - extroverted expression'
        }
    elif count <= 2:
        return {
            'level': 'low',
            'meaning': 'Few retrogrades - mostly outward expression with some introspection'
        }
    elif count <= 4:
        return {
            'level': 'moderate',
            'meaning': 'Moderate retrogrades - balanced between inner and outer worlds'
        }
    else:
        return {
            'level': 'high',
            'meaning': 'Many retrogrades - highly introspective, karmic soul, old soul qualities'
        }


def generate_natal_retrograde_overview(
    retrograde_planets: List[Dict[str, Any]],
    significance: Dict[str, Any]
) -> str:
    """Generate overall interpretation of natal retrogrades"""
    
    if not retrograde_planets:
        return (
            "You have no natal retrograde planets. This suggests a more "
            "extroverted expression of planetary energies, with lessons "
            "learned through external experiences."
        )
    
    planet_names = [p['planet'].title() for p in retrograde_planets]
    
    overview = (
        f"You were born with {len(retrograde_planets)} retrograde planet(s): "
        f"{', '.join(planet_names)}. {significance['meaning']}.\n\n"
        "Natal retrograde planets suggest:\n"
        "• Internalized expression of these planetary energies\n"
        "• Karmic lessons or unfinished business from past lives\n"
        "• Need to revisit and rework themes of these planets\n"
        "• Unique, non-traditional approach to these life areas\n\n"
        "These planets often become areas of deep wisdom later in life, "
        "as you master their internalized expressions."
    )
    
    return overview


def analyze_retrograde_impact_on_natal(
    natal_chart: AstrologicalSubject,
    current_retrograde_planet: str,
    current_retrograde_position: float
) -> Dict[str, Any]:
    """
    Analyze how a current retrograde impacts the natal chart
    
    Args:
        natal_chart: Natal chart
        current_retrograde_planet: Name of currently retrograde planet
        current_retrograde_position: Current position of retrograde planet
        
    Returns:
        Impact analysis
    """
    try:
        # Find natal position of this planet
        planet_obj = getattr(natal_chart, current_retrograde_planet.lower(), None)
        if not planet_obj:
            return {'impact': 'none', 'reason': 'Planet not found in natal chart'}
        
        natal_position = planet_obj['position']
        natal_house = planet_obj.get('house')
        
        # Check if retrograde is transiting natal planet
        orb = abs((current_retrograde_position - natal_position + 180) % 360 - 180)
        
        impact = {
            'planet': current_retrograde_planet,
            'natal_position': natal_position,
            'current_position': current_retrograde_position,
            'orb': round(orb, 2),
            'natal_house': natal_house
        }
        
        if orb <= 3:
            impact['intensity'] = 'strong'
            impact['message'] = (
                f"The current {current_retrograde_planet} retrograde is "
                f"conjunct your natal {current_retrograde_planet}! This is a "
                "powerful time for review and revision of this planet's themes."
            )
        elif orb <= 8:
            impact['intensity'] = 'moderate'
            impact['message'] = (
                f"The current {current_retrograde_planet} retrograde is "
                f"within orb of your natal {current_retrograde_planet}. "
                "You'll feel this retrograde more personally."
            )
        else:
            impact['intensity'] = 'general'
            impact['message'] = (
                f"The current {current_retrograde_planet} retrograde will "
                "affect you in more general ways through its house position."
            )
        
        return impact
        
    except Exception as e:
        logger.error(f"Error analyzing retrograde impact: {str(e)}")
        return {'impact': 'error', 'message': str(e)}


# Example usage
if __name__ == "__main__":
    # Current retrogrades
    current = get_current_retrogrades()
    print("Currently Retrograde:")
    for r in current:
        print(f"  {r['planet'].title()}: {r['start_date']} to {r['end_date']}")
        print(f"    Days remaining: {r['days_remaining']}")
        print(f"    Themes: {', '.join(r['meaning']['themes'])}")
        print()
    
    # Upcoming retrogrades
    upcoming = get_upcoming_retrogrades(months_ahead=3)
    print("\nUpcoming Retrogrades (next 3 months):")
    for r in upcoming[:5]:  # Show first 5
        print(f"  {r['planet'].title()}: {r['retrograde_start']} to {r['retrograde_end']}")
        print(f"    Starts in {r['days_until_start']} days")
        print()
