"""Turn one animal's GPS fixes into a fact sheet. Every number in a script must come from here."""

from dataclasses import dataclass, field
from itertools import groupby
from typing import Optional

import numpy as np
import pandas as pd

from . import geo
from .study import nickname

MIN_STEP_KM = 2.0          # ignore GPS jitter / local foraging when summing distance
STAY_RADIUS_KM = 40.0      # a "stay" is consecutive days within this radius
MIN_STAY_DAYS = 4
TRAVEL_DAY_KM = 50.0       # a day counts as a travel day if roost-to-roost displacement exceeds this
ARRIVAL_STAY_DAYS = 14


@dataclass
class Stay:
    start: pd.Timestamp
    end: pd.Timestamp
    lat: float
    lon: float
    place: dict = field(default_factory=dict)

    @property
    def days(self) -> int:
        return (self.end.normalize() - self.start.normalize()).days + 1


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Adds cumulative distance plus a coarse place for every fix.

    Distance is the sum of straight lines between nightly roosts, interpolated through each day.
    It ignores local foraging flights, so narration can safely say "at least".
    """
    df = df.sort_values("timestamp").reset_index(drop=True).copy()
    lat, lon = df.lat.to_numpy(), df.lon.to_numpy()
    roosts = daily_roosts(df)
    hops = [0.0] + [geo.haversine_km(roosts.lat[i - 1], roosts.lon[i - 1], roosts.lat[i], roosts.lon[i]) for i in range(1, len(roosts))]
    roost_t = roosts.timestamp.astype("int64").to_numpy()
    df["cum_km"] = np.interp(df.timestamp.astype("int64").to_numpy(), roost_t, np.cumsum(hops))
    countries, seas, regions = geo.countries(), geo.seas(), geo.regions()
    c, s, d, r = [], [], [], []
    for la, lo in zip(lat, lon):
        country = countries.lookup(la, lo)
        region = regions.lookup(la, lo)
        c.append(country)
        s.append(None if country else seas.lookup(la, lo))
        d.append(region[1] if region and region[0] == "Desert" else None)
        r.append(region[1] if region and region[0] == "Range/mtn" else None)
    df["country"], df["sea"], df["desert"], df["range"] = c, s, d, r
    return df


def daily_roosts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(day=df.timestamp.dt.floor("D"))
    return df.groupby("day").tail(1).reset_index(drop=True)


def find_stays(daily: pd.DataFrame) -> list:
    stays, i = [], 0
    while i < len(daily):
        a = daily.iloc[i]
        j = i
        while j + 1 < len(daily) and geo.haversine_km(a.lat, a.lon, daily.iloc[j + 1].lat, daily.iloc[j + 1].lon) <= STAY_RADIUS_KM:
            j += 1
        block = daily.iloc[i : j + 1]
        if (block.day.iloc[-1] - block.day.iloc[0]).days + 1 >= MIN_STAY_DAYS:
            stays.append(Stay(block.timestamp.iloc[0], block.timestamp.iloc[-1], float(block.lat.mean()), float(block.lon.mean())))
        i = j + 1
    return merge_stays(stays)


def merge_stays(stays: list, radius_km: float = 80.0, max_gap_days: int = 5) -> list:
    """Back-to-back stays in the same area are one stopover, as far as a viewer is concerned."""
    merged = []
    for s in stays:
        p = merged[-1] if merged else None
        if p and (s.start - p.end).days <= max_gap_days and geo.haversine_km(p.lat, p.lon, s.lat, s.lon) <= radius_km:
            w1, w2 = p.days, s.days
            merged[-1] = Stay(p.start, s.end, (p.lat * w1 + s.lat * w2) / (w1 + w2), (p.lon * w1 + s.lon * w2) / (w1 + w2))
        else:
            merged.append(s)
    return merged


def journey_window(df: pd.DataFrame, daily: pd.DataFrame, stays: list) -> tuple:
    """First real departure until the first long stay far from home."""
    start = df.iloc[0]
    disp = daily.apply(lambda r: geo.haversine_km(start.lat, start.lon, r.lat, r.lon), axis=1)
    max_disp = disp.max()
    moves = daily.index[(disp > 2 * STAY_RADIUS_KM)]
    if max_disp < 200 or len(moves) == 0:
        return df.timestamp.iloc[0], df.timestamp.iloc[-1]
    depart_day = daily.day.iloc[max(moves[0] - 1, 0)]
    arrival = None
    for s in stays:
        if s.start < depart_day or s.days < ARRIVAL_STAY_DAYS:
            continue
        if geo.haversine_km(start.lat, start.lon, s.lat, s.lon) >= 0.6 * max_disp:
            arrival = s
            break
    end = arrival.start if arrival else df.timestamp.iloc[-1]
    begin = df.timestamp[df.timestamp >= depart_day].iloc[0]
    return begin, end


def runs(series: pd.Series, times: pd.Series, min_fixes: int = 1) -> list:
    out = []
    for name, group in groupby(zip(series, times), key=lambda x: x[0]):
        group = list(group)
        if isinstance(name, str) and len(group) >= min_fixes:
            out.append({"name": name, "first": group[0][1], "fixes": len(group)})
    return out


def ordered_unique(items) -> list:
    seen, out = set(), []
    for i in items:
        if isinstance(i, str) and i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


OPEN_WATER_KM = 50.0


def sea_contacts(seg: pd.DataFrame) -> list:
    """Seas touched, and whether the animal was ever well offshore (a real crossing) or just along the coast."""
    out = {}
    for row in seg[seg.sea.notna()].itertuples():
        km = geo.offshore_km(row.lat, row.lon)
        out[row.sea] = max(out.get(row.sea, 0.0), km)
    return [{"name": k, "max_offshore_km": round(v), "open_water": v >= OPEN_WATER_KM} for k, v in out.items()]


def segment_facts(seg: pd.DataFrame) -> dict:
    """Facts for any slice of the track."""
    if seg.empty:
        return {}
    a, b = seg.iloc[0], seg.iloc[-1]
    countries = [r["name"] for r in runs(seg.country, seg.timestamp, min_fixes=3)]
    return {
        "start": a.timestamp.isoformat(),
        "end": b.timestamp.isoformat(),
        "days": round((b.timestamp - a.timestamp).total_seconds() / 86400, 1),
        "km": round(float(seg.cum_km.iloc[-1] - seg.cum_km.iloc[0])),
        "straight_km": round(geo.haversine_km(a.lat, a.lon, b.lat, b.lon)),
        "heading": geo.compass(geo.bearing_deg(a.lat, a.lon, b.lat, b.lon)),
        "countries": ordered_unique(countries),
        "seas": sea_contacts(seg),
        "deserts": ordered_unique(seg.desert),
        "ranges": ordered_unique(seg["range"]),
        "start_place": geo.describe(a.lat, a.lon),
        "end_place": geo.describe(b.lat, b.lon),
    }


def build_facts(df: pd.DataFrame, animal: str, taxon_info: dict, reference: dict, study: dict) -> dict:
    df = prepare(df)
    daily = daily_roosts(df)
    stays = find_stays(daily)
    for s in stays:
        s.place = geo.describe(s.lat, s.lon)
    j0, j1 = journey_window(df, daily, stays)
    journey = df[(df.timestamp >= j0) & (df.timestamp <= j1)]

    hop_km = [
        geo.haversine_km(daily.lat[i - 1], daily.lon[i - 1], daily.lat[i], daily.lon[i])
        if (daily.day[i] - daily.day[i - 1]).days == 1 else 0.0
        for i in range(1, len(daily))
    ]
    best_i = int(np.argmax(hop_km)) + 1 if hop_km else 0
    best_day, best_fix = daily.day[best_i], daily.iloc[best_i]
    best_km = hop_km[best_i - 1] if hop_km else 0.0

    start = df.iloc[0]
    disp = df.apply(lambda r: geo.haversine_km(start.lat, start.lon, r.lat, r.lon), axis=1)
    far = df.loc[disp.idxmax()]

    end_type = (reference.get("deployment-end-type") or "").lower()
    death = (reference.get("animal-death-comments") or "").lower()
    outcome: Optional[str] = "died" if ("dead" in end_type or "dead" in death) else None

    return {
        "animal": animal,
        "name": nickname(animal),
        "has_nickname": nickname(animal) != animal.strip(),
        "species": taxon_info,
        "life_stage": reference.get("animal-life-stage"),
        "sex": reference.get("animal-sex"),
        "tagged_site": reference.get("study-site"),
        "tag_deployed": reference.get("deploy-on-date"),
        "tag_maker": reference.get("tag-manufacturer-name"),
        "outcome": outcome,
        "study": {k: study.get(k) for k in ("title", "authors", "year", "license", "data_citation", "doi", "repository_url")},
        "fixes": int(len(df)),
        "whole": segment_facts(df),
        "journey": segment_facts(journey),
        "journey_window": [j0.isoformat(), j1.isoformat()],
        "best_day": {"date": best_day.isoformat(), "km": round(best_km), "place": geo.describe(best_fix.lat, best_fix.lon)},
        "farthest": {"date": far.timestamp.isoformat(), "km_from_start": round(float(disp.max())), "place": geo.describe(far.lat, far.lon)},
        "stays": [
            {"start": s.start.isoformat(), "end": s.end.isoformat(), "days": s.days, "lat": round(s.lat, 4), "lon": round(s.lon, 4), "place": s.place}
            for s in stays
        ],
        "travel_days": int((daily.assign(prev_lat=daily.lat.shift(), prev_lon=daily.lon.shift()).dropna(subset=["prev_lat"])
                            .apply(lambda r: geo.haversine_km(r.prev_lat, r.prev_lon, r.lat, r.lon), axis=1) > TRAVEL_DAY_KM).sum()),
    }, df
