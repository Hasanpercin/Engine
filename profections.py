"""
Annual Profections - COMPLETE VERSION
Ancient Hellenistic timing technique (12-year cycle)
Each year activates a different house of the natal chart
"""

from typing import Dict, Any, List
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def calculate_profection(
    birth_date: date,
    current_age: int,
    natal_chart: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate annual profection year
    
    Profections move through the natal houses in a 12-year cycle.
    At birth (age 0), 1st house is activated.
    At age 1, 2nd house is activated, etc.
    
    Args:
        birth_date: Birth date
        current_age: Current age in years
        natal_chart: Natal chart data with houses
        
    Returns:
        Profection year analysis
    """
    try:
        logger.info(f"Calculating profection for age {current_age}")
        
        # Calculate profection house (age mod 12, starting from 1st house at age 0)
        profection_house = (current_age % 12) + 1
        
        # Get natal houses
        natal_houses = natal_chart.get('houses', {})
        natal_planets = natal_chart.get('planets', {})
        
        # Get house cusp position
        house_data = natal_houses.get(str(profection_house), {})
        house_cusp = house_data.get('cusp', 0)
        
        # Determine sign on house cusp
        profection_sign = get_sign_from_longitude(house_cusp)
        
        # Determine time lord (ruler of profection sign)
        time_lord = get_sign_ruler(profection_sign)
        
        # Get year theme based on house
        year_theme = get_profection_house_theme(profection_house)
        
        # Find planets in profection house
        planets_in_house = find_planets_in_house(profection_house, natal_planets, natal_houses)
        
        # Calculate time lord natal position
        time_lord_position = get_time_lord_position(time_lord, natal_planets, natal_houses)
        
        # Calculate previous and next profections
        previous_profection = calculate_adjacent_profection(
            current_age - 1,
            natal_houses
        ) if current_age > 0 else None
        
        next_profection = calculate_adjacent_profection(
            current_age + 1,
            natal_houses
        )
        
        # Generate interpretation
        interpretation = generate_profection_interpretation(
            current_age,
            profection_house,
            profection_sign,
            time_lord,
            year_theme,
            planets_in_house
        )
        
        return {
            'age': current_age,
            'profection_house': profection_house,
            'profection_sign': profection_sign,
            'time_lord': time_lord,
            'time_lord_position': time_lord_position,
            'year_theme': year_theme,
            'planets_in_house': planets_in_house,
            'previous_profection': previous_profection,
            'next_profection': next_profection,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Profection calculation failed: {str(e)}")
        raise


def calculate_adjacent_profection(
    age: int,
    natal_houses: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate profection for adjacent year"""
    if age < 0:
        return None
    
    profection_house = (age % 12) + 1
    house_data = natal_houses.get(str(profection_house), {})
    house_cusp = house_data.get('cusp', 0)
    profection_sign = get_sign_from_longitude(house_cusp)
    time_lord = get_sign_ruler(profection_sign)
    
    return {
        'age': age,
        'house': profection_house,
        'sign': profection_sign,
        'time_lord': time_lord
    }


def get_12_year_profection_cycle(
    birth_date: date,
    current_age: int,
    natal_chart: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Get complete 12-year profection cycle from current age
    
    Returns:
        List of 12 profection years
    """
    cycle = []
    natal_houses = natal_chart.get('houses', {})
    
    for offset in range(12):
        age = current_age + offset
        profection = calculate_adjacent_profection(age, natal_houses)
        
        if profection:
            # Calculate date range
            birthday = birth_date.replace(year=birth_date.year + age)
            next_birthday = birth_date.replace(year=birth_date.year + age + 1)
            
            profection['date_range'] = {
                'start': birthday.isoformat(),
                'end': (next_birthday - timedelta(days=1)).isoformat()
            }
            
            cycle.append(profection)
    
    return cycle


def get_sign_from_longitude(longitude: float) -> str:
    """Get zodiac sign from ecliptic longitude"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]


def get_sign_ruler(sign: str) -> str:
    """
    Get traditional ruler of zodiac sign
    
    Returns:
        Planet name that rules the sign
    """
    rulers = {
        'Aries': 'Mars',
        'Taurus': 'Venus',
        'Gemini': 'Mercury',
        'Cancer': 'Moon',
        'Leo': 'Sun',
        'Virgo': 'Mercury',
        'Libra': 'Venus',
        'Scorpio': 'Mars',
        'Sagittarius': 'Jupiter',
        'Capricorn': 'Saturn',
        'Aquarius': 'Saturn',
        'Pisces': 'Jupiter'
    }
    
    return rulers.get(sign, 'Unknown')


def get_profection_house_theme(house: int) -> Dict[str, Any]:
    """
    Get theme and focus for profection house
    
    Returns:
        House themes and keywords
    """
    themes = {
        1: {
            'title': 'Self and Identity',
            'keywords': ['personal development', 'appearance', 'new beginnings', 'independence'],
            'description': 'Focus on self, identity, and personal goals. Time for new beginnings.'
        },
        2: {
            'title': 'Resources and Values',
            'keywords': ['finances', 'possessions', 'self-worth', 'earning'],
            'description': 'Focus on resources, money, and personal values. Building security.'
        },
        3: {
            'title': 'Communication and Learning',
            'keywords': ['learning', 'siblings', 'short trips', 'communication'],
            'description': 'Focus on learning, communication, and local connections.'
        },
        4: {
            'title': 'Home and Family',
            'keywords': ['home', 'family', 'roots', 'emotional foundation'],
            'description': 'Focus on home, family matters, and emotional security.'
        },
        5: {
            'title': 'Creativity and Romance',
            'keywords': ['creativity', 'romance', 'children', 'pleasure', 'self-expression'],
            'description': 'Focus on creativity, romance, and self-expression.'
        },
        6: {
            'title': 'Work and Health',
            'keywords': ['health', 'daily work', 'service', 'routines', 'pets'],
            'description': 'Focus on health, daily work, and service to others.'
        },
        7: {
            'title': 'Partnerships and Relationships',
            'keywords': ['marriage', 'partnerships', 'contracts', 'relationships'],
            'description': 'Focus on partnerships, relationships, and one-on-one connections.'
        },
        8: {
            'title': 'Transformation and Shared Resources',
            'keywords': ['transformation', 'shared resources', 'intimacy', 'inheritance'],
            'description': 'Focus on transformation, shared resources, and deep change.'
        },
        9: {
            'title': 'Philosophy and Travel',
            'keywords': ['travel', 'higher education', 'philosophy', 'expansion'],
            'description': 'Focus on travel, higher learning, and philosophical expansion.'
        },
        10: {
            'title': 'Career and Public Life',
            'keywords': ['career', 'reputation', 'public life', 'achievement'],
            'description': 'Focus on career, public reputation, and achievements.'
        },
        11: {
            'title': 'Friends and Aspirations',
            'keywords': ['friends', 'groups', 'hopes', 'aspirations', 'social causes'],
            'description': 'Focus on friendships, groups, and long-term aspirations.'
        },
        12: {
            'title': 'Spirituality and Solitude',
            'keywords': ['spirituality', 'solitude', 'healing', 'unconscious', 'retreat'],
            'description': 'Focus on spirituality, solitude, and inner work.'
        }
    }
    
    return themes.get(house, {
        'title': 'Unknown',
        'keywords': [],
        'description': 'House themes unavailable'
    })


def find_planets_in_house(
    house_number: int,
    natal_planets: Dict[str, Any],
    natal_houses: Dict[str, Any]
) -> List[str]:
    """
    Find which natal planets are in the profection house
    
    Returns:
        List of planet names in the house
    """
    planets_in_house = []
    
    for planet_name, planet_data in natal_planets.items():
        planet_lon = planet_data.get('longitude', 0)
        planet_house = determine_planet_house(planet_lon, natal_houses)
        
        if planet_house == house_number:
            planets_in_house.append(planet_name)
    
    return planets_in_house


def determine_planet_house(longitude: float, houses: Dict[str, Any]) -> int:
    """Determine which house a planet longitude falls in"""
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
    
    return 1


def get_time_lord_position(
    time_lord: str,
    natal_planets: Dict[str, Any],
    natal_houses: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get natal position of time lord planet
    
    Returns:
        Time lord's natal house, sign, and any aspects
    """
    planet_name = time_lord.lower()
    planet_data = natal_planets.get(planet_name, {})
    
    if not planet_data:
        return {'error': f'{time_lord} not found in natal chart'}
    
    planet_lon = planet_data.get('longitude', 0)
    planet_sign = planet_data.get('sign', 'Unknown')
    planet_house = determine_planet_house(planet_lon, natal_houses)
    
    return {
        'planet': time_lord,
        'natal_sign': planet_sign,
        'natal_house': planet_house,
        'longitude': planet_lon,
        'interpretation': f"{time_lord} rules this year from {planet_sign} in {planet_house}th house"
    }


def generate_profection_interpretation(
    age: int,
    house: int,
    sign: str,
    time_lord: str,
    theme: Dict[str, Any],
    planets_in_house: List[str]
) -> str:
    """Generate comprehensive profection interpretation"""
    
    interpretation = f"# Profection Year - Age {age}\n\n"
    
    interpretation += f"## Activated House: {house}th House\n"
    interpretation += f"**Sign:** {sign}\n"
    interpretation += f"**Time Lord:** {time_lord}\n\n"
    
    interpretation += f"## Year Theme: {theme['title']}\n"
    interpretation += f"{theme['description']}\n\n"
    
    interpretation += f"**Keywords:** {', '.join(theme['keywords'])}\n\n"
    
    if planets_in_house:
        interpretation += f"## Natal Planets in this House:\n"
        for planet in planets_in_house:
            interpretation += f"- {planet.title()}: This planet will be especially active this year\n"
        interpretation += "\n"
    
    interpretation += f"## Guidance:\n"
    interpretation += f"The {house}th house profection suggests this is a year to focus on {theme['title'].lower()}. "
    interpretation += f"Pay attention to {time_lord} by transit and progression, as it rules this year.\n"
    
    return interpretation


def analyze_profection_transits(
    profection_data: Dict[str, Any],
    transit_dates: List[date]
) -> Dict[str, Any]:
    """
    Analyze when time lord planet is activated by transits
    
    Important dates when transiting planets aspect the time lord
    
    Args:
        profection_data: Profection year data
        transit_dates: Dates to check for transits
        
    Returns:
        Important transit dates for the profection year
    """
    time_lord = profection_data['time_lord'].lower()
    time_lord_position = profection_data.get('time_lord_position', {})
    time_lord_lon = time_lord_position.get('longitude', 0)
    
    # This would integrate with transits.py to find when
    # outer planets aspect the time lord
    # Simplified version here
    
    return {
        'time_lord': time_lord,
        'watch_for': f"Transits to {time_lord} will be especially significant this year",
        'focus_months': 'Months when outer planets aspect your time lord'
    }


def get_profection_advice(house: int, time_lord: str) -> List[str]:
    """
    Get practical advice for profection year
    
    Returns:
        List of actionable advice
    """
    house_advice = {
        1: [
            "Focus on personal development",
            "Start new projects aligned with your identity",
            "Work on physical health and appearance",
            "Assert your independence"
        ],
        2: [
            "Review your financial situation",
            "Develop new income streams",
            "Clarify your values",
            "Build financial security"
        ],
        3: [
            "Take courses or learn new skills",
            "Improve communication",
            "Connect with siblings or neighbors",
            "Write, speak, or teach"
        ],
        4: [
            "Focus on home and family",
            "Address family matters",
            "Create emotional security",
            "Consider moving or home improvements"
        ],
        5: [
            "Express creativity",
            "Explore romance",
            "Spend time with children",
            "Pursue hobbies and pleasure"
        ],
        6: [
            "Establish healthy routines",
            "Focus on physical health",
            "Improve work situation",
            "Be of service to others"
        ],
        7: [
            "Focus on partnerships",
            "Marriage or significant relationship developments",
            "Sign important contracts",
            "Work on one-on-one relationships"
        ],
        8: [
            "Face transformation",
            "Deal with shared resources",
            "Deepen intimacy",
            "Handle inheritance or taxes"
        ],
        9: [
            "Travel or plan trips",
            "Pursue higher education",
            "Explore philosophy or spirituality",
            "Expand your worldview"
        ],
        10: [
            "Focus on career advancement",
            "Build public reputation",
            "Take on leadership roles",
            "Achieve professional goals"
        ],
        11: [
            "Cultivate friendships",
            "Join groups or organizations",
            "Pursue aspirations",
            "Engage in social causes"
        ],
        12: [
            "Practice spirituality",
            "Spend time in solitude",
            "Address unconscious patterns",
            "Rest and recharge"
        ]
    }
    
    advice = house_advice.get(house, ["Focus on personal growth"])
    advice.append(f"Pay attention to {time_lord} - it rules this year")
    
    return advice


# Example usage
if __name__ == "__main__":
    from datetime import date
    
    # Sample natal chart
    natal_chart = {
        'houses': {
            '1': {'cusp': 0, 'sign': 'Aries'},
            '2': {'cusp': 30, 'sign': 'Taurus'},
            '3': {'cusp': 60, 'sign': 'Gemini'},
            '4': {'cusp': 90, 'sign': 'Cancer'},
            '5': {'cusp': 120, 'sign': 'Leo'},
            '6': {'cusp': 150, 'sign': 'Virgo'},
            '7': {'cusp': 180, 'sign': 'Libra'},
            '8': {'cusp': 210, 'sign': 'Scorpio'},
            '9': {'cusp': 240, 'sign': 'Sagittarius'},
            '10': {'cusp': 270, 'sign': 'Capricorn'},
            '11': {'cusp': 300, 'sign': 'Aquarius'},
            '12': {'cusp': 330, 'sign': 'Pisces'}
        },
        'planets': {
            'sun': {'longitude': 45, 'sign': 'Taurus'},
            'moon': {'longitude': 120, 'sign': 'Leo'},
            'mercury': {'longitude': 60, 'sign': 'Gemini'}
        }
    }
    
    birth_date = date(1990, 5, 15)
    current_age = 35
    
    # Calculate profection
    profection = calculate_profection(birth_date, current_age, natal_chart)
    
    print(profection['interpretation'])
    print()
    
    # Get 12-year cycle
    cycle = get_12_year_profection_cycle(birth_date, current_age, natal_chart)
    print("12-Year Profection Cycle:")
    for year in cycle[:3]:  # Show next 3 years
        print(f"Age {year['age']}: {year['house']}th House ({year['sign']}) - {year['time_lord']}")
