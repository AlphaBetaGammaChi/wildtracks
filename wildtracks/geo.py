"""Place lookups (country, sea, desert, mountain range, nearby town) using Natural Earth (public domain)."""

import json
import math
from functools import lru_cache
from typing import Optional

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from .paths import NATURAL_EARTH_DIR

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass(deg: float) -> str:
    return ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][round(deg / 45) % 8]


class _Layer:
    def __init__(self, filename: str, name_fn, filter_fn=lambda p: True):
        data = json.loads((NATURAL_EARTH_DIR / filename).read_text())
        self.geoms, self.names = [], []
        for f in data["features"]:
            if f["geometry"] and filter_fn(f["properties"]):
                self.geoms.append(shape(f["geometry"]))
                self.names.append(name_fn(f["properties"]))
        self.tree = STRtree(self.geoms)

    def lookup(self, lat: float, lon: float) -> Optional[str]:
        pt = Point(lon, lat)
        hits = [i for i in self.tree.query(pt) if self.geoms[i].covers(pt)]
        if not hits:
            return None
        return self.names[min(hits, key=lambda i: self.geoms[i].area)]


def _title(s: str) -> str:
    return " ".join(w if w.isupper() and len(w) <= 3 else w.capitalize() for w in s.split()) if s.isupper() else s


@lru_cache(maxsize=None)
def countries() -> _Layer:
    return _Layer("ne_50m_admin_0_countries.geojson", lambda p: p["NAME"])


@lru_cache(maxsize=None)
def seas() -> _Layer:
    return _Layer("ne_10m_geography_marine_polys.geojson", lambda p: p.get("name_en") or p["name"])


@lru_cache(maxsize=None)
def regions() -> _Layer:
    return _Layer(
        "ne_50m_geography_regions_polys.geojson",
        lambda p: (p["FEATURECLA"], _title(p["NAME"])),
        lambda p: p["FEATURECLA"] in ("Desert", "Range/mtn"),
    )


@lru_cache(maxsize=None)
def _land():
    from shapely.ops import unary_union
    from shapely.prepared import prep

    data = json.loads((NATURAL_EARTH_DIR / "ne_50m_land.geojson").read_text())
    land = unary_union([shape(f["geometry"]) for f in data["features"]])
    return land, prep(land)


def offshore_km(lat: float, lon: float) -> float:
    """Approximate distance to the nearest coast (0 on land)."""
    land, prepared = _land()
    pt = Point(lon, lat)
    if prepared.covers(pt):
        return 0.0
    return land.exterior.distance(pt) * 111.0 if hasattr(land, "exterior") else land.boundary.distance(pt) * 111.0


@lru_cache(maxsize=None)
def _towns():
    data = json.loads((NATURAL_EARTH_DIR / "ne_10m_populated_places_simple.geojson").read_text())
    rows = [(p["latitude"], p["longitude"], p["name"], p["pop_max"] or 0) for p in (f["properties"] for f in data["features"])]
    return rows


def nearest_town(lat: float, lon: float, max_km: float = 60.0, min_pop: int = 20000) -> Optional[tuple]:
    best = None
    for tlat, tlon, name, pop in _towns():
        if pop < min_pop or abs(tlat - lat) > 1.5 or abs(tlon - lon) > 2.5:
            continue
        d = haversine_km(lat, lon, tlat, tlon)
        if d <= max_km and (best is None or d < best[1]):
            best = (name, d)
    return best


def describe(lat: float, lon: float) -> dict:
    """Everything we can honestly say about a single position."""
    country = countries().lookup(lat, lon)
    sea = None if country else seas().lookup(lat, lon)
    region = regions().lookup(lat, lon)
    town = nearest_town(lat, lon) if country else None
    return {
        "country": country,
        "sea": sea,
        "desert": region[1] if region and region[0] == "Desert" else None,
        "range": region[1] if region and region[0] == "Range/mtn" else None,
        "town": town[0] if town else None,
        "town_km": round(town[1]) if town else None,
    }


def place_label(d: dict) -> str:
    if d["country"]:
        return f"near {d['town']}, {d['country']}" if d["town"] else d["country"]
    return f"over the {d['sea']}" if d["sea"] else "over open water"
