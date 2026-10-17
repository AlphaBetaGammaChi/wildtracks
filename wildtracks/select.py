"""Rank animals in a study by how good a video their track would make."""

import pandas as pd

from . import geo
from .study import nickname


def score_animals(df: pd.DataFrame, min_fixes: int = 50) -> pd.DataFrame:
    rows = []
    for animal, g in df.groupby("animal"):
        if len(g) < min_fixes:
            continue
        a = g.iloc[0]
        disp = [geo.haversine_km(a.lat, a.lon, la, lo) for la, lo in zip(g.lat, g.lon)]
        days = g.timestamp.dt.floor("D")
        span = (days.iloc[-1] - days.iloc[0]).days + 1
        coverage = days.nunique() / max(span, 1)
        daily = g.groupby(days).tail(1)
        hops = [geo.haversine_km(*p, *q) for p, q in zip(zip(daily.lat, daily.lon), zip(daily.lat[1:], daily.lon[1:]))]
        biggest_gap = days.drop_duplicates().diff().max()
        rows.append({
            "animal": animal,
            "name": nickname(animal),
            "named": nickname(animal) != animal.strip(),
            "max_km_from_start": round(max(disp)),
            "lat_span": round(g.lat.max() - g.lat.min(), 1),
            "days": span,
            "coverage": round(coverage, 2),
            "biggest_gap_days": biggest_gap.days if pd.notna(biggest_gap) else 0,
            "daily_km_sum": round(sum(hops)),
        })
    s = pd.DataFrame(rows)
    if s.empty:
        return s
    s["score"] = (
        s.max_km_from_start.clip(upper=12000) / 1000 * 3
        + s.coverage * 4
        - (s.biggest_gap_days.clip(lower=3) - 3) * 0.3
        + s.named * 2
        + (s.days.clip(upper=200) / 100)
    ).round(2)
    return s.sort_values("score", ascending=False).reset_index(drop=True)
