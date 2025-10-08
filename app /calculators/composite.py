"""
Composite and Davison chart calculations - COMPLETE VERSION
Analyzes the relationship as its own entity
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging
from kerykeion import AstrologicalSubject

logger = logging.getLogger(__name__)


def calculate_composite_chart(
    person1_data: Dict[str, Any],
    person2_data: Dict[str, Any],
    method: str = 'midpoint'
) -> Dict[str, Any]:
    """
    Calculate composite chart
    
    Args:
        person1_data: Person 1 birth data
        person2_data: Person 2 birth data
        method: 'midpoint' (standard composite) or 'davison' (Davison relationship chart)
        
    Returns:
        Composite chart data
    """
    try:
        logger.info(f"Calculating {method} composite for {person1_data['name']} & {person2_data['name']}")
        
        if method == 'midpoint':
            return calculate_midpoint_composite(person1_data, person2_data)
        elif method == 'davison':
            return calculate_davison_chart(person1_data, person2_data)
        else:
            raise ValueError(f"Unknown composite method: {method}")
            
    except Exception as e:
        logger.error(f"Composite calculation failed: {str(e)}")
        raise


def calculate_midpoint_composite(
    person1_data: Dict[str, Any],
    person2_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate midpoint composite chart
    Each planet is at the midpoint between the two natal positions
    """
    
    # Create both charts
    chart1 = create_chart(person1_data)
    chart2 = create_chart(person2_data)
    
    # Extract planets
    planets1 = extract_planets(chart1)
    planets2 = extract_planets(chart2)
    
    # Calculate midpoints
    composite_planets = calculate_planet_midpoints(planets1, planets2)
    
    # Calculate composite ascendant (midpoint of natal ascendants)
    asc1 = chart1.first_house['position']
    asc2 = chart2.first_house['position']
    composite_asc = calculate_midpoint_longitude(asc1, asc2)
    
    # Calculate composite MC
    mc1 = chart1.tenth_house['position']
    mc2 = chart2.tenth_house['position']
    composite_mc = calculate_midpoint_longitude(mc1, mc2)
    
    # Generate composite houses from composite ascendant
    composite_houses = generate_houses_from_ascendant(composite_asc)
    
    # Analyze the composite chart
    analysis = analyze_composite_chart(composite_planets, composite_houses)
    
    # Generate interpretation
    interpretation = generate_composite_interpretation(
        person1_data['name'],
        person2_data['name'],
        composite_planets,
        analysis
    )
    
    return {
        'method': 'midpoint',
        'person1': person1_data['name'],
        'person2': person2_data['name'],
        'composite_planets': composite_planets,
        'composite_ascendant': {
            'longitude': composite_asc,
            'sign': get_sign_from_longitude(composite_asc)
        },
        'composite_mc': {
            'longitude': composite_mc,
            'sign': get_sign_from_longitude(composite_mc)
        },
        'composite_houses': composite_houses,
        'analysis': analysis,
        'interpretation': interpretation
    }


