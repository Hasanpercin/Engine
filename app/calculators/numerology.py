"""
Numerology calculations and analysis
Pythagorean and Chaldean systems, integration with astrology
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


# Pythagorean letter values (1-9)
PYTHAGOREAN_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

# Chaldean letter values (1-8, no 9)
CHALDEAN_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 8, 'G': 3, 'H': 5, 'I': 1,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 7, 'P': 8, 'Q': 1, 'R': 2,
    'S': 3, 'T': 4, 'U': 6, 'V': 6, 'W': 6, 'X': 5, 'Y': 1, 'Z': 7
}

# Master numbers (not reduced)
MASTER_NUMBERS = [11, 22, 33, 44]

# Karmic debt numbers
KARMIC_DEBT_NUMBERS = [13, 14, 16, 19]


def calculate_complete_numerology(
    full_name: str,
    birth_date: date,
    system: str = 'pythagorean',
    include_astrology: bool = False,
    natal_chart_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate complete numerology profile
    
    Args:
        full_name: Full birth name
        birth_date: Date of birth
        system: 'pythagorean' or 'chaldean'
        include_astrology: Whether to include astrology integration
        natal_chart_data: Natal chart data for integration
        
    Returns:
        Complete numerology profile
    """
    try:
        logger.info(f"Calculating numerology for {full_name}, system: {system}")
        
        # Core numbers
        life_path = calculate_life_path_number(birth_date)
        expression = calculate_expression_number(full_name, system)
        soul_urge = calculate_soul_urge_number(full_name, system)
        personality = calculate_personality_number(full_name, system)
        destiny = expression  # Same as Expression in most systems
        
        # Additional numbers
        maturity = calculate_maturity_number(life_path['number'], expression['number'])
        birth_day = birth_date.day
        birth_day_meaning = get_birth_day_meaning(birth_day)
        
        # Personal year
        current_year = datetime.now().year
        personal_year = calculate_personal_year(birth_date, current_year)
        
        # Karmic lessons
        karmic_lessons = identify_karmic_lessons(full_name, system)
        karmic_debts = identify_karmic_debts(birth_date, full_name, system)
        
        # Hidden passions and challenges
        hidden_passion = find_hidden_passion(full_name, system)
        challenge_numbers = calculate_challenge_numbers(birth_date)
        
        # Pinnacles and cycles
        pinnacles = calculate_pinnacles(birth_date)
        personal_cycles = calculate_personal_cycles(birth_date)
        
        result = {
            'system': system,
            'full_name': full_name,
            'birth_date': birth_date.isoformat(),
            'core_numbers': {
                'life_path': life_path,
                'expression': expression,
                'soul_urge': soul_urge,
                'personality': personality,
                'maturity': maturity,
                'birth_day': {
                    'number': birth_day,
                    'meaning': birth_day_meaning
                }
            },
            'current_cycles': {
                'personal_year': personal_year,
                'personal_year_theme': get_personal_year_theme(personal_year)
            },
            'karmic_indicators': {
                'karmic_lessons': karmic_lessons,
                'karmic_debts': karmic_debts,
                'hidden_passion': hidden_passion,
                'challenge_numbers': challenge_numbers
            },
            'life_cycles': {
                'pinnacles': pinnacles,
                'personal_cycles': personal_cycles
            },
            'interpretation': generate_numerology_interpretation(
                life_path,
                expression,
                soul_urge,
                personality
            )
        }
        
        # Astrology integration
        if include_astrology and natal_chart_data:
            astro_integration = integrate_with_astrology(
                result,
                natal_chart_data
            )
            result['astrology_integration'] = astro_integration
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating numerology: {str(e)}")
        raise


