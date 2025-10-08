import json
import os
import pytest
from datetime import datetime, timezone
import swisseph as swe

from app.calculators.electional import lunar_phase, moon_void_of_course, search_electional_windows

DATA_GOLDEN = os.path.join(os.path.dirname(__file__), "data", "golden_charts.json")
ELECTIONAL = os.path.join(os.path.dirname(__file__), "data", "electional_scenarios.json")

@pytest.mark.skipif(not os.path.exists(DATA_GOLDEN), reason="golden test data missing")
def test_lunar_phase_against_known():
    cases = json.load(open(DATA_GOLDEN))
    for c in cases.get("lunar_phase", []):
        dt = datetime.fromisoformat(c["datetime"]).astimezone(timezone.utc)
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        phase = lunar_phase(jd)
        assert c["phase"] in phase["phase"]

@pytest.mark.skipif(not os.path.exists(ELECTIONAL), reason="electional scenarios missing")
def test_electional_search_smoke():
    cfg = json.load(open(ELECTIONAL))
    scenario = cfg["scenarios"][0]
    start = datetime.fromisoformat(scenario["start"]).astimezone(timezone.utc)
    end = datetime.fromisoformat(scenario["end"]).astimezone(timezone.utc)
    jd_start = swe.julday(start.year, start.month, start.day, start.hour + start.minute/60.0)
    jd_end = swe.julday(end.year, end.month, end.day, end.hour + end.minute/60.0)
    res = search_electional_windows(jd_start, jd_end, scenario["lat"], scenario["lon"],
                                    step_minutes=scenario.get("step_minutes", 15))
    assert len(res) > 0
