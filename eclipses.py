"""
Eclipse calculations and data retrieval - COMPLETE VERSION
Provides eclipse data and natal chart impact analysis
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


def get_eclipses(
    start_date: date,
    end_date: date,
    natal_chart: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get eclipses for a date range
    
    Args:
        start_date: Start date
        end_date: End date
        natal_chart: Optional natal chart for house placement
        
    Returns:
        Eclipse data
    """
    try:
        logger.info(f"Getting eclipses from {start_date} to {end_date}")
        
        # Load eclipse data from JSON file
        eclipses = load_eclipse_data()
        
        # Filter eclipses within date range
        filtered_eclipses = []
        
        for eclipse in eclipses:
            eclipse_date = datetime.fromisoformat(eclipse['date']).date()
            
            if start_date <= eclipse_date <= end_date:
                eclipse_info = eclipse.copy()
                
                # Add natal chart analysis if provided
                if natal_chart:
                    eclipse_info['natal_analysis'] = analyze_eclipse_to_natal(
                        eclipse,
                        natal_chart
                    )
                
                filtered_eclipses.append(eclipse_info)
        
        # Find next upcoming eclipse
        upcoming_eclipse = find_upcoming_eclipse(eclipses, date.today())
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'eclipses': filtered_eclipses,
            'eclipse_count': len(filtered_eclipses),
            'upcoming_eclipse': upcoming_eclipse
        }
        
    except Exception as e:
        logger.error(f"Eclipse retrieval failed: {str(e)}")
        raise


def load_eclipse_data() -> List[Dict[str, Any]]:
    """
    Load eclipse data from JSON file
    
    Returns:
        List of eclipse data
    """
    # Default eclipse data file path
    data_file = os.path.join('data', 'eclipse_data', 'eclipses_2020_2050.json')
    
    try:
        # If file exists, load from file
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return built-in eclipse data for 2025
            logger.warning(f"Eclipse data file not found at {data_file}, using built-in data")
            return get_builtin_eclipse_data()
            
    except Exception as e:
        logger.error(f"Failed to load eclipse data: {str(e)}")
        return get_builtin_eclipse_data()


def get_builtin_eclipse_data() -> List[Dict[str, Any]]:
    """
    Built-in eclipse data for 2025 as fallback
    
    Returns:
        List of eclipse data
    """
    return [
        {
            'date': '2025-03-14T06:00:00',
            'type': 'Total Lunar Eclipse',
            'saros_series': 132,
            'longitude': 354.2,
            'latitude': 0,
            'sign': 'Pisces',
            'degree': 24.2,
            'visibility': 'Americas, Europe, Africa',
            'description': 'Total Lunar Eclipse in Pisces'
        },
        {
            'date': '2025-03-29T10:00:00',
            'type': 'Partial Solar Eclipse',
            'saros_series': 149,
            'longitude': 8.8,
            'latitude': 0,
            'sign': 'Aries',
            'degree': 8.8,
            'visibility': 'Europe, Africa, Asia',
            'description': 'Partial Solar Eclipse in Aries'
        },
        {
            'date': '2025-09-07T18:00:00',
            'type': 'Total Lunar Eclipse',
            'saros_series': 137,
            'longitude': 165.4,
            'latitude': 0,
            'sign': 'Virgo',
            'degree': 15.4,
            'visibility': 'Asia, Australia, Pacific',
            'description': 'Total Lunar Eclipse in Virgo'
        },
        {
            'date': '2025-09-21T19:00:00',
            'type': 'Partial Solar Eclipse',
            'saros_series': 154,
            'longitude': 178.9,
            'latitude': 0,
            'sign': 'Virgo',
            'degree': 28.9,
            'visibility': 'Pacific, New Zealand, Antarctica',
            'description': 'Partial Solar Eclipse in Virgo'
        }
    ]


def find_upcoming_eclipse(
    eclipses: List[Dict[str, Any]],
    from_date: date
) -> Optional[Dict[str, Any]]:
    """
    Find the next upcoming eclipse from a given date
    
    Args:
        eclipses: List of eclipse data
        from_date: Starting date
        
    Returns:
        Next eclipse data or None
    """
    future_eclipses = []
    
    for eclipse in eclipses:
        eclipse_date = datetime.fromisoformat(eclipse['date']).date()
        
        if eclipse_date >= from_date:
            future_eclipses.append(eclipse)
    
    if future_eclipses:
        # Sort by date and return first
        future_eclipses.sort(key=lambda x: datetime.fromisoformat(x['date']))
        return future_eclipses[0]
    
    return None