def calculate_life_path_number(birth_date: date) -> Dict[str, Any]:
    """
    Calculate Life Path Number - most important number
    
    Shows your life's purpose and journey
    """
    
    # Method: Add all digits of birth date, reduce to single digit or master number
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Check for karmic debt in day
    day_sum = reduce_to_single_digit(day, check_karmic=True)
    month_sum = reduce_to_single_digit(month, check_karmic=True)
    year_sum = reduce_to_single_digit(year, check_karmic=True)
    
    # Add all together
    total = day_sum['final_number'] + month_sum['final_number'] + year_sum['final_number']
    
    # Check for karmic debt before final reduction
    has_karmic_debt = total in KARMIC_DEBT_NUMBERS
    karmic_debt_note = None
    if has_karmic_debt:
        karmic_debt_note = get_karmic_debt_meaning(total)
    
    # Reduce to master number or single digit
    final = reduce_to_single_digit(total, check_master=True)
    
    return {
        'number': final['final_number'],
        'is_master': final.get('is_master', False),
        'karmic_debt': karmic_debt_note,
        'meaning': get_life_path_meaning(final['final_number']),
        'calculation': f"{birth_date.day}/{birth_date.month}/{birth_date.year} = {final['final_number']}"
    }


def calculate_expression_number(full_name: str, system: str = 'pythagorean') -> Dict[str, Any]:
    """
    Calculate Expression/Destiny Number
    
    Shows your natural talents and abilities
    """
    
    values = PYTHAGOREAN_VALUES if system == 'pythagorean' else CHALDEAN_VALUES
    
    # Remove spaces and convert to uppercase
    name = full_name.upper().replace(' ', '')
    
    # Calculate total
    total = 0
    for char in name:
        if char.isalpha():
            total += values.get(char, 0)
    
    # Reduce
    result = reduce_to_single_digit(total, check_master=True)
    
    return {
        'number': result['final_number'],
        'is_master': result.get('is_master', False),
        'meaning': get_expression_meaning(result['final_number']),
        'calculation': f"Total of {full_name} = {result['final_number']}"
    }


def calculate_soul_urge_number(full_name: str, system: str = 'pythagorean') -> Dict[str, Any]:
    """
    Calculate Soul Urge/Heart's Desire Number
    
    Shows your inner desires and motivations
    Uses only VOWELS
    """
    
    values = PYTHAGOREAN_VALUES if system == 'pythagorean' else CHALDEAN_VALUES
    vowels = 'AEIOU'
    
    name = full_name.upper()
    total = 0
    
    for char in name:
        if char in vowels:
            total += values.get(char, 0)
    
    result = reduce_to_single_digit(total, check_master=True)
    
    return {
        'number': result['final_number'],
        'is_master': result.get('is_master', False),
        'meaning': get_soul_urge_meaning(result['final_number']),
        'calculation': f"Vowels of {full_name} = {result['final_number']}"
    }


def calculate_personality_number(full_name: str, system: str = 'pythagorean') -> Dict[str, Any]:
    """
    Calculate Personality Number
    
    Shows how others see you
    Uses only CONSONANTS
    """
    
    values = PYTHAGOREAN_VALUES if system == 'pythagorean' else CHALDEAN_VALUES
    vowels = 'AEIOU'
    
    name = full_name.upper()
    total = 0
    
    for char in name:
        if char.isalpha() and char not in vowels:
            total += values.get(char, 0)
    
    result = reduce_to_single_digit(total, check_master=True)
    
    return {
        'number': result['final_number'],
        'is_master': result.get('is_master', False),
        'meaning': get_personality_meaning(result['final_number']),
        'calculation': f"Consonants of {full_name} = {result['final_number']}"
    }


def calculate_maturity_number(life_path: int, expression: int) -> Dict[str, Any]:
    """
    Calculate Maturity Number
    
    Shows what you develop in later life (after age 35-40)
    Life Path + Expression
    """
    
    total = life_path + expression
    result = reduce_to_single_digit(total, check_master=True)
    
    return {
        'number': result['final_number'],
        'is_master': result.get('is_master', False),
        'meaning': get_maturity_meaning(result['final_number']),
        'activation_age': '35-40 years'
    }


def calculate_personal_year(birth_date: date, year: int) -> int:
    """
    Calculate Personal Year Number
    
    Shows the theme for a specific year
    Birth month + Birth day + Current year
    """
    
    month = birth_date.month
    day = birth_date.day
    
    total = month + day + year
    result = reduce_to_single_digit(total, check_master=False)
    
    return result['final_number']


