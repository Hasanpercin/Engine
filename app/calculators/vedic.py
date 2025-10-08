"""
Vedic (Jyotish) astrology calculations
Hindu/Indian astrology system with sidereal zodiac, nakshatras, dashas
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


# Lahiri Ayanamsa (most commonly used)
AYANAMSA_LAHIRI = swe.SIDM_LAHIRI

# Nakshatras (27 lunar mansions)
NAKSHATRAS = [
    {'name': 'Ashwini', 'start': 0.0, 'end': 13.333333, 'ruler': 'Ketu', 'deity': 'Ashwini Kumaras'},
    {'name': 'Bharani', 'start': 13.333333, 'end': 26.666667, 'ruler': 'Venus', 'deity': 'Yama'},
    {'name': 'Krittika', 'start': 26.666667, 'end': 40.0, 'ruler': 'Sun', 'deity': 'Agni'},
    {'name': 'Rohini', 'start': 40.0, 'end': 53.333333, 'ruler': 'Moon', 'deity': 'Brahma'},
    {'name': 'Mrigashira', 'start': 53.333333, 'end': 66.666667, 'ruler': 'Mars', 'deity': 'Soma'},
    {'name': 'Ardra', 'start': 66.666667, 'end': 80.0, 'ruler': 'Rahu', 'deity': 'Rudra'},
    {'name': 'Punarvasu', 'start': 80.0, 'end': 93.333333, 'ruler': 'Jupiter', 'deity': 'Aditi'},
    {'name': 'Pushya', 'start': 93.333333, 'end': 106.666667, 'ruler': 'Saturn', 'deity': 'Brihaspati'},
    {'name': 'Ashlesha', 'start': 106.666667, 'end': 120.0, 'ruler': 'Mercury', 'deity': 'Nagas'},
    {'name': 'Magha', 'start': 120.0, 'end': 133.333333, 'ruler': 'Ketu', 'deity': 'Pitris'},
    {'name': 'Purva Phalguni', 'start': 133.333333, 'end': 146.666667, 'ruler': 'Venus', 'deity': 'Bhaga'},
    {'name': 'Uttara Phalguni', 'start': 146.666667, 'end': 160.0, 'ruler': 'Sun', 'deity': 'Aryaman'},
    {'name': 'Hasta', 'start': 160.0, 'end': 173.333333, 'ruler': 'Moon', 'deity': 'Savitar'},
    {'name': 'Chitra', 'start': 173.333333, 'end': 186.666667, 'ruler': 'Mars', 'deity': 'Vishwakarma'},
    {'name': 'Swati', 'start': 186.666667, 'end': 200.0, 'ruler': 'Rahu', 'deity': 'Vayu'},
    {'name': 'Vishakha', 'start': 200.0, 'end': 213.333333, 'ruler': 'Jupiter', 'deity': 'Indra-Agni'},
    {'name': 'Anuradha', 'start': 213.333333, 'end': 226.666667, 'ruler': 'Saturn', 'deity': 'Mitra'},
    {'name': 'Jyeshtha', 'start': 226.666667, 'end': 240.0, 'ruler': 'Mercury', 'deity': 'Indra'},
    {'name': 'Mula', 'start': 240.0, 'end': 253.333333, 'ruler': 'Ketu', 'deity': 'Nirriti'},
    {'name': 'Purva Ashadha', 'start': 253.333333, 'end': 266.666667, 'ruler': 'Venus', 'deity': 'Apas'},
    {'name': 'Uttara Ashadha', 'start': 266.666667, 'end': 280.0, 'ruler': 'Sun', 'deity': 'Vishvadevas'},
    {'name': 'Shravana', 'start': 280.0, 'end': 293.333333, 'ruler': 'Moon', 'deity': 'Vishnu'},
    {'name': 'Dhanishta', 'start': 293.333333, 'end': 306.666667, 'ruler': 'Mars', 'deity': 'Vasus'},
    {'name': 'Shatabhisha', 'start': 306.666667, 'end': 320.0, 'ruler': 'Rahu', 'deity': 'Varuna'},
    {'name': 'Purva Bhadrapada', 'start': 320.0, 'end': 333.333333, 'ruler': 'Jupiter', 'deity': 'Aja Ekapada'},
    {'name': 'Uttara Bhadrapada', 'start': 333.333333, 'end': 346.666667, 'ruler': 'Saturn', 'deity': 'Ahir Budhnya'},
    {'name': 'Revati', 'start': 346.666667, 'end': 360.0, 'ruler': 'Mercury', 'deity': 'Pushan'}
]

# Vimshottari Dasha periods (in years)
VIMSHOTTARI_PERIODS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17
}


def calculate_vedic_chart(
    birth_data: Dict[str, Any],
    include_divisional: bool = True,
    include_dashas: bool = True
) -> Dict[str, Any]:
    """
    Calculate complete Vedic astrology chart
    
    Args:
        birth_data: Birth data dictionary
        include_divisional: Include divisional charts (D9, D10, etc.)
        include_dashas: Include Vimshottari Dasha calculations
        
    Returns:
        Complete Vedic chart analysis
    """
    try:
        birth_date = birth_data['birth_date']
        birth_time = birth_data['birth_time']
        
        logger.info(f"Calculating Vedic chart for {birth_data['name']}")
        
        # Set ayanamsa (Lahiri is standard)
        swe.set_sid_mode(AYANAMSA_LAHIRI)
        
        # Calculate Julian Day
        jd = swe.julday(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            birth_time.hour + birth_time.minute / 60.0
        )
        
        # Calculate sidereal positions
        planets = calculate_sidereal_planets(jd)
        
        # Calculate houses (Whole Sign system is traditional in Vedic)
        houses = calculate_vedic_houses(jd, birth_data['latitude'], birth_data['longitude'])
        
        # Calculate nakshatras
        nakshatras_data = calculate_nakshatras(planets)
        
        # Calculate planetary strengths (Shadbala)
        strengths = calculate_shadbala(planets, houses, jd)
        
        # Calculate yogas (planetary combinations)
        yogas = identify_yogas(planets, houses)
        
        # Calculate aspects (Vedic aspects are different from Western)
        vedic_aspects = calculate_vedic_aspects(planets)
        
        # Ascendant analysis
        ascendant_analysis = analyze_ascendant_vedic(houses, planets)
        
        # Moon chart (Chandra Lagna)
        moon_chart = calculate_moon_chart(planets, houses)
        
        result = {
            'system': 'vedic',
            'ayanamsa': 'Lahiri',
            'ayanamsa_value': swe.get_ayanamsa_ut(jd),
            'birth_data': birth_data,
            'planets': planets,
            'houses': houses,
            'nakshatras': nakshatras_data,
            'planetary_strengths': strengths,
            'yogas': yogas,
            'vedic_aspects': vedic_aspects,
            'ascendant_analysis': ascendant_analysis,
            'moon_chart': moon_chart
        }
        
        # Divisional charts (Vargas)
        if include_divisional:
            divisional = calculate_divisional_charts(jd, birth_data)
            result['divisional_charts'] = divisional
        
        # Vimshottari Dasha
        if include_dashas:
            dashas = calculate_vimshottari_dasha(
                nakshatras_data['moon_nakshatra'],
                birth_date,
                birth_time
            )
            result['dashas'] = dashas
        
        # Generate interpretation
        result['interpretation'] = generate_vedic_interpretation(
            planets,
            houses,
            nakshatras_data,
            yogas,
            result.get('dashas')
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating Vedic chart: {str(e)}")
        raise


def calculate_sidereal_planets(jd: float) -> Dict[str, Any]:
    """
    Calculate sidereal positions of planets
    
    Vedic astrology uses sidereal zodiac (star-based)
    vs tropical zodiac (season-based) in Western
    """
    
    planets = {}
    
    # Planet IDs for Swiss Ephemeris
    planet_ids = {
        'sun': swe.SUN,
        'moon': swe.MOON,
        'mercury': swe.MERCURY,
        'venus': swe.VENUS,
        'mars': swe.MARS,
        'jupiter': swe.JUPITER,
        'saturn': swe.SATURN,
        'rahu': swe.MEAN_NODE,  # North Node = Rahu
        # Ketu is opposite of Rahu
    }
    
    for planet_name, planet_id in planet_ids.items():
        # Calculate sidereal position
        pos, ret = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        
        longitude = pos[0]
        sign = get_vedic_sign(longitude)
        
        # Calculate speed (for retrograde)
        speed = pos[3]
        is_retrograde = speed < 0
        
        planets[planet_name] = {
            'longitude': longitude,
            'sign': sign,
            'sign_num': int(longitude / 30) + 1,
            'degree_in_sign': longitude % 30,
            'retrograde': is_retrograde,
            'speed': speed
        }
    
    # Calculate Ketu (opposite of Rahu)
    rahu_lon = planets['rahu']['longitude']
    ketu_lon = (rahu_lon + 180) % 360
    
    planets['ketu'] = {
        'longitude': ketu_lon,
        'sign': get_vedic_sign(ketu_lon),
        'sign_num': int(ketu_lon / 30) + 1,
        'degree_in_sign': ketu_lon % 30,
        'retrograde': True,  # Ketu is always retrograde
        'speed': 0
    }
    
    return planets


def calculate_vedic_houses(jd: float, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calculate Vedic houses
    
    Vedic astrology traditionally uses Whole Sign houses
    (each house = one complete sign)
    """
    
    # Calculate Ascendant
    houses_data = swe.houses_ex(jd, latitude, longitude, b'W')  # Whole Sign
    ascendant = houses_data[1][0]  # Ascendant in sidereal
    
    # In Whole Sign system, Ascendant sign becomes 1st house
    # and each subsequent sign is the next house
    asc_sign_num = int(ascendant / 30) + 1
    
    houses = {}
    
    for house_num in range(1, 13):
        # Calculate which sign this house falls in
        sign_num = ((asc_sign_num - 1 + house_num - 1) % 12) + 1
        sign_start = (sign_num - 1) * 30
        
        houses[str(house_num)] = {
            'cusp': sign_start,  # House starts at beginning of sign
            'sign': get_vedic_sign(sign_start),
            'sign_num': sign_num
        }
    
    houses['ascendant'] = {
        'longitude': ascendant,
        'sign': get_vedic_sign(ascendant),
        'degree': ascendant % 30
    }
    
    return houses


