import json
import re

import pandas as pd
import pytest

from wildtracks import script as S
from wildtracks.study import load_thinned

SLUG = "white-stork-8-populations"


@pytest.fixture(scope="module")
def prepared():
    from wildtracks import facts as F

    df = load_thinned(SLUG)
    g = df[df.animal == "DER AR445"]
    return F.prepare(g)


@pytest.fixture(scope="module")
def scenes_short(prepared, stork_facts):
    return S.build_scenes(stork_facts, prepared, "short")


@pytest.fixture(scope="module")
def scenes_long(prepared, stork_facts):
    return S.build_scenes(stork_facts, prepared, "long")


def test_short_fits_in_a_minute(scenes_short):
    total = sum(s["seconds"] for s in scenes_short["scenes"])
    assert total <= S.SHORT_MAX_SECONDS + 0.5


def test_scenes_cover_journey_in_order(scenes_short):
    kinds = [s["kind"] for s in scenes_short["scenes"]]
    assert kinds[0] == "hook"
    assert kinds[-1] == "credits"
    assert "leg" in kinds
    # scene track times must be non-decreasing through the journey
    t0s = [s["t0"] for s in scenes_short["scenes"] if s["kind"] in ("intro", "leg", "arrival")]
    assert t0s == sorted(t0s)


def test_every_scene_has_required_fields(scenes_short):
    for s in scenes_short["scenes"]:
        for k in ("id", "kind", "text", "t0", "t1", "camera", "seconds"):
            assert k in s, f"{s['id']} missing {k}"
        assert s["seconds"] > 0


def test_narration_numbers_come_from_facts(scenes_short, stork_facts):
    from wildtracks.track import track_dir

    txt = S.narration_text(scenes_short)
    pts = json.loads((track_dir("white-stork-8-populations--der-ar445") / "points.json").read_text())

    def km_at(iso):
        t = pd.Timestamp(iso).timestamp() * 1000
        after = [p["km"] for p in pts if p["t"] >= t]
        before = [p["km"] for p in pts if p["t"] <= t]
        return (after[0] if not before else before[-1]) if after else before[-1]

    # valid distance claims: any span between scene boundaries, plus journey/whole totals
    bounds = sorted({s["t0"] for s in scenes_short["scenes"]} | {s["t1"] for s in scenes_short["scenes"]})
    valid = {round(stork_facts["journey"]["km"] / 100) * 100, round(stork_facts["whole"]["km"] / 100) * 100}
    for i in range(len(bounds)):
        for j in range(i + 1, len(bounds)):
            valid.add(round((km_at(bounds[j]) - km_at(bounds[i])) / 100) * 100)
    for m in re.finditer(r"at least ([\d,]+) kilometres", txt):
        n = int(m.group(1).replace(",", ""))
        assert any(abs(n - f) <= 150 for f in valid), f"{n} km not grounded in track data"


def test_long_has_more_detail(scenes_long, scenes_short):
    assert len(scenes_long["scenes"]) > len(scenes_short["scenes"])
    assert sum(s["seconds"] for s in scenes_long["scenes"]) > 60


def test_narration_does_not_overclaim(scenes_short):
    txt = S.narration_text(scenes_short).lower()
    # this stork hugged coasts; no sea crossing claims allowed
    assert "across the mediterranean" not in txt
    assert "across the sea" not in txt
    # never claim the year-long tag life is the first migration
    assert "full year" not in txt