def calculate_davison_chart(
    person1_data: Dict[str, Any],
    person2_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate Davison relationship chart
    Uses the midpoint in time and space between two birth charts
    """
    
    # Calculate midpoint datetime
    dt1 = datetime.combine(person1_data['birth_date'], person1_data['birth_time'])
    dt2 = datetime.combine(person2_data['birth_date'], person2_data['birth_time'])
    
    time_diff = abs((dt2 - dt1).total_seconds())
    midpoint_dt = dt1 + timedelta(seconds=time_diff / 2)
    
    # Calculate midpoint location
    lat1 = person1_data.get('latitude', 41.0082)
    lat2 = person2_data.get('latitude', 41.0082)
    lon1 = person1_data.get('longitude', 28.9784)
    lon2 = person2_data.get('longitude', 28.9784)
    
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    
    # Create Davison chart at midpoint time and place
    davison_chart = AstrologicalSubject(
        name=f"Davison: {person1_data['name']} & {person2_data['name']}",
        year=midpoint_dt.year,
        month=midpoint_dt.month,
        day=midpoint_dt.day,
        hour=midpoint_dt.hour,
        minute=midpoint_dt.minute,
        city="Relationship Midpoint",
        lat=mid_lat,
        lng=mid_lon,
        tz_str=person1_data.get('timezone', 'Europe/Istanbul')
    )
    
    # Extract chart data
    planets = extract_planets(davison_chart)
    houses = extract_houses(davison_chart)
    
    # Analyze
    analysis = analyze_composite_chart(planets, houses)
    
    # Generate interpretation
    interpretation = generate_composite_interpretation(
        person1_data['name'],
        person2_data['name'],
        planets,
        analysis
    )
    
    return {
        'method': 'davison',
        'person1': person1_data['name'],
        'person2': person2_data['name'],
        'midpoint_datetime': midpoint_dt.isoformat(),
        'midpoint_location': {'latitude': mid_lat, 'longitude': mid_lon},
        'planets': planets,
        'houses': houses,
        'analysis': analysis,
        'interpretation': interpretation
    }


def create_chart(person_data: Dict[str, Any]) -> AstrologicalSubject:
    """Create chart from person data"""
    birth_date = person_data['birth_date']
    birth_time = person_data['birth_time']
    
    return AstrologicalSubject(
        name=person_data['name'],
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=birth_time.hour,
        minute=birth_time.minute,
        city=person_data.get('birth_place', 'Location'),
        nation=person_data.get('nation', 'TR'),
        lat=person_data.get('latitude', 41.0082),
        lng=person_data.get('longitude', 28.9784),
        tz_str=person_data.get('timezone', 'Europe/Istanbul')
    )


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


def calculate_planet_midpoints(
    planets1: Dict[str, Any],
    planets2: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate midpoint for each planet pair"""
    composite_planets = {}
    
    for planet_name in planets1.keys():
        if planet_name in planets2:
            lon1 = planets1[planet_name]['longitude']
            lon2 = planets2[planet_name]['longitude']
            
            midpoint_lon = calculate_midpoint_longitude(lon1, lon2)
            
            composite_planets[planet_name] = {
                'longitude': midpoint_lon,
                'sign': get_sign_from_longitude(midpoint_lon),
                'degree': midpoint_lon % 30
            }
    
    return composite_planets


def calculate_midpoint_longitude(lon1: float, lon2: float) -> float:
    """
    Calculate midpoint between two longitudes
    Always takes the shorter arc
    """
    # Calculate difference
    diff = abs(lon2 - lon1)
    
    # If difference > 180, take the longer arc (which becomes shorter)
    if diff > 180:
        # Take opposite midpoint
        if lon1 < lon2:
            midpoint = (lon1 + (360 - diff) / 2) % 360
        else:
            midpoint = (lon2 + (360 - diff) / 2) % 360
    else:
        # Normal midpoint
        midpoint = (lon1 + lon2) / 2
    
    return midpoint


def get_sign_from_longitude(longitude: float) -> str:
    """Get zodiac sign from longitude"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]


def generate_houses_from_ascendant(asc_longitude: float) -> Dict[str, Any]:
    """
    Generate house cusps from ascendant
    Using equal house system for simplicity
    """
    houses = {}
    
    for i in range(1, 13):
        cusp = (asc_longitude + (i - 1) * 30) % 360
        houses[str(i)] = {
            'cusp': cusp,
            'sign': get_sign_from_longitude(cusp)
        }
    
    return houses


def analyze_composite_chart(
    planets: Dict[str, Any],
    houses: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze composite chart for relationship themes"""
    
    analysis = {
        'relationship_identity': analyze_sun_position(planets),
        'emotional_bond': analyze_moon_position(planets),
        'communication': analyze_mercury_position(planets),
        'affection': analyze_venus_position(planets),
        'passion': analyze_mars_position(planets),
        'growth': analyze_jupiter_position(planets),
        'challenges': analyze_saturn_position(planets),
        'element_balance': analyze_element_balance(planets),
        'house_emphasis': analyze_house_emphasis(planets, houses)
    }
    
    return analysis


def analyze_sun_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Sun for relationship identity"""
    sun = planets.get('sun', {})
    sign = sun.get('sign', 'Unknown')
    
    interpretations = {
        'Aries': "Dynamic, pioneering relationship with focus on independence",
        'Taurus': "Stable, sensual relationship valuing security and comfort",
        'Gemini': "Communicative, versatile relationship with mental stimulation",
        'Cancer': "Nurturing, emotional relationship centered on home and family",
        'Leo': "Creative, expressive relationship with dramatic flair",
        'Virgo': "Practical, service-oriented relationship with attention to detail",
        'Libra': "Harmonious, partnership-focused relationship valuing balance",
        'Scorpio': "Intense, transformative relationship with deep intimacy",
        'Sagittarius': "Adventurous, philosophical relationship seeking growth",
        'Capricorn': "Ambitious, structured relationship with long-term goals",
        'Aquarius': "Unconventional, friendship-based relationship valuing freedom",
        'Pisces': "Compassionate, spiritual relationship with merged boundaries"
    }
    
    return interpretations.get(sign, f"Relationship identity expressed through {sign}")


def analyze_moon_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Moon for emotional dynamics"""
    moon = planets.get('moon', {})
    sign = moon.get('sign', 'Unknown')
    
    return f"Emotional needs and nurturing expressed through {sign}"


def analyze_mercury_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Mercury for communication"""
    mercury = planets.get('mercury', {})
    sign = mercury.get('sign', 'Unknown')
    
    return f"Communication style: {sign}"


def analyze_venus_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Venus for affection"""
    venus = planets.get('venus', {})
    sign = venus.get('sign', 'Unknown')
    
    return f"Expression of affection through {sign}"


def analyze_mars_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Mars for action/passion"""
    mars = planets.get('mars', {})
    sign = mars.get('sign', 'Unknown')
    
    return f"Action and passion expressed through {sign}"


def analyze_jupiter_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Jupiter for growth"""
    jupiter = planets.get('jupiter', {})
    sign = jupiter.get('sign', 'Unknown')
    
    return f"Growth and expansion through {sign}"


def analyze_saturn_position(planets: Dict[str, Any]) -> str:
    """Analyze composite Saturn for challenges/structure"""
    saturn = planets.get('saturn', {})
    sign = saturn.get('sign', 'Unknown')
    
    return f"Challenges and responsibilities in {sign}"


def analyze_element_balance(planets: Dict[str, Any]) -> Dict[str, int]:
    """Analyze element distribution in composite"""
    element_map = {
        'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
        'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
        'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
        'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
    }
    
    elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    
    for planet_data in planets.values():
        sign = planet_data.get('sign', 'Unknown')
        element = element_map.get(sign, 'Unknown')
        if element != 'Unknown':
            elements[element] += 1
    
    return elements


def analyze_house_emphasis(planets: Dict[str, Any], houses: Dict[str, Any]) -> List[int]:
    """Find which houses have planetary emphasis"""
    house_counts = {i: 0 for i in range(1, 13)}
    
    for planet_data in planets.values():
        planet_lon = planet_data['longitude']
        house_num = determine_house(planet_lon, houses)
        house_counts[house_num] += 1
    
    # Return houses with planets
    emphasized = [house for house, count in house_counts.items() if count > 0]
    return emphasized


def determine_house(longitude: float, houses: Dict[str, Any]) -> int:
    """Determine which house a longitude falls in"""
    for house_num in range(1, 13):
        house_data = houses.get(str(house_num), {})
        next_house = houses.get(str((house_num % 12) + 1), {})
        
        cusp = house_data.get('cusp', 0)
        next_cusp = next_house.get('cusp', 0)
        
        if next_cusp < cusp:
            if longitude >= cusp or longitude < next_cusp:
                return house_num
        else:
            if cusp <= longitude < next_cusp:
                return house_num
    
    return 1


def generate_composite_interpretation(
    name1: str,
    name2: str,
    planets: Dict[str, Any],
    analysis: Dict[str, Any]
) -> str:
    """Generate comprehensive composite interpretation"""
    
    report = f"# Composite Chart: {name1} & {name2}\n\n"
    
    report += "## Relationship Identity\n"
    report += f"{analysis['relationship_identity']}\n\n"
    
    report += "## Emotional Dynamics\n"
    report += f"{analysis['emotional_bond']}\n\n"
    
    report += "## Communication\n"
    report += f"{analysis['communication']}\n\n"
    
    report += "## Affection & Values\n"
    report += f"{analysis['affection']}\n\n"
    
    report += "## Passion & Drive\n"
    report += f"{analysis['passion']}\n\n"
    
    report += "## Element Balance\n"
    elements = analysis['element_balance']
    for element, count in elements.items():
        report += f"- {element}: {count} planets\n"
    
    report += "\n## House Emphasis\n"
    emphasized = analysis['house_emphasis']
    if emphasized:
        report += f"Planets in houses: {', '.join(str(h) for h in emphasized)}\n"
    
    return report


# Example usage
if __name__ == "__main__":
    from datetime import datetime, time
    
    person1 = {
        'name': 'Alice',
        'birth_date': datetime(1990, 5, 15).date(),
        'birth_time': time(14, 30),
        'latitude': 41.0082,
        'longitude': 28.9784
    }
    
    person2 = {
        'name': 'Bob',
        'birth_date': datetime(1988, 11, 22).date(),
        'birth_time': time(10, 15),
        'latitude': 39.9334,
        'longitude': 32.8597
    }
    
    # Midpoint composite
    composite = calculate_composite_chart(person1, person2, method='midpoint')
    print(composite['interpretation'])
    
    # Davison chart
    davison = calculate_composite_chart(person1, person2, method='davison')
    print(davison['interpretation'])
