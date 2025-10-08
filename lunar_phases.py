"""
Lunar phases and moon calendar calculations - COMPLETE VERSION
Tracks moon phases, void of course, and lunar phenomena
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def calculate_current_moon_phase() -> Dict[str, Any]:
    """
    Calculate current moon phase
    
    Returns:
        Current moon phase data
    """
    try:
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60)
        
        # Get Sun and Moon positions
        sun_pos = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
        
        # Calculate phase angle
        phase_angle = (moon_pos - sun_pos) % 360
        
        # Determine phase name
        phase_info = get_phase_from_angle(phase_angle)
        
        # Calculate illumination percentage
        illumination = calculate_illumination(phase_angle)
        
        return {
            'datetime': now.isoformat(),
            'phase_angle': round(phase_angle, 2),
            'phase_name': phase_info['name'],
            'phase_emoji': phase_info['emoji'],
            'illumination': round(illumination, 1),
            'description': phase_info['description']
        }
        
    except Exception as e:
        logger.error(f"Moon phase calculation failed: {str(e)}")
        raise


def get_moon_calendar(year: int, month: int) -> Dict[str, Any]:
    """
    Get moon calendar for a specific month
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Daily moon data for the month
    """
    try:
        logger.info(f"Generating moon calendar for {year}-{month:02d}")
        
        # Determine number of days in month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        
        last_day = (next_month - timedelta(days=1)).day
        
        # Calculate for each day
        daily_data = []
        for day in range(1, last_day + 1):
            day_date = date(year, month, day)
            day_moon = calculate_daily_moon(day_date)
            daily_data.append(day_moon)
        
        # Find new moons and full moons
        new_moons = [d for d in daily_data if 'New Moon' in d['phase_name']]
        full_moons = [d for d in daily_data if 'Full Moon' in d['phase_name']]
        
        return {
            'year': year,
            'month': month,
            'daily_moon': daily_data,
            'new_moons': new_moons,
            'full_moons': full_moons
        }
        
    except Exception as e:
        logger.error(f"Moon calendar generation failed: {str(e)}")
        raise


def calculate_daily_moon(day: date) -> Dict[str, Any]:
    """
    Calculate moon data for a specific day
    
    Returns:
        Moon data for the day
    """
    try:
        # Use noon UTC for daily calculation
        dt = datetime.combine(day, datetime.min.time().replace(hour=12))
        jd = swe.julday(dt.year, dt.month, dt.day, 12.0)
        
        # Get Moon position
        moon_result = swe.calc_ut(jd, swe.MOON)
        moon_lon = moon_result[0][0]
        moon_speed = moon_result[0][3]
        
        # Get Sun position
        sun_result = swe.calc_ut(jd, swe.SUN)
        sun_lon = sun_result[0][0]
        
        # Calculate phase
        phase_angle = (moon_lon - sun_lon) % 360
        phase_info = get_phase_from_angle(phase_angle)
        illumination = calculate_illumination(phase_angle)
        
        # Get Moon sign
        moon_sign = get_zodiac_sign(moon_lon)
        
        # Check if Moon is void of course
        void_of_course = check_void_of_course_simple(moon_lon, moon_speed)
        
        return {
            'date': day.isoformat(),
            'moon_longitude': round(moon_lon, 4),
            'moon_sign': moon_sign,
            'phase_angle': round(phase_angle, 2),
            'phase_name': phase_info['name'],
            'phase_emoji': phase_info['emoji'],
            'illumination': round(illumination, 1),
            'void_of_course': void_of_course,
            'description': phase_info['description']
        }
        
    except Exception as e:
        logger.error(f"Daily moon calculation failed: {str(e)}")
        return {
            'date': day.isoformat(),
            'error': str(e)
        }


def get_phase_from_angle(angle: float) -> Dict[str, str]:
    """
    Determine moon phase from Sun-Moon angle
    
    Args:
        angle: Angle between Sun and Moon (0-360)
        
    Returns:
        Phase information
    """
    if angle < 45:
        return {
            'name': 'New Moon',
            'emoji': '🌑',
            'description': 'New beginnings, setting intentions'
        }
    elif angle < 90:
        return {
            'name': 'Waxing Crescent',
            'emoji': '🌒',
            'description': 'Growth, taking action'
        }
    elif angle < 135:
        return {
            'name': 'First Quarter',
            'emoji': '🌓',
            'description': 'Challenges, decision making'
        }
    elif angle < 180:
        return {
            'name': 'Waxing Gibbous',
            'emoji': '🌔',
            'description': 'Refinement, preparation'
        }
    elif angle < 225:
        return {
            'name': 'Full Moon',
            'emoji': '🌕',
            'description': 'Culmination, illumination'
        }
    elif angle < 270:
        return {
            'name': 'Waning Gibbous',
            'emoji': '🌖',
            'description': 'Gratitude, sharing'
        }
    elif angle < 315:
        return {
            'name': 'Last Quarter',
            'emoji': '🌗',
            'description': 'Release, letting go'
        }
    else:
        return {
            'name': 'Waning Crescent',
            'emoji': '🌘',
            'description': 'Rest, reflection'
        }


def calculate_illumination(phase_angle: float) -> float:
    """
    Calculate moon illumination percentage from phase angle
    
    Args:
        phase_angle: Sun-Moon angle (0-360)
        
    Returns:
        Illumination percentage (0-100)
    """
    # Formula: illumination peaks at 180° (full moon)
    illumination = 50 * (1 - abs(phase_angle - 180) / 180)
    return max(0, min(100, illumination))


def get_zodiac_sign(longitude: float) -> str:
    """Get zodiac sign from ecliptic longitude"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]