def identify_karmic_lessons(full_name: str, system: str = 'pythagorean') -> List[Dict[str, Any]]:
    """
    Identify Karmic Lessons
    
    Numbers missing from the name show karmic lessons
    """
    
    values = PYTHAGOREAN_VALUES if system == 'pythagorean' else CHALDEAN_VALUES
    
    name = full_name.upper().replace(' ', '')
    
    # Count occurrences of each number
    number_counts = {i: 0 for i in range(1, 10)}
    
    for char in name:
        if char.isalpha():
            num = values.get(char, 0)
            if num > 0:
                number_counts[num] += 1
    
    # Missing numbers are karmic lessons
    missing = [num for num, count in number_counts.items() if count == 0]
    
    lessons = []
    for num in missing:
        lessons.append({
            'number': num,
            'lesson': get_karmic_lesson_meaning(num)
        })
    
    return lessons


def identify_karmic_debts(birth_date: date, full_name: str, system: str = 'pythagorean') -> List[Dict[str, Any]]:
    """
    Identify Karmic Debt Numbers (13, 14, 16, 19)
    
    Found in birth date or name calculations
    """
    
    debts = []
    
    # Check birth date components
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    if day in KARMIC_DEBT_NUMBERS:
        debts.append({
            'number': day,
            'source': 'birth_day',
            'meaning': get_karmic_debt_meaning(day)
        })
    
    # Check intermediate calculations in Life Path
    day_sum = sum(int(d) for d in str(day))
    month_sum = sum(int(d) for d in str(month))
    year_sum = sum(int(d) for d in str(year))
    
    total_before_reduction = day_sum + month_sum + year_sum
    if total_before_reduction in KARMIC_DEBT_NUMBERS:
        debts.append({
            'number': total_before_reduction,
            'source': 'life_path_calculation',
            'meaning': get_karmic_debt_meaning(total_before_reduction)
        })
    
    return debts


def find_hidden_passion(full_name: str, system: str = 'pythagorean') -> Dict[str, Any]:
    """
    Find Hidden Passion Number
    
    The number that appears most frequently in the name
    Shows a hidden talent or passion
    """
    
    values = PYTHAGOREAN_VALUES if system == 'pythagorean' else CHALDEAN_VALUES
    
    name = full_name.upper().replace(' ', '')
    
    number_counts = {i: 0 for i in range(1, 10)}
    
    for char in name:
        if char.isalpha():
            num = values.get(char, 0)
            if num > 0:
                number_counts[num] += 1
    
    # Find most frequent
    max_count = max(number_counts.values())
    most_frequent = [num for num, count in number_counts.items() if count == max_count]
    
    if most_frequent:
        passion_num = most_frequent[0]
        return {
            'number': passion_num,
            'frequency': max_count,
            'meaning': get_hidden_passion_meaning(passion_num)
        }
    
    return {'number': None, 'frequency': 0, 'meaning': 'No dominant number'}


def calculate_challenge_numbers(birth_date: date) -> List[Dict[str, Any]]:
    """
    Calculate Challenge Numbers
    
    Shows obstacles and lessons to overcome
    Derived from birth date
    """
    
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Reduce each to single digit
    day_digit = reduce_to_single_digit(day, check_master=False)['final_number']
    month_digit = reduce_to_single_digit(month, check_master=False)['final_number']
    year_digit = reduce_to_single_digit(year, check_master=False)['final_number']
    
    # Calculate challenges
    first_challenge = abs(day_digit - month_digit)
    second_challenge = abs(day_digit - year_digit)
    third_challenge = abs(first_challenge - second_challenge)
    fourth_challenge = abs(month_digit - year_digit)
    
    challenges = [
        {'number': first_challenge, 'period': 'Birth to ~age 35', 'meaning': get_challenge_meaning(first_challenge)},
        {'number': second_challenge, 'period': '~age 36 to 45', 'meaning': get_challenge_meaning(second_challenge)},
        {'number': third_challenge, 'period': '~age 46 to 55', 'meaning': get_challenge_meaning(third_challenge)},
        {'number': fourth_challenge, 'period': '~age 56+', 'meaning': get_challenge_meaning(fourth_challenge)}
    ]
    
    return challenges


