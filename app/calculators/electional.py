"""
Electional astrology - selecting optimal times for important events
Finding auspicious moments for weddings, business launches, surgeries, etc.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import swisseph as swe
from kerykeion import AstrologicalSubject
import logging

logger = logging.getLogger(__name__)


# Event types and their requirements
EVENT_REQUIREMENTS = {
    'wedding': {
        'emphasis': ['7th house', 'Venus', 'Moon', 'Jupiter'],
        'avoid': ['Saturn in 7th', 'Mars afflicting 7th', 'Moon void', 'Venus retrograde'],
        'preferred_signs': {
            'moon': ['Taurus', 'Cancer', 'Libra', 'Pisces'],
            'ascendant': ['Taurus', 'Cancer', 'Libra', 'Pisces']
        },
        'description': 'Marriage ceremony'
    },
    'business_launch': {
        'emphasis': ['10th house', 'Sun', 'Jupiter', 'Mercury'],
        'avoid': ['Saturn in 10th', 'Mercury retrograde', 'Moon void'],
        'preferred_signs': {
            'moon': ['Aries', 'Leo', 'Sagittarius', 'Capricorn'],
            'ascendant': ['Leo', 'Capricorn', 'Aries']
        },
        'description': 'Starting a business or company launch'
    },
    'surgery': {
        'emphasis': ['6th house', '8th house', 'Mars strength'],
        'avoid': ['Mars afflicting body part', 'Moon in affected sign', 'Mercury retrograde'],
        'preferred_signs': {
            'moon': ['Avoid sign ruling affected body part']
        },
        'description': 'Medical surgery'
    },
    'travel': {
        'emphasis': ['9th house', 'Jupiter', 'Mercury'],
        'avoid': ['Mercury retrograde', 'Mars afflicting 9th', 'Moon void'],
        'preferred_signs': {
            'moon': ['Gemini', 'Sagittarius', 'Aquarius'],
            'ascendant': ['Gemini', 'Sagittarius']
        },
        'description': 'Long-distance travel or relocation'
    },
    'contract_signing': {
        'emphasis': ['3rd house', '7th house', 'Mercury'],
        'avoid': ['Mercury retrograde', 'Moon void', 'Saturn afflicting Mercury'],
        'preferred_signs': {
            'moon': ['Gemini', 'Virgo', 'Libra'],
            'ascendant': ['Gemini', 'Libra']
        },
        'description': 'Signing contracts or agreements'
    },
    'real_estate': {
        'emphasis': ['4th house', 'Moon', 'Venus'],
        'avoid': ['Saturn in 4th', 'Moon void', 'Mars afflicting 4th'],
        'preferred_signs': {
            'moon': ['Taurus', 'Cancer', 'Capricorn'],
            'ascendant': ['Taurus', 'Cancer']
        },
        'description': 'Buying or selling property'
    },
    'job_interview': {
        'emphasis': ['10th house', 'Sun', 'Jupiter'],
        'avoid': ['Saturn in 10th', 'Mercury retrograde', 'Sun afflicted'],
        'preferred_signs': {
            'moon': ['Leo', 'Capricorn', 'Aries'],
            'ascendant': ['Leo', 'Capricorn']
        },
        'description': 'Job interview or career opportunity'
    }
}


def find_optimal_times(
    event_type: str,
    start_date: date,
    end_date: date,
    location: Dict[str, Any],
    natal_chart_data: Optional[Dict[str, Any]] = None,
    preferred_time_ranges: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, Any]:
    """
    Find optimal times for an event within a date range
    
    Args:
        event_type: Type of event (wedding, business_launch, surgery, etc.)
        start_date: Start of search period
        end_date: End of search period
        location: Location dict with latitude, longitude, timezone
        natal_chart_data: Optional natal chart for person-specific timing
        preferred_time_ranges: Optional list of (hour_start, hour_end) tuples
            e.g., [(9, 12), (14, 17)] for 9am-12pm and 2pm-5pm
            
    Returns:
        List of optimal times with scores and reasons
    """
    try:
        logger.info(f"Finding optimal times for {event_type} from {start_date} to {end_date}")
        
        # Get event requirements
        requirements = EVENT_REQUIREMENTS.get(event_type)
        if not requirements:
            raise ValueError(f"Unknown event type: {event_type}. Available: {list(EVENT_REQUIREMENTS.keys())}")
        
        # Scan all potential times
        all_candidates = []
        current_date = start_date
        
        while current_date <= end_date:
            # Check each hour of the day
            if preferred_time_ranges:
                hours_to_check = []
                for start_hour, end_hour in preferred_time_ranges:
                    hours_to_check.extend(range(start_hour, end_hour))
            else:
                hours_to_check = range(6, 22)  # 6am to 10pm by default
            
            for hour in hours_to_check:
                candidate_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour)
                
                # Score this candidate
                score_result = score_election_chart(
                    candidate_time,
                    location,
                    requirements,
                    natal_chart_data
                )
                
                if score_result['score'] >= 6:  # Only include decent candidates
                    all_candidates.append({
                        'datetime': candidate_time.isoformat(),
                        'score': score_result['score'],
                        'factors': score_result['factors'],
                        'chart_data': score_result['chart_summary']
                    })
            
            current_date += timedelta(days=1)
        
        # Sort by score
        all_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Group into excellent, good, acceptable
        excellent = [c for c in all_candidates if c['score'] >= 9]
        good = [c for c in all_candidates if 7 <= c['score'] < 9]
        acceptable = [c for c in all_candidates if 6 <= c['score'] < 7]
        
        # Generate recommendations
        recommendations = generate_election_recommendations(
            event_type,
            excellent,
            good,
            acceptable,
            requirements
        )
        
        return {
            'event_type': event_type,
            'event_description': requirements['description'],
            'search_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'location': location,
            'total_candidates_found': len(all_candidates),
            'excellent_times': excellent[:10],  # Top 10
            'good_times': good[:20],  # Top 20
            'acceptable_times': acceptable[:30],  # Top 30
            'recommendations': recommendations,
            'requirements': {
                'emphasis': requirements['emphasis'],
                'avoid': requirements['avoid'],
                'preferred_signs': requirements.get('preferred_signs', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error finding optimal times: {str(e)}")
        raise


def score_election_chart(
    election_time: datetime,
    location: Dict[str, Any],
    requirements: Dict[str, Any],
    natal_chart_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Score a potential election chart
    
    Returns score 0-10 and reasons
    """
    try:
        # Create chart for this time
        chart = AstrologicalSubject(
            name=f"Election {election_time.strftime('%Y-%m-%d %H:%M')}",
            year=election_time.year,
            month=election_time.month,
            day=election_time.day,
            hour=election_time.hour,
            minute=election_time.minute,
            city=location.get('city', 'Location'),
            nation=location.get('nation', 'TR'),
            lat=location['latitude'],
            lng=location['longitude'],
            tz_str=location.get('timezone', 'UTC')
        )
        
        # Extract data
        planets = extract_election_planets(chart)
        houses = extract_election_houses(chart)
        
        score = 5  # Start at neutral
        factors = []
        
        # Check Moon void of course (major negative)
        moon_void = check_moon_void_of_course_simple(planets, election_time)
        if moon_void:
            score -= 3
            factors.append('❌ Moon void of course - avoid!')
        else:
            score += 1
            factors.append('✓ Moon not void of course')
        
        # Check retrograde planets
        retrogrades = check_important_retrogrades(planets)
        for planet, is_retro in retrogrades.items():
            if is_retro and planet in requirements.get('emphasis', []):
                score -= 2
                factors.append(f'❌ {planet.title()} retrograde (important for this event)')
            elif not is_retro and planet in requirements.get('emphasis', []):
                score += 0.5
                factors.append(f'✓ {planet.title()} direct')
        
        # Check Moon sign
        moon = planets.get('moon', {})
        moon_sign = moon.get('sign', 'Unknown')
        
        preferred_moon_signs = requirements.get('preferred_signs', {}).get('moon', [])
        if preferred_moon_signs:
            if moon_sign in preferred_moon_signs:
                score += 2
                factors.append(f'✓ Moon in favorable sign: {moon_sign}')
            else:
                score -= 0.5
                factors.append(f'Moon in {moon_sign} (not optimal)')
        
        # Check Ascendant sign
        asc_sign = houses.get('1', {}).get('sign', 'Unknown')
        preferred_asc_signs = requirements.get('preferred_signs', {}).get('ascendant', [])
        
        if preferred_asc_signs:
            if asc_sign in preferred_asc_signs:
                score += 1.5
                factors.append(f'✓ Ascendant in favorable sign: {asc_sign}')
        
        # Check for malefics in angular houses (can be problematic)
        saturn = planets.get('saturn', {})
        mars = planets.get('mars', {})
        
        saturn_house = get_planet_house_simple(saturn, houses)
        mars_house = get_planet_house_simple(mars, houses)
        
        angular_houses = [1, 4, 7, 10]
        
        if saturn_house in angular_houses and '7th house' in requirements.get('avoid', []):
            if saturn_house == 7:
                score -= 2
                factors.append('❌ Saturn in 7th house (avoid for this event)')
        
        if mars_house in angular_houses:
            if mars_house == 7 and 'Mars afflicting 7th' in requirements.get('avoid', []):
                score -= 1.5
                factors.append('❌ Mars in 7th house (challenging)')
        
        # Check benefics in good positions
        jupiter = planets.get('jupiter', {})
        venus = planets.get('venus', {})
        
        jupiter_house = get_planet_house_simple(jupiter, houses)
        venus_house = get_planet_house_simple(venus, houses)
        
        if jupiter_house in angular_houses:
            score += 1
            factors.append(f'✓ Jupiter in {jupiter_house}th house (beneficial)')
        
        if venus_house in angular_houses:
            score += 0.5
            factors.append(f'✓ Venus in {venus_house}th house (pleasant)')
        
        # Cap score between 0-10
        score = max(0, min(10, score))
        
        # Chart summary
        chart_summary = {
            'ascendant': asc_sign,
            'moon_sign': moon_sign,
            'moon_void': moon_void,
            'retrogrades': [k for k, v in retrogrades.items() if v],
            'angular_planets': find_angular_planets_simple(planets, houses)
        }
        
        return {
            'score': round(score, 1),
            'factors': factors,
            'chart_summary': chart_summary
        }
        
    except Exception as e:
        logger.error(f"Error scoring election chart: {str(e)}")
        return {
            'score': 0,
            'factors': [f'Error: {str(e)}'],
            'chart_summary': {}
        }


