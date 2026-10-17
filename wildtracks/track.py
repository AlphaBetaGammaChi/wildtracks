"""Build a track folder: facts, map points, scenes and narration for one animal."""

import json
from pathlib import Path

import pandas as pd

from . import facts as F
from . import script as S
from .paths import TRACKS_DIR
from .species import species_info
from .study import load_meta, load_reference, load_thinned, reference_for, slugify

MAX_RENDER_POINTS = 4000


def track_dir(track_id: str) -> Path:
    return TRACKS_DIR / track_id


def track_id_for(study_slug: str, animal: str) -> str:
    return f"{study_slug}--{slugify(animal)}"


def _render_points(df: pd.DataFrame) -> list:
    step = max(1, len(df) // MAX_RENDER_POINTS)
    sub = pd.concat([df.iloc[::step], df.iloc[[-1]]]).drop_duplicates("timestamp")
    out = []
    for r in sub.itertuples():
        place = r.country if isinstance(r.country, str) else (r.sea if isinstance(r.sea, str) else "Open water")
        out.append({"t": int(r.timestamp.timestamp() * 1000), "lat": round(r.lat, 5), "lon": round(r.lon, 5),
                    "km": round(float(r.cum_km), 1), "place": place})
    return out


def build_track(study_slug: str, animal: str, force_scenes: bool = False) -> Path:
    df = load_thinned(study_slug)
    g = df[df.animal == animal]
    if g.empty:
        raise ValueError(f"No animal {animal!r} in study {study_slug}")
    taxon = g.taxon.dropna().iloc[0] if "taxon" in g and g.taxon.notna().any() else ""
    facts, prepared = F.build_facts(g, animal, species_info(taxon), reference_for(load_reference(study_slug), animal), load_meta(study_slug))

    out = track_dir(track_id_for(study_slug, animal))
    out.mkdir(parents=True, exist_ok=True)
    (out / "facts.json").write_text(json.dumps({"study_slug": study_slug, **facts}, indent=2, default=str))
    (out / "points.json").write_text(json.dumps(_render_points(prepared)))

    for fmt in ("short", "long"):
        scenes_path = out / f"scenes_{fmt}.json"
        if force_scenes or not scenes_path.exists():
            scenes_path.write_text(json.dumps(S.build_scenes(facts, prepared, fmt), indent=2))
        write_narration(out, fmt)
    (out / "description.txt").write_text(_description(facts))
    return out


def _description(facts: dict) -> str:
    j, w, study = facts["journey"], facts["whole"], facts["study"]
    countries = j.get("countries") or []
    route = " → ".join([countries[0], countries[-1]]) if len(countries) >= 2 else ""
    return f"""{facts.get('name', facts['animal'])} the {facts['species']['common']} — a real GPS track

A wild {facts['species']['common']} ({facts['species'].get('taxon', '')}), tracked by GPS from
{j.get('start', '')[:10]} to {j.get('end', '')[:10]}: at least {j.get('km', '?')} km, {route}.
The whole recording spans {w.get('days', '?')} days.

Every position in this video is a real GPS fix. Distances are straight lines between
nightly roosts, so the true distance flown was higher.

Data (please keep this credit):
{study.get('data_citation', '')}
Licence: {study.get('license', '')} · DOI: {study.get('doi', '')}
Map data: Natural Earth (public domain); street style: © OpenMapTiles, © OpenStreetMap contributors.
"""


def write_narration(out: Path, fmt: str):
    scenes = json.loads((out / f"scenes_{fmt}.json").read_text())
    (out / f"narration_{fmt}.txt").write_text(S.narration_text(scenes))
