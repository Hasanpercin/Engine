"""
Relationship timing analysis
Identifies favorable and challenging periods for relationships
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from kerykeion import AstrologicalSubject
import swisseph as swe
import logging

logger = logging.getLogger(__name__)


def analyze_relationship_timing(
    natal_chart_data: Dict[str, Any],
    start_date: date,
    end_date: date,
    analysis_type: str = 'comprehensive'
) -> Dict[str, Any]:
    """
    Analyze relationship timing for a period
    
    Focuses on transits to:
    - 5th house (romance, dating)
    - 7th house (partnerships, marriage)
    - Venus (love, attraction)
    - Mars (passion, sexuality)
    - Jupiter (expansion, luck)
    
    Args:
        natal_chart_data: Natal chart data
        start_date: Start of analysis period
        end_date: End of analysis period
        analysis_type: 'comprehensive', 'romance', or 'commitment'
        
    Returns:
        Relationship timing analysis
    """
    try:
        logger.info(
            f"Analyzing relationship timing from {start_date} to {end_date}"
        )
        
        planets = natal_chart_data['planets']
        houses = natal_chart_data['houses']
        
        # Key relationship points in natal chart
        venus = planets.get('venus', {})
        mars = planets.get('mars', {})
        
        seventh_house_cusp = houses.get('7', {}).get('cusp')
        fifth_house_cusp = houses.get('5', {}).get('cusp')
        
        # Scan transits day by day
        favorable_periods = []
        challenging_periods = []
        neutral_periods = []
        
        current_date = start_date
        
        while current_date <= end_date:
            day_analysis = analyze_single_day_relationship(
                current_date,
                venus,
                mars,
                seventh_house_cusp,
                fifth_house_cusp,
                analysis_type
            )
            
            if day_analysis['score'] >= 7:
                favorable_periods.append(day_analysis)
            elif day_analysis['score'] <= 3:
                challenging_periods.append(day_analysis)
            else:
                neutral_periods.append(day_analysis)
            
            current_date += timedelta(days=1)
        
        # Group consecutive days into periods
        favorable_ranges = group_consecutive_days(favorable_periods)
        challenging_ranges = group_consecutive_days(challenging_periods)
        
        # Find peak favorable times
        peak_times = identify_peak_relationship_times(favorable_ranges)
        
        # Generate recommendations
        recommendations = generate_relationship_recommendations(
            favorable_ranges,
            challenging_ranges,
            peak_times,
            analysis_type
        )
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'analysis_type': analysis_type,
            'summary': {
                'favorable_days': len(favorable_periods),
                'challenging_days': len(challenging_periods),
                'neutral_days': len(neutral_periods),
                'total_days': (end_date - start_date).days + 1
            },
            'favorable_periods': favorable_ranges[:10],  # Top 10
            'challenging_periods': challenging_ranges[:5],  # Top 5 to avoid
            'peak_times': peak_times,
            'recommendations': recommendations,
            'daily_scores': calculate_daily_average_scores(
                favorable_periods,
                challenging_periods,
                neutral_periods
            )
        }
        
    except Exception as e:
        logger.error(f"Error analyzing relationship timing: {str(e)}")
        raise


def analyze_single_day_relationship(
    target_date: date,
    natal_venus: Dict[str, Any],
    natal_mars: Dict[str, Any],
    seventh_cusp: float,
    fifth_cusp: float,
    analysis_type: str
) -> Dict[str, Any]:
    """
    Analyze a single day for relationship potential
    
    Returns a score from 0-10
    """
    try:
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        
        score = 5  # Start at neutral
        factors = []
        
        # Check Venus transits
        venus_pos, _ = swe.calc_ut(jd, swe.VENUS)
        venus_lon = venus_pos[0]
        
        # Venus to natal Venus
        venus_to_venus = abs((venus_lon - natal_venus['longitude'] + 180) % 360 - 180)
        if venus_to_venus <= 3:  # Conjunction
            score += 2
            factors.append('Venus return - heightened attraction')
        elif abs(venus_to_venus - 120) <= 3:  # Trine
            score += 2
            factors.append('Venus trine - harmony in love')
        elif abs(venus_to_venus - 60) <= 3:  # Sextile
            score += 1
            factors.append('Venus sextile - pleasant connections')
        elif abs(venus_to_venus - 90) <= 3:  # Square
            score -= 1
            factors.append('Venus square - relationship tension')
        elif abs(venus_to_venus - 180) <= 3:  # Opposition
            score -= 1
            factors.append('Venus opposition - relationship challenges')
        
        # Check Jupiter transits (expansion, luck)
        jupiter_pos, _ = swe.calc_ut(jd, swe.JUPITER)
        jupiter_lon = jupiter_pos[0]
        
        # Jupiter to Venus
        jupiter_to_venus = abs((jupiter_lon - natal_venus['longitude'] + 180) % 360 - 180)
        if jupiter_to_venus <= 3:
            score += 2
            factors.append('Jupiter conjunct Venus - lucky in love!')
        elif abs(jupiter_to_venus - 120) <= 3:
            score += 1
            factors.append('Jupiter trine Venus - expansive love energy')
        
        # Jupiter to 7th house cusp
        if seventh_cusp:
            jupiter_to_7th = abs((jupiter_lon - seventh_cusp + 180) % 360 - 180)
            if jupiter_to_7th <= 3:
                score += 2
                factors.append('Jupiter on 7th house - relationship expansion')
        
        # Check Mars transits
        mars_pos, _ = swe.calc_ut(jd, swe.MARS)
        mars_lon = mars_pos[0]
        
        # Mars to Venus (passion)
        mars_to_venus = abs((mars_lon - natal_venus['longitude'] + 180) % 360 - 180)
        if mars_to_venus <= 3:
            score += 1
            factors.append('Mars conjunct Venus - intense attraction')
        elif abs(mars_to_venus - 90) <= 3:
            score -= 1
            factors.append('Mars square Venus - sexual tension')
        
        # Check for retrograde Venus (caution period)
        venus_speed = venus_pos[3]
        if venus_speed < 0:
            score -= 1
            factors.append('Venus retrograde - review, not initiate')
        
        # Check for retrograde Mercury (communication issues)
        mercury_pos, _ = swe.calc_ut(jd, swe.MERCURY)
        mercury_speed = mercury_pos[3]
        if mercury_speed < 0:
            score -= 0.5
            factors.append('Mercury retrograde - communication care needed')
        
        # Check Moon (daily emotional climate)
        moon_pos, _ = swe.calc_ut(jd, swe.MOON)
        moon_lon = moon_pos[0]
        moon_sign = get_sign_from_longitude(moon_lon)
        
        # Moon in relationship-friendly signs
        if moon_sign in ['Libra', 'Taurus', 'Cancer', 'Pisces']:
            score += 0.5
            factors.append(f'Moon in {moon_sign} - emotional harmony')
        
        # Void of Course Moon (avoid important decisions)
        # Simplified: just note if Moon is late in sign
        moon_degree = moon_lon % 30
        if moon_degree > 27:
            score -= 0.5
            factors.append('Moon void of course - wait for next sign')
        
        # Cap score between 0 and 10
        score = max(0, min(10, score))
        
        return {
            'date': target_date.isoformat(),
            'score': round(score, 1),
            'factors': factors,
            'day_of_week': target_date.strftime('%A'),
            'moon_sign': moon_sign
        }
        
    except Exception as e:
        logger.error(f"Error analyzing day {target_date}: {str(e)}")
        return {
            'date': target_date.isoformat(),
            'score': 5,
            'factors': ['Error in calculation'],
            'day_of_week': target_date.strftime('%A'),
            'moon_sign': 'Unknown'
        }


def group_consecutive_days(day_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group consecutive days into periods"""
    if not day_analyses:
        return []
    
    # Sort by date
    sorted_days = sorted(day_analyses, key=lambda x: x['date'])
    
    periods = []
    current_period_start = None
    current_period_end = None
    current_period_factors = []
    current_period_scores = []
    
    for i, day in enumerate(sorted_days):
        day_date = date.fromisoformat(day['date'])
        
        if current_period_start is None:
            # Start new period
            current_period_start = day_date
            current_period_end = day_date
            current_period_factors = day['factors']
            current_period_scores = [day['score']]
        else:
            # Check if consecutive
            if (day_date - current_period_end).days == 1:
                # Extend period
                current_period_end = day_date
                current_period_factors.extend(day['factors'])
                current_period_scores.append(day['score'])
            else:
                # Save current period and start new one
                periods.append({
                    'start_date': current_period_start.isoformat(),
                    'end_date': current_period_end.isoformat(),
                    'duration_days': (current_period_end - current_period_start).days + 1,
                    'average_score': round(sum(current_period_scores) / len(current_period_scores), 1),
                    'key_factors': list(set(current_period_factors))[:5]  # Unique, top 5
                })
                
                current_period_start = day_date
                current_period_end = day_date
                current_period_factors = day['factors']
                current_period_scores = [day['score']]
    
    # Add last period
    if current_period_start:
        periods.append({
            'start_date': current_period_start.isoformat(),
            'end_date': current_period_end.isoformat(),
            'duration_days': (current_period_end - current_period_start).days + 1,
            'average_score': round(sum(current_period_scores) / len(current_period_scores), 1),
            'key_factors': list(set(current_period_factors))[:5]
        })
    
    # Sort by average score (descending)
    periods.sort(key=lambda x: x['average_score'], reverse=True)
    
    return periods


