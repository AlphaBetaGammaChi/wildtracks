import math

from wildtracks import geo


def test_haversine_known_distances():
    # London to Paris is about 344 km
    d = geo.haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < d < 360
    # same point is zero
    assert geo.haversine_km(10, 20, 10, 20) == 0
    # antipodes is about half the circumference
    d = geo.haversine_km(0, 0, 0, 180)
    assert math.isclose(d, math.pi * geo.EARTH_RADIUS_KM, rel_tol=1e-3)


def test_compass_directions():
    assert geo.compass(geo.bearing_deg(0, 0, 0, 1)) == "east"
    assert geo.compass(geo.bearing_deg(0, 0, -1, 0)) == "south"
    assert geo.compass(geo.bearing_deg(0, 0, 1, 0)) == "north"


def test_country_lookup():
    c = geo.countries()
    assert c.lookup(55.75, 37.61) == "Russia"      # Moscow
    assert c.lookup(-25.7, 28.2) == "South Africa"  # Pretoria
    assert c.lookup(30.0444, 31.2357) == "Egypt"   # Cairo
    assert c.lookup(20, -30) is None               # mid-Atlantic


def test_sea_lookup_and_offshore():
    seas = geo.seas()
    # a point in the middle of the Mediterranean
    name = seas.lookup(35.5, 18.0)
    assert name and "Mediterranean" in name
    # offshore distance: mid-Mediterranean should be far from land, coastal point near shore
    assert geo.offshore_km(35.5, 18.0) > 100
    assert geo.offshore_km(55.75, 37.61) == 0.0  # Moscow is on land


def test_describe_real_places():
    moscow = geo.describe(55.75, 37.61)
    assert moscow["country"] == "Russia"
    assert moscow["sea"] is None
    sahara = geo.describe(23.5, 12.0)
    assert sahara["desert"] == "Sahara"
