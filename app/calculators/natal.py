"""
Expanded natal chart calculations with career and child chart analysis
"""

from kerykeion import AstrologicalSubject, KerykeionChartSVG
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_natal_chart(
    birth_data: Dict[str, Any],
    include_svg: bool = False
) -> Dict[str, Any]:
    """
    Calculate complete natal chart
    
    Args:
        birth_data: Birth data dictionary with keys:
            - name, birth_date, birth_time, birth_place
            - latitude, longitude, timezone
        include_svg: Whether to generate SVG chart
        
    Returns:
        Complete natal chart data
    """
    try:
        birth_date = birth_data['birth_date']
        birth_time = birth_data['birth_time']
        
        subject = AstrologicalSubject(
            name=birth_data['name'],
            year=birth_date.year,
            month=birth_date.month,
            day=birth_date.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            city=birth_data['birth_place'],
            nation=birth_data.get('nation', 'TR'),
            lat=birth_data['latitude'],
            lng=birth_data['longitude'],
            tz_str=birth_data['timezone']
        )
        
        # Extract all chart data
        planets = extract_planets(subject)
        houses = extract_houses(subject)
        aspects = extract_aspects(subject)
        elements_modalities = calculate_elements_modalities(planets)
        
        result = {
            'birth_data': birth_data,
            'planets': planets,
            'houses': houses,
            'aspects': aspects,
            'elements_modalities': elements_modalities,
            'chart_shape': determine_chart_shape(planets),
            'dominant_elements': get_dominant_elements(elements_modalities),
            'planetary_dignities': calculate_dignities(planets)
        }
        
        if include_svg:
            svg_chart = KerykeionChartSVG(subject)
            result['svg'] = svg_chart.makeSVG()
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating natal chart: {str(e)}")
        raise


