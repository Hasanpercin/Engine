"""
Horary astrology - answering specific questions through chart cast at moment of question
Complex traditional rules and judgment
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from kerykeion import AstrologicalSubject
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def analyze_horary_question(
    question: str,
    question_time: datetime,
    location: Dict[str, Any],
    querent_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze horary question
    
    Horary astrology answers specific questions by casting a chart
    for the moment the question is asked (or understood by astrologer)
    
    Args:
        question: The specific question being asked
        question_time: Exact time question was asked/understood
        location: Location where question was asked
        querent_details: Optional details about questioner
        
    Returns:
        Complete horary analysis with judgment
    """
    try:
        logger.info(f"Analyzing horary question: {question[:50]}...")
        
        # Create horary chart
        horary_chart = AstrologicalSubject(
            name=f"Horary: {question[:30]}",
            year=question_time.year,
            month=question_time.month,
            day=question_time.day,
            hour=question_time.hour,
            minute=question_time.minute,
            city=location.get('city', 'Location'),
            nation=location.get('nation', 'TR'),
            lat=location['latitude'],
            lng=location['longitude'],
            tz_str=location.get('timezone', 'UTC')
        )
        
        # Extract chart data
        planets = extract_horary_planets(horary_chart)
        houses = extract_horary_houses(horary_chart)
        aspects = extract_horary_aspects(horary_chart)
        
        # Radical chart? (Is chart valid for judgment?)
        radical_check = check_if_radical(planets, houses)
        
        if not radical_check['is_radical']:
            return {
                'question': question,
                'question_time': question_time.isoformat(),
                'is_radical': False,
                'reason': radical_check['reason'],
                'judgment': 'Chart is not radical - question cannot be judged reliably',
                'advice': radical_check['advice']
            }
        
        # Determine question type and houses involved
        question_analysis = analyze_question_type(question)
        
        # Identify significators (Querent and Quesited)
        significators = identify_significators(
            question_analysis,
            planets,
            houses
        )
        
        # Check aspects between significators
        aspect_analysis = analyze_significator_aspects(
            significators,
            aspects,
            planets
        )
        
        # Check receptions (mutual reception, etc.)
        receptions = analyze_receptions(significators, planets)
        
        # Apply/Separate analysis
        applying_separating = analyze_applying_separating(aspect_analysis, planets)
        
        # Check for prohibitions and frustrations
        prohibitions = check_prohibitions(aspect_analysis, planets)
        
        # Translation of light / Collection of light
        translations = check_translation_of_light(significators, aspects, planets)
        
        # Timing estimate
        timing = estimate_timing(aspect_analysis, houses, planets)
        
        # Final judgment
        judgment = make_horary_judgment(
            question_analysis,
            significators,
            aspect_analysis,
            receptions,
            applying_separating,
            prohibitions,
            translations,
            radical_check
        )
        
        return {
            'question': question,
            'question_time': question_time.isoformat(),
            'location': location,
            'is_radical': True,
            'radical_check': radical_check,
            'question_analysis': question_analysis,
            'significators': significators,
            'aspect_analysis': aspect_analysis,
            'receptions': receptions,
            'applying_separating': applying_separating,
            'prohibitions': prohibitions,
            'translations': translations,
            'timing': timing,
            'judgment': judgment,
            'confidence_level': assess_confidence_level(judgment, aspect_analysis),
            'interpretation': generate_horary_interpretation(
                question,
                question_analysis,
                significators,
                judgment
            )
        }
        
    except Exception as e:
        logger.error(f"Error analyzing horary question: {str(e)}")
        raise


