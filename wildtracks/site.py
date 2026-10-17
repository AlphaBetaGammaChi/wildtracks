"""Build a static website of rendered tracks for GitHub Pages.

`wildtracks site` writes site/index.html + site/videos/... and can be pushed
as the repo's GitHub Pages site. Files over ~95 MB are skipped (GitHub's hard
limit is 100 MB per file).
"""

import json
import shutil
from pathlib import Path

from .cli import _load_status
from .paths import ROOT, TRACKS_DIR

SITE_DIR = ROOT / "docs"  # GitHub Pages can serve from /docs on the default branch
MAX_FILE_BYTES = 95 * 1024 * 1024

PAGE = """<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>WildTracks — real animal GPS journeys</title>
<style>
body{font-family:-apple-system,Avenir Next,sans-serif;background:#0b1420;color:#eee;max-width:1100px;margin:0 auto;padding:2rem 1rem}
h1{font-size:1.8rem}.sub{color:#8aa0b8;margin-bottom:2rem}
.track{background:#12202f;border:1px solid #22344a;border-radius:12px;padding:1.2rem;margin:1rem 0}
h2{margin:0 0 .3rem;font-size:1.2rem}.facts{color:#9db4ca;font-size:.9rem;margin:.3rem 0 .8rem}
.videos{display:flex;flex-wrap:wrap;gap:1rem}
video{max-width:100%;border-radius:8px;background:#000}
video.short{max-width:260px}video.long{max-width:560px}
.vlabel{font-size:.8rem;color:#8aa0b8;margin-top:.3rem}
.credit{font-size:.78rem;color:#7c93ab;margin-top:.8rem}
.state{font-size:.75rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:.15rem .5rem;border-radius:5px;background:#22364d;color:#7cc7ff;margin-left:.5rem}
footer{color:#64748b;font-size:.8rem;margin-top:2rem;border-top:1px solid #22344a;padding-top:1rem}
</style></head><body>
<h1>WildTracks</h1>
<p class=sub>Every line on these maps is a real GPS fix from a wild, tracked animal.</p>
__TRACKS__
<footer>Built by WildTracks. Each video credits its dataset and licence in the end card.</footer>
</body></html>"""


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def track_card(d: Path, site: Path, status: dict) -> str:
    facts = json.loads((d / "facts.json").read_text()) if (d / "facts.json").exists() else {}
    j = facts.get("journey", {})
    name = facts.get("name") or facts.get("animal", d.name)
    common = facts.get("species", {}).get("common", "")
    state = status.get(d.name, {}).get("state", "new")
    stats = []
    if j.get("days"):
        stats.append(f"{round(j['days'])} days")
    if j.get("km"):
        stats.append(f"at least {j['km']:,} km")
    if j.get("countries"):
        stats.append(f"{len(j['countries'])} countries")
    vids, skipped = "", []
    out = d / "out"
    vdir = site / "videos" / d.name
    if out.exists():
        for v in sorted(out.glob("*.mp4")):
            if v.stat().st_size > MAX_FILE_BYTES:
                skipped.append(v.name)
                continue
            vdir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(v, vdir / v.name)
            cls = "short" if "short" in v.name else "long"
            vids += (f'<div><video class="{cls}" controls preload="metadata" '
                     f'src="videos/{d.name}/{v.name}"></video>'
                     f'<div class=vlabel>{v.stem}</div></div>')
    if not vids:
        vids = '<p class=facts>No published-size videos yet.</p>'
    if skipped:
        vids += f'<p class=facts>Skipped over GitHub&#39;s 100 MB file limit: {", ".join(skipped)}</p>'
    credit = _esc(facts.get("study", {}).get("data_citation", ""))
    return f"""<div class=track>
<h2>{_esc(name)} the {_esc(common)}<span class=state>{state}</span></h2>
<p class=facts>{_esc(' · '.join(stats))}</p>
<div class=videos>{vids}</div>
<p class=credit>{credit}</p>
</div>"""


def build_site(out: Path = SITE_DIR) -> Path:
    out.mkdir(exist_ok=True)
    status = _load_status()
    cards = ""
    if TRACKS_DIR.exists():
        for d in sorted(TRACKS_DIR.iterdir()):
            if d.is_dir():
                cards += track_card(d, out, status)
    (out / "index.html").write_text(PAGE.replace("__TRACKS__", cards or "<p>No tracks yet.</p>"))
    return out