def analyze_eclipse_to_natal(
    eclipse: Dict[str, Any],
    natal_chart: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze eclipse's impact on natal chart
    
    Args:
        eclipse: Eclipse data
        natal_chart: Natal chart data
        
    Returns:
        Analysis of eclipse impact
    """
    try:
        eclipse_lon = eclipse.get('longitude', 0)
        eclipse_sign = eclipse.get('sign', 'Unknown')
        
        # Find which natal house the eclipse falls in
        natal_houses = natal_chart.get('houses', {})
        eclipse_house = determine_eclipse_house(eclipse_lon, natal_houses)
        
        # Find aspects to natal planets
        natal_planets = natal_chart.get('planets', {})
        eclipse_aspects = calculate_eclipse_aspects(eclipse_lon, natal_planets)
        
        # Determine significance
        significance = calculate_eclipse_significance(eclipse_aspects, eclipse_house)
        
        # Generate interpretation
        interpretation = generate_eclipse_interpretation(
            eclipse_sign,
            eclipse_house,
            eclipse_aspects,
            significance
        )
        
        return {
            'eclipse_house': eclipse_house,
            'eclipse_sign': eclipse_sign,
            'aspects_to_natal': eclipse_aspects,
            'significance': significance,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Eclipse natal analysis failed: {str(e)}")
        return {'error': str(e)}


def determine_eclipse_house(eclipse_lon: float, natal_houses: Dict[str, Any]) -> int:
    """Determine which natal house eclipse falls in"""
    for house_num in range(1, 13):
        house_data = natal_houses.get(str(house_num), {})
        next_house = natal_houses.get(str((house_num % 12) + 1), {})
        
        cusp = house_data.get('cusp', 0)
        next_cusp = next_house.get('cusp', 0)
        
        if next_cusp < cusp:  # House crosses 0° Aries
            if eclipse_lon >= cusp or eclipse_lon < next_cusp:
                return house_num
        else:
            if cusp <= eclipse_lon < next_cusp:
                return house_num
    
    return 1


def calculate_eclipse_aspects(
    eclipse_lon: float,
    natal_planets: Dict[str, Any],
    orb: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between eclipse point and natal planets
    
    Eclipse aspects have a wider orb (up to 10°)
    """
    aspects = []
    
    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for planet_name, planet_data in natal_planets.items():
        planet_lon = planet_data.get('longitude', 0)
        
        # Calculate angle
        angle = abs(eclipse_lon - planet_lon)
        if angle > 180:
            angle = 360 - angle
        
        # Check for aspects
        for aspect_name, aspect_angle in aspect_angles.items():
            diff = abs(angle - aspect_angle)
            
            if diff <= orb:
                aspects.append({
                    'planet': planet_name,
                    'aspect': aspect_name,
                    'orb': round(diff, 2),
                    'exact': diff < 2.0,
                    'description': f"Eclipse {aspect_name} Natal {planet_name.title()}"
                })
    
    return sorted(aspects, key=lambda x: x['orb'])


def calculate_eclipse_significance(
    aspects: List[Dict[str, Any]],
    house: int
) -> str:
    """
    Calculate overall significance of eclipse
    
    Returns:
        'high', 'medium', or 'low'
    """
    # High significance if:
    # - Exact aspects to personal planets (Sun, Moon, Mercury, Venus, Mars)
    # - Eclipse in angular house (1, 4, 7, 10)
    
    personal_planets = ['sun', 'moon', 'mercury', 'venus', 'mars']
    angular_houses = [1, 4, 7, 10]
    
    has_exact_personal = any(
        a['exact'] and a['planet'] in personal_planets
        for a in aspects
    )
    
    in_angular_house = house in angular_houses
    
    if has_exact_personal or (in_angular_house and len(aspects) >= 2):
        return 'high'
    elif len(aspects) >= 1 or in_angular_house:
        return 'medium'
    else:
        return 'low'


def generate_eclipse_interpretation(
    sign: str,
    house: int,
    aspects: List[Dict[str, Any]],
    significance: str
) -> str:
    """Generate human-readable eclipse interpretation"""
    
    house_meanings = {
        1: "Self, identity, new beginnings",
        2: "Resources, values, self-worth",
        3: "Communication, learning, siblings",
        4: "Home, family, emotional foundation",
        5: "Creativity, romance, self-expression",
        6: "Work, health, daily routines",
        7: "Partnerships, relationships, one-on-one connections",
        8: "Transformation, shared resources, intimacy",
        9: "Philosophy, travel, higher education",
        10: "Career, public life, reputation",
        11: "Friends, groups, aspirations",
        12: "Spirituality, unconscious, release"
    }
    
    interpretation = f"Eclipse in {sign}, {house}th house:\n"
    interpretation += f"Focus on {house_meanings.get(house, 'life themes')}\n"
    interpretation += f"Significance: {significance.upper()}\n\n"
    
    if aspects:
        interpretation += "Key Aspects:\n"
        for aspect in aspects[:3]:  # Top 3
            interpretation += f"- {aspect['description']}\n"
    
    return interpretation


def get_eclipse_season_info(year: int) -> Dict[str, Any]:
    """
    Get information about eclipse seasons for a year
    
    Eclipse seasons occur approximately every 6 months
    
    Args:
        year: Year to query
        
    Returns:
        Eclipse season information
    """
    eclipses = load_eclipse_data()
    
    # Filter eclipses for this year
    year_eclipses = [
        e for e in eclipses
        if datetime.fromisoformat(e['date']).year == year
    ]
    
    if not year_eclipses:
        return {
            'year': year,
            'eclipse_count': 0,
            'eclipses': []
        }
    
    # Group by season (within 35 days of each other)
    seasons = []
    current_season = []
    
    for eclipse in sorted(year_eclipses, key=lambda x: datetime.fromisoformat(x['date'])):
        if not current_season:
            current_season.append(eclipse)
        else:
            last_date = datetime.fromisoformat(current_season[-1]['date'])
            current_date = datetime.fromisoformat(eclipse['date'])
            
            if (current_date - last_date).days <= 35:
                current_season.append(eclipse)
            else:
                seasons.append(current_season)
                current_season = [eclipse]
    
    if current_season:
        seasons.append(current_season)
    
    return {
        'year': year,
        'eclipse_count': len(year_eclipses),
        'season_count': len(seasons),
        'seasons': [
            {
                'eclipses': season,
                'start_date': season[0]['date'],
                'end_date': season[-1]['date']
            }
            for season in seasons
        ]
    }


def get_eclipse_meditation_guide(eclipse_type: str) -> Dict[str, Any]:
    """
    Get meditation and ritual guide for eclipse
    
    Args:
        eclipse_type: 'Solar Eclipse' or 'Lunar Eclipse'
        
    Returns:
        Eclipse guide
    """
    if 'Solar' in eclipse_type:
        return {
            'type': 'Solar Eclipse',
            'energy': 'New beginnings, fresh starts',
            'meditation_focus': [
                'Set powerful intentions',
                'Visualize new paths opening',
                'Release old identity patterns',
                'Embrace change and transformation'
            ],
            'timing': 'Meditate during the eclipse or within 3 days after',
            'caution': 'Do not look directly at the sun during eclipse'
        }
    else:  # Lunar Eclipse
        return {
            'type': 'Lunar Eclipse',
            'energy': 'Release, emotional culmination',
            'meditation_focus': [
                'Release emotional patterns',
                'Let go of what no longer serves',
                'Honor feelings and intuition',
                'Complete emotional cycles'
            ],
            'timing': 'Meditate during the eclipse or within 3 days after',
            'ritual': 'Write down what you\'re releasing and burn it (safely)'
        }


def calculate_eclipse_axis(natal_chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate where current eclipse axis falls in natal chart
    
    Eclipses occur along the lunar nodes axis
    
    Args:
        natal_chart: Natal chart data
        
    Returns:
        Eclipse axis information
    """
    try:
        # Get North Node from natal chart
        north_node_lon = natal_chart.get('north_node', {}).get('longitude', 0)
        south_node_lon = (north_node_lon + 180) % 360
        
        # Determine houses
        houses = natal_chart.get('houses', {})
        north_node_house = determine_eclipse_house(north_node_lon, houses)
        south_node_house = determine_eclipse_house(south_node_lon, houses)
        
        return {
            'north_node_house': north_node_house,
            'south_node_house': south_node_house,
            'axis': f"{north_node_house}-{south_node_house}",
            'themes': get_axis_themes(north_node_house, south_node_house)
        }
        
    except Exception as e:
        logger.error(f"Eclipse axis calculation failed: {str(e)}")
        return {'error': str(e)}


def get_axis_themes(north_house: int, south_house: int) -> Dict[str, str]:
    """Get themes for eclipse axis"""
    house_axes = {
        '1-7': {
            'growth': 'Self-development and independence',
            'release': 'Over-dependence on others'
        },
        '2-8': {
            'growth': 'Personal resources and values',
            'release': 'Over-reliance on shared resources'
        },
        '3-9': {
            'growth': 'Learning, communication, local connections',
            'release': 'Dogmatic beliefs, over-travel'
        },
        '4-10': {
            'growth': 'Home, family, emotional foundation',
            'release': 'Over-focus on career and public image'
        },
        '5-11': {
            'growth': 'Creative self-expression, romance',
            'release': 'Over-identification with groups'
        },
        '6-12': {
            'growth': 'Health, daily routines, practical service',
            'release': 'Escapism, isolation'
        }
    }
    
    axis_key = f"{min(north_house, south_house)}-{max(north_house, south_house)}"
    return house_axes.get(axis_key, {'growth': 'Personal evolution', 'release': 'Old patterns'})


# Example usage
if __name__ == "__main__":
    # Get eclipses for 2025
    eclipses_2025 = get_eclipses(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
    )
    
    print(f"Eclipses in 2025: {eclipses_2025['eclipse_count']}")
    
    for eclipse in eclipses_2025['eclipses']:
        print(f"- {eclipse['date']}: {eclipse['description']}")
    
    print()
    
    # Upcoming eclipse
    upcoming = eclipses_2025.get('upcoming_eclipse')
    if upcoming:
        print(f"Next Eclipse: {upcoming['date']}")
        print(f"Type: {upcoming['type']}")
        print(f"Sign: {upcoming['sign']}")
        
        # Eclipse guide
        guide = get_eclipse_meditation_guide(upcoming['type'])
        print(f"\nEclipse Guide:")
        print(f"Energy: {guide['energy']}")
        print("Focus:", ", ".join(guide['meditation_focus']))