def calculate_nakshatras(planets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate nakshatra positions for all planets
    
    Nakshatras are 27 lunar mansions, each 13°20' of the zodiac
    """
    
    nakshatra_data = {}
    
    for planet_name, planet_info in planets.items():
        longitude = planet_info['longitude']
        
        # Find which nakshatra
        nakshatra = get_nakshatra(longitude)
        
        nakshatra_data[planet_name] = nakshatra
    
    # Moon's nakshatra is especially important (for Dasha calculation)
    moon_nakshatra = nakshatra_data.get('moon', {})
    
    return {
        'all_nakshatras': nakshatra_data,
        'moon_nakshatra': moon_nakshatra,
        'moon_nakshatra_ruler': moon_nakshatra.get('ruler'),
        'interpretation': generate_nakshatra_interpretation(nakshatra_data)
    }


def get_nakshatra(longitude: float) -> Dict[str, Any]:
    """Get nakshatra details for a given longitude"""
    
    for nakshatra in NAKSHATRAS:
        if nakshatra['start'] <= longitude < nakshatra['end']:
            # Calculate pada (quarter within nakshatra)
            nakshatra_progress = longitude - nakshatra['start']
            pada_size = 13.333333 / 4  # Each nakshatra has 4 padas
            pada = int(nakshatra_progress / pada_size) + 1
            
            return {
                'name': nakshatra['name'],
                'ruler': nakshatra['ruler'],
                'deity': nakshatra['deity'],
                'pada': pada,
                'degree_in_nakshatra': nakshatra_progress
            }
    
    # Fallback
    return {
        'name': 'Unknown',
        'ruler': 'Unknown',
        'deity': 'Unknown',
        'pada': 1,
        'degree_in_nakshatra': 0
    }


def calculate_vimshottari_dasha(
    moon_nakshatra: Dict[str, Any],
    birth_date: date,
    birth_time: datetime
) -> Dict[str, Any]:
    """
    Calculate Vimshottari Dasha system
    
    120-year planetary period system
    Starting planet determined by Moon's nakshatra at birth
    """
    
    # Get starting planet from Moon's nakshatra ruler
    starting_planet = moon_nakshatra.get('ruler', 'Ketu')
    
    # Calculate how much of starting dasha is remaining at birth
    degree_in_nakshatra = moon_nakshatra.get('degree_in_nakshatra', 0)
    nakshatra_span = 13.333333
    
    # Proportion completed in nakshatra
    proportion_completed = degree_in_nakshatra / nakshatra_span
    
    # Starting dasha period
    starting_period_years = VIMSHOTTARI_PERIODS[starting_planet]
    
    # Years remaining in starting dasha
    years_remaining = starting_period_years * (1 - proportion_completed)
    
    # Calculate dasha periods
    dasha_sequence = get_dasha_sequence(starting_planet)
    
    # Calculate dates for each Maha Dasha (major period)
    maha_dashas = []
    current_date = datetime.combine(birth_date, birth_time.time())
    
    # First dasha (partial)
    first_dasha_end = current_date + timedelta(days=years_remaining * 365.25)
    maha_dashas.append({
        'planet': starting_planet,
        'start_date': current_date.isoformat(),
        'end_date': first_dasha_end.isoformat(),
        'duration_years': round(years_remaining, 2),
        'is_partial': True
    })
    
    current_date = first_dasha_end
    
    # Subsequent dashas (full periods)
    for i in range(1, len(dasha_sequence)):
        planet = dasha_sequence[i]
        period_years = VIMSHOTTARI_PERIODS[planet]
        
        end_date = current_date + timedelta(days=period_years * 365.25)
        
        maha_dashas.append({
            'planet': planet,
            'start_date': current_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_years': period_years,
            'is_partial': False
        })
        
        current_date = end_date
    
    # Find current dasha
    now = datetime.now()
    current_maha_dasha = None
    
    for dasha in maha_dashas:
        start = datetime.fromisoformat(dasha['start_date'])
        end = datetime.fromisoformat(dasha['end_date'])
        
        if start <= now <= end:
            current_maha_dasha = dasha
            break
    
    return {
        'system': 'Vimshottari',
        'total_cycle': '120 years',
        'starting_planet': starting_planet,
        'years_remaining_at_birth': round(years_remaining, 2),
        'maha_dashas': maha_dashas[:9],  # Show next 9 major periods
        'current_maha_dasha': current_maha_dasha,
        'interpretation': generate_dasha_interpretation(current_maha_dasha) if current_maha_dasha else None
    }


def get_dasha_sequence(starting_planet: str) -> List[str]:
    """Get the sequence of dashas starting from a given planet"""
    
    # Standard Vimshottari sequence
    standard_sequence = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    
    # Find starting index
    start_index = standard_sequence.index(starting_planet)
    
    # Rotate sequence
    sequence = standard_sequence[start_index:] + standard_sequence[:start_index]
    
    return sequence


def calculate_shadbala(
    planets: Dict[str, Any],
    houses: Dict[str, Any],
    jd: float
) -> Dict[str, Any]:
    """
    Calculate Shadbala (six-fold strength) for planets
    
    Six sources of strength:
    1. Sthana Bala (Positional strength)
    2. Dig Bala (Directional strength)
    3. Kala Bala (Temporal strength)
    4. Chesta Bala (Motional strength)
    5. Naisargika Bala (Natural strength)
    6. Drik Bala (Aspectual strength)
    """
    
    # Simplified Shadbala calculation
    # Full calculation is very complex
    
    strengths = {}
    
    for planet_name, planet_data in planets.items():
        if planet_name in ['rahu', 'ketu']:
            continue  # Nodes don't have Shadbala
        
        # Simplified strength score (0-100)
        strength_score = 50  # Base score
        
        # Sign strength (Exaltation, Own sign, etc.)
        sign = planet_data['sign']
        dignity = get_vedic_dignity(planet_name, sign)
        
        if dignity == 'exalted':
            strength_score += 30
        elif dignity == 'own_sign':
            strength_score += 20
        elif dignity == 'friend_sign':
            strength_score += 10
        elif dignity == 'debilitated':
            strength_score -= 30
        elif dignity == 'enemy_sign':
            strength_score -= 10
        
        # Retrograde reduces strength (except Jupiter and Saturn)
        if planet_data.get('retrograde') and planet_name not in ['jupiter', 'saturn']:
            strength_score -= 10
        
        # Cap between 0-100
        strength_score = max(0, min(100, strength_score))
        
        strengths[planet_name] = {
            'total_strength': strength_score,
            'dignity': dignity,
            'strong': strength_score >= 70,
            'weak': strength_score <= 30
        }
    
    return strengths


def identify_yogas(planets: Dict[str, Any], houses: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify yogas (planetary combinations) in chart
    
    Yogas indicate specific life outcomes
    There are hundreds of yogas; we'll check major ones
    """
    
    yogas = []
    
    # Panch Mahapurusha Yogas (5 great person yogas)
    # Mars, Mercury, Jupiter, Venus, or Saturn in own/exalted sign in kendra (1,4,7,10)
    
    kendra_houses = [1, 4, 7, 10]
    
    for planet_name in ['mars', 'mercury', 'jupiter', 'venus', 'saturn']:
        if planet_name not in planets:
            continue
            
        planet = planets[planet_name]
        house = get_planet_house(planet, houses)
        
        if house in kendra_houses:
            dignity = get_vedic_dignity(planet_name, planet['sign'])
            
            if dignity in ['own_sign', 'exalted']:
                yoga_name = f"{planet_name.title()} Mahapurusha Yoga"
                yogas.append({
                    'name': yoga_name,
                    'type': 'Panch Mahapurusha',
                    'planet': planet_name,
                    'significance': f'Great person yoga - {planet_name} excellence',
                    'strength': 'strong'
                })
    
    # Gaja Kesari Yoga (Moon-Jupiter yoga)
    # Jupiter in kendra from Moon
    if 'moon' in planets and 'jupiter' in planets:
        moon_sign = planets['moon']['sign_num']
        jupiter_sign = planets['jupiter']['sign_num']
        
        diff = abs(moon_sign - jupiter_sign)
        if diff in [0, 3, 6, 9]:  # Kendra relationship (1, 4, 7, 10)
            yogas.append({
                'name': 'Gaja Kesari Yoga',
                'type': 'Wealth & Fame',
                'planets': ['Moon', 'Jupiter'],
                'significance': 'Fame, wisdom, prosperity - elephant and lion',
                'strength': 'strong'
            })
    
    # Raja Yoga (combinations for power/authority)
    # Lords of kendras (1,4,7,10) with lords of trikonas (1,5,9) = Raja Yoga
    # Simplified check
    
    # Dhana Yoga (wealth combinations)
    # Lords of 2nd and 11th house in good positions = wealth
    
    return yogas


def calculate_vedic_aspects(planets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate Vedic aspects (Drishtis)
    
    Different from Western aspects:
    - All planets aspect 7th house/sign from themselves
    - Mars also aspects 4th and 8th
    - Jupiter also aspects 5th and 9th
    - Saturn also aspects 3rd and 10th
    """
    
    aspects = []
    
    for planet_name, planet_data in planets.items():
        planet_sign = planet_data['sign_num']
        
        # 7th aspect (all planets)
        seventh_sign = ((planet_sign + 6) % 12) + 1
        aspects.append({
            'planet': planet_name,
            'aspect_type': '7th house',
            'target_sign': seventh_sign,
            'strength': 'full'
        })
        
        # Special aspects
        if planet_name == 'mars':
            fourth_sign = ((planet_sign + 3) % 12) + 1
            eighth_sign = ((planet_sign + 7) % 12) + 1
            
            aspects.append({
                'planet': 'mars',
                'aspect_type': '4th house',
                'target_sign': fourth_sign,
                'strength': 'full'
            })
            
            aspects.append({
                'planet': 'mars',
                'aspect_type': '8th house',
                'target_sign': eighth_sign,
                'strength': 'full'
            })
        
        elif planet_name == 'jupiter':
            fifth_sign = ((planet_sign + 4) % 12) + 1
            ninth_sign = ((planet_sign + 8) % 12) + 1
            
            aspects.append({
                'planet': 'jupiter',
                'aspect_type': '5th house',
                'target_sign': fifth_sign,
                'strength': 'full'
            })
            
            aspects.append({
                'planet': 'jupiter',
                'aspect_type': '9th house',
                'target_sign': ninth_sign,
                'strength': 'full'
            })
        
        elif planet_name == 'saturn':
            third_sign = ((planet_sign + 2) % 12) + 1
            tenth_sign = ((planet_sign + 9) % 12) + 1
            
            aspects.append({
                'planet': 'saturn',
                'aspect_type': '3rd house',
                'target_sign': third_sign,
                'strength': 'full'
            })
            
            aspects.append({
                'planet': 'saturn',
                'aspect_type': '10th house',
                'target_sign': tenth_sign,
                'strength': 'full'
            })
    
    return aspects


def analyze_ascendant_vedic(houses: Dict[str, Any], planets: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Ascendant (Lagna) in Vedic astrology"""
    
    ascendant = houses.get('ascendant', {})
    asc_sign = ascendant.get('sign', 'Unknown')
    
    # Find Lagna lord (ruler of ascendant)
    lagna_lord = get_vedic_ruler(asc_sign)
    
    lagna_lord_data = None
    if lagna_lord.lower() in planets:
        lagna_lord_data = planets[lagna_lord.lower()]
    
    return {
        'ascendant_sign': asc_sign,
        'lagna_lord': lagna_lord,
        'lagna_lord_position': lagna_lord_data,
        'interpretation': f"Ascendant in {asc_sign} suggests {get_vedic_ascendant_meaning(asc_sign)}"
    }


def calculate_moon_chart(planets: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate Chandra Lagna (Moon chart)
    
    In Vedic astrology, chart is also read from Moon's position
    """
    
    moon = planets.get('moon', {})
    moon_sign = moon.get('sign_num', 1)
    
    # Treat Moon's sign as 1st house
    moon_houses = {}
    
    for house_num in range(1, 13):
        sign_num = ((moon_sign - 1 + house_num - 1) % 12) + 1
        moon_houses[house_num] = {
            'sign_num': sign_num,
            'sign': get_vedic_sign((sign_num - 1) * 30)
        }
    
    return {
        'moon_sign': moon.get('sign'),
        'moon_as_ascendant': moon_sign,
        'houses_from_moon': moon_houses,
        'interpretation': 'Chart read from Moon shows emotional and mental patterns'
    }


def calculate_divisional_charts(jd: float, birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate divisional charts (Vargas)
    
    Most important:
    - D9 (Navamsha) - Marriage, spouse, dharma
    - D10 (Dasamsha) - Career, profession
    """
    
    # Navamsha (D9) - Each sign divided into 9 parts
    # This is complex calculation, simplified here
    
    return {
        'd9_navamsha': {
            'note': 'D9 Navamsha chart for marriage and dharma',
            'status': 'Calculation requires detailed implementation'
        },
        'd10_dasamsha': {
            'note': 'D10 Dasamsha chart for career',
            'status': 'Calculation requires detailed implementation'
        }
    }


# Helper functions

def get_vedic_sign(longitude: float) -> str:
    """Get Vedic zodiac sign from longitude"""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30)
    return signs[sign_index % 12]


def get_vedic_ruler(sign: str) -> str:
    """Get traditional Vedic ruler of sign"""
    rulers = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
        'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
        'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
        'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }
    return rulers.get(sign, 'Unknown')


def get_vedic_dignity(planet: str, sign: str) -> str:
    """Get Vedic dignity (exaltation, debilitation, etc.)"""
    
    # Exaltations
    exaltations = {
        'sun': 'Aries', 'moon': 'Taurus', 'mars': 'Capricorn',
        'mercury': 'Virgo', 'jupiter': 'Cancer', 'venus': 'Pisces',
        'saturn': 'Libra'
    }
    
    # Debilitations (opposite of exaltation)
    debilitations = {
        'sun': 'Libra', 'moon': 'Scorpio', 'mars': 'Cancer',
        'mercury': 'Pisces', 'jupiter': 'Capricorn', 'venus': 'Virgo',
        'saturn': 'Aries'
    }
    
    # Own signs
    own_signs = {
        'sun': ['Leo'], 'moon': ['Cancer'], 'mars': ['Aries', 'Scorpio'],
        'mercury': ['Gemini', 'Virgo'], 'jupiter': ['Sagittarius', 'Pisces'],
        'venus': ['Taurus', 'Libra'], 'saturn': ['Capricorn', 'Aquarius']
    }
    
    if exaltations.get(planet) == sign:
        return 'exalted'
    elif debilitations.get(planet) == sign:
        return 'debilitated'
    elif sign in own_signs.get(planet, []):
        return 'own_sign'
    else:
        # Would need to check friend/enemy signs
        return 'neutral'


def get_planet_house(planet: Dict[str, Any], houses: Dict[str, Any]) -> int:
    """Determine which house a planet is in"""
    
    planet_sign = planet['sign_num']
    
    for house_num in range(1, 13):
        house_data = houses.get(str(house_num), {})
        house_sign = house_data.get('sign_num')
        
        if house_sign == planet_sign:
            return house_num
    
    return 1  # Default


def get_vedic_ascendant_meaning(sign: str) -> str:
    """Get Vedic meaning of ascendant sign"""
    
    meanings = {
        'Aries': 'dynamic, pioneering personality',
        'Taurus': 'stable, practical nature',
        'Gemini': 'communicative, intellectual approach',
        'Cancer': 'emotional, nurturing character',
        'Leo': 'confident, leadership qualities',
        'Virgo': 'analytical, service-oriented',
        'Libra': 'diplomatic, relationship-focused',
        'Scorpio': 'intense, transformative nature',
        'Sagittarius': 'philosophical, adventurous spirit',
        'Capricorn': 'ambitious, disciplined approach',
        'Aquarius': 'innovative, humanitarian nature',
        'Pisces': 'spiritual, compassionate character'
    }
    
    return meanings.get(sign, 'unique personality')


def generate_nakshatra_interpretation(nakshatra_data: Dict[str, Any]) -> str:
    """Generate nakshatra interpretation"""
    
    moon_nak = nakshatra_data.get('moon_nakshatra', {})
    
    return (
        f"Moon in {moon_nak.get('name', 'Unknown')} nakshatra "
        f"(ruled by {moon_nak.get('ruler', 'Unknown')}, "
        f"deity: {moon_nak.get('deity', 'Unknown')}). "
        f"This nakshatra influences emotional nature and life path."
    )


def generate_dasha_interpretation(dasha: Dict[str, Any]) -> str:
    """Generate Dasha period interpretation"""
    
    planet = dasha.get('planet', 'Unknown')
    
    dasha_meanings = {
        'Sun': 'Focus on self-expression, authority, and father figures',
        'Moon': 'Emotional fulfillment, mother, home matters',
        'Mars': 'Energy, action, conflicts, property matters',
        'Mercury': 'Communication, learning, business, siblings',
        'Jupiter': 'Growth, wisdom, spirituality, children',
        'Venus': 'Relationships, beauty, luxury, marriage',
        'Saturn': 'Discipline, hard work, delays, karmic lessons',
        'Rahu': 'Worldly desires, foreign connections, sudden changes',
        'Ketu': 'Spirituality, isolation, detachment, moksha'
    }
    
    meaning = dasha_meanings.get(planet, 'Planetary influence period')
    
    return f"Current {planet} Maha Dasha: {meaning}"


def generate_vedic_interpretation(
    planets: Dict[str, Any],
    houses: Dict[str, Any],
    nakshatras: Dict[str, Any],
    yogas: List[Dict[str, Any]],
    dashas: Optional[Dict[str, Any]]
) -> str:
    """Generate comprehensive Vedic interpretation"""
    
    parts = []
    
    parts.append("VEDIC ASTROLOGY ANALYSIS (JYOTISH)\n\n")
    parts.append("=" * 50 + "\n\n")
    
    # Ascendant
    asc = houses.get('ascendant', {})
    parts.append(f"ASCENDANT (LAGNA): {asc.get('sign', 'Unknown')}\n")
    parts.append(f"{get_vedic_ascendant_meaning(asc.get('sign', ''))}\n\n")
    
    # Moon Nakshatra
    moon_nak = nakshatras.get('moon_nakshatra', {})
    parts.append(f"MOON NAKSHATRA: {moon_nak.get('name', 'Unknown')}\n")
    parts.append(f"Ruler: {moon_nak.get('ruler', 'Unknown')}\n")
    parts.append(f"Deity: {moon_nak.get('deity', 'Unknown')}\n\n")
    
    # Current Dasha
    if dashas:
        current = dashas.get('current_maha_dasha')
        if current:
            parts.append(f"CURRENT DASHA: {current.get('planet', 'Unknown')}\n")
            parts.append(f"Period: {current.get('start_date', '')} to {current.get('end_date', '')}\n\n")
    
    # Yogas
    if yogas:
        parts.append("YOGAS (PLANETARY COMBINATIONS):\n")
        for yoga in yogas[:3]:
            parts.append(f"• {yoga['name']}: {yoga['significance']}\n")
    
    return ''.join(parts)


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    example_birth_data = {
        'name': 'Example Person',
        'birth_date': date(1990, 6, 15),
        'birth_time': datetime(1990, 6, 15, 14, 30),
        'birth_place': 'Mumbai',
        'nation': 'IN',
        'latitude': 19.0760,
        'longitude': 72.8777,
        'timezone': 'Asia/Kolkata'
    }
    
    vedic_chart = calculate_vedic_chart(example_birth_data)
    
    print("Vedic Chart Calculated:")
    print(f"Ascendant: {vedic_chart['houses']['ascendant']['sign']}")
    print(f"Moon Nakshatra: {vedic_chart['nakshatras']['moon_nakshatra']['name']}")
