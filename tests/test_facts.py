import json
import math

import pandas as pd

from conftest import STUDY_META, make_track
from wildtracks import facts as F
from wildtracks.species import species_info


def test_daily_roosts_last_fix_per_day():
    df = make_track([(0, 10, 10), (0, 10.01, 10), (1, 10.5, 10), (1, 10.6, 10)])
    df = pd.concat([df, df.assign(timestamp=df.timestamp + pd.Timedelta(hours=1))]).sort_values("timestamp")
    roosts = F.daily_roosts(df)
    assert len(roosts) == 2


def test_stays_detected_and_merged():
    # 6 days in one spot (< STAY_RADIUS_KM wiggle), then a long jump, then 6 more days
    pts = [(i, 10 + 0.01 * (i % 3), 10) for i in range(6)]
    pts += [(6 + i, 20 + 0.01 * (i % 3), 20) for i in range(6)]
    df = make_track(pts)
    daily = F.daily_roosts(df)
    stays = F.find_stays(daily)
    assert len(stays) == 2
    assert all(s.days >= F.MIN_STAY_DAYS for s in stays)


def test_best_day_ignores_timestamp_gaps():
    # 5 days local, a 10-day gap (tag offline) then a 1000 km jump, then normal 100 km/day travel
    pts = [(i, 10 + i * 0.005, 10) for i in range(5)]
    pts += [(15, 20, 10)]  # after 10-day gap: big displacement must NOT be "best day"
    pts += [(16 + i, 20 + i * 0.9, 10) for i in range(3)]
    df = make_track(pts)
    facts, _ = F.build_facts(df, "TEST A1", species_info("Ciconia ciconia"), {}, STUDY_META)
    # best day must be one of the real consecutive-day hops (~100 km), not the gap jump (~1100 km)
    assert facts["best_day"]["km"] < 200


def test_facts_json_is_nan_free(stork_facts):
    # NaN would silently break JSON consumers and the Remotion props
    txt = json.dumps(stork_facts, default=str, allow_nan=False)
    assert "NaN" not in txt
    for v in _walk(stork_facts):
        if isinstance(v, float):
            assert not math.isnan(v)


def _walk(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)
    else:
        yield o


def test_ar445_facts(stork_facts):
    f = stork_facts
    assert f["animal"] == "DER AR445"
    assert f["species"]["common"] == "white stork"
    # journey runs Russia -> South Africa in 2013/14
    assert f["journey"]["countries"][0] == "Russia"
    assert f["journey"]["countries"][-1] == "South Africa"
    assert f["journey"]["km"] > 10000
    assert f["journey"]["straight_km"] < f["journey"]["km"]
    # all listed seas should be coastal contacts, not open-water crossings
    assert all(not s["open_water"] for s in f["journey"]["seas"])
    # the long Ethiopia stopover is real
    assert any(s["days"] >= 20 and "Ethiopia" in json.dumps(s["place"]) for s in f["stays"])
