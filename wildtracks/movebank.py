"""Download open-licence studies from the Movebank Data Repository."""

import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

from .paths import STUDIES_DIR

API = "https://datarepository.movebank.org/server/api"
ALLOWED_LICENSES = {
    "http://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
    "http://creativecommons.org/licenses/by/4.0/": "CC BY 4.0",
    "https://creativecommons.org/licenses/by/4.0/": "CC BY 4.0",
}


class LicenseError(Exception):
    pass


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "WildTracks/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def _resolve_item_url(ref: str) -> str:
    """Accepts a DOI, a doi.org URL, a handle (10255/move.417) or a repository URL."""
    ref = ref.strip()
    handle = None
    m = re.search(r"10\.5441/\S+", ref)
    if m:
        req = urllib.request.Request(f"https://doi.org/{m.group(0)}", method="HEAD", headers={"User-Agent": "WildTracks/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            ref = r.geturl()
    m = re.search(r"10255/move\.\d+", ref)
    if m:
        handle = m.group(0)
    if not handle:
        raise ValueError(f"Could not find a Movebank DOI or handle in {ref!r}")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(f"{API}/pid/find?id={handle}", timeout=60)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303) and e.headers.get("Location"):
            return e.headers["Location"]
        raise
    raise ValueError(f"Movebank did not resolve handle {handle}")


def _download(url: str, dest: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "WildTracks/0.1"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def fetch_study(ref: str, slug: str, skip_existing: bool = True) -> Path:
    item = _get_json(_resolve_item_url(ref) + "?embed=bundles/bitstreams")
    md = item["metadata"]
    first = lambda k: (md.get(k) or [{"value": ""}])[0]["value"]
    license_uri = first("dc.rights.uri")
    if license_uri not in ALLOWED_LICENSES:
        raise LicenseError(
            f"Study licence is {first('dc.rights') or license_uri!r}; only CC0 and CC BY allow monetised use."
        )

    out = STUDIES_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for bundle in item["_embedded"]["bundles"]["_embedded"]["bundles"]:
        if bundle["name"] != "ORIGINAL":
            continue
        for bs in bundle["_embedded"]["bitstreams"]["_embedded"]["bitstreams"]:
            name = bs["name"]
            href = bs["_links"]["content"]["href"]
            if name.endswith("-gps.csv.zip") or name.endswith("-gps.csv"):
                files["gps"] = (name, href)
            elif name.endswith("-reference-data.csv"):
                files["reference"] = (name, href)
            elif name.lower().startswith("readme"):
                files["readme"] = (name, href)
    if "gps" not in files:
        raise ValueError("Study has no GPS csv file")

    for kind, (name, href) in files.items():
        if skip_existing and kind == "gps" and (out / "gps.csv").exists():
            continue
        print(f"  downloading {name}")
        target = out / ("gps.csv.zip" if name.endswith(".zip") else f"{kind}.{name.rsplit('.', 1)[-1]}")
        _download(href, target)
        if target.suffix == ".zip":
            with zipfile.ZipFile(target) as z:
                member = next(n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX"))
                with z.open(member) as src, open(out / "gps.csv", "wb") as dst:
                    shutil.copyfileobj(src, dst)
            target.unlink()

    doi_match = re.search(r"10\.5441/[\w./]+", ref) or re.search(r"10\.5441/[\w./]+", json.dumps(md.get("dc.identifier.uri", [])) + json.dumps(md))
    doi = doi_match.group(0).rstrip(".") if doi_match else ""
    authors = [v["value"] for v in md.get("dc.contributor.author", [])]
    year = first("dc.date.issued")[:4]
    meta = {
        "slug": slug,
        "title": first("dc.title"),
        "authors": authors,
        "year": year,
        "license": ALLOWED_LICENSES[license_uri],
        "license_uri": license_uri,
        "data_citation": f"{'; '.join(authors)} ({year}). {first('dc.title')}. Movebank Data Repository. https://doi.org/{doi}",
        "paper_citation": first("dc.identifier.citation"),
        "repository_url": first("dc.identifier.uri"),
        "doi": doi,
        "source_ref": ref,
    }
    (out / "study.json").write_text(json.dumps(meta, indent=2))
    return out