def calculate_pinnacles(birth_date: date) -> List[Dict[str, Any]]:
    """
    Calculate Pinnacle Numbers
    
    Four major periods of achievement and focus
    """
    
    day = birth_date.day
    month = birth_date.month
    year = birth_date.year
    
    # Reduce to single digits
    day_digit = reduce_to_single_digit(day, check_master=False)['final_number']
    month_digit = reduce_to_single_digit(month, check_master=False)['final_number']
    year_digit = reduce_to_single_digit(year, check_master=False)['final_number']
    
    # Calculate pinnacles
    first_pinnacle = reduce_to_single_digit(month_digit + day_digit, check_master=False)['final_number']
    second_pinnacle = reduce_to_single_digit(day_digit + year_digit, check_master=False)['final_number']
    third_pinnacle = reduce_to_single_digit(first_pinnacle + second_pinnacle, check_master=False)['final_number']
    fourth_pinnacle = reduce_to_single_digit(month_digit + year_digit, check_master=False)['final_number']
    
    # Calculate life path for period calculation
    life_path_num = reduce_to_single_digit(day + month + year, check_master=False)['final_number']
    
    # Pinnacle periods
    first_period_end = 36 - life_path_num
    second_period_end = first_period_end + 9
    third_period_end = second_period_end + 9
    
    pinnacles = [
        {
            'number': first_pinnacle,
            'period': f'Birth to ~age {first_period_end}',
            'theme': get_pinnacle_theme(first_pinnacle)
        },
        {
            'number': second_pinnacle,
            'period': f'~age {first_period_end + 1} to {second_period_end}',
            'theme': get_pinnacle_theme(second_pinnacle)
        },
        {
            'number': third_pinnacle,
            'period': f'~age {second_period_end + 1} to {third_period_end}',
            'theme': get_pinnacle_theme(third_pinnacle)
        },
        {
            'number': fourth_pinnacle,
            'period': f'~age {third_period_end + 1}+',
            'theme': get_pinnacle_theme(fourth_pinnacle)
        }
    ]
    
    return pinnacles


def calculate_personal_cycles(birth_date: date) -> Dict[str, Any]:
    """
    Calculate three major life cycles
    
    Based on birth date components
    """
    
    month = birth_date.month
    day = birth_date.day
    year = birth_date.year
    
    # Reduce each
    month_digit = reduce_to_single_digit(month, check_master=False)['final_number']
    day_digit = reduce_to_single_digit(day, check_master=False)['final_number']
    year_digit = reduce_to_single_digit(year, check_master=False)['final_number']
    
    # Calculate life path for period lengths
    life_path_num = reduce_to_single_digit(day + month + year, check_master=False)['final_number']
    
    first_cycle_end = 36 - life_path_num
    second_cycle_end = first_cycle_end + 27
    
    return {
        'first_cycle': {
            'number': month_digit,
            'period': f'Birth to ~age {first_cycle_end}',
            'theme': 'Early life foundation',
            'focus': get_cycle_focus(month_digit)
        },
        'second_cycle': {
            'number': day_digit,
            'period': f'~age {first_cycle_end + 1} to {second_cycle_end}',
            'theme': 'Productive years',
            'focus': get_cycle_focus(day_digit)
        },
        'third_cycle': {
            'number': year_digit,
            'period': f'~age {second_cycle_end + 1}+',
            'theme': 'Harvest years',
            'focus': get_cycle_focus(year_digit)
        }
    }