def identify_peak_relationship_times(favorable_periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify the absolute best times for relationships"""
    
    # Peak times are periods with:
    # - High average score (>= 8)
    # - Duration >= 3 days
    
    peak_times = []
    
    for period in favorable_periods:
        if period['average_score'] >= 8 and period['duration_days'] >= 3:
            peak_times.append({
                'start_date': period['start_date'],
                'end_date': period['end_date'],
                'duration_days': period['duration_days'],
                'score': period['average_score'],
                'why_peak': 'Sustained high-energy favorable period',
                'best_for': determine_best_relationship_activity(period['key_factors'])
            })
    
    return peak_times[:5]  # Top 5 peak times


def determine_best_relationship_activity(factors: List[str]) -> List[str]:
    """Determine what activities are best during this period"""
    
    activities = set()
    
    for factor in factors:
        if 'jupiter' in factor.lower() and '7th house' in factor.lower():
            activities.add('Marriage or commitment')
        elif 'venus return' in factor.lower():
            activities.add('First dates')
            activities.add('Rekindling romance')
        elif 'venus trine' in factor.lower():
            activities.add('Relationship talks')
            activities.add('Quality time together')
        elif 'mars conjunct venus' in factor.lower():
            activities.add('Passionate encounters')
            activities.add('Physical intimacy')
        elif 'jupiter' in factor.lower() and 'venus' in factor.lower():
            activities.add('Travel together')
            activities.add('Big romantic gestures')
        elif 'moon' in factor.lower():
            activities.add('Emotional bonding')
    
    if not activities:
        activities = {'General relationship activities', 'Dates', 'Quality time'}
    
    return list(activities)


def generate_relationship_recommendations(
    favorable_periods: List[Dict[str, Any]],
    challenging_periods: List[Dict[str, Any]],
    peak_times: List[Dict[str, Any]],
    analysis_type: str
) -> Dict[str, List[str]]:
    """Generate actionable relationship timing recommendations"""
    
    recommendations = {
        'best_actions': [],
        'avoid_actions': [],
        'general_tips': []
    }
    
    # Best actions
    if peak_times:
        for peak in peak_times[:3]:
            recommendations['best_actions'].append(
                f"{peak['start_date']} to {peak['end_date']}: "
                f"Excellent time for {', '.join(peak['best_for'][:2])}"
            )
    elif favorable_periods:
        for period in favorable_periods[:3]:
            recommendations['best_actions'].append(
                f"{period['start_date']} to {period['end_date']}: "
                f"Good relationship energy (score: {period['average_score']}/10)"
            )
    else:
        recommendations['best_actions'].append(
            "No strongly favorable periods found. Focus on internal work."
        )
    
    # Actions to avoid
    if challenging_periods:
        for period in challenging_periods[:3]:
            recommendations['avoid_actions'].append(
                f"{period['start_date']} to {period['end_date']}: "
                f"Avoid major relationship decisions or conflicts"
            )
    
    # General tips
    if analysis_type == 'romance':
        recommendations['general_tips'].extend([
            "Best first date times are during favorable periods",
            "Avoid starting new relationships during Venus retrograde",
            "Moon in Libra, Taurus, or Pisces favors romance"
        ])
    elif analysis_type == 'commitment':
        recommendations['general_tips'].extend([
            "Jupiter transits to 7th house excellent for commitments",
            "Avoid commitments during Venus or Mercury retrograde",
            "Peak times ideal for proposals or marriage"
        ])
    else:
        recommendations['general_tips'].extend([
            "Use peak times for important relationship milestones",
            "Challenging periods are for reflection, not action",
            "Trust the cosmic timing - patience pays off"
        ])
    
    return recommendations


def calculate_daily_average_scores(
    favorable: List[Dict[str, Any]],
    challenging: List[Dict[str, Any]],
    neutral: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Calculate average scores by day of week"""
    
    day_scores = {
        'Monday': [],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [],
        'Saturday': [],
        'Sunday': []
    }
    
    for day in favorable + challenging + neutral:
        day_of_week = day['day_of_week']
        score = day['score']
        day_scores[day_of_week].append(score)
    
    # Calculate averages
    day_averages = {}
    for day, scores in day_scores.items():
        if scores:
            day_averages[day] = round(sum(scores) / len(scores), 1)
        else:
            day_averages[day] = 5.0
    
    return day_averages


def get_sign_from_longitude(longitude: float) -> str:
    """Convert longitude to zodiac sign"""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30)
    return signs[sign_index % 12]


