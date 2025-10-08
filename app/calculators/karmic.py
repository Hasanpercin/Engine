"""
Karmic astrology analysis
Lunar Nodes, Chiron, past life indicators, soul lessons
"""

from typing import Dict, Any, List, Optional
from kerykeion import AstrologicalSubject
import logging

logger = logging.getLogger(__name__)


def analyze_karmic_chart(natal_chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive karmic astrology analysis
    
    Focuses on:
    - Lunar Nodes (North/South Node)
    - Chiron (wounded healer)
    - Saturn (karmic lessons)
    - Pluto (transformation)
    - 12th house (past life, hidden)
    - 8th house (death/rebirth, shared karma)
    - Retrograde planets (unfinished business)
    
    Args:
        natal_chart_data: Complete natal chart data
        
    Returns:
        Comprehensive karmic analysis
    """
    try:
        planets = natal_chart_data['planets']
        houses = natal_chart_data['houses']
        
        # North Node (future path, soul's purpose)
        north_node = planets.get('north_node', {})
        north_node_sign = north_node.get('sign', 'Unknown')
        north_node_house = north_node.get('house', 'Unknown')
        
        # South Node (past life skills, comfort zone)
        south_node_sign = get_opposite_sign(north_node_sign)
        south_node_house = get_opposite_house(north_node_house)
        
        nodal_axis = analyze_nodal_axis(
            north_node_sign,
            north_node_house,
            south_node_sign,
            south_node_house
        )
        
        # Chiron (deepest wound, healing gift)
        chiron = planets.get('chiron', {})
        chiron_analysis = analyze_chiron_wound(chiron, houses)
        
        # Saturn (karmic lessons, responsibilities)
        saturn = planets.get('saturn', {})
        saturn_lessons = analyze_saturn_karma(saturn, houses)
        
        # Pluto (deep transformation, power issues)
        pluto = planets.get('pluto', {})
        pluto_transformation = analyze_pluto_transformation(pluto, houses)
        
        # 12th House (past life, subconscious, hidden)
        twelfth_house = analyze_12th_house_karma(planets, houses.get('12', {}))
        
        # 8th House (shared karma, death/rebirth)
        eighth_house = analyze_8th_house_karma(planets, houses.get('8', {}))
        
        # Retrograde planets (unfinished karmic business)
        retrograde_karma = analyze_retrograde_karma(planets)
        
        # Aspect patterns (karmic configurations)
        karmic_aspects = identify_karmic_aspects(natal_chart_data.get('aspects', []))
        
        # Life purpose synthesis
        soul_purpose = synthesize_soul_purpose(
            nodal_axis,
            chiron_analysis,
            saturn_lessons
        )
        
        # Past life indicators
        past_life_indicators = identify_past_life_themes(
            south_node_sign,
            south_node_house,
            twelfth_house,
            retrograde_karma
        )
        
        return {
            'nodal_axis': nodal_axis,
            'chiron_wound_and_gift': chiron_analysis,
            'saturn_lessons': saturn_lessons,
            'pluto_transformation': pluto_transformation,
            'twelfth_house_karma': twelfth_house,
            'eighth_house_karma': eighth_house,
            'retrograde_karma': retrograde_karma,
            'karmic_aspects': karmic_aspects,
            'soul_purpose': soul_purpose,
            'past_life_indicators': past_life_indicators,
            'karmic_debt_numbers': calculate_karmic_debt_numbers(natal_chart_data),
            'interpretation': generate_karmic_interpretation(
                nodal_axis,
                chiron_analysis,
                saturn_lessons,
                soul_purpose
            )
        }
        
    except Exception as e:
        logger.error(f"Error analyzing karmic chart: {str(e)}")
        raise


def analyze_nodal_axis(
    north_node_sign: str,
    north_node_house: int,
    south_node_sign: str,
    south_node_house: int
) -> Dict[str, Any]:
    """
    Analyze the Lunar Nodes axis
    
    North Node = Soul's evolutionary direction, what to develop
    South Node = Past life gifts, what to release/balance
    """
    
    # North Node meanings by sign
    north_node_meanings = {
        'Aries': {
            'soul_purpose': 'Develop courage, independence, self-assertion',
            'qualities_to_develop': ['Leadership', 'Independence', 'Initiative', 'Courage'],
            'challenge': 'Moving from others-focused to self-focused'
        },
        'Taurus': {
            'soul_purpose': 'Build stability, develop self-worth, ground in the physical',
            'qualities_to_develop': ['Stability', 'Patience', 'Self-worth', 'Practicality'],
            'challenge': 'Moving from crisis to calm, from intensity to peace'
        },
        'Gemini': {
            'soul_purpose': 'Develop communication, curiosity, logical thinking',
            'qualities_to_develop': ['Communication', 'Curiosity', 'Flexibility', 'Learning'],
            'challenge': 'Moving from seeking meaning to gathering information'
        },
        'Cancer': {
            'soul_purpose': 'Develop emotional intelligence, nurturing, home',
            'qualities_to_develop': ['Emotional security', 'Nurturing', 'Family', 'Sensitivity'],
            'challenge': 'Moving from career to home, public to private'
        },
        'Leo': {
            'soul_purpose': 'Develop creativity, self-expression, leadership',
            'qualities_to_develop': ['Creativity', 'Confidence', 'Joy', 'Leadership'],
            'challenge': 'Moving from group to individual, from cool to warm'
        },
        'Virgo': {
            'soul_purpose': 'Develop discernment, service, practical skills',
            'qualities_to_develop': ['Organization', 'Service', 'Health', 'Analysis'],
            'challenge': 'Moving from faith to practical action'
        },
        'Libra': {
            'soul_purpose': 'Develop partnership, balance, diplomacy',
            'qualities_to_develop': ['Partnership', 'Harmony', 'Diplomacy', 'Fairness'],
            'challenge': 'Moving from independence to interdependence'
        },
        'Scorpio': {
            'soul_purpose': 'Develop depth, transformation, shared resources',
            'qualities_to_develop': ['Intimacy', 'Transformation', 'Depth', 'Shared power'],
            'challenge': 'Moving from material security to emotional depth'
        },
        'Sagittarius': {
            'soul_purpose': 'Develop philosophy, faith, higher learning',
            'qualities_to_develop': ['Faith', 'Philosophy', 'Adventure', 'Optimism'],
            'challenge': 'Moving from details to big picture'
        },
        'Capricorn': {
            'soul_purpose': 'Develop responsibility, achievement, authority',
            'qualities_to_develop': ['Responsibility', 'Achievement', 'Structure', 'Authority'],
            'challenge': 'Moving from emotional dependency to self-sufficiency'
        },
        'Aquarius': {
            'soul_purpose': 'Develop innovation, humanitarian ideals, friendship',
            'qualities_to_develop': ['Innovation', 'Humanitarianism', 'Detachment', 'Community'],
            'challenge': 'Moving from personal drama to universal perspective'
        },
        'Pisces': {
            'soul_purpose': 'Develop spirituality, compassion, surrender',
            'qualities_to_develop': ['Spirituality', 'Compassion', 'Intuition', 'Universal love'],
            'challenge': 'Moving from analysis to faith, from order to flow'
        }
    }
    
    # South Node meanings (opposite qualities to release)
    south_node_meanings = {
        'Libra': {
            'past_life_gifts': 'Partnership skills, diplomacy, aesthetics',
            'comfort_zone': 'Depending on others, people-pleasing',
            'to_release': 'Over-dependence on relationships for identity'
        },
        'Scorpio': {
            'past_life_gifts': 'Intensity, depth, psychological insight',
            'comfort_zone': 'Control, secrecy, emotional intensity',
            'to_release': 'Need for control and power over others'
        },
        'Sagittarius': {
            'past_life_gifts': 'Philosophy, teaching, faith',
            'comfort_zone': 'Preaching, knowing it all, restlessness',
            'to_release': 'Over-emphasis on beliefs, restless seeking'
        },
        'Capricorn': {
            'past_life_gifts': 'Leadership, responsibility, achievement',
            'comfort_zone': 'Over-work, emotional distance, authority',
            'to_release': 'Rigid control, fear of vulnerability'
        },
        'Aquarius': {
            'past_life_gifts': 'Innovation, humanitarian ideals, uniqueness',
            'comfort_zone': 'Emotional detachment, rebellion, isolation',
            'to_release': 'Detachment from personal emotions'
        },
        'Pisces': {
            'past_life_gifts': 'Spirituality, compassion, mysticism',
            'comfort_zone': 'Escapism, victimhood, confusion',
            'to_release': 'Escaping reality, martyrdom'
        },
        'Aries': {
            'past_life_gifts': 'Independence, courage, pioneering',
            'comfort_zone': 'Self-focus, impulsiveness, aggression',
            'to_release': 'Excessive independence, ignoring others'
        },
        'Taurus': {
            'past_life_gifts': 'Stability, sensuality, practicality',
            'comfort_zone': 'Stubbornness, materialism, resistance',
            'to_release': 'Over-attachment to material security'
        },
        'Gemini': {
            'past_life_gifts': 'Communication, curiosity, versatility',
            'comfort_zone': 'Scattered energy, superficiality, gossip',
            'to_release': 'Information overload, lack of depth'
        },
        'Cancer': {
            'past_life_gifts': 'Nurturing, emotional sensitivity, family',
            'comfort_zone': 'Emotional dependency, clinging, moodiness',
            'to_release': 'Over-dependence on family/home'
        },
        'Leo': {
            'past_life_gifts': 'Creativity, leadership, self-expression',
            'comfort_zone': 'Need for attention, drama, ego',
            'to_release': 'Excessive need for recognition'
        },
        'Virgo': {
            'past_life_gifts': 'Service, analysis, health awareness',
            'comfort_zone': 'Perfectionism, criticism, worry',
            'to_release': 'Over-analysis, critical judgment'
        }
    }
    
    north_info = north_node_meanings.get(north_node_sign, {
        'soul_purpose': f'Develop {north_node_sign} qualities',
        'qualities_to_develop': [north_node_sign],
        'challenge': 'Evolutionary growth'
    })
    
    south_info = south_node_meanings.get(south_node_sign, {
        'past_life_gifts': f'{south_node_sign} skills',
        'comfort_zone': f'{south_node_sign} patterns',
        'to_release': 'Old patterns'
    })
    
    return {
        'north_node': {
            'sign': north_node_sign,
            'house': north_node_house,
            'soul_purpose': north_info['soul_purpose'],
            'qualities_to_develop': north_info['qualities_to_develop'],
            'life_direction': f'Move towards {north_node_sign} themes in {north_node_house}th house'
        },
        'south_node': {
            'sign': south_node_sign,
            'house': south_node_house,
            'past_life_gifts': south_info['past_life_gifts'],
            'comfort_zone': south_info['comfort_zone'],
            'to_release': south_info['to_release'],
            'caution': f'Don\'t over-rely on {south_node_sign} patterns in {south_node_house}th house'
        },
        'axis_challenge': north_info['challenge'],
        'life_lesson': f'Balance {south_node_sign} gifts with {north_node_sign} growth'
    }


def analyze_chiron_wound(chiron: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze Chiron - the wounded healer
    
    Chiron represents our deepest wound and our greatest healing gift
    """
    
    chiron_sign = chiron.get('sign', 'Unknown')
    chiron_house = chiron.get('house', 'Unknown')
    
    # Chiron wounds by sign
    chiron_wounds = {
        'Aries': {
            'wound': 'Wounded sense of self, lack of confidence, fear of asserting self',
            'healing_gift': 'Teaching others to be courageous and authentic',
            'path_to_healing': 'Embrace your uniqueness, assert your needs'
        },
        'Taurus': {
            'wound': 'Wounded self-worth, material insecurity, fear of scarcity',
            'healing_gift': 'Teaching others about self-value and abundance',
            'path_to_healing': 'Develop self-worth independent of possessions'
        },
        'Gemini': {
            'wound': 'Wounded communication, fear of being misunderstood, learning difficulties',
            'healing_gift': 'Helping others find their voice',
            'path_to_healing': 'Trust your own truth, speak authentically'
        },
        'Cancer': {
            'wound': 'Wounded family/childhood, emotional abandonment, fear of vulnerability',
            'healing_gift': 'Nurturing and creating emotional safety for others',
            'path_to_healing': 'Parent yourself, create your own emotional security'
        },
        'Leo': {
            'wound': 'Wounded creativity/expression, shame, fear of being seen',
            'healing_gift': 'Inspiring others to shine',
            'path_to_healing': 'Express yourself authentically, own your talents'
        },
        'Virgo': {
            'wound': 'Wounded perfectionism, health issues, fear of imperfection',
            'healing_gift': 'Helping others find wholeness',
            'path_to_healing': 'Accept imperfection, practice self-compassion'
        },
        'Libra': {
            'wound': 'Wounded relationships, co-dependency, fear of rejection',
            'healing_gift': 'Teaching healthy relationship dynamics',
            'path_to_healing': 'Balance self and others, set boundaries'
        },
        'Scorpio': {
            'wound': 'Wounded trust, betrayal, fear of intimacy/transformation',
            'healing_gift': 'Guiding others through transformation',
            'path_to_healing': 'Trust the process of death and rebirth'
        },
        'Sagittarius': {
            'wound': 'Wounded beliefs, loss of faith, fear of meaning',
            'healing_gift': 'Restoring faith and meaning for others',
            'path_to_healing': 'Find your own truth, embrace the journey'
        },
        'Capricorn': {
            'wound': 'Wounded authority, fear of failure, over-responsibility',
            'healing_gift': 'Teaching responsible success',
            'path_to_healing': 'Balance ambition with self-compassion'
        },
        'Aquarius': {
            'wound': 'Wounded belonging, alienation, fear of rejection for uniqueness',
            'healing_gift': 'Creating acceptance for all',
            'path_to_healing': 'Celebrate your uniqueness, find your tribe'
        },
        'Pisces': {
            'wound': 'Wounded spirituality, loss of connection, victim mentality',
            'healing_gift': 'Spiritual healing and compassion',
            'path_to_healing': 'Set boundaries, ground your spirituality'
        }
    }
    
    # Chiron wounds by house
    house_wounds = {
        1: 'Identity and self-expression',
        2: 'Self-worth and material security',
        3: 'Communication and early learning',
        4: 'Family, home, and emotional foundation',
        5: 'Creativity, joy, and self-expression',
        6: 'Health, work, and service',
        7: 'Relationships and partnerships',
        8: 'Intimacy, transformation, and shared resources',
        9: 'Beliefs, higher learning, and meaning',
        10: 'Career, public life, and achievement',
        11: 'Community, friendships, and groups',
        12: 'Spirituality, isolation, and the unconscious'
    }
    
    wound_info = chiron_wounds.get(chiron_sign, {
        'wound': f'{chiron_sign} wound',
        'healing_gift': 'Healing others',
        'path_to_healing': 'Self-healing journey'
    })
    
    return {
        'chiron_sign': chiron_sign,
        'chiron_house': chiron_house,
        'primary_wound': wound_info['wound'],
        'wound_area': house_wounds.get(chiron_house, 'Life area'),
        'healing_gift': wound_info['healing_gift'],
        'path_to_healing': wound_info['path_to_healing'],
        'chiron_return_age': '50-51 years (major healing milestone)',
        'note': 'Your wound becomes your wisdom - use it to help others'
    }


def analyze_saturn_karma(saturn: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze Saturn - karmic lessons and responsibilities
    
    Saturn shows where we face tests and learn discipline
    """
    
    saturn_sign = saturn.get('sign', 'Unknown')
    saturn_house = saturn.get('house', 'Unknown')
    is_retrograde = saturn.get('retrograde', False)
    
    # Saturn lessons by sign
    saturn_lessons = {
        'Aries': 'Learn to assert yourself with maturity, develop patient leadership',
        'Taurus': 'Learn financial responsibility, develop sustainable security',
        'Gemini': 'Learn focused communication, develop mental discipline',
        'Cancer': 'Learn emotional maturity, create healthy family structures',
        'Leo': 'Learn humble creativity, develop authentic self-expression',
        'Virgo': 'Learn healthy perfectionism, develop compassionate service',
        'Libra': 'Learn relationship responsibility, develop mature partnerships',
        'Scorpio': 'Learn emotional control, develop transformative power',
        'Sagittarius': 'Learn grounded philosophy, develop practical wisdom',
        'Capricorn': 'Learn balanced ambition, develop responsible authority',
        'Aquarius': 'Learn structured innovation, develop committed friendships',
        'Pisces': 'Learn spiritual discipline, develop practical compassion'
    }
    
    # Saturn by house
    house_lessons = {
        1: 'Self-mastery and identity development',
        2: 'Financial responsibility and self-worth',
        3: 'Communication discipline and mental structure',
        4: 'Emotional maturity and family responsibilities',
        5: 'Creative discipline and joy through effort',
        6: 'Work ethic and health maintenance',
        7: 'Relationship commitments and partnership lessons',
        8: 'Transformation and shared resource management',
        9: 'Philosophical discipline and educational structure',
        10: 'Career responsibility and public achievement',
        11: 'Community commitments and goal discipline',
        12: 'Spiritual discipline and facing the unconscious'
    }
    
    lesson = saturn_lessons.get(saturn_sign, f'Lessons in {saturn_sign}')
    house_area = house_lessons.get(saturn_house, f'{saturn_house}th house lessons')
    
    return {
        'saturn_sign': saturn_sign,
        'saturn_house': saturn_house,
        'is_retrograde': is_retrograde,
        'primary_lesson': lesson,
        'life_area': house_area,
        'saturn_return_ages': [29, 58, 87],
        'current_lesson': f'Mastering {saturn_sign} themes in {house_area}',
        'retrograde_note': (
            'Saturn retrograde: Internalized authority, self-discipline focus, '
            'karmic lessons from past lives'
        ) if is_retrograde else None
    }


def analyze_pluto_transformation(pluto: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze Pluto - deep transformation and power
    
    Pluto shows where we undergo profound transformation
    """
    
    pluto_sign = pluto.get('sign', 'Unknown')
    pluto_house = pluto.get('house', 'Unknown')
    
    # Pluto generational themes
    pluto_generation = {
        'Leo': 'Generation of personal power and creativity (1937-1958)',
        'Virgo': 'Generation of service and health transformation (1958-1972)',
        'Libra': 'Generation of relationship revolution (1972-1984)',
        'Scorpio': 'Generation of deep transformation (1984-1995)',
        'Sagittarius': 'Generation of belief transformation (1995-2008)',
        'Capricorn': 'Generation of structural transformation (2008-2024)',
        'Aquarius': 'Generation of technological/social transformation (2024-2043)'
    }
    
    # Pluto by house (personal transformation)
    house_transformation = {
        1: 'Personal power and identity transformation',
        2: 'Material and self-worth transformation',
        3: 'Communication and mental transformation',
        4: 'Deep family and emotional transformation',
        5: 'Creative and romantic transformation',
        6: 'Work and health transformation',
        7: 'Relationship and partnership transformation',
        8: 'Profound death/rebirth cycles',
        9: 'Belief and philosophical transformation',
        10: 'Career and public image transformation',
        11: 'Social and community transformation',
        12: 'Spiritual and subconscious transformation'
    }
    
    return {
        'pluto_sign': pluto_sign,
        'pluto_house': pluto_house,
        'generational_theme': pluto_generation.get(pluto_sign, 'Generational transformation'),
        'personal_transformation': house_transformation.get(pluto_house, 'Transformation area'),
        'note': 'Pluto requires surrender to transformation - resistance creates crisis'
    }


def analyze_12th_house_karma(planets: Dict[str, Any], twelfth_house: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze 12th house - past life, hidden, subconscious
    """
    
    twelfth_sign = twelfth_house.get('sign', 'Unknown')
    planets_in_12th = [
        name for name, data in planets.items()
        if data.get('house') == 12
    ]
    
    return {
        'twelfth_house_sign': twelfth_sign,
        'planets_in_12th': planets_in_12th,
        'theme': 'Past life memories, hidden gifts, spiritual lessons',
        'interpretation': (
            f'The 12th house in {twelfth_sign} suggests past life experiences '
            f'related to {twelfth_sign} themes. Planets here: {", ".join(planets_in_12th) if planets_in_12th else "None"}'
        )
    }


def analyze_8th_house_karma(planets: Dict[str, Any], eighth_house: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze 8th house - shared karma, transformation
    """
    
    eighth_sign = eighth_house.get('sign', 'Unknown')
    planets_in_8th = [
        name for name, data in planets.items()
        if data.get('house') == 8
    ]
    
    return {
        'eighth_house_sign': eighth_sign,
        'planets_in_8th': planets_in_8th,
        'theme': 'Shared karma, death/rebirth, intimacy lessons',
        'interpretation': (
            f'The 8th house in {eighth_sign} shows transformation through '
            f'{eighth_sign} themes'
        )
    }


def analyze_retrograde_karma(planets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze retrograde planets - unfinished karmic business
    
    Retrograde planets suggest areas of unfinished business from past lives
    """
    
    retrograde_planets = []
    
    for planet_name, planet_data in planets.items():
        if planet_data.get('retrograde', False):
            retrograde_planets.append({
                'planet': planet_name,
                'sign': planet_data.get('sign'),
                'house': planet_data.get('house'),
                'karmic_meaning': get_retrograde_karmic_meaning(planet_name)
            })
    
    return {
        'retrograde_count': len(retrograde_planets),
        'retrograde_planets': retrograde_planets,
        'significance': (
            'Many retrogrades (3+) suggest an old soul with much karmic work'
            if len(retrograde_planets) >= 3
            else 'Few retrogrades suggest focus on external lessons'
        )
    }


def get_retrograde_karmic_meaning(planet_name: str) -> str:
    """Get karmic meaning of retrograde planet"""
    
    meanings = {
        'mercury': 'Past life communication or learning issues to resolve',
        'venus': 'Past life relationship or value lessons',
        'mars': 'Past life action or anger issues to master',
        'jupiter': 'Past life excess or philosophical lessons',
        'saturn': 'Past life authority or responsibility karma',
        'uranus': 'Past life rebellion or individuation',
        'neptune': 'Past life spiritual or boundary lessons',
        'pluto': 'Past life power or transformation issues'
    }
    
    return meanings.get(planet_name, 'Karmic lessons')


def identify_karmic_aspects(aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify karmic aspect patterns
    
    - North Node aspects
    - Saturn aspects
    - Pluto aspects
    - 12th house planet aspects
    """
    
    karmic_aspects = []
    
    for aspect in aspects:
        planet1 = aspect.get('planet1', '').lower()
        planet2 = aspect.get('planet2', '').lower()
        aspect_type = aspect.get('aspect', '')
        
        # North Node aspects
        if 'north_node' in [planet1, planet2]:
            karmic_aspects.append({
                'aspect': f"{aspect['planet1']} {aspect_type} {aspect['planet2']}",
                'significance': 'Node aspect - karmic relationship between planets',
                'orb': aspect.get('orb')
            })
        
        # Saturn aspects (karmic lessons)
        if 'saturn' in [planet1, planet2]:
            other_planet = planet2 if planet1 == 'saturn' else planet1
            karmic_aspects.append({
                'aspect': f"{aspect['planet1']} {aspect_type} {aspect['planet2']}",
                'significance': f'Saturn-{other_planet}: Karmic lesson in {other_planet} area',
                'orb': aspect.get('orb')
            })
    
    return karmic_aspects[:5]  # Top 5 most significant


def synthesize_soul_purpose(
    nodal_axis: Dict[str, Any],
    chiron_analysis: Dict[str, Any],
    saturn_lessons: Dict[str, Any]
) -> str:
    """Synthesize overall soul purpose from karmic indicators"""
    
    north_node_purpose = nodal_axis['north_node']['soul_purpose']
    chiron_gift = chiron_analysis['healing_gift']
    saturn_mastery = saturn_lessons['primary_lesson']
    
    synthesis = (
        f"SOUL PURPOSE SYNTHESIS:\n\n"
        f"Your soul's evolutionary direction (North Node): {north_node_purpose}\n\n"
        f"Your healing gift to the world (Chiron): {chiron_gift}\n\n"
        f"Your karmic lesson to master (Saturn): {saturn_mastery}\n\n"
        f"By integrating these three themes, you fulfill your soul's purpose and "
        f"contribute your unique gifts to the world."
    )
    
    return synthesis


def identify_past_life_themes(
    south_node_sign: str,
    south_node_house: int,
    twelfth_house: Dict[str, Any],
    retrograde_karma: Dict[str, Any]
) -> List[str]:
    """Identify likely past life themes"""
    
    themes = []
    
    themes.append(f"Past life expertise in {south_node_sign} themes (South Node)")
    themes.append(f"Past life experiences in {south_node_house}th house areas")
    
    if twelfth_house.get('planets_in_12th'):
        themes.append(
            f"Hidden past life memories related to: "
            f"{', '.join(twelfth_house['planets_in_12th'])}"
        )
    
    if retrograde_karma['retrograde_count'] >= 3:
        themes.append("Old soul with multiple past lives of unfinished business")
    
    return themes


def calculate_karmic_debt_numbers(natal_chart_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calculate karmic debt numbers (from numerology perspective)
    
    Karmic debt numbers: 13, 14, 16, 19
    Found in birth date
    """
    # This would connect to numerology module
    # Placeholder for now
    return {
        'note': 'Karmic debt numbers calculation (integrate with numerology module)',
        'karmic_debts': []
    }


def get_opposite_sign(sign: str) -> str:
    """Get opposite sign in zodiac"""
    opposites = {
        'Aries': 'Libra', 'Libra': 'Aries',
        'Taurus': 'Scorpio', 'Scorpio': 'Taurus',
        'Gemini': 'Sagittarius', 'Sagittarius': 'Gemini',
        'Cancer': 'Capricorn', 'Capricorn': 'Cancer',
        'Leo': 'Aquarius', 'Aquarius': 'Leo',
        'Virgo': 'Pisces', 'Pisces': 'Virgo'
    }
    return opposites.get(sign, 'Unknown')


def get_opposite_house(house: int) -> int:
    """Get opposite house"""
    if house == 'Unknown':
        return 'Unknown'
    return ((house + 5) % 12) + 1


def generate_karmic_interpretation(
    nodal_axis: Dict[str, Any],
    chiron_analysis: Dict[str, Any],
    saturn_lessons: Dict[str, Any],
    soul_purpose: str
) -> str:
    """Generate comprehensive karmic interpretation"""
    
    parts = []
    
    parts.append("KARMIC ASTROLOGY REPORT\n\n")
    parts.append("=" * 50 + "\n\n")
    
    parts.append("1. SOUL'S EVOLUTIONARY PATH (Lunar Nodes)\n\n")
    parts.append(f"North Node in {nodal_axis['north_node']['sign']}: ")
    parts.append(f"{nodal_axis['north_node']['soul_purpose']}\n\n")
    parts.append(f"South Node in {nodal_axis['south_node']['sign']}: ")
    parts.append(f"Release {nodal_axis['south_node']['to_release']}\n\n")
    
    parts.append("2. CHIRON WOUND AND HEALING GIFT\n\n")
    parts.append(f"Wound: {chiron_analysis['primary_wound']}\n")
    parts.append(f"Gift: {chiron_analysis['healing_gift']}\n")
    parts.append(f"Path: {chiron_analysis['path_to_healing']}\n\n")
    
    parts.append("3. SATURN KARMIC LESSONS\n\n")
    parts.append(f"Lesson: {saturn_lessons['primary_lesson']}\n")
    parts.append(f"Area: {saturn_lessons['life_area']}\n\n")
    
    parts.append("4. SOUL PURPOSE SYNTHESIS\n\n")
    parts.append(soul_purpose)
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    # Example: would need full natal chart data
    example_natal = {
        'planets': {
            'north_node': {'longitude': 125.5, 'sign': 'Leo', 'house': 7},
            'chiron': {'longitude': 85.2, 'sign': 'Gemini', 'house': 5},
            'saturn': {'longitude': 310.8, 'sign': 'Aquarius', 'house': 1, 'retrograde': True},
            'pluto': {'longitude': 220.5, 'sign': 'Scorpio', 'house': 10},
            'mercury': {'longitude': 45.3, 'sign': 'Taurus', 'house': 4, 'retrograde': True}
        },
        'houses': {
            '1': {'cusp': 300.0, 'sign': 'Aquarius'},
            '7': {'cusp': 120.0, 'sign': 'Leo'},
            '12': {'cusp': 270.0, 'sign': 'Capricorn'}
        },
        'aspects': []
    }
    
    karmic = analyze_karmic_chart(example_natal)
    
    print("Karmic Analysis:")
    print(f"North Node: {karmic['nodal_axis']['north_node']['sign']}")
    print(f"Soul Purpose: {karmic['nodal_axis']['north_node']['soul_purpose']}")
    print(f"\nChiron Wound: {karmic['chiron_wound_and_gift']['primary_wound']}")
    print(f"Healing Gift: {karmic['chiron_wound_and_gift']['healing_gift']}")
