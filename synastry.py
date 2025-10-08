"""
Synastry (relationship compatibility) calculations - COMPLETE VERSION
Analyzes compatibility between two birth charts
"""

from typing import Dict, Any, List
import logging
from kerykeion import AstrologicalSubject

logger = logging.getLogger(__name__)


def calculate_synastry(
    person1_data: Dict[str, Any],
    person2_data: Dict[str, Any],
    include_svg: bool = False
) -> Dict[str, Any]:
    """
    Calculate synastry between two people
    
    Args:
        person1_data: Person 1 birth data
        person2_data: Person 2 birth data
        include_svg: Whether to include SVG chart
        
    Returns:
        Synastry analysis with cross-aspects and compatibility scores
    """
    try:
        logger.info(f"Calculating synastry between {person1_data['name']} and {person2_data['name']}")
        
        # Create both natal charts
        chart1 = create_chart_from_data(person1_data)
        chart2 = create_chart_from_data(person2_data)
        
        # Extract planets and houses
        planets1 = extract_planets(chart1)
        planets2 = extract_planets(chart2)
        houses1 = extract_houses(chart1)
        houses2 = extract_houses(chart2)
        
        # Calculate cross-aspects (Person 1 planets to Person 2 planets)
        cross_aspects = calculate_cross_aspects(planets1, planets2)
        
        # Calculate house overlays (Person 1 planets in Person 2 houses)
        house_overlays_1_to_2 = calculate_house_overlays(planets1, houses2)
        house_overlays_2_to_1 = calculate_house_overlays(planets2, houses1)
        
        # Calculate compatibility scores
        compatibility_scores = calculate_compatibility_scores(cross_aspects, house_overlays_1_to_2)
        
        # Find key connections
        key_connections = find_key_connections(cross_aspects)
        
        # Analyze specific planetary pairs
        sun_moon_analysis = analyze_sun_moon_connections(planets1, planets2, cross_aspects)
        venus_mars_analysis = analyze_venus_mars_connections(planets1, planets2, cross_aspects)
        
        # Generate synastry report
        report = generate_synastry_report(
            person1_data['name'],
            person2_data['name'],
            compatibility_scores,
            key_connections,
            sun_moon_analysis,
            venus_mars_analysis
        )
        
        return {
            'person1': person1_data['name'],
            'person2': person2_data['name'],
            'cross_aspects': cross_aspects,
            'house_overlays': {
                f"{person1_data['name']}_to_{person2_data['name']}": house_overlays_1_to_2,
                f"{person2_data['name']}_to_{person1_data['name']}": house_overlays_2_to_1
            },
            'compatibility_scores': compatibility_scores,
            'key_connections': key_connections,
            'sun_moon_analysis': sun_moon_analysis,
            'venus_mars_analysis': venus_mars_analysis,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Synastry calculation failed: {str(e)}")
        raise


def create_chart_from_data(person_data: Dict[str, Any]) -> AstrologicalSubject:
    """Create AstrologicalSubject from person data"""
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
    """Extract planet positions from chart"""
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
    """Extract house cusps from chart"""
    houses = {}
    
    for i in range(1, 13):
        house_obj = getattr(chart, f'house{i}', None)
        if house_obj:
            houses[str(i)] = {
                'cusp': house_obj['position'],
                'sign': house_obj['sign']
            }
    
    return houses


def calculate_cross_aspects(
    planets1: Dict[str, Any],
    planets2: Dict[str, Any],
    orb: float = 8.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between two sets of planets
    
    Returns:
        List of cross-aspects with orbs
    """
    aspects = []
    
    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }
    
    for planet1_name, planet1_data in planets1.items():
        lon1 = planet1_data['longitude']
        
        for planet2_name, planet2_data in planets2.items():
            lon2 = planet2_data['longitude']
            
            # Calculate angle
            angle = abs(lon1 - lon2)
            if angle > 180:
                angle = 360 - angle
            
            # Check for aspects
            for aspect_name, aspect_angle in aspect_angles.items():
                diff = abs(angle - aspect_angle)
                
                if diff <= orb:
                    quality = get_aspect_quality(aspect_name)
                    aspects.append({
                        'planet1': planet1_name,
                        'planet2': planet2_name,
                        'aspect': aspect_name,
                        'orb': round(diff, 2),
                        'exact': diff < 1.0,
                        'quality': quality,
                        'description': f"{planet1_name.title()} {aspect_name} {planet2_name.title()}",
                        'interpretation': get_synastry_aspect_interpretation(
                            planet1_name, planet2_name, aspect_name
                        )
                    })
    
    return sorted(aspects, key=lambda x: x['orb'])


def calculate_house_overlays(
    planets: Dict[str, Any],
    target_houses: Dict[str, Any]
) -> Dict[str, int]:
    """
    Calculate which houses planets fall in
    
    Args:
        planets: Planet positions from one person
        target_houses: House cusps from another person
        
    Returns:
        Dict mapping planet names to house numbers
    """
    overlays = {}
    
    for planet_name, planet_data in planets.items():
        planet_lon = planet_data['longitude']
        house_num = determine_house_from_longitude(planet_lon, target_houses)
        overlays[planet_name] = house_num
    
    return overlays


def determine_house_from_longitude(longitude: float, houses: Dict[str, Any]) -> int:
    """Determine which house a longitude falls in"""
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


def calculate_compatibility_scores(
    cross_aspects: List[Dict[str, Any]],
    house_overlays: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculate various compatibility scores
    
    Returns:
        Dict with different compatibility metrics
    """
    # Overall score based on aspects
    harmonious_count = sum(1 for a in cross_aspects if a['quality'] == 'harmonious')
    challenging_count = sum(1 for a in cross_aspects if a['quality'] == 'challenging')
    total_aspects = len(cross_aspects)
    
    if total_aspects > 0:
        harmony_ratio = harmonious_count / total_aspects
        overall_score = harmony_ratio * 10
    else:
        overall_score = 5.0
    
    # Romantic compatibility (Venus-Mars, Sun-Moon)
    romantic_aspects = [a for a in cross_aspects 
                       if {a['planet1'], a['planet2']} & {'venus', 'mars', 'sun', 'moon'}]
    romantic_score = calculate_sub_score(romantic_aspects)
    
    # Communication (Mercury aspects)
    communication_aspects = [a for a in cross_aspects 
                           if 'mercury' in [a['planet1'], a['planet2']]]
    communication_score = calculate_sub_score(communication_aspects)
    
    # Long-term (Saturn, Jupiter aspects)
    longterm_aspects = [a for a in cross_aspects 
                       if {a['planet1'], a['planet2']} & {'saturn', 'jupiter'}]
    longterm_score = calculate_sub_score(longterm_aspects)
    
    # Emotional (Moon aspects)
    emotional_aspects = [a for a in cross_aspects 
                        if 'moon' in [a['planet1'], a['planet2']]]
    emotional_score = calculate_sub_score(emotional_aspects)
    
    return {
        'overall': round(overall_score, 1),
        'romantic': round(romantic_score, 1),
        'communication': round(communication_score, 1),
        'long_term': round(longterm_score, 1),
        'emotional': round(emotional_score, 1),
        'total_aspects': total_aspects,
        'harmonious_aspects': harmonious_count,
        'challenging_aspects': challenging_count
    }


def calculate_sub_score(aspects: List[Dict[str, Any]]) -> float:
    """Calculate score for a subset of aspects"""
    if not aspects:
        return 5.0
    
    score = 0
    for aspect in aspects:
        if aspect['quality'] == 'harmonious':
            score += 2
        elif aspect['quality'] == 'challenging':
            score += 1
        else:
            score += 1.5
    
    return min(score / len(aspects) * 5, 10.0)


def find_key_connections(cross_aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify the most important synastry connections
    
    Key connections:
    - Sun-Moon aspects (emotional compatibility)
    - Venus-Mars aspects (romantic/sexual attraction)
    - Moon-Moon aspects (emotional understanding)
    - Sun-Sun aspects (identity resonance)
    - Saturn aspects (karmic/long-term)
    """
    key_pairs = [
        {'sun', 'moon'},
        {'venus', 'mars'},
        {'moon', 'moon'},
        {'sun', 'sun'},
        {'venus', 'venus'},
        {'mars', 'mars'}
    ]
    
    key_connections = []
    
    for aspect in cross_aspects:
        planet_pair = {aspect['planet1'], aspect['planet2']}
        
        if planet_pair in key_pairs:
            key_connections.append({
                **aspect,
                'importance': 'high',
                'category': categorize_connection(planet_pair)
            })
        elif 'saturn' in planet_pair:
            key_connections.append({
                **aspect,
                'importance': 'medium',
                'category': 'karmic'
            })
    
    return sorted(key_connections, key=lambda x: (x['importance'], x['orb']))


def categorize_connection(planet_pair: set) -> str:
    """Categorize what a planetary connection represents"""
    if planet_pair == {'sun', 'moon'}:
        return 'emotional_compatibility'
    elif planet_pair == {'venus', 'mars'}:
        return 'romantic_attraction'
    elif planet_pair == {'moon', 'moon'}:
        return 'emotional_understanding'
    elif planet_pair == {'sun', 'sun'}:
        return 'identity_resonance'
    elif planet_pair == {'venus', 'venus'}:
        return 'shared_values'
    elif planet_pair == {'mars', 'mars'}:
        return 'sexual_chemistry'
    else:
        return 'other'


def analyze_sun_moon_connections(
    planets1: Dict[str, Any],
    planets2: Dict[str, Any],
    cross_aspects: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze Sun-Moon connections specifically"""
    
    # Find Sun-Moon aspects
    sun_moon_aspects = [a for a in cross_aspects 
                       if {a['planet1'], a['planet2']} == {'sun', 'moon'}]
    
    # Calculate element compatibility
    sun1_sign = planets1.get('sun', {}).get('sign', 'Unknown')
    moon1_sign = planets1.get('moon', {}).get('sign', 'Unknown')
    sun2_sign = planets2.get('sun', {}).get('sign', 'Unknown')
    moon2_sign = planets2.get('moon', {}).get('sign', 'Unknown')
    
    element_compat = calculate_element_compatibility(
        [sun1_sign, moon1_sign],
        [sun2_sign, moon2_sign]
    )
    
    return {
        'aspects': sun_moon_aspects,
        'element_compatibility': element_compat,
        'interpretation': "Sun-Moon connections indicate emotional compatibility and mutual understanding"
    }


def analyze_venus_mars_connections(
    planets1: Dict[str, Any],
    planets2: Dict[str, Any],
    cross_aspects: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze Venus-Mars connections for romantic compatibility"""
    
    venus_mars_aspects = [a for a in cross_aspects 
                         if {a['planet1'], a['planet2']} == {'venus', 'mars'}]
    
    venus1_sign = planets1.get('venus', {}).get('sign', 'Unknown')
    mars1_sign = planets1.get('mars', {}).get('sign', 'Unknown')
    venus2_sign = planets2.get('venus', {}).get('sign', 'Unknown')
    mars2_sign = planets2.get('mars', {}).get('sign', 'Unknown')
    
    return {
        'aspects': venus_mars_aspects,
        'venus_signs': [venus1_sign, venus2_sign],
        'mars_signs': [mars1_sign, mars2_sign],
        'interpretation': "Venus-Mars connections indicate romantic and sexual attraction"
    }


def calculate_element_compatibility(signs1: List[str], signs2: List[str]) -> str:
    """Calculate element compatibility between sign sets"""
    element_map = {
        'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
        'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
        'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
        'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
    }
    
    elements1 = {element_map.get(sign, 'Unknown') for sign in signs1}
    elements2 = {element_map.get(sign, 'Unknown') for sign in signs2}
    
    # Compatible elements
    fire_air = ({'Fire', 'Air'} & elements1) and ({'Fire', 'Air'} & elements2)
    earth_water = ({'Earth', 'Water'} & elements1) and ({'Earth', 'Water'} & elements2)
    
    if fire_air or earth_water:
        return 'highly_compatible'
    elif elements1 & elements2:  # Shared elements
        return 'compatible'
    else:
        return 'challenging'


def get_aspect_quality(aspect_name: str) -> str:
    """Determine if aspect is harmonious, challenging, or neutral"""
    harmonious = ['trine', 'sextile']
    challenging = ['square', 'opposition']
    
    if aspect_name in harmonious:
        return 'harmonious'
    elif aspect_name in challenging:
        return 'challenging'
    else:
        return 'neutral'


def get_synastry_aspect_interpretation(planet1: str, planet2: str, aspect: str) -> str:
    """Get interpretation for a synastry aspect"""
    
    # Simplified interpretation system
    interpretations = {
        ('sun', 'moon', 'conjunction'): "Deep emotional understanding and compatibility",
        ('sun', 'moon', 'trine'): "Natural harmony between ego and emotions",
        ('sun', 'moon', 'square'): "Tension between conscious will and emotional needs",
        ('venus', 'mars', 'conjunction'): "Intense romantic and sexual attraction",
        ('venus', 'mars', 'trine'): "Easy flow of affection and desire",
        ('venus', 'mars', 'square'): "Passionate but potentially conflicting desires",
    }
    
    key = (planet1, planet2, aspect)
    return interpretations.get(key, f"{planet1.title()} {aspect} {planet2.title()} creates interesting dynamics")


def generate_synastry_report(
    name1: str,
    name2: str,
    scores: Dict[str, Any],
    key_connections: List[Dict[str, Any]],
    sun_moon: Dict[str, Any],
    venus_mars: Dict[str, Any]
) -> str:
    """Generate a comprehensive synastry report"""
    
    report = f"# Synastry Report: {name1} & {name2}\n\n"
    
    # Overall compatibility
    report += f"## Overall Compatibility: {scores['overall']}/10\n\n"
    
    # Breakdown
    report += "### Compatibility Breakdown:\n"
    report += f"- Romantic: {scores['romantic']}/10\n"
    report += f"- Communication: {scores['communication']}/10\n"
    report += f"- Long-term Potential: {scores['long_term']}/10\n"
    report += f"- Emotional Connection: {scores['emotional']}/10\n\n"
    
    # Key connections
    report += "### Key Connections:\n"
    for conn in key_connections[:5]:
        report += f"- {conn['description']} ({conn['category']}): {conn['interpretation']}\n"
    
    report += "\n"
    
    # Sun-Moon analysis
    if sun_moon.get('aspects'):
        report += "### Sun-Moon Dynamics:\n"
        report += f"Element Compatibility: {sun_moon['element_compatibility']}\n"
        report += f"{sun_moon['interpretation']}\n\n"
    
    # Venus-Mars analysis
    if venus_mars.get('aspects'):
        report += "### Romantic Attraction:\n"
        report += f"{venus_mars['interpretation']}\n"
    
    return report


# Example usage
if __name__ == "__main__":
    from datetime import datetime, time
    
    person1 = {
        'name': 'Alice',
        'birth_date': datetime(1990, 5, 15),
        'birth_time': time(14, 30),
        'birth_place': 'Istanbul',
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timezone': 'Europe/Istanbul'
    }
    
    person2 = {
        'name': 'Bob',
        'birth_date': datetime(1988, 11, 22),
        'birth_time': time(10, 15),
        'birth_place': 'Ankara',
        'latitude': 39.9334,
        'longitude': 32.8597,
        'timezone': 'Europe/Istanbul'
    }
    
    synastry = calculate_synastry(person1, person2)
    print(synastry['report'])