def integrate_with_astrology(
    numerology_data: Dict[str, Any],
    natal_chart_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Integrate numerology with astrology
    
    Shows correlations and combined insights
    """
    
    life_path = numerology_data['core_numbers']['life_path']['number']
    sun_sign = natal_chart_data['planets']['sun']['sign']
    
    # Find correlations
    correlations = []
    
    # Life Path and Sun Sign correlation
    if life_path in [1, 5, 9]:  # Fire numbers
        if sun_sign in ['Aries', 'Leo', 'Sagittarius']:
            correlations.append("Life Path and Sun Sign both emphasize fire energy - dynamic, passionate")
    
    if life_path in [2, 6]:  # Relationship numbers
        if natal_chart_data['planets']['venus']['house'] in [5, 7]:
            correlations.append("Life Path and Venus placement both emphasize relationships")
    
    if life_path == 8:  # Power/achievement number
        if natal_chart_data['planets']['saturn']['house'] == 10:
            correlations.append("Life Path 8 and Saturn in 10th - strong career focus")
    
    return {
        'life_path_sun_correlation': f"Life Path {life_path} with Sun in {sun_sign}",
        'key_correlations': correlations,
        'combined_purpose': (
            f"Numerology Life Path {life_path} combined with astrological "
            f"Sun in {sun_sign} suggests a unique blend of {get_number_archetype(life_path)} "
            f"and {sun_sign} energies."
        )
    }


# Helper functions

def reduce_to_single_digit(
    number: int,
    check_master: bool = True,
    check_karmic: bool = False
) -> Dict[str, Any]:
    """Reduce number to single digit, preserving master numbers if needed"""
    
    # Check for karmic debt
    is_karmic_debt = check_karmic and number in KARMIC_DEBT_NUMBERS
    
    # Check for master number
    is_master = check_master and number in MASTER_NUMBERS
    
    if is_master:
        return {'final_number': number, 'is_master': True, 'is_karmic_debt': is_karmic_debt}
    
    # Reduce to single digit
    while number > 9:
        number = sum(int(d) for d in str(number))
        # Check again for master during reduction
        if check_master and number in MASTER_NUMBERS:
            return {'final_number': number, 'is_master': True, 'is_karmic_debt': is_karmic_debt}
    
    return {'final_number': number, 'is_master': False, 'is_karmic_debt': is_karmic_debt}


def get_life_path_meaning(number: int) -> str:
    """Get Life Path meaning by number"""
    meanings = {
        1: "Leader, pioneer, independent - here to develop self-reliance and leadership",
        2: "Peacemaker, diplomat, sensitive - here to create harmony and partnership",
        3: "Creative expresser, communicator - here to inspire and create joy",
        4: "Builder, organizer, practical - here to create stability and structure",
        5: "Freedom seeker, adventurer - here to experience and teach about freedom",
        6: "Nurturer, teacher, responsible - here to serve and create harmony",
        7: "Seeker, analyst, spiritual - here to search for truth and wisdom",
        8: "Achiever, powerful, ambitious - here to master material world",
        9: "Humanitarian, compassionate - here to serve humanity",
        11: "Master intuitive, visionary - here to inspire and illuminate",
        22: "Master builder, manifester - here to build something lasting",
        33: "Master teacher, healer - here to uplift humanity"
    }
    return meanings.get(number, "Life purpose")


def get_expression_meaning(number: int) -> str:
    """Get Expression/Destiny meaning"""
    meanings = {
        1: "Natural leader with pioneering abilities",
        2: "Natural diplomat with mediation skills",
        3: "Natural creative communicator",
        4: "Natural organizer and builder",
        5: "Natural freedom-lover and change agent",
        6: "Natural nurturer and teacher",
        7: "Natural researcher and truth-seeker",
        8: "Natural business person and achiever",
        9: "Natural humanitarian and philanthropist",
        11: "Natural intuitive and inspirer",
        22: "Natural master builder",
        33: "Natural master teacher"
    }
    return meanings.get(number, "Natural abilities")


def get_soul_urge_meaning(number: int) -> str:
    """Get Soul Urge/Heart's Desire meaning"""
    meanings = {
        1: "Desire for independence and self-achievement",
        2: "Desire for peace, partnership, and harmony",
        3: "Desire for creative self-expression and joy",
        4: "Desire for security, stability, and order",
        5: "Desire for freedom, variety, and adventure",
        6: "Desire to nurture, teach, and create harmony",
        7: "Desire for knowledge, truth, and spirituality",
        8: "Desire for success, power, and material abundance",
        9: "Desire to help humanity and make a difference",
        11: "Desire to inspire and illuminate others",
        22: "Desire to build something significant",
        33: "Desire to heal and uplift humanity"
    }
    return meanings.get(number, "Inner motivation")


def get_personality_meaning(number: int) -> str:
    """Get Personality number meaning"""
    meanings = {
        1: "Appears confident, independent, and strong",
        2: "Appears gentle, diplomatic, and cooperative",
        3: "Appears friendly, creative, and expressive",
        4: "Appears practical, reliable, and organized",
        5: "Appears dynamic, adventurous, and exciting",
        6: "Appears caring, responsible, and nurturing",
        7: "Appears mysterious, intellectual, and reserved",
        8: "Appears powerful, successful, and confident",
        9: "Appears compassionate, wise, and philanthropic",
        11: "Appears inspiring, intuitive, and charismatic",
        22: "Appears ambitious, capable, and visionary",
        33: "Appears healing, teaching, and uplifting"
    }
    return meanings.get(number, "Outer impression")


def get_maturity_meaning(number: int) -> str:
    """Get Maturity number meaning"""
    meanings = {
        1: "Develop independence and leadership in later life",
        2: "Develop peace and partnership focus in later life",
        3: "Develop creative expression in later life",
        4: "Develop solid foundations in later life",
        5: "Develop freedom and adventure in later life",
        6: "Develop service and responsibility in later life",
        7: "Develop wisdom and spirituality in later life",
        8: "Develop mastery and achievement in later life",
        9: "Develop humanitarianism in later life",
        11: "Develop inspirational gifts in later life",
        22: "Develop master building abilities in later life",
        33: "Develop master teaching abilities in later life"
    }
    return meanings.get(number, "Later life development")


def get_birth_day_meaning(day: int) -> str:
    """Get birth day number meaning (simplified)"""
    if day > 9:
        day = reduce_to_single_digit(day, check_master=False)['final_number']
    
    meanings = {
        1: "Independent, original, leadership qualities",
        2: "Cooperative, sensitive, diplomatic",
        3: "Creative, expressive, social",
        4: "Practical, hardworking, stable",
        5: "Freedom-loving, adventurous, versatile",
        6: "Responsible, nurturing, family-oriented",
        7: "Analytical, spiritual, introspective",
        8: "Ambitious, business-minded, powerful",
        9: "Humanitarian, compassionate, idealistic"
    }
    return meanings.get(day, "Special qualities")


def get_personal_year_theme(year: int) -> str:
    """Get Personal Year theme"""
    themes = {
        1: "New beginnings, fresh start, initiation",
        2: "Patience, cooperation, relationships",
        3: "Creativity, expression, social expansion",
        4: "Hard work, building foundations, discipline",
        5: "Change, freedom, adventure, transition",
        6: "Responsibility, service, family focus",
        7: "Introspection, spiritual growth, analysis",
        8: "Achievement, power, material success",
        9: "Completion, letting go, humanitarian service"
    }
    return themes.get(year, "Yearly theme")


def get_karmic_lesson_meaning(number: int) -> str:
    """Get Karmic Lesson meaning for missing numbers"""
    lessons = {
        1: "Learn self-reliance and independence",
        2: "Learn cooperation and sensitivity",
        3: "Learn self-expression and creativity",
        4: "Learn discipline and practical skills",
        5: "Learn to embrace change and freedom",
        6: "Learn responsibility and service",
        7: "Learn faith and spiritual development",
        8: "Learn about power and material world",
        9: "Learn compassion and humanitarianism"
    }
    return lessons.get(number, "Life lesson")


def get_karmic_debt_meaning(number: int) -> str:
    """Get Karmic Debt meaning"""
    debts = {
        13: "Karmic Debt 13: Learn discipline and hard work (avoid laziness)",
        14: "Karmic Debt 14: Learn moderation and balance (avoid excess)",
        16: "Karmic Debt 16: Learn humility and rebuild ego (past life abuse of love)",
        19: "Karmic Debt 19: Learn independence and avoid power abuse"
    }
    return debts.get(number, "Karmic debt")


def get_hidden_passion_meaning(number: int) -> str:
    """Get Hidden Passion meaning"""
    passions = {
        1: "Hidden passion for leadership and independence",
        2: "Hidden passion for harmony and partnership",
        3: "Hidden passion for creative expression",
        4: "Hidden passion for building and organizing",
        5: "Hidden passion for freedom and adventure",
        6: "Hidden passion for nurturing and service",
        7: "Hidden passion for knowledge and spirituality",
        8: "Hidden passion for achievement and success",
        9: "Hidden passion for humanitarian work"
    }
    return passions.get(number, "Hidden talent")


def get_challenge_meaning(number: int) -> str:
    """Get Challenge number meaning"""
    if number == 0:
        return "No specific challenge - all experiences are lessons"
    
    challenges = {
        1: "Challenge: Develop self-confidence, overcome fear of standing alone",
        2: "Challenge: Balance giving and receiving, overcome over-sensitivity",
        3: "Challenge: Express yourself fully, overcome self-doubt",
        4: "Challenge: Create discipline and structure, overcome rigidity",
        5: "Challenge: Embrace change wisely, overcome restlessness",
        6: "Challenge: Balance responsibility, overcome perfectionism",
        7: "Challenge: Trust intuition, overcome isolation",
        8: "Challenge: Balance material and spiritual, overcome greed"
    }
    return challenges.get(number, "Life challenge")


def get_pinnacle_theme(number: int) -> str:
    """Get Pinnacle period theme"""
    themes = {
        1: "Focus on independence and new beginnings",
        2: "Focus on relationships and cooperation",
        3: "Focus on creativity and self-expression",
        4: "Focus on building and stability",
        5: "Focus on freedom and change",
        6: "Focus on responsibility and service",
        7: "Focus on spiritual growth and learning",
        8: "Focus on achievement and material success",
        9: "Focus on humanitarian service and completion"
    }
    return themes.get(number, "Period theme")


def get_cycle_focus(number: int) -> str:
    """Get life cycle focus"""
    return get_pinnacle_theme(number)


def get_number_archetype(number: int) -> str:
    """Get number archetype for integration"""
    archetypes = {
        1: "The Leader", 2: "The Diplomat", 3: "The Creator",
        4: "The Builder", 5: "The Freedom Seeker", 6: "The Nurturer",
        7: "The Seeker", 8: "The Powerhouse", 9: "The Humanitarian",
        11: "The Visionary", 22: "The Master Builder", 33: "The Master Teacher"
    }
    return archetypes.get(number, "The Seeker")


def generate_numerology_interpretation(
    life_path: Dict[str, Any],
    expression: Dict[str, Any],
    soul_urge: Dict[str, Any],
    personality: Dict[str, Any]
) -> str:
    """Generate comprehensive numerology interpretation"""
    
    parts = []
    
    parts.append("NUMEROLOGY PROFILE SUMMARY\n\n")
    parts.append("=" * 50 + "\n\n")
    
    parts.append(f"LIFE PATH {life_path['number']}: {life_path['meaning']}\n\n")
    parts.append(f"EXPRESSION {expression['number']}: {expression['meaning']}\n\n")
    parts.append(f"SOUL URGE {soul_urge['number']}: {soul_urge['meaning']}\n\n")
    parts.append(f"PERSONALITY {personality['number']}: {personality['meaning']}\n\n")
    
    parts.append("SYNTHESIS:\n")
    parts.append(
        f"You are here to {life_path['meaning'].lower()}, "
        f"using your natural talents as {expression['meaning'].lower()}. "
        f"Deep inside, you {soul_urge['meaning'].lower()}, "
        f"while others see you as someone who {personality['meaning'].lower()}."
    )
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    full_name = "John Doe"
    birth_date = date(1990, 6, 15)
    
    numerology = calculate_complete_numerology(
        full_name=full_name,
        birth_date=birth_date,
        system='pythagorean'
    )
    
    print("Numerology Profile:")
    print(f"Life Path: {numerology['core_numbers']['life_path']['number']}")
    print(f"Expression: {numerology['core_numbers']['expression']['number']}")
    print(f"Soul Urge: {numerology['core_numbers']['soul_urge']['number']}")
    print(f"Personality: {numerology['core_numbers']['personality']['number']}")
    print(f"\nCurrent Personal Year: {numerology['current_cycles']['personal_year']}")