def check_void_of_course_simple(moon_lon: float, moon_speed: float) -> bool:
    """
    Simplified void of course check
    
    Moon is void when it's late in sign (last 3 degrees)
    Real calculation would check for aspects before sign change
    
    Args:
        moon_lon: Moon's ecliptic longitude
        moon_speed: Moon's daily motion
        
    Returns:
        True if void of course
    """
    degree_in_sign = moon_lon % 30
    
    # If Moon is in last 3 degrees of sign, consider it void
    # (Simplified - real calculation checks for applying aspects)
    return degree_in_sign >= 27


def find_next_new_moon(start_date: date = None) -> Dict[str, Any]:
    """
    Find the next New Moon date
    
    Args:
        start_date: Starting date (default: today)
        
    Returns:
        Next new moon data
    """
    if start_date is None:
        start_date = date.today()
    
    # Search up to 40 days ahead
    for days_ahead in range(40):
        check_date = start_date + timedelta(days=days_ahead)
        day_moon = calculate_daily_moon(check_date)
        
        if 'New Moon' in day_moon['phase_name'] and day_moon['illumination'] < 5:
            return {
                'date': check_date.isoformat(),
                'moon_sign': day_moon['moon_sign'],
                'phase_angle': day_moon['phase_angle']
            }
    
    return {'error': 'No New Moon found in next 40 days'}


def find_next_full_moon(start_date: date = None) -> Dict[str, Any]:
    """
    Find the next Full Moon date
    
    Args:
        start_date: Starting date (default: today)
        
    Returns:
        Next full moon data
    """
    if start_date is None:
        start_date = date.today()
    
    # Search up to 40 days ahead
    for days_ahead in range(40):
        check_date = start_date + timedelta(days=days_ahead)
        day_moon = calculate_daily_moon(check_date)
        
        if 'Full Moon' in day_moon['phase_name'] and day_moon['illumination'] > 95:
            return {
                'date': check_date.isoformat(),
                'moon_sign': day_moon['moon_sign'],
                'phase_angle': day_moon['phase_angle']
            }
    
    return {'error': 'No Full Moon found in next 40 days'}