def check_if_radical(planets: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if horary chart is "radical" (fit to be judged)
    
    Considerations against radicality:
    1. Ascendant in early degrees (0-3°) - too soon
    2. Ascendant in late degrees (27-30°) - too late
    3. Moon void of course
    4. Saturn in 7th house (often indicates astrologer can't judge)
    5. Saturn in 1st house (querent not serious)
    """
    
    is_radical = True
    reasons = []
    advice = []
    
    # Check Ascendant degree
    asc_cusp = houses.get('1', {}).get('cusp', 0)
    asc_degree = asc_cusp % 30
    
    if asc_degree < 3:
        is_radical = False
        reasons.append("Ascendant too early (< 3°) - question premature")
        advice.append("Wait and re-ask question later")
    
    if asc_degree > 27:
        is_radical = False
        reasons.append("Ascendant too late (> 27°) - question overdue or outcome already set")
        advice.append("Outcome may already be decided")
    
    # Check Moon void of course
    moon = planets.get('moon', {})
    moon_void = check_moon_void_of_course(moon, planets)
    
    if moon_void:
        # Not always non-radical, but cautionary
        reasons.append("Moon is void of course - 'nothing will come of the matter'")
        advice.append("Outcome likely to be 'nothing happens' or unexpected turn")
    
    # Check Saturn in 7th (traditional: astrologer can't judge)
    saturn = planets.get('saturn', {})
    if saturn.get('house') == 7:
        reasons.append("Saturn in 7th house - traditional: astrologer may not be able to judge clearly")
        advice.append("Seek second opinion or wait to re-ask")
    
    # Check Saturn in 1st (querent not serious)
    if saturn.get('house') == 1:
        reasons.append("Saturn in 1st house - querent may not be serious about question")
        advice.append("Reflect on your true intentions with this question")
    
    return {
        'is_radical': is_radical if not reasons else len(reasons) <= 2,  # Allow minor issues
        'reason': ' | '.join(reasons) if reasons else 'Chart is radical',
        'advice': advice,
        'warning_count': len(reasons)
    }


def analyze_question_type(question: str) -> Dict[str, Any]:
    """
    Analyze question type to determine relevant houses
    
    Question types:
    - Romance/Love: 5th (dating), 7th (partnership)
    - Marriage: 7th house
    - Career/Job: 10th house, 6th (work)
    - Money: 2nd house
    - Lost object: Determined by what was lost
    - Relocation: 4th house
    - Legal matters: 9th house
    - Health: 1st, 6th house
    """
    
    question_lower = question.lower()
    
    # Keywords for categorization
    if any(word in question_lower for word in ['love', 'relationship', 'dating', 'boyfriend', 'girlfriend']):
        if 'marry' in question_lower or 'marriage' in question_lower:
            return {
                'type': 'marriage',
                'querent_house': 1,
                'quesited_house': 7,
                'description': 'Marriage question - 7th house'
            }
        else:
            return {
                'type': 'romance',
                'querent_house': 1,
                'quesited_house': 5,
                'description': 'Romance/dating question - 5th house'
            }
    
    elif any(word in question_lower for word in ['job', 'career', 'promotion', 'work', 'employ']):
        return {
            'type': 'career',
            'querent_house': 1,
            'quesited_house': 10,
            'secondary_house': 6,
            'description': 'Career question - 10th house (career), 6th house (work)'
        }
    
    elif any(word in question_lower for word in ['money', 'finance', 'salary', 'income', 'pay']):
        return {
            'type': 'money',
            'querent_house': 1,
            'quesited_house': 2,
            'description': 'Money question - 2nd house'
        }
    
    elif any(word in question_lower for word in ['lost', 'find', 'missing', 'where is']):
        return {
            'type': 'lost_object',
            'querent_house': 1,
            'quesited_house': 2,  # Default, but depends on object
            'description': 'Lost object question - house depends on what was lost'
        }
    
    elif any(word in question_lower for word in ['move', 'relocat', 'house', 'home', 'apartment']):
        return {
            'type': 'relocation',
            'querent_house': 1,
            'quesited_house': 4,
            'description': 'Home/relocation question - 4th house'
        }
    
    elif any(word in question_lower for word in ['legal', 'lawsuit', 'court', 'contract']):
        return {
            'type': 'legal',
            'querent_house': 1,
            'quesited_house': 9,
            'description': 'Legal question - 9th house'
        }
    
    elif any(word in question_lower for word in ['health', 'sick', 'illness', 'doctor', 'medical']):
        return {
            'type': 'health',
            'querent_house': 1,
            'quesited_house': 6,
            'description': 'Health question - 1st and 6th house'
        }
    
    else:
        return {
            'type': 'general',
            'querent_house': 1,
            'quesited_house': 7,  # Default to 7th for "other"
            'description': 'General question'
        }


def identify_significators(
    question_analysis: Dict[str, Any],
    planets: Dict[str, Any],
    houses: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Identify significators:
    - Querent (person asking): 1st house ruler + Moon
    - Quesited (thing asked about): Relevant house ruler
    """
    
    querent_house = question_analysis['querent_house']
    quesited_house = question_analysis['quesited_house']
    
    # Querent significator: 1st house ruler
    first_house_sign = houses.get(str(querent_house), {}).get('sign', 'Aries')
    querent_ruler = get_sign_ruler(first_house_sign)
    
    querent_planet_data = None
    if querent_ruler.lower() in planets:
        querent_planet_data = planets[querent_ruler.lower()]
    
    # Moon is co-significator of querent
    moon_data = planets.get('moon', {})
    
    # Quesited significator: Relevant house ruler
    quesited_house_sign = houses.get(str(quesited_house), {}).get('sign', 'Libra')
    quesited_ruler = get_sign_ruler(quesited_house_sign)
    
    quesited_planet_data = None
    if quesited_ruler.lower() in planets:
        quesited_planet_data = planets[quesited_ruler.lower()]
    
    return {
        'querent': {
            'primary': querent_ruler,
            'data': querent_planet_data,
            'house': querent_house,
            'co_significator': 'Moon',
            'moon_data': moon_data
        },
        'quesited': {
            'primary': quesited_ruler,
            'data': quesited_planet_data,
            'house': quesited_house
        }
    }


def analyze_significator_aspects(
    significators: Dict[str, Any],
    aspects: List[Dict[str, Any]],
    planets: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze aspects between significators
    
    Key aspects in horary:
    - Conjunction (0°): Strong connection
    - Sextile (60°): Opportunity, mild positive
    - Square (90°): Challenge, but still connection
    - Trine (120°): Easy flow, positive
    - Opposition (180°): Awareness, confrontation
    
    Also important:
    - Applying vs Separating
    - Orb (tight orbs more significant)
    """
    
    querent_planet = significators['querent']['primary'].lower()
    quesited_planet = significators['quesited']['primary'].lower()
    
    # Find aspects between significators
    significator_aspects = []
    
    for aspect in aspects:
        planet1 = aspect.get('planet1', '').lower()
        planet2 = aspect.get('planet2', '').lower()
        
        if (querent_planet in [planet1, planet2]) and (quesited_planet in [planet1, planet2]):
            significator_aspects.append(aspect)
    
    # Also check Moon to quesited
    moon_aspects = []
    for aspect in aspects:
        planet1 = aspect.get('planet1', '').lower()
        planet2 = aspect.get('planet2', '').lower()
        
        if ('moon' in [planet1, planet2]) and (quesited_planet in [planet1, planet2]):
            moon_aspects.append(aspect)
    
    has_aspect = len(significator_aspects) > 0 or len(moon_aspects) > 0
    
    return {
        'has_aspect': has_aspect,
        'querent_quesited_aspects': significator_aspects,
        'moon_quesited_aspects': moon_aspects,
        'primary_aspect': significator_aspects[0] if significator_aspects else None,
        'aspect_quality': assess_aspect_quality(significator_aspects[0]) if significator_aspects else 'No aspect'
    }


def analyze_receptions(significators: Dict[str, Any], planets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze receptions between significators
    
    Reception: When one planet is in a sign ruled by another
    Mutual Reception: Both planets in each other's signs
    This is VERY favorable in horary
    """
    
    querent_data = significators['querent']['data']
    quesited_data = significators['quesited']['data']
    
    if not querent_data or not quesited_data:
        return {'has_reception': False}
    
    querent_sign = querent_data.get('sign')
    quesited_sign = quesited_data.get('sign')
    
    querent_planet = significators['querent']['primary']
    quesited_planet = significators['quesited']['primary']
    
    # Check if querent is in quesited's sign
    quesited_rules = get_sign_ruler(querent_sign)
    querent_in_quesited_sign = (quesited_rules == quesited_planet)
    
    # Check if quesited is in querent's sign
    querent_rules = get_sign_ruler(quesited_sign)
    quesited_in_querent_sign = (querent_rules == querent_planet)
    
    mutual_reception = querent_in_quesited_sign and quesited_in_querent_sign
    
    return {
        'has_reception': querent_in_quesited_sign or quesited_in_querent_sign,
        'mutual_reception': mutual_reception,
        'querent_in_quesited_sign': querent_in_quesited_sign,
        'quesited_in_querent_sign': quesited_in_querent_sign,
        'significance': 'Mutual reception is highly favorable' if mutual_reception else 'Reception shows connection'
    }


def analyze_applying_separating(
    aspect_analysis: Dict[str, Any],
    planets: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Determine if aspects are applying or separating
    
    Applying: Faster planet moving toward slower - event WILL happen
    Separating: Faster planet moving away - event already happened or won't happen
    """
    
    if not aspect_analysis['has_aspect']:
        return {'applying': False, 'separating': False, 'note': 'No aspect between significators'}
    
    primary_aspect = aspect_analysis.get('primary_aspect')
    if not primary_aspect:
        return {'applying': False, 'separating': False}
    
    # Check if applying (this would require speed calculation)
    # Simplified: check if aspect is exact or past exact
    orb = primary_aspect.get('orb', 10)
    applying = orb < 5  # Simplified: tight orb suggests applying
    
    return {
        'applying': applying,
        'separating': not applying,
        'significance': 'Applying aspects indicate event will happen' if applying else 'Separating aspects suggest event already past or unlikely'
    }


def check_prohibitions(
    aspect_analysis: Dict[str, Any],
    planets: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check for prohibitions and frustrations
    
    Prohibition: A third planet interferes before significators aspect
    Frustration: Significator changes sign before completing aspect
    """
    
    # Simplified check
    # Would need complex calculation of which planet aspects first
    
    return {
        'has_prohibition': False,
        'has_frustration': False,
        'note': 'Detailed prohibition/frustration analysis requires complex calculation'
    }


def check_translation_of_light(
    significators: Dict[str, Any],
    aspects: List[Dict[str, Any]],
    planets: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check for translation of light
    
    Translation: A third planet aspects both significators,
    carrying the "light" from one to the other
    This can bring about the matter even without direct aspect
    """
    
    querent_planet = significators['querent']['primary'].lower()
    quesited_planet = significators['quesited']['primary'].lower()
    
    # Find planets that aspect both
    translators = []
    
    planet_list = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    
    for planet in planet_list:
        if planet in [querent_planet, quesited_planet]:
            continue
        
        aspects_querent = False
        aspects_quesited = False
        
        for aspect in aspects:
            p1 = aspect.get('planet1', '').lower()
            p2 = aspect.get('planet2', '').lower()
            
            if planet in [p1, p2]:
                if querent_planet in [p1, p2]:
                    aspects_querent = True
                if quesited_planet in [p1, p2]:
                    aspects_quesited = True
        
        if aspects_querent and aspects_quesited:
            translators.append(planet)
    
    has_translation = len(translators) > 0
    
    return {
        'has_translation': has_translation,
        'translator_planets': translators,
        'significance': f'{translators[0].title()} acts as intermediary' if has_translation else 'No translation'
    }


def estimate_timing(
    aspect_analysis: Dict[str, Any],
    houses: Dict[str, Any],
    planets: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Estimate timing of event in horary
    
    Methods:
    1. Degrees until aspect perfects
    2. Houses (angular: days/weeks, succedent: weeks/months, cadent: months/years)
    3. Signs (cardinal: fast, fixed: slow, mutable: variable)
    """
    
    if not aspect_analysis['has_aspect']:
        return {
            'timing': 'Unknown - no aspect between significators',
            'timeframe': 'Event may not occur'
        }
    
    primary_aspect = aspect_analysis.get('primary_aspect')
    if not primary_aspect:
        return {'timing': 'Unknown', 'timeframe': 'Uncertain'}
    
    orb = primary_aspect.get('orb', 10)
    
    # Rough timing based on orb
    if orb < 1:
        timing = 'Very soon (days)'
    elif orb < 3:
        timing = 'Soon (1-2 weeks)'
    elif orb < 5:
        timing = 'Medium term (2-4 weeks)'
    else:
        timing = 'Longer term (1-3 months)'
    
    return {
        'timing': timing,
        'orb_degrees': round(orb, 2),
        'method': 'Based on orb to perfection',
        'note': 'Timing in horary is complex and depends on multiple factors'
    }


def make_horary_judgment(
    question_analysis: Dict[str, Any],
    significators: Dict[str, Any],
    aspect_analysis: Dict[str, Any],
    receptions: Dict[str, Any],
    applying_separating: Dict[str, Any],
    prohibitions: Dict[str, Any],
    translations: Dict[str, Any],
    radical_check: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make final horary judgment: YES, NO, or MAYBE
    
    Factors for YES:
    - Applying aspect between significators
    - Mutual reception
    - Translation of light
    - Benefic aspects (trine, sextile)
    
    Factors for NO:
    - Separating aspect
    - No aspect and no translation
    - Moon void of course
    - Prohibitions
    - Malefic aspects without receptions
    """
    
    points_yes = 0
    points_no = 0
    reasons_yes = []
    reasons_no = []
    
    # Aspect analysis
    if aspect_analysis['has_aspect']:
        if applying_separating.get('applying'):
            points_yes += 3
            reasons_yes.append("Applying aspect between significators")
        elif applying_separating.get('separating'):
            points_no += 3
            reasons_no.append("Separating aspect - event past or unlikely")
        
        # Aspect quality
        aspect_quality = aspect_analysis.get('aspect_quality', '')
        if 'favorable' in aspect_quality.lower():
            points_yes += 2
            reasons_yes.append("Favorable aspect (trine/sextile)")
        elif 'challenging' in aspect_quality.lower():
            points_no += 1
            reasons_no.append("Challenging aspect (square/opposition)")
    else:
        points_no += 2
        reasons_no.append("No direct aspect between significators")
    
    # Reception
    if receptions.get('mutual_reception'):
        points_yes += 4
        reasons_yes.append("Mutual reception - very favorable!")
    elif receptions.get('has_reception'):
        points_yes += 2
        reasons_yes.append("Reception shows connection")
    
    # Translation
    if translations.get('has_translation'):
        points_yes += 3
        reasons_yes.append(f"Translation of light via {translations['translator_planets'][0]}")
    
    # Prohibitions
    if prohibitions.get('has_prohibition'):
        points_no += 3
        reasons_no.append("Prohibition present - interference")
    
    # Radicality issues
    if radical_check.get('warning_count', 0) > 2:
        points_no += 2
        reasons_no.append("Chart radicality concerns")
    
    # Make judgment
    if points_yes > points_no + 2:
        answer = 'YES'
        confidence = 'High' if points_yes > points_no + 4 else 'Moderate'
    elif points_no > points_yes + 2:
        answer = 'NO'
        confidence = 'High' if points_no > points_yes + 4 else 'Moderate'
    else:
        answer = 'UNCLEAR/MAYBE'
        confidence = 'Low'
    
    return {
        'answer': answer,
        'confidence': confidence,
        'points_yes': points_yes,
        'points_no': points_no,
        'reasons_yes': reasons_yes,
        'reasons_no': reasons_no,
        'summary': f"Judgment: {answer} (Confidence: {confidence})"
    }


# Helper functions

def extract_horary_planets(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract planets for horary"""
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


def extract_horary_houses(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract houses for horary"""
    houses = {}
    
    for i in range(1, 13):
        house_obj = getattr(chart, f'house{i}', None)
        if house_obj:
            houses[str(i)] = {
                'cusp': house_obj['position'],
                'sign': house_obj['sign']
            }
    
    return houses


def extract_horary_aspects(chart: AstrologicalSubject) -> List[Dict[str, Any]]:
    """Extract aspects for horary"""
    aspects = []
    
    if hasattr(chart, 'aspects_list'):
        for aspect in chart.aspects_list:
            aspects.append({
                'planet1': aspect['p1_name'],
                'planet2': aspect['p2_name'],
                'aspect': aspect['aspect'],
                'orb': aspect['orbit']
            })
    
    return aspects


def check_moon_void_of_course(moon: Dict[str, Any], planets: Dict[str, Any]) -> bool:
    """Check if Moon is void of course"""
    # Simplified: would need to check if Moon makes any more aspects before leaving sign
    # This requires speed and position calculations
    return False  # Placeholder


def get_sign_ruler(sign: str) -> str:
    """Get traditional ruler of sign"""
    rulers = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
        'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
        'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
        'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }
    return rulers.get(sign, 'Unknown')


def assess_aspect_quality(aspect: Dict[str, Any]) -> str:
    """Assess whether aspect is favorable or challenging"""
    aspect_type = aspect.get('aspect', '')
    
    if aspect_type in ['trine', 'sextile']:
        return 'Favorable'
    elif aspect_type in ['square', 'opposition']:
        return 'Challenging'
    elif aspect_type == 'conjunction':
        return 'Neutral (depends on planets)'
    else:
        return 'Minor aspect'


def assess_confidence_level(judgment: Dict[str, Any], aspect_analysis: Dict[str, Any]) -> str:
    """Assess overall confidence in judgment"""
    return judgment.get('confidence', 'Moderate')


def generate_horary_interpretation(
    question: str,
    question_analysis: Dict[str, Any],
    significators: Dict[str, Any],
    judgment: Dict[str, Any]
) -> str:
    """Generate human-readable interpretation"""
    
    parts = []
    
    parts.append(f"HORARY QUESTION: {question}\n\n")
    parts.append(f"Question Type: {question_analysis['type'].title()}\n")
    parts.append(f"Relevant Houses: {question_analysis['description']}\n\n")
    
    parts.append(f"SIGNIFICATORS:\n")
    parts.append(f"Querent (You): {significators['querent']['primary']}\n")
    parts.append(f"Quesited (What you ask about): {significators['quesited']['primary']}\n\n")
    
    parts.append(f"JUDGMENT: {judgment['answer']}\n")
    parts.append(f"Confidence: {judgment['confidence']}\n\n")
    
    if judgment['reasons_yes']:
        parts.append("Factors supporting YES:\n")
        for reason in judgment['reasons_yes']:
            parts.append(f"  • {reason}\n")
        parts.append("\n")
    
    if judgment['reasons_no']:
        parts.append("Factors supporting NO:\n")
        for reason in judgment['reasons_no']:
            parts.append(f"  • {reason}\n")
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    question = "Will I get the job?"
    question_time = datetime.now()
    location = {
        'city': 'Istanbul',
        'nation': 'TR',
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timezone': 'Europe/Istanbul'
    }
    
    # Note: This is a complex example, real horary requires deep knowledge
    print("Horary astrology calculator ready")
    print("Note: Horary requires expert interpretation!")