def check_moon_void_of_course_simple(planets: Dict[str, Any], current_time: datetime) -> bool:
    """
    Simplified void of course Moon check
    
    Moon is void when it makes no more major aspects before changing signs
    This is a simplified version
    """
    
    moon = planets.get('moon', {})
    moon_lon = moon.get('longitude', 0)
    
    # Calculate how far Moon is through its sign
    degree_in_sign = moon_lon % 30
    
    # If Moon is very late in sign (>27°), consider it void
    # (Real calculation would check if it makes aspects before leaving)
    if degree_in_sign > 27:
        return True
    
    return False


def check_important_retrogrades(planets: Dict[str, Any]) -> Dict[str, bool]:
    """Check if important planets are retrograde"""
    
    return {
        'mercury': planets.get('mercury', {}).get('retrograde', False),
        'venus': planets.get('venus', {}).get('retrograde', False),
        'mars': planets.get('mars', {}).get('retrograde', False),
        'jupiter': planets.get('jupiter', {}).get('retrograde', False),
        'saturn': planets.get('saturn', {}).get('retrograde', False)
    }


def get_planet_house_simple(planet: Dict[str, Any], houses: Dict[str, Any]) -> Optional[int]:
    """Get which house a planet is in (simplified)"""
    
    if not planet:
        return None
    
    planet_lon = planet.get('longitude', 0)
    
    # Find which house this falls in
    for house_num in range(1, 13):
        house_data = houses.get(str(house_num), {})
        cusp = house_data.get('cusp', 0)
        
        # Simplified: check if planet is in same 30° segment
        if int(planet_lon / 30) == int(cusp / 30):
            return house_num
    
    return None