def get_moon_manifestation_guide(phase_name: str) -> Dict[str, Any]:
    """
    Get manifestation and intention-setting guide for moon phase
    
    Args:
        phase_name: Name of the moon phase
        
    Returns:
        Manifestation guide
    """
    guides = {
        'New Moon': {
            'energy': 'Planting seeds, new beginnings',
            'activities': [
                'Set new intentions',
                'Start new projects',
                'Write goals for the lunar cycle',
                'Meditate on desires'
            ],
            'avoid': ['Major decisions', 'Starting without a plan']
        },
        'Waxing Crescent': {
            'energy': 'Growth, taking first steps',
            'activities': [
                'Take action on intentions',
                'Gather resources',
                'Build momentum',
                'Network and connect'
            ],
            'avoid': ['Giving up too soon', 'Lack of follow-through']
        },
        'First Quarter': {
            'energy': 'Challenges, perseverance',
            'activities': [
                'Push through obstacles',
                'Make decisions',
                'Adjust plans',
                'Stay committed'
            ],
            'avoid': ['Giving in to resistance', 'Impulsive changes']
        },
        'Waxing Gibbous': {
            'energy': 'Refinement, patience',
            'activities': [
                'Perfect your approach',
                'Prepare for completion',
                'Trust the process',
                'Fine-tune details'
            ],
            'avoid': ['Impatience', 'Forcing outcomes']
        },
        'Full Moon': {
            'energy': 'Culmination, celebration',
            'activities': [
                'Celebrate achievements',
                'Release what no longer serves',
                'Perform Full Moon rituals',
                'Express gratitude'
            ],
            'avoid': ['Major decisions', 'Overreacting emotionally']
        },
        'Waning Gibbous': {
            'energy': 'Sharing, teaching',
            'activities': [
                'Share your wisdom',
                'Give back',
                'Reflect on lessons',
                'Integrate experiences'
            ],
            'avoid': ['Holding on too tightly', 'Overgiving']
        },
        'Last Quarter': {
            'energy': 'Release, letting go',
            'activities': [
                'Release old patterns',
                'Forgive and move on',
                'Clear space',
                'Prepare for renewal'
            ],
            'avoid': ['Starting new projects', 'Clinging to past']
        },
        'Waning Crescent': {
            'energy': 'Rest, surrender',
            'activities': [
                'Rest and recharge',
                'Meditate',
                'Journal insights',
                'Prepare for new cycle'
            ],
            'avoid': ['Overwork', 'Major commitments']
        }
    }
    
    return guides.get(phase_name, {
        'energy': 'Transitional phase',
        'activities': ['Observe and adapt'],
        'avoid': ['Forcing outcomes']
    })


def calculate_lunar_return(
    natal_moon_lon: float,
    target_date: date
) -> Dict[str, Any]:
    """
    Calculate when Moon returns to natal position (approximately every 27.3 days)
    
    Args:
        natal_moon_lon: Natal Moon longitude
        target_date: Date to search around
        
    Returns:
        Lunar return data
    """
    # Search 5 days before and after target date
    best_match = None
    smallest_diff = 360
    
    for days_offset in range(-5, 6):
        check_date = target_date + timedelta(days=days_offset)
        day_moon = calculate_daily_moon(check_date)
        
        moon_lon = day_moon.get('moon_longitude', 0)
        diff = abs(moon_lon - natal_moon_lon)
        if diff > 180:
            diff = 360 - diff
        
        if diff < smallest_diff:
            smallest_diff = diff
            best_match = {
                'date': check_date.isoformat(),
                'moon_longitude': moon_lon,
                'natal_moon_longitude': natal_moon_lon,
                'difference': round(smallest_diff, 2),
                'exact': smallest_diff < 1.0
            }
    
    return best_match


# Example usage
if __name__ == "__main__":
    # Current moon phase
    current_phase = calculate_current_moon_phase()
    print(f"Current Phase: {current_phase['phase_emoji']} {current_phase['phase_name']}")
    print(f"Illumination: {current_phase['illumination']}%")
    print()
    
    # Moon calendar for current month
    today = date.today()
    calendar = get_moon_calendar(today.year, today.month)
    print(f"Moon Calendar for {today.year}-{today.month:02d}:")
    print(f"New Moons: {len(calendar['new_moons'])}")
    print(f"Full Moons: {len(calendar['full_moons'])}")
    print()
    
    # Next New Moon
    next_new = find_next_new_moon()
    print(f"Next New Moon: {next_new['date']} in {next_new['moon_sign']}")
    
    # Next Full Moon
    next_full = find_next_full_moon()
    print(f"Next Full Moon: {next_full['date']} in {next_full['moon_sign']}")
    print()
    
    # Manifestation guide
    guide = get_moon_manifestation_guide(current_phase['phase_name'])
    print(f"Manifestation Guide for {current_phase['phase_name']}:")
    print(f"Energy: {guide['energy']}")
    print("Activities:", ", ".join(guide['activities']))