def find_venus_retrograde_periods(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """
    Find Venus retrograde periods (caution for starting relationships)
    Venus goes retrograde approximately every 18 months for ~6 weeks
    """
    retrograde_periods = []
    current_date = start_date
    in_retrograde = False
    retro_start = None
    
    while current_date <= end_date:
        jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
        venus_pos, _ = swe.calc_ut(jd, swe.VENUS)
        venus_speed = venus_pos[3]
        
        is_retro = venus_speed < 0
        
        if is_retro and not in_retrograde:
            retro_start = current_date
            in_retrograde = True
        elif not is_retro and in_retrograde:
            retrograde_periods.append({
                'start': retro_start.isoformat(),
                'end': current_date.isoformat(),
                'advice': 'Venus retrograde: Review existing relationships, avoid starting new ones'
            })
            in_retrograde = False
            retro_start = None
        
        current_date += timedelta(days=1)
    
    # Handle ongoing retrograde
    if in_retrograde and retro_start:
        retrograde_periods.append({
            'start': retro_start.isoformat(),
            'end': end_date.isoformat(),
            'advice': 'Venus retrograde: Review existing relationships, avoid starting new ones',
            'ongoing': True
        })
    
    return retrograde_periods


# Example usage
if __name__ == "__main__":
    # Example: need natal chart data first
    example_natal = {
        'planets': {
            'venus': {'longitude': 85.5, 'sign': 'Gemini', 'house': 5},
            'mars': {'longitude': 130.2, 'sign': 'Leo', 'house': 7}
        },
        'houses': {
            '5': {'cusp': 75.0, 'sign': 'Gemini'},
            '7': {'cusp': 125.0, 'sign': 'Leo'}
        }
    }
    
    # Analyze next 3 months
    start = date.today()
    end = start + timedelta(days=90)
    
    timing = analyze_relationship_timing(
        example_natal,
        start,
        end,
        analysis_type='romance'
    )
    
    print("Relationship Timing Analysis:")
    print(f"Favorable days: {timing['summary']['favorable_days']}")
    print(f"Challenging days: {timing['summary']['challenging_days']}")
    
    if timing['peak_times']:
        print("\nPeak Times:")
        for peak in timing['peak_times'][:3]:
            print(f"  {peak['start_date']} to {peak['end_date']}")
            print(f"  Score: {peak['score']}/10")
            print(f"  Best for: {', '.join(peak['best_for'])}")
