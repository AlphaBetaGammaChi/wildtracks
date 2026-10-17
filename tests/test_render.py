import json

import pytest

from wildtracks.render import build_props, read_markers
from wildtracks.track import track_dir

TRACK = "white-stork-8-populations--der-ar445"


def test_build_props_shape():
    props = build_props(track_dir(TRACK), "short", "vector")
    for k in ("style", "title", "points", "scenes", "credits", "audio", "markers", "maptilerKey"):
        assert k in props
    assert props["style"] == "vector"
    assert len(props["points"]) > 1000
    assert all({"t", "lat", "lon", "km", "place"} <= set(p) for p in props["points"][:50])
    assert props["credits"]["license"].startswith("CC")


def test_points_have_no_nan():
    pts = json.loads((track_dir(TRACK) / "points.json").read_text())
    for p in pts[:200] + pts[-200:]:
        assert p["place"] is not None and p["place"] == p["place"]
        assert -90 <= p["lat"] <= 90 and -180 <= p["lon"] <= 180


def test_markers_mismatch_rejected(tmp_path):
    tr = track_dir(TRACK)
    for name in ("facts.json", "scenes_short.json", "points.json"):
        (tmp_path / name).write_text((tr / name).read_text())
    spoken = len([s for s in json.loads((tmp_path / "scenes_short.json").read_text())["scenes"] if s["text"]])
    (tmp_path / "markers_short.txt").write_text("\n".join(str(i * 5) for i in range(spoken + 2)))
    with pytest.raises(ValueError):
        build_props(tmp_path, "short", "vector")


def test_satellite_needs_key(monkeypatch):
    monkeypatch.delenv("MAPTILER_KEY", raising=False)
    props = build_props(track_dir(TRACK), "short", "satellite")
    assert props["maptilerKey"] is None
    monkeypatch.setenv("MAPTILER_KEY", "test-key")
    props = build_props(track_dir(TRACK), "short", "satellite")
    assert props["maptilerKey"] == "test-key"
