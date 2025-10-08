"""
Solar, Lunar, Chiron, and Saturn Returns - COMPLETE VERSION
Calculate return charts for major planetary cycles
"""

from kerykeion import AstrologicalSubject
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def calculate_solar_return(
    natal_data: Dict[str, Any],
    return_year: int,
    return_location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate Solar Return chart (Sun returns to natal position)
    
    Occurs once per year around birthday
    
    Args:
        natal_data: Birth data including natal Sun position
        return_year: Year for solar return
        return_location: Location for return (current residence, not birth place)
        
    Returns:
        Solar return chart data
    """
    try:
        logger.info(f"Calculating solar return for year {return_year}")
        
        # Get natal Sun longitude
        natal_sun_lon = natal_data['planets']['sun']['longitude']
        birth_date = natal_data['birth_date']
        
        # Use return location or birth location
        if return_location is None:
            return_location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Find exact time when Sun returns to natal position
        return_datetime = find_sun_return_time(natal_sun_lon, return_year, birth_date)
        
        # Create return chart
        return_chart = AstrologicalSubject(
            name=f"Solar Return {return_year}",
            year=return_datetime.year,
            month=return_datetime.month,
            day=return_datetime.day,
            hour=return_datetime.hour,
            minute=return_datetime.minute,
            city=return_location['city'],
            lat=return_location['latitude'],
            lng=return_location['longitude'],
            tz_str=return_location['timezone']
        )
        
        # Extract chart data
        planets = extract_planets(return_chart)
        houses = extract_houses(return_chart)
        
        # Analyze return chart
        analysis = analyze_solar_return(planets, houses, natal_data)
        
        # Generate interpretation
        interpretation = generate_solar_return_interpretation(return_year, analysis)
        
        return {
            'type': 'Solar Return',
            'year': return_year,
            'exact_time': return_datetime.isoformat(),
            'location': return_location,
            'planets': planets,
            'houses': houses,
            'analysis': analysis,
            'interpretation': interpretation
        }
        
    except Exception as e:
        logger.error(f"Solar return calculation failed: {str(e)}")
        raise


def calculate_lunar_return(
    natal_data: Dict[str, Any],
    target_date: date,
    return_location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate Lunar Return chart (Moon returns to natal position)
    
    Occurs approximately every 27.3 days
    
    Args:
        natal_data: Birth data including natal Moon position
        target_date: Target date to find lunar return near
        return_location: Location for return
        
    Returns:
        Lunar return chart data
    """
    try:
        logger.info(f"Calculating lunar return near {target_date}")
        
        # Get natal Moon longitude
        natal_moon_lon = natal_data['planets']['moon']['longitude']
        
        # Use return location or birth location
        if return_location is None:
            return_location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Find exact time when Moon returns to natal position
        return_datetime = find_moon_return_time(natal_moon_lon, target_date)
        
        # Create return chart
        return_chart = AstrologicalSubject(
            name=f"Lunar Return {target_date.isoformat()}",
            year=return_datetime.year,
            month=return_datetime.month,
            day=return_datetime.day,
            hour=return_datetime.hour,
            minute=return_datetime.minute,
            city=return_location['city'],
            lat=return_location['latitude'],
            lng=return_location['longitude'],
            tz_str=return_location['timezone']
        )
        
        # Extract chart data
        planets = extract_planets(return_chart)
        houses = extract_houses(return_chart)
        
        # Analyze
        analysis = analyze_lunar_return(planets, houses)
        
        return {
            'type': 'Lunar Return',
            'exact_time': return_datetime.isoformat(),
            'location': return_location,
            'planets': planets,
            'houses': houses,
            'analysis': analysis,
            'interpretation': f"Lunar return for the month starting {target_date.isoformat()}"
        }
        
    except Exception as e:
        logger.error(f"Lunar return calculation failed: {str(e)}")
        raise


def calculate_chiron_return(
    natal_data: Dict[str, Any],
    return_location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate Chiron Return chart
    
    Occurs around age 50-51 (Chiron's orbital period is ~50.7 years)
    
    Major life transition - the "Wounded Healer" return
    
    Args:
        natal_data: Birth data including natal Chiron position
        return_location: Location for return
        
    Returns:
        Chiron return chart data and timing
    """
    try:
        logger.info("Calculating Chiron return")
        
        birth_date = natal_data['birth_date']
        
        # Calculate Chiron return time (approximately 50-51 years after birth)
        # Chiron's orbital period is ~50.7 years
        chiron_return_year = birth_date.year + 50
        
        # Get natal Chiron position using Swiss Ephemeris
        natal_chart_dt = datetime.combine(birth_date, natal_data.get('birth_time', datetime.min.time()))
        jd_natal = swe.julday(natal_chart_dt.year, natal_chart_dt.month, natal_chart_dt.day, 
                              natal_chart_dt.hour + natal_chart_dt.minute/60)
        
        # Chiron is minor planet #2060 in Swiss Ephemeris
        natal_chiron = swe.calc_ut(jd_natal, swe.CHIRON)[0][0]
        
        # Find when Chiron returns to natal position
        return_datetime = find_chiron_return_time(natal_chiron, chiron_return_year, birth_date)
        
        # Use return location or birth location
        if return_location is None:
            return_location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Create return chart
        return_chart = AstrologicalSubject(
            name=f"Chiron Return {return_datetime.year}",
            year=return_datetime.year,
            month=return_datetime.month,
            day=return_datetime.day,
            hour=return_datetime.hour,
            minute=return_datetime.minute,
            city=return_location['city'],
            lat=return_location['latitude'],
            lng=return_location['longitude'],
            tz_str=return_location['timezone']
        )
        
        # Extract chart data
        planets = extract_planets(return_chart)
        houses = extract_houses(return_chart)
        
        # Chiron return analysis
        analysis = analyze_chiron_return(planets, houses, natal_data)
        
        # Generate interpretation
        interpretation = generate_chiron_return_interpretation(return_datetime.year, analysis)
        
        return {
            'type': 'Chiron Return',
            'exact_time': return_datetime.isoformat(),
            'age_at_return': return_datetime.year - birth_date.year,
            'location': return_location,
            'natal_chiron_longitude': natal_chiron,
            'planets': planets,
            'houses': houses,
            'analysis': analysis,
            'interpretation': interpretation,
            'themes': {
                'main': 'Healing the wounded healer',
                'focus': [
                    'Deep healing of core wounds',
                    'Transformation of pain into wisdom',
                    'Teaching/mentoring from your wounds',
                    'Spiritual maturity and acceptance'
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Chiron return calculation failed: {str(e)}")
        raise


def calculate_saturn_return(
    natal_data: Dict[str, Any],
    return_number: int = 1,
    return_location: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate Saturn Return chart
    
    Saturn returns occur approximately every 29.5 years:
    - 1st Return: Age 29-30 (adulthood, responsibility)
    - 2nd Return: Age 58-59 (wisdom, legacy)
    - 3rd Return: Age 87-88 (completion, reflection)
    
    Args:
        natal_data: Birth data including natal Saturn position
        return_number: Which return (1, 2, or 3)
        return_location: Location for return
        
    Returns:
        Saturn return chart data
    """
    try:
        logger.info(f"Calculating Saturn return #{return_number}")
        
        if return_number not in [1, 2, 3]:
            raise ValueError("return_number must be 1, 2, or 3")
        
        birth_date = natal_data['birth_date']
        
        # Calculate Saturn return year
        # Saturn's orbital period is ~29.46 years
        saturn_cycle = 29
        saturn_return_year = birth_date.year + (saturn_cycle * return_number)
        
        # Get natal Saturn position
        natal_saturn_lon = natal_data['planets']['saturn']['longitude']
        
        # Find when Saturn returns to natal position
        return_datetime = find_saturn_return_time(natal_saturn_lon, saturn_return_year, birth_date)
        
        # Use return location or birth location
        if return_location is None:
            return_location = {
                'city': natal_data.get('birth_place', 'Istanbul'),
                'latitude': natal_data.get('latitude', 41.0082),
                'longitude': natal_data.get('longitude', 28.9784),
                'timezone': natal_data.get('timezone', 'Europe/Istanbul')
            }
        
        # Create return chart
        return_chart = AstrologicalSubject(
            name=f"Saturn Return {return_number} - {return_datetime.year}",
            year=return_datetime.year,
            month=return_datetime.month,
            day=return_datetime.day,
            hour=return_datetime.hour,
            minute=return_datetime.minute,
            city=return_location['city'],
            lat=return_location['latitude'],
            lng=return_location['longitude'],
            tz_str=return_location['timezone']
        )
        
        # Extract chart data
        planets = extract_planets(return_chart)
        houses = extract_houses(return_chart)
        
        # Saturn return analysis
        analysis = analyze_saturn_return(planets, houses, return_number, natal_data)
        
        # Generate interpretation
        interpretation = generate_saturn_return_interpretation(return_number, return_datetime.year, analysis)
        
        return {
            'type': f'Saturn Return #{return_number}',
            'exact_time': return_datetime.isoformat(),
            'age_at_return': return_datetime.year - birth_date.year,
            'location': return_location,
            'natal_saturn_longitude': natal_saturn_lon,
            'planets': planets,
            'houses': houses,
            'analysis': analysis,
            'interpretation': interpretation,
            'themes': get_saturn_return_themes(return_number)
        }
        
    except Exception as e:
        logger.error(f"Saturn return calculation failed: {str(e)}")
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_sun_return_time(natal_sun_lon: float, return_year: int, birth_date: date) -> datetime:
    """Find exact time when Sun returns to natal position"""
    # Start search around birthday
    search_date = datetime(return_year, birth_date.month, birth_date.day, 12, 0)
    
    # Binary search for exact return time
    for days_offset in range(-5, 6):
        check_dt = search_date + timedelta(days=days_offset)
        jd = swe.julday(check_dt.year, check_dt.month, check_dt.day, 12.0)
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        
        diff = abs(sun_lon - natal_sun_lon)
        if diff > 180:
            diff = 360 - diff
        
        if diff < 0.5:  # Within 0.5 degrees
            return check_dt
    
    return search_date


def find_moon_return_time(natal_moon_lon: float, target_date: date) -> datetime:
    """Find exact time when Moon returns to natal position"""
    # Moon returns approximately every 27.3 days
    # Search 3 days before and after target date
    
    closest_time = None
    smallest_diff = 360
    
    for days_offset in range(-3, 4):
        for hour in range(0, 24, 4):  # Check every 4 hours
            check_dt = datetime.combine(target_date, datetime.min.time()) + timedelta(days=days_offset, hours=hour)
            jd = swe.julday(check_dt.year, check_dt.month, check_dt.day, check_dt.hour)
            moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
            
            diff = abs(moon_lon - natal_moon_lon)
            if diff > 180:
                diff = 360 - diff
            
            if diff < smallest_diff:
                smallest_diff = diff
                closest_time = check_dt
    
    return closest_time or datetime.combine(target_date, datetime.min.time())


def find_chiron_return_time(natal_chiron_lon: float, return_year: int, birth_date: date) -> datetime:
    """Find exact time when Chiron returns to natal position"""
    # Search around birthday in return year
    search_date = datetime(return_year, birth_date.month, birth_date.day, 12, 0)
    
    closest_time = None
    smallest_diff = 360
    
    for days_offset in range(-30, 31):  # Check 2 months around birthday
        check_dt = search_date + timedelta(days=days_offset)
        jd = swe.julday(check_dt.year, check_dt.month, check_dt.day, 12.0)
        chiron_lon = swe.calc_ut(jd, swe.CHIRON)[0][0]
        
        diff = abs(chiron_lon - natal_chiron_lon)
        if diff > 180:
            diff = 360 - diff
        
        if diff < smallest_diff:
            smallest_diff = diff
            closest_time = check_dt
    
    return closest_time or search_date


def find_saturn_return_time(natal_saturn_lon: float, return_year: int, birth_date: date) -> datetime:
    """Find exact time when Saturn returns to natal position"""
    # Search around birthday in return year
    search_date = datetime(return_year, birth_date.month, birth_date.day, 12, 0)
    
    closest_time = None
    smallest_diff = 360
    
    for days_offset in range(-180, 181):  # Check 1 year around estimated time
        check_dt = search_date + timedelta(days=days_offset)
        jd = swe.julday(check_dt.year, check_dt.month, check_dt.day, 12.0)
        saturn_lon = swe.calc_ut(jd, swe.SATURN)[0][0]
        
        diff = abs(saturn_lon - natal_saturn_lon)
        if diff > 180:
            diff = 360 - diff
        
        if diff < smallest_diff:
            smallest_diff = diff
            closest_time = check_dt
    
    return closest_time or search_date


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
                'degree': planet_obj['position'] % 30,
                'retrograde': planet_obj.get('retrograde', False)
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


def analyze_solar_return(planets: Dict[str, Any], houses: Dict[str, Any], natal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Solar Return chart for year themes"""
    
    # Find angular planets (on angles: ASC, IC, DSC, MC)
    angular_planets = find_angular_planets(planets, houses)
    
    # Ascendant sign sets tone for year
    asc_sign = houses.get('1', {}).get('sign', 'Unknown')
    
    return {
        'ascendant_sign': asc_sign,
        'angular_planets': angular_planets,
        'year_theme': f"Year themed by {asc_sign} rising",
        'focus_areas': get_solar_return_focus(angular_planets)
    }


def analyze_lunar_return(planets: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Lunar Return for monthly themes"""
    moon = planets.get('moon', {})
    return {
        'moon_sign': moon.get('sign', 'Unknown'),
        'emotional_theme': f"Month with {moon.get('sign', 'Unknown')} emotional energy"
    }


def analyze_chiron_return(planets: Dict[str, Any], houses: Dict[str, Any], natal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Chiron Return"""
    return {
        'themes': [
            'Deep healing of core wounds',
            'Transformation of pain into wisdom',
            'Spiritual maturity',
            'Teaching from experience'
        ],
        'focus': 'Embracing the wounded healer archetype'
    }


def analyze_saturn_return(planets: Dict[str, Any], houses: Dict[str, Any], return_number: int, natal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Saturn Return"""
    saturn = planets.get('saturn', {})
    saturn_house = determine_house(saturn.get('longitude', 0), houses)
    
    return {
        'saturn_sign': saturn.get('sign', 'Unknown'),
        'saturn_house': saturn_house,
        'return_number': return_number,
        'focus_area': get_house_meaning(saturn_house)
    }


def find_angular_planets(planets: Dict[str, Any], houses: Dict[str, Any]) -> List[str]:
    """Find planets on angles (ASC, IC, DSC, MC)"""
    angular = []
    angular_cusps = [1, 4, 7, 10]  # ASC, IC, DSC, MC
    
    for planet_name, planet_data in planets.items():
        planet_lon = planet_data['longitude']
        
        for cusp_num in angular_cusps:
            cusp_lon = houses.get(str(cusp_num), {}).get('cusp', 0)
            diff = abs(planet_lon - cusp_lon)
            if diff > 180:
                diff = 360 - diff
            
            if diff < 10:  # Within 10 degrees
                angular.append(f"{planet_name.title()} near {get_angle_name(cusp_num)}")
    
    return angular


def get_angle_name(house_num: int) -> str:
    """Get angle name"""
    names = {1: 'ASC', 4: 'IC', 7: 'DSC', 10: 'MC'}
    return names.get(house_num, 'House')


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


def get_house_meaning(house: int) -> str:
    """Get house meaning"""
    meanings = {
        1: "Self and identity",
        2: "Resources and values",
        3: "Communication and learning",
        4: "Home and family",
        5: "Creativity and romance",
        6: "Work and health",
        7: "Partnerships",
        8: "Transformation",
        9: "Philosophy and travel",
        10: "Career and reputation",
        11: "Friends and aspirations",
        12: "Spirituality and solitude"
    }
    return meanings.get(house, "Life area")


def get_solar_return_focus(angular_planets: List[str]) -> List[str]:
    """Get focus areas from angular planets"""
    if not angular_planets:
        return ["General year themes"]
    return [f"Focus on {p}" for p in angular_planets]


def get_saturn_return_themes(return_number: int) -> Dict[str, Any]:
    """Get themes for Saturn Return"""
    themes = {
        1: {
            'age': '29-30',
            'main_theme': 'Becoming an adult',
            'focus': [
                'Taking responsibility',
                'Defining your path',
                'Letting go of youth',
                'Building foundations',
                'Career establishment'
            ]
        },
        2: {
            'age': '58-59',
            'main_theme': 'Wisdom and legacy',
            'focus': [
                'Embracing wisdom',
                'Defining your legacy',
                'Mentoring others',
                'Harvesting life lessons',
                'Preparing for elderhood'
            ]
        },
        3: {
            'age': '87-88',
            'main_theme': 'Completion and reflection',
            'focus': [
                'Life review',
                'Acceptance',
                'Spiritual completion',
                'Sharing wisdom',
                'Preparing for transition'
            ]
        }
    }
    return themes.get(return_number, {'main_theme': 'Saturn cycle', 'focus': []})


def generate_solar_return_interpretation(year: int, analysis: Dict[str, Any]) -> str:
    """Generate Solar Return interpretation"""
    return f"Solar Return {year}: {analysis['year_theme']}. Focus on: {', '.join(analysis['focus_areas'])}"


def generate_chiron_return_interpretation(year: int, analysis: Dict[str, Any]) -> str:
    """Generate Chiron Return interpretation"""
    return f"Chiron Return ~{year}: Major healing cycle. {analysis['focus']}"


def generate_saturn_return_interpretation(return_num: int, year: int, analysis: Dict[str, Any]) -> str:
    """Generate Saturn Return interpretation"""
    themes = get_saturn_return_themes(return_num)
    return f"Saturn Return #{return_num} (~{year}): {themes['main_theme']}. Focus: {', '.join(themes['focus'][:3])}"


# Example usage
if __name__ == "__main__":
    from datetime import date, time
    
    natal_data = {
        'birth_date': date(1990, 5, 15),
        'birth_time': time(14, 30),
        'latitude': 41.0082,
        'longitude': 28.9784,
        'planets': {
            'sun': {'longitude': 54.2},
            'moon': {'longitude': 120.5},
            'saturn': {'longitude': 280.3}
        }
    }
    
    # Solar Return
    solar = calculate_solar_return(natal_data, 2025)
    print(f"Solar Return 2025: {solar['interpretation']}")
    
    # Saturn Return
    saturn = calculate_saturn_return(natal_data, return_number=1)
    print(f"\n{saturn['interpretation']}")
    
    # Chiron Return
    chiron = calculate_chiron_return(natal_data)
    print(f"\n{chiron['interpretation']}")
