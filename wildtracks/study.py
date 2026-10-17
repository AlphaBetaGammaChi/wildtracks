"""Load a downloaded Movebank study into per-animal tracks."""

import json
import re
from pathlib import Path

import pandas as pd

from .paths import STUDIES_DIR

GPS_COLS = {
    "timestamp": "timestamp",
    "location-lat": "lat",
    "location-long": "lon",
    "individual-local-identifier": "animal",
    "individual-taxon-canonical-name": "taxon",
}


def study_dir(slug: str) -> Path:
    return STUDIES_DIR / slug


def load_meta(slug: str) -> dict:
    return json.loads((study_dir(slug) / "study.json").read_text())


def load_thinned(slug: str) -> pd.DataFrame:
    """One fix per animal per hour (cached), which is plenty for maps and distances."""
    d = study_dir(slug)
    cache = d / "thinned_hourly.csv.gz"
    if cache.exists():
        df = pd.read_csv(cache)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="ISO8601")
        return df
    chunks = []
    reader = pd.read_csv(
        d / "gps.csv",
        usecols=lambda c: c in GPS_COLS or c == "visible",
        chunksize=500_000,
        low_memory=False,
    )
    for chunk in reader:
        if "visible" in chunk:
            chunk = chunk[chunk["visible"].astype(str).str.lower() != "false"]
        chunk = chunk.rename(columns=GPS_COLS).dropna(subset=["lat", "lon", "timestamp"])
        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], utc=True, errors="coerce")
        chunk = chunk.dropna(subset=["timestamp"])
        chunk["hour"] = chunk["timestamp"].dt.floor("h")
        chunks.append(chunk.drop_duplicates(["animal", "hour"]))
    df = pd.concat(chunks).drop_duplicates(["animal", "hour"]).drop(columns="hour")
    df = df[(df.lat.abs() <= 90) & (df.lon.abs() <= 180) & ~((df.lat == 0) & (df.lon == 0))]
    df = df.sort_values(["animal", "timestamp"]).reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def load_reference(slug: str) -> pd.DataFrame:
    p = study_dir(slug) / "reference.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def reference_for(ref: pd.DataFrame, animal: str) -> dict:
    if ref.empty or "animal-id" not in ref:
        return {}
    rows = ref[ref["animal-id"].astype(str) == str(animal)]
    if rows.empty:
        return {}
    row = rows.iloc[0]
    return {k: (None if pd.isna(v) else v) for k, v in row.items()}


COLUMN_CANDIDATES = {
    "timestamp": ["timestamp", "time", "datetime", "date", "recorded_at", "location-timestamp", "timestamp_utc"],
    "lat": ["location-lat", "lat", "latitude", "y"],
    "lon": ["location-long", "lon", "lng", "long", "longitude", "x"],
    "animal": ["individual-local-identifier", "animal", "animal-id", "individual", "tag", "tag-id", "track_id", "id", "name"],
    "taxon": ["individual-taxon-canonical-name", "taxon", "species", "species-name"],
}


def import_csv(path: Path, slug: str, license_name: str, credit: str, title: str = "") -> Path:
    """Import any CSV of fixes (columns: time, lat, lon, individual id[, species]) as a study.

    Works for non-Movebank sources — your own tags, GBIF exports, etc. Columns are
    matched case-insensitively against common names.
    """
    src = Path(path)
    df = pd.read_csv(src)
    lower = {c.lower().strip(): c for c in df.columns}
    mapping = {}
    for want, candidates in COLUMN_CANDIDATES.items():
        for c in candidates:
            if c in lower:
                mapping[lower[c]] = want
                break
        if want not in mapping.values() and want != "taxon":
            raise ValueError(f"can't find a {want} column in {src.name} (tried: {', '.join(candidates)})")
    df = df.rename(columns=mapping)
    keep = ["timestamp", "lat", "lon", "animal"] + (["taxon"] if "taxon" in df.columns else [])
    df = df[keep]
    df = df.dropna(subset=["timestamp", "lat", "lon", "animal"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if "taxon" not in df:
        df["taxon"] = ""
    if df.empty:
        raise ValueError(f"no usable rows in {src.name}")

    out = study_dir(slug)
    out.mkdir(parents=True, exist_ok=True)
    df.rename(columns={v: k for k, v in GPS_COLS.items()}).to_csv(out / "gps.csv", index=False)
    meta = {
        "slug": slug,
        "title": title or slug.replace("-", " "),
        "authors": [],
        "year": "",
        "license": license_name,
        "license_uri": "",
        "data_citation": credit or title or slug,
        "paper_citation": "",
        "repository_url": "",
        "doi": "",
        "source_ref": str(src),
    }
    (out / "study.json").write_text(json.dumps(meta, indent=2))
    # drop stale cache so load_thinned rebuilds
    cache = out / "thinned_hourly.csv.gz"
    if cache.exists():
        cache.unlink()
    return out


def nickname(animal: str) -> str:
    """'Kakau (DER AN864)' -> 'Kakau'; codes are left as-is."""
    m = re.match(r"^\s*([A-Za-zÀ-ÿ'\- ]+?)\s*\(", animal)
    return m.group(1) if m else animal.strip()


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