def analyze_career_indicators(natal_chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze career indicators in natal chart
    
    Focuses on:
    - MC (Midheaven) and 10th house
    - 2nd house (income)
    - 6th house (work environment)
    - Sun (life purpose)
    - Saturn (discipline, career structure)
    
    Args:
        natal_chart_data: Complete natal chart data from calculate_natal_chart()
        
    Returns:
        Comprehensive career analysis
    """
    try:
        planets = natal_chart_data['planets']
        houses = natal_chart_data['houses']
        
        # MC Analysis
        mc = houses.get('10', {})
        mc_sign = mc.get('sign', 'Unknown')
        mc_ruler = get_sign_ruler(mc_sign)
        
        # Find planets in career houses
        planets_in_10th = find_planets_in_house(planets, 10)
        planets_in_2nd = find_planets_in_house(planets, 2)
        planets_in_6th = find_planets_in_house(planets, 6)
        
        # Sun analysis (life purpose)
        sun = planets.get('sun', {})
        sun_sign = sun.get('sign', 'Unknown')
        sun_house = sun.get('house', 'Unknown')
        
        # Saturn analysis (career structure)
        saturn = planets.get('saturn', {})
        saturn_sign = saturn.get('sign', 'Unknown')
        saturn_house = saturn.get('house', 'Unknown')
        
        # Determine career types based on MC sign
        career_suggestions = get_career_suggestions_by_mc(mc_sign)
        
        # Natural talents based on elements
        elements = natal_chart_data['elements_modalities']
        natural_talents = determine_natural_talents(elements, sun_sign)
        
        # Work environment preferences (6th house)
        work_environment = analyze_work_environment(planets_in_6th, houses.get('6', {}))
        
        # Income potential (2nd house)
        income_indicators = analyze_income_potential(planets_in_2nd, houses.get('2', {}))
        
        # Career timing (Saturn cycles)
        career_milestones = calculate_career_milestones(saturn)
        
        # Generate comprehensive interpretation
        interpretation = generate_career_interpretation(
            mc_sign=mc_sign,
            mc_ruler=mc_ruler,
            planets_in_10th=planets_in_10th,
            sun_sign=sun_sign,
            sun_house=sun_house,
            saturn_sign=saturn_sign,
            career_suggestions=career_suggestions,
            natural_talents=natural_talents
        )
        
        return {
            'mc_analysis': {
                'mc_sign': mc_sign,
                'mc_ruler': mc_ruler,
                'planets_in_10th': planets_in_10th,
                'career_direction': get_mc_career_direction(mc_sign)
            },
            'life_purpose': {
                'sun_sign': sun_sign,
                'sun_house': sun_house,
                'purpose_themes': get_sun_purpose_themes(sun_sign, sun_house)
            },
            'career_structure': {
                'saturn_sign': saturn_sign,
                'saturn_house': saturn_house,
                'discipline_style': get_saturn_discipline_style(saturn_sign)
            },
            'career_suggestions': career_suggestions,
            'natural_talents': natural_talents,
            'work_environment': work_environment,
            'income_indicators': income_indicators,
            'career_milestones': career_milestones,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Error analyzing career indicators: {str(e)}")
        raise


def analyze_child_chart(natal_chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specialized analysis for children's natal charts
    
    Focuses on:
    - Temperament and personality
    - Learning style
    - Emotional needs
    - Talents and gifts
    - Parenting approaches
    - Potential challenges
    
    Args:
        natal_chart_data: Complete natal chart data
        
    Returns:
        Child-specific analysis
    """
    try:
        planets = natal_chart_data['planets']
        houses = natal_chart_data['houses']
        elements = natal_chart_data['elements_modalities']
        
        # Core personality (Sun, Moon, Ascendant)
        sun = planets.get('sun', {})
        moon = planets.get('moon', {})
        ascendant = houses.get('1', {})
        
        temperament = analyze_child_temperament(sun, moon, ascendant, elements)
        
        # Learning style (Mercury, 3rd house, 9th house)
        mercury = planets.get('mercury', {})
        third_house = houses.get('3', {})
        ninth_house = houses.get('9', {})
        
        learning_style = analyze_learning_style(mercury, third_house, ninth_house)
        
        # Emotional needs (Moon, 4th house)
        moon_sign = moon.get('sign', 'Unknown')
        moon_house = moon.get('house', 'Unknown')
        fourth_house = houses.get('4', {})
        
        emotional_needs = analyze_emotional_needs(moon, fourth_house)
        
        # Natural talents (5th house, Venus, Jupiter)
        venus = planets.get('venus', {})
        jupiter = planets.get('jupiter', {})
        fifth_house = houses.get('5', {})
        
        talents_and_gifts = analyze_child_talents(venus, jupiter, fifth_house, elements)
        
        # Social needs (7th house, 11th house)
        seventh_house = houses.get('7', {})
        eleventh_house = houses.get('11', {})
        
        social_needs = analyze_social_needs(seventh_house, eleventh_house)
        
        # Potential challenges
        saturn = planets.get('saturn', {})
        challenges = identify_child_challenges(saturn, planets)
        
        # Parenting guidance
        parenting_tips = generate_parenting_guidance(
            temperament,
            emotional_needs,
            learning_style,
            moon_sign
        )
        
        # Generate interpretation
        interpretation = generate_child_interpretation(
            temperament,
            learning_style,
            emotional_needs,
            talents_and_gifts,
            parenting_tips
        )
        
        return {
            'temperament': temperament,
            'learning_style': learning_style,
            'emotional_needs': emotional_needs,
            'talents_and_gifts': talents_and_gifts,
            'social_needs': social_needs,
            'potential_challenges': challenges,
            'parenting_guidance': parenting_tips,
            'developmental_stages': calculate_developmental_stages(planets),
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Error analyzing child chart: {str(e)}")
        raise


# Helper Functions

def extract_planets(subject: AstrologicalSubject) -> Dict[str, Any]:
    """Extract planet data from chart"""
    planets = {}
    planet_list = [
        'sun', 'moon', 'mercury', 'venus', 'mars',
        'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
        'chiron', 'north_node'
    ]
    
    for planet_name in planet_list:
        planet_obj = getattr(subject, planet_name, None)
        if planet_obj:
            planets[planet_name] = {
                'longitude': planet_obj['position'],
                'sign': planet_obj['sign'],
                'house': planet_obj.get('house', 'Unknown'),
                'retrograde': planet_obj.get('retrograde', False),
                'degree': planet_obj['abs_pos'] % 30
            }
    
    return planets


def extract_houses(subject: AstrologicalSubject) -> Dict[str, Any]:
    """Extract house data from chart"""
    houses = {}
    
    for i in range(1, 13):
        house_obj = getattr(subject, f'house{i}', None)
        if house_obj:
            houses[str(i)] = {
                'cusp': house_obj['position'],
                'sign': house_obj['sign']
            }
    
    return houses


def extract_aspects(subject: AstrologicalSubject) -> List[Dict[str, Any]]:
    """Extract aspects from chart"""
    aspects = []
    
    # Kerykeion provides aspects
    if hasattr(subject, 'aspects_list'):
        for aspect in subject.aspects_list:
            aspects.append({
                'planet1': aspect['p1_name'],
                'planet2': aspect['p2_name'],
                'aspect': aspect['aspect'],
                'orb': aspect['orbit'],
                'applying': aspect.get('applying', False)
            })
    
    return aspects


def calculate_elements_modalities(planets: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate element and modality distribution"""
    elements = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
    modalities = {'cardinal': 0, 'fixed': 0, 'mutable': 0}
    
    element_map = {
        'Aries': 'fire', 'Taurus': 'earth', 'Gemini': 'air', 'Cancer': 'water',
        'Leo': 'fire', 'Virgo': 'earth', 'Libra': 'air', 'Scorpio': 'water',
        'Sagittarius': 'fire', 'Capricorn': 'earth', 'Aquarius': 'air', 'Pisces': 'water'
    }
    
    modality_map = {
        'Aries': 'cardinal', 'Taurus': 'fixed', 'Gemini': 'mutable', 'Cancer': 'cardinal',
        'Leo': 'fixed', 'Virgo': 'mutable', 'Libra': 'cardinal', 'Scorpio': 'fixed',
        'Sagittarius': 'mutable', 'Capricorn': 'cardinal', 'Aquarius': 'fixed', 'Pisces': 'mutable'
    }
    
    for planet_name, planet_data in planets.items():
        if planet_name == 'north_node':
            continue
        
        sign = planet_data.get('sign')
        if sign:
            elements[element_map.get(sign, 'air')] += 1
            modalities[modality_map.get(sign, 'mutable')] += 1
    
    return {'elements': elements, 'modalities': modalities}


def get_sign_ruler(sign: str) -> str:
    """Get traditional ruler of a sign"""
    rulers = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
        'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
        'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }
    return rulers.get(sign, 'Unknown')


def find_planets_in_house(planets: Dict[str, Any], house_number: int) -> List[str]:
    """Find all planets in a specific house"""
    planets_in_house = []
    for planet_name, planet_data in planets.items():
        if planet_data.get('house') == house_number:
            planets_in_house.append(planet_name)
    return planets_in_house


def get_career_suggestions_by_mc(mc_sign: str) -> List[str]:
    """Get career suggestions based on MC sign"""
    suggestions = {
        'Aries': ['Entrepreneur', 'Military', 'Athletics', 'Emergency Services', 'Leadership'],
        'Taurus': ['Finance', 'Banking', 'Real Estate', 'Agriculture', 'Arts & Crafts'],
        'Gemini': ['Writing', 'Teaching', 'Communications', 'Sales', 'Media'],
        'Cancer': ['Hospitality', 'Nursing', 'Social Work', 'Food Industry', 'Real Estate'],
        'Leo': ['Entertainment', 'Management', 'Politics', 'Creative Arts', 'Education'],
        'Virgo': ['Healthcare', 'Analysis', 'Editing', 'Quality Control', 'Service Industry'],
        'Libra': ['Law', 'Diplomacy', 'Design', 'HR', 'Counseling'],
        'Scorpio': ['Psychology', 'Research', 'Investigation', 'Surgery', 'Finance'],
        'Sagittarius': ['Education', 'Travel', 'Philosophy', 'Publishing', 'International Business'],
        'Capricorn': ['Management', 'Government', 'Architecture', 'Engineering', 'Business'],
        'Aquarius': ['Technology', 'Science', 'Innovation', 'Social Reform', 'Astrology'],
        'Pisces': ['Arts', 'Music', 'Healing', 'Spirituality', 'Film/Photography']
    }
    return suggestions.get(mc_sign, ['General career options'])


def determine_natural_talents(elements: Dict[str, Any], sun_sign: str) -> List[str]:
    """Determine natural talents based on element distribution"""
    talents = []
    element_dist = elements.get('elements', {})
    
    # Dominant element talents
    max_element = max(element_dist, key=element_dist.get)
    
    talent_map = {
        'fire': ['Leadership', 'Enthusiasm', 'Courage', 'Innovation'],
        'earth': ['Practicality', 'Reliability', 'Patience', 'Building'],
        'air': ['Communication', 'Analysis', 'Social Skills', 'Ideas'],
        'water': ['Empathy', 'Intuition', 'Healing', 'Creativity']
    }
    
    talents.extend(talent_map.get(max_element, []))
    return talents


def get_mc_career_direction(mc_sign: str) -> str:
    """Get general career direction based on MC"""
    directions = {
        'Aries': 'Pioneer and initiator - best in leadership roles',
        'Taurus': 'Builder and stabilizer - excel in tangible results',
        'Gemini': 'Communicator and connector - thrive in information exchange',
        'Cancer': 'Nurturer and caretaker - excel in supportive roles',
        'Leo': 'Leader and performer - shine in creative authority',
        'Virgo': 'Analyst and perfectionist - excel in detail-oriented work',
        'Libra': 'Diplomat and harmonizer - thrive in relationship work',
        'Scorpio': 'Transformer and investigator - excel in depth work',
        'Sagittarius': 'Educator and explorer - thrive in expansive roles',
        'Capricorn': 'Manager and achiever - excel in structured authority',
        'Aquarius': 'Innovator and humanitarian - thrive in progressive work',
        'Pisces': 'Artist and healer - excel in creative/spiritual work'
    }
    return directions.get(mc_sign, 'Career direction')


def get_sun_purpose_themes(sun_sign: str, sun_house: int) -> List[str]:
    """Get life purpose themes based on Sun placement"""
    sign_themes = {
        'Aries': ['Self-discovery', 'Courage', 'Independence'],
        'Taurus': ['Security building', 'Value creation', 'Stability'],
        'Gemini': ['Communication', 'Learning', 'Connection'],
        'Cancer': ['Nurturing', 'Emotional security', 'Home'],
        'Leo': ['Self-expression', 'Creativity', 'Recognition'],
        'Virgo': ['Service', 'Improvement', 'Analysis'],
        'Libra': ['Harmony', 'Partnership', 'Balance'],
        'Scorpio': ['Transformation', 'Depth', 'Power'],
        'Sagittarius': ['Expansion', 'Truth', 'Adventure'],
        'Capricorn': ['Achievement', 'Structure', 'Responsibility'],
        'Aquarius': ['Innovation', 'Freedom', 'Community'],
        'Pisces': ['Compassion', 'Spirituality', 'Unity']
    }
    return sign_themes.get(sun_sign, ['General life purpose'])


def get_saturn_discipline_style(saturn_sign: str) -> str:
    """Get discipline and work style based on Saturn sign"""
    styles = {
        'Aries': 'Direct and assertive discipline - learns through action',
        'Taurus': 'Patient and persistent discipline - builds slowly',
        'Gemini': 'Flexible and adaptive discipline - learns through variety',
        'Cancer': 'Emotional discipline - needs security to perform',
        'Leo': 'Proud and dignified discipline - motivated by recognition',
        'Virgo': 'Detailed and perfectionist discipline - masters craft',
        'Libra': 'Balanced and fair discipline - needs harmony',
        'Scorpio': 'Intense and transformative discipline - all or nothing',
        'Sagittarius': 'Philosophical discipline - needs meaning',
        'Capricorn': 'Traditional and structured discipline - natural authority',
        'Aquarius': 'Unconventional discipline - rebels against tradition',
        'Pisces': 'Compassionate discipline - spiritual approach'
    }
    return styles.get(saturn_sign, 'Discipline style')


def analyze_work_environment(planets_in_6th: List[str], sixth_house: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze ideal work environment"""
    sixth_sign = sixth_house.get('sign', 'Unknown')
    
    environment_prefs = {
        'Aries': 'Fast-paced, competitive, independent',
        'Taurus': 'Stable, comfortable, aesthetic',
        'Gemini': 'Varied, social, intellectual',
        'Cancer': 'Nurturing, secure, family-like',
        'Leo': 'Creative, recognition-oriented, leadership',
        'Virgo': 'Organized, efficient, service-oriented',
        'Libra': 'Harmonious, collaborative, beautiful',
        'Scorpio': 'Intense, private, transformative',
        'Sagittarius': 'Free, expansive, philosophical',
        'Capricorn': 'Structured, professional, ambitious',
        'Aquarius': 'Innovative, independent, humanitarian',
        'Pisces': 'Creative, compassionate, spiritual'
    }
    
    return {
        'ideal_environment': environment_prefs.get(sixth_sign, 'Balanced environment'),
        'planets_influencing': planets_in_6th,
        'sixth_house_sign': sixth_sign
    }


def analyze_income_potential(planets_in_2nd: List[str], second_house: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze income potential and money attitudes"""
    second_sign = second_house.get('sign', 'Unknown')
    
    # Check for benefics in 2nd house
    has_jupiter = 'jupiter' in planets_in_2nd
    has_venus = 'venus' in planets_in_2nd
    
    income_level = 'moderate'
    if has_jupiter or has_venus:
        income_level = 'potentially high'
    elif 'saturn' in planets_in_2nd:
        income_level = 'builds slowly'
    
    return {
        'income_potential': income_level,
        'planets_in_2nd': planets_in_2nd,
        'money_attitude': f'Approaches money with {second_sign} energy',
        'second_house_sign': second_sign
    }


def calculate_career_milestones(saturn: Dict[str, Any]) -> List[Dict[str, int]]:
    """Calculate career milestone ages based on Saturn cycles"""
    return [
        {'age': 29, 'milestone': 'First Saturn Return - Career foundation'},
        {'age': 36, 'milestone': 'Saturn square - Mid-career adjustment'},
        {'age': 44, 'milestone': 'Saturn opposition - Career reassessment'},
        {'age': 58, 'milestone': 'Second Saturn Return - Legacy building'}
    ]


def analyze_child_temperament(
    sun: Dict[str, Any],
    moon: Dict[str, Any],
    ascendant: Dict[str, Any],
    elements: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze child's core temperament"""
    sun_sign = sun.get('sign', 'Unknown')
    moon_sign = moon.get('sign', 'Unknown')
    rising_sign = ascendant.get('sign', 'Unknown')
    
    element_dist = elements.get('elements', {})
    dominant_element = max(element_dist, key=element_dist.get)
    
    temperament_map = {
        'fire': 'Active, energetic, enthusiastic, needs physical activity',
        'earth': 'Calm, practical, needs routine and security',
        'air': 'Social, curious, mental stimulation important',
        'water': 'Sensitive, emotional, needs nurturing'
    }
    
    return {
        'sun_sign': sun_sign,
        'moon_sign': moon_sign,
        'rising_sign': rising_sign,
        'dominant_element': dominant_element,
        'temperament': temperament_map.get(dominant_element, 'Balanced'),
        'core_traits': [
            f'Identity: {sun_sign}',
            f'Emotions: {moon_sign}',
            f'Outward manner: {rising_sign}'
        ]
    }


def analyze_learning_style(
    mercury: Dict[str, Any],
    third_house: Dict[str, Any],
    ninth_house: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze child's learning style"""
    mercury_sign = mercury.get('sign', 'Unknown')
    third_sign = third_house.get('sign', 'Unknown')
    
    learning_styles = {
        'Aries': 'Learns by doing, competitive, quick',
        'Taurus': 'Learns slowly but retains well, practical',
        'Gemini': 'Fast learner, needs variety',
        'Cancer': 'Learns through emotions, needs security',
        'Leo': 'Learns through play, needs encouragement',
        'Virgo': 'Detail-oriented, analytical learner',
        'Libra': 'Social learner, needs harmony',
        'Scorpio': 'Intense focus, research-oriented',
        'Sagittarius': 'Philosophical, big-picture learner',
        'Capricorn': 'Structured, goal-oriented learner',
        'Aquarius': 'Innovative, unconventional learner',
        'Pisces': 'Intuitive, creative learner'
    }
    
    return {
        'mercury_sign': mercury_sign,
        'learning_style': learning_styles.get(mercury_sign, 'Balanced learner'),
        'communication_style': f'Communicates in {mercury_sign} manner',
        'is_retrograde': mercury.get('retrograde', False),
        'retrograde_note': 'May process information internally before expressing' if mercury.get('retrograde') else None
    }


def analyze_emotional_needs(moon: Dict[str, Any], fourth_house: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze child's emotional needs"""
    moon_sign = moon.get('sign', 'Unknown')
    
    emotional_needs = {
        'Aries': 'Independence, physical activity, quick emotional processing',
        'Taurus': 'Physical comfort, routine, security, affection',
        'Gemini': 'Communication, variety, mental stimulation',
        'Cancer': 'Nurturing, security, emotional expression',
        'Leo': 'Attention, praise, creative expression',
        'Virgo': 'Order, helping others, feeling useful',
        'Libra': 'Harmony, fairness, social connection',
        'Scorpio': 'Privacy, deep bonds, emotional intensity',
        'Sagittarius': 'Freedom, adventure, optimism',
        'Capricorn': 'Structure, achievement, respect',
        'Aquarius': 'Individuality, friendship, intellectual connection',
        'Pisces': 'Empathy, imagination, spiritual connection'
    }
    
    return {
        'moon_sign': moon_sign,
        'emotional_needs': emotional_needs.get(moon_sign, 'Balanced emotional needs'),
        'how_to_comfort': f'Comforted through {moon_sign} approaches',
        'emotional_style': f'Processes emotions in {moon_sign} way'
    }


def analyze_child_talents(
    venus: Dict[str, Any],
    jupiter: Dict[str, Any],
    fifth_house: Dict[str, Any],
    elements: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze child's natural talents and gifts"""
    venus_sign = venus.get('sign', 'Unknown')
    jupiter_sign = jupiter.get('sign', 'Unknown')
    fifth_sign = fifth_house.get('sign', 'Unknown')
    
    element_dist = elements.get('elements', {})
    
    talents = []
    
    # Element-based talents
    if element_dist.get('fire', 0) >= 3:
        talents.append('Natural leadership and enthusiasm')
    if element_dist.get('earth', 0) >= 3:
        talents.append('Practical skills and building things')
    if element_dist.get('air', 0) >= 3:
        talents.append('Communication and social skills')
    if element_dist.get('water', 0) >= 3:
        talents.append('Artistic and empathic abilities')
    
    return {
        'creative_expression': f'{fifth_sign} creativity style',
        'natural_gifts': talents,
        'venus_talents': f'Appreciation for {venus_sign} beauty',
        'jupiter_expansion': f'Growth through {jupiter_sign} experiences'
    }


def analyze_social_needs(seventh_house: Dict[str, Any], eleventh_house: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze child's social needs"""
    seventh_sign = seventh_house.get('sign', 'Unknown')
    eleventh_sign = eleventh_house.get('sign', 'Unknown')
    
    return {
        'one_on_one_style': f'Relates one-on-one in {seventh_sign} manner',
        'group_style': f'Socializes in groups with {eleventh_sign} energy',
        'friendship_needs': f'Needs friendships that honor {eleventh_sign} qualities'
    }


def identify_child_challenges(saturn: Dict[str, Any], planets: Dict[str, Any]) -> List[str]:
    """Identify potential challenges for child"""
    challenges = []
    saturn_sign = saturn.get('sign', 'Unknown')
    saturn_house = saturn.get('house', 'Unknown')
    
    challenges.append(f'May struggle with {saturn_sign} themes - needs support here')
    challenges.append(f'{saturn_house}th house may be area of insecurity initially')
    
    # Check for retrograde planets
    retrograde_count = sum(1 for p in planets.values() if p.get('retrograde', False))
    if retrograde_count >= 3:
        challenges.append('Multiple retrogrades suggest introspective nature')
    
    return challenges


def generate_parenting_guidance(
    temperament: Dict[str, Any],
    emotional_needs: Dict[str, Any],
    learning_style: Dict[str, Any],
    moon_sign: str
) -> List[str]:
    """Generate practical parenting guidance"""
    guidance = []
    
    # Temperament-based
    element = temperament.get('dominant_element')
    if element == 'fire':
        guidance.append('Provide plenty of physical outlets for energy')
        guidance.append('Encourage independence while maintaining boundaries')
    elif element == 'earth':
        guidance.append('Maintain consistent routines and structure')
        guidance.append('Use tangible rewards and practical examples')
    elif element == 'air':
        guidance.append('Engage in lots of conversation and explain things')
        guidance.append('Provide variety and mental stimulation')
    elif element == 'water':
        guidance.append('Validate emotions and create safe space for feelings')
        guidance.append('Be sensitive to their emotional sensitivity')
    
    # Moon-based emotional guidance
    guidance.append(f'Emotional security comes through {emotional_needs["emotional_needs"]}')
    
    # Learning style guidance
    guidance.append(f'Learning: {learning_style["learning_style"]}')
    
    return guidance


def calculate_developmental_stages(planets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Calculate important developmental stages"""
    return [
        {'age': '0-7', 'focus': 'Moon themes - emotional foundation', 'planet': 'Moon'},
        {'age': '7-14', 'focus': 'Mercury themes - learning and communication', 'planet': 'Mercury'},
        {'age': '14-21', 'focus': 'Venus themes - relationships and values', 'planet': 'Venus'},
        {'age': '21-28', 'focus': 'Mars themes - independence and action', 'planet': 'Mars'},
        {'age': '29', 'focus': 'Saturn Return - maturity milestone', 'planet': 'Saturn'}
    ]


def determine_chart_shape(planets: Dict[str, Any]) -> str:
    """Determine chart shape pattern"""
    # Simplified - would need more complex algorithm
    return "Pattern analysis"


def get_dominant_elements(elements_modalities: Dict[str, Any]) -> Dict[str, Any]:
    """Get dominant element and modality"""
    elements = elements_modalities.get('elements', {})
    modalities = elements_modalities.get('modalities', {})
    
    return {
        'dominant_element': max(elements, key=elements.get) if elements else 'balanced',
        'dominant_modality': max(modalities, key=modalities.get) if modalities else 'balanced'
    }


def calculate_dignities(planets: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate planetary dignities (domicile, exaltation, etc.)"""
    # Simplified version
    dignities = {}
    
    # Would check each planet's sign against dignity tables
    # This is a placeholder
    
    return dignities


def generate_career_interpretation(
    mc_sign: str,
    mc_ruler: str,
    planets_in_10th: List[str],
    sun_sign: str,
    sun_house: int,
    saturn_sign: str,
    career_suggestions: List[str],
    natural_talents: List[str]
) -> str:
    """Generate comprehensive career interpretation"""
    
    parts = []
    
    parts.append(f"Your Midheaven (MC) in {mc_sign} suggests a career path in {mc_sign} style.")
    parts.append(f"\nIdeal career fields: {', '.join(career_suggestions[:3])}.")
    
    if planets_in_10th:
        parts.append(f"\n\nPlanets in your 10th house ({', '.join(planets_in_10th)}) ")
        parts.append("will strongly influence your career and public image.")
    
    parts.append(f"\n\nYour natural talents include: {', '.join(natural_talents)}.")
    parts.append(f"\n\nWith Sun in {sun_sign} in house {sun_house}, your life purpose ")
    parts.append(f"centers around {sun_sign} themes expressed through {sun_house}th house areas.")
    
    return ''.join(parts)


def generate_child_interpretation(
    temperament: Dict[str, Any],
    learning_style: Dict[str, Any],
    emotional_needs: Dict[str, Any],
    talents: Dict[str, Any],
    parenting_tips: List[str]
) -> str:
    """Generate comprehensive child chart interpretation"""
    
    parts = []
    
    parts.append(f"TEMPERAMENT: {temperament['temperament']}\n\n")
    parts.append(f"LEARNING STYLE: {learning_style['learning_style']}\n\n")
    parts.append(f"EMOTIONAL NEEDS: {emotional_needs['emotional_needs']}\n\n")
    
    parts.append("NATURAL TALENTS:\n")
    for talent in talents.get('natural_gifts', []):
        parts.append(f"• {talent}\n")
    
    parts.append("\n\nPARENTING GUIDANCE:\n")
    for tip in parenting_tips[:5]:
        parts.append(f"• {tip}\n")
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    example_birth_data = {
        'name': 'Example Person',
        'birth_date': datetime(1990, 6, 15),
        'birth_time': datetime(1990, 6, 15, 14, 30),
        'birth_place': 'Istanbul',
        'nation': 'TR',
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timezone': 'Europe/Istanbul'
    }
    
    # Calculate natal chart
    natal_chart = calculate_natal_chart(example_birth_data)
    
    # Career analysis
    career = analyze_career_indicators(natal_chart)
    print("Career Analysis:")
    print(f"MC Sign: {career['mc_analysis']['mc_sign']}")
    print(f"Career Direction: {career['mc_analysis']['career_direction']}")
    print(f"\nCareer Suggestions:")
    for suggestion in career['career_suggestions'][:3]:
        print(f"  • {suggestion}")
    
    # Child analysis
    child_analysis = analyze_child_chart(natal_chart)
    print("\n\nChild Chart Analysis:")
    print(f"Temperament: {child_analysis['temperament']['temperament']}")
    print(f"Learning Style: {child_analysis['learning_style']['learning_style']}")