def find_angular_planets_simple(planets: Dict[str, Any], houses: Dict[str, Any]) -> List[str]:
    """Find planets in angular houses (1, 4, 7, 10)"""
    
    angular = []
    angular_houses = [1, 4, 7, 10]
    
    for planet_name, planet_data in planets.items():
        house = get_planet_house_simple(planet_data, houses)
        if house in angular_houses:
            angular.append(f"{planet_name.title()} in {house}th")
    
    return angular


def extract_election_planets(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract planet positions from election chart"""
    
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
                'retrograde': planet_obj.get('retrograde', False)
            }
    
    return planets


def extract_election_houses(chart: AstrologicalSubject) -> Dict[str, Any]:
    """Extract house cusps from election chart"""
    
    houses = {}
    
    for i in range(1, 13):
        house_obj = getattr(chart, f'house{i}', None)
        if house_obj:
            houses[str(i)] = {
                'cusp': house_obj['position'],
                'sign': house_obj['sign']
            }
    
    return houses


def generate_election_recommendations(
    event_type: str,
    excellent: List[Dict[str, Any]],
    good: List[Dict[str, Any]],
    acceptable: List[Dict[str, Any]],
    requirements: Dict[str, Any]
) -> List[str]:
    """Generate practical recommendations"""
    
    recommendations = []
    
    if excellent:
        recommendations.append(
            f"✨ EXCELLENT: Found {len(excellent)} optimal times with scores 9+. "
            f"Top choice: {excellent[0]['datetime']}"
        )
    elif good:
        recommendations.append(
            f"✓ GOOD: Found {len(good)} favorable times with scores 7-9. "
            f"Top choice: {good[0]['datetime']}"
        )
    elif acceptable:
        recommendations.append(
            f"⚠ ACCEPTABLE: Found {len(acceptable)} decent times with scores 6-7. "
            f"Consider: {acceptable[0]['datetime']}"
        )
    else:
        recommendations.append(
            "❌ No good times found in this period. Consider expanding date range."
        )
    
    # Event-specific advice
    if event_type == 'wedding':
        recommendations.append(
            "For weddings: Prioritize Venus and Moon placements, "
            "avoid Saturn in 7th house and Venus retrograde"
        )
    elif event_type == 'business_launch':
        recommendations.append(
            "For business: Strong 10th house and Jupiter-Sun aspects "
            "are ideal. Avoid Mercury retrograde."
        )
    elif event_type == 'surgery':
        recommendations.append(
            "For surgery: Avoid Moon in sign ruling affected body part. "
            "Mars should not afflict the relevant area."
        )
    
    # General electional advice
    recommendations.extend([
        "Always avoid Moon void of course for important events",
        "Mercury retrograde problematic for contracts and communication",
        "Waxing Moon (after New Moon) generally better for new beginnings"
    ])
    
    return recommendations


def analyze_specific_election(
    event_datetime: datetime,
    event_type: str,
    location: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a specific date/time for an event
    
    Useful when you have a pre-determined date and want to assess it
    """
    try:
        logger.info(f"Analyzing specific election: {event_datetime} for {event_type}")
        
        requirements = EVENT_REQUIREMENTS.get(event_type)
        if not requirements:
            raise ValueError(f"Unknown event type: {event_type}")
        
        # Score this specific time
        score_result = score_election_chart(
            event_datetime,
            location,
            requirements,
            None
        )
        
        # Determine verdict
        score = score_result['score']
        
        if score >= 9:
            verdict = 'EXCELLENT'
            recommendation = 'This is an optimal time for this event.'
        elif score >= 7:
            verdict = 'GOOD'
            recommendation = 'This is a favorable time for this event.'
        elif score >= 5:
            verdict = 'ACCEPTABLE'
            recommendation = 'This time is acceptable but not ideal. Consider alternatives if possible.'
        else:
            verdict = 'NOT RECOMMENDED'
            recommendation = 'This time has significant challenges. Strongly consider changing the date/time.'
        
        # Suggest improvements
        improvements = suggest_improvements(score_result, requirements)
        
        return {
            'event_type': event_type,
            'event_datetime': event_datetime.isoformat(),
            'location': location,
            'score': score,
            'verdict': verdict,
            'recommendation': recommendation,
            'factors': score_result['factors'],
            'chart_summary': score_result['chart_summary'],
            'suggested_improvements': improvements,
            'requirements': {
                'emphasis': requirements['emphasis'],
                'avoid': requirements['avoid']
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing specific election: {str(e)}")
        raise


def suggest_improvements(score_result: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
    """Suggest how to improve the election time"""
    
    improvements = []
    factors = score_result.get('factors', [])
    chart_summary = score_result.get('chart_summary', {})
    
    # Check for void Moon
    if chart_summary.get('moon_void'):
        improvements.append("Wait until Moon enters the next sign")
    
    # Check for retrogrades
    retrogrades = chart_summary.get('retrogrades', [])
    if 'mercury' in retrogrades:
        improvements.append("Ideally wait until Mercury goes direct")
    if 'venus' in retrogrades and 'Venus' in requirements.get('emphasis', []):
        improvements.append("Wait until Venus goes direct (important for this event)")
    
    # Moon sign suggestions
    moon_sign = chart_summary.get('moon_sign')
    preferred_moon_signs = requirements.get('preferred_signs', {}).get('moon', [])
    
    if preferred_moon_signs and moon_sign not in preferred_moon_signs:
        improvements.append(
            f"Consider times when Moon is in: {', '.join(preferred_moon_signs)}"
        )
    
    if not improvements:
        improvements.append("This timing is already quite favorable!")
    
    return improvements


def get_lunar_phase_recommendation(event_type: str) -> Dict[str, Any]:
    """
    Get lunar phase recommendations for event type
    
    Some events better during waxing Moon, others during waning
    """
    
    waxing_favorable = [
        'wedding', 'business_launch', 'contract_signing', 
        'real_estate', 'job_interview', 'travel'
    ]
    
    waning_favorable = [
        'surgery', 'ending_relationships', 'quitting_habits'
    ]
    
    if event_type in waxing_favorable:
        return {
            'preferred_phase': 'Waxing Moon (New Moon to Full Moon)',
            'reason': 'Growth, expansion, new beginnings',
            'avoid_phase': 'Avoid Balsamic Moon (last 3 days before New Moon)'
        }
    elif event_type in waning_favorable:
        return {
            'preferred_phase': 'Waning Moon (Full Moon to New Moon)',
            'reason': 'Release, letting go, surgery/removal',
            'avoid_phase': 'Avoid Waxing Moon for endings'
        }
    else:
        return {
            'preferred_phase': 'Waxing Moon generally better for most events',
            'reason': 'Building and growth energy',
            'avoid_phase': 'New Moon day itself (can be too potent)'
        }


# Example usage
if __name__ == "__main__":
    location = {
        'city': 'Istanbul',
        'nation': 'TR',
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timezone': 'Europe/Istanbul'
    }
    
    # Find optimal wedding times in next 3 months
    start = date.today()
    end = start + timedelta(days=90)
    
    results = find_optimal_times(
        event_type='wedding',
        start_date=start,
        end_date=end,
        location=location,
        preferred_time_ranges=[(10, 16)]  # 10am to 4pm
    )
    
    print("Electional Astrology Results:")
    print(f"Excellent times found: {len(results['excellent_times'])}")
    if results['excellent_times']:
        print(f"Top recommendation: {results['excellent_times'][0]['datetime']}")
        print(f"Score: {results['excellent_times'][0]['score']}/10")
