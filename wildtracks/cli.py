"""wildtracks command line: fetch, pick, track, script, narration, render, status, approve."""

import argparse
import json
import sys
from pathlib import Path

from .paths import STATUS_FILE, TRACKS_DIR

REVIEW_STATES = ("new", "rendered", "reviewed", "approved", "published")


def _load_status() -> dict:
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text())
    return {}


def _save_status(status: dict):
    STATUS_FILE.write_text(json.dumps(status, indent=2))


def _set_state(track_id: str, state: str, **extra):
    status = _load_status()
    entry = status.setdefault(track_id, {})
    entry["state"] = state
    entry.update(extra)
    _save_status(status)


def cmd_fetch(args):
    from .movebank import fetch_study

    slug = args.slug or None
    if slug is None:
        print("error: pass --slug <name> for the folder name (e.g. --slug white-stork-8-populations)")
        return 2
    out = fetch_study(args.ref, slug, skip_existing=not args.force)
    print(f"study saved to {out}")
    return 0


def cmd_pick(args):
    from .select import score_animals
    from .study import load_thinned

    df = load_thinned(args.slug)
    s = score_animals(df, min_fixes=args.min_fixes)
    if s.empty:
        print("no animals with enough fixes")
        return 1
    print(s.head(args.top).to_string(index=False))
    print("\nBuild one with: wildtracks track", args.slug, "<animal>")
    return 0


def cmd_track(args):
    from .track import build_track, track_id_for

    out = build_track(args.slug, args.animal, force_scenes=args.force_scenes)
    tid = track_id_for(args.slug, args.animal)
    _set_state(tid, "new", slug=args.slug, animal=args.animal)
    print(f"track package: {out}")
    return 0


def cmd_script(args):
    from .track import build_track, track_dir

    out = track_dir(args.track_id)
    facts_path = out / "facts.json"
    if not facts_path.exists():
        print(f"no such track: {args.track_id}")
        return 1
    facts = json.loads(facts_path.read_text())
    build_track(facts["study_slug"], facts["animal"], force_scenes=True)
    print(f"rebuilt scenes + narration in {out}")
    return 0


def cmd_narration(args):
    from . import script as S
    from .track import track_dir, write_narration

    out = track_dir(args.track_id)
    fmts = [args.format] if args.format else ["short", "long"]
    for fmt in fmts:
        if not (out / f"scenes_{fmt}.json").exists():
            print(f"no scenes_{fmt}.json in {out}")
            continue
        write_narration(out, fmt)
        print(f"wrote {out / f'narration_{fmt}.txt'}")
    return 0


def cmd_render(args):
    from .render import STYLES, render
    from .track import track_dir

    out = track_dir(args.track_id)
    if not out.exists():
        print(f"no such track: {args.track_id}")
        return 1
    fmts = [args.format] if args.format else ["short"]
    styles = list(STYLES) if args.style == "all" else [args.style]
    made = False
    for fmt in fmts:
        for style in styles:
            try:
                path = render(out, fmt, style, frame=args.frame)
            except Exception as e:
                print(f"{fmt}/{style}: FAILED - {e}")
                continue
            print(f"{fmt}/{style}: {path}")
            made = made or args.frame is None
    if made and _load_status().get(args.track_id, {}).get("state", "new") == "new":
        _set_state(args.track_id, "rendered")
    return 0


def _run_batch(slug: str, count: int, fmt: str, style: str, animals=None, dry_run: bool = False, min_fixes: int = 50) -> int:
    from .render import render
    from .select import score_animals
    from .study import load_thinned
    from .track import build_track, track_id_for

    df = load_thinned(slug)
    if animals:
        found = df[df.animal.isin(animals)].animal.unique().tolist()
        missing = set(animals) - set(found)
        if missing:
            print(f"not found in study: {', '.join(sorted(missing))}")
        chosen = [(a, None) for a in found]
    else:
        ranked = score_animals(df, min_fixes=min_fixes)
        if ranked.empty:
            print(f"no animals with at least {min_fixes} fixes")
            return 1
        top = ranked.head(count)
        if dry_run:
            print(top[["animal", "name", "score", "daily_km_sum", "days"]].to_string(index=False))
            return 0
        chosen = [(r["animal"], r["score"]) for _, r in top.iterrows()]
    styles = ["vector", "street", "satellite"] if style == "all" else [style]
    fmts = ["short", "long"] if fmt == "both" else [fmt]
    for animal, score in chosen:
        tid = track_id_for(slug, animal)
        print(f"\n=== {tid}" + (f" (score {score})" if score is not None else "") + " ===")
        try:
            out = build_track(slug, animal)
        except Exception as e:
            print(f"  build failed: {e}")
            _set_state(tid, "new", error=str(e))
            continue
        _set_state(tid, "new", slug=slug, animal=animal)
        made = False
        for f in fmts:
            for s in styles:
                try:
                    path = render(out, f, s)
                    print(f"  {f}/{s}: {path.name}")
                    made = True
                except Exception as e:
                    print(f"  {f}/{s}: FAILED - {e}")
        _set_state(tid, "rendered" if made else "new")
    print("\nDone. Review with: python -m wildtracks dashboard")
    return 0


def cmd_batch(args):
    return _run_batch(args.slug, args.count, args.format, args.style,
                      animals=args.animal or None, dry_run=args.dry_run, min_fixes=args.min_fixes)


def cmd_run(args):
    """One command: fetch (or import) -> pick -> build -> render."""
    from .movebank import fetch_study
    from .study import import_csv

    if not args.slug:
        print("error: pass --slug <name> for the study folder")
        return 2
    src = Path(args.source)
    if src.suffix.lower() == ".csv" and src.exists():
        out = import_csv(src, args.slug, args.license or "own/unknown", args.credit or "", args.title or "")
        print(f"imported {src.name} -> {out}")
    else:
        out = fetch_study(args.source, args.slug, skip_existing=True)
        print(f"fetched -> {out}")
    return _run_batch(args.slug, args.count, args.format, args.style,
                      animals=args.animal or None, dry_run=False, min_fixes=args.min_fixes)


def cmd_status(args):
    status = _load_status()
    if not TRACKS_DIR.exists():
        print("no tracks yet")
        return 0
    for d in sorted(TRACKS_DIR.iterdir()):
        if not d.is_dir():
            continue
        entry = status.get(d.name, {})
        state = entry.get("state", "new")
        videos = sorted(p.name for p in (d / "out").glob("*.mp4")) if (d / "out").exists() else []
        audio = [p.name for p in d.glob("audio_*.*")]
        print(f"{d.name}\n  state: {state}\n  videos: {', '.join(videos) or '-'}\n  audio: {', '.join(audio) or '-'}")
    return 0


def cmd_approve(args):
    out = TRACKS_DIR / args.track_id
    if not out.exists():
        print(f"no such track: {args.track_id}")
        return 1
    _set_state(args.track_id, args.state)
    print(f"{args.track_id} -> {args.state}")
    return 0


def _dashboard(port: int):
    from .dashboard import serve

    serve(port)
    return 0


def _site():
    from .site import build_site

    out = build_site()
    print(f"site built at {out}  (serve it or push to GitHub Pages)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="wildtracks", description="Real animal tracks -> narrated map videos.")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download a Movebank study (CC0/CC-BY only)")
    f.add_argument("ref", help="DOI, handle URL, or repository reference")
    f.add_argument("--slug", help="folder name under data/studies/")
    f.add_argument("--force", action="store_true", help="re-download even if gps.csv exists")
    f.set_defaults(fn=cmd_fetch)

    pk = sub.add_parser("pick", help="rank animals in a study by story-worthiness")
    pk.add_argument("slug")
    pk.add_argument("--top", type=int, default=10)
    pk.add_argument("--min-fixes", type=int, default=50)
    pk.set_defaults(fn=cmd_pick)

    t = sub.add_parser("track", help="build a track package (facts, points, scenes, narration)")
    t.add_argument("slug")
    t.add_argument("animal")
    t.add_argument("--force-scenes", action="store_true")
    t.set_defaults(fn=cmd_track)

    sc = sub.add_parser("script", help="rebuild scenes and narration for a track")
    sc.add_argument("track_id")
    sc.add_argument("--format", choices=["short", "long"])
    sc.set_defaults(fn=cmd_script)

    n = sub.add_parser("narration", help="rewrite narration txt from scenes (after editing scenes json)")
    n.add_argument("track_id")
    n.add_argument("--format", choices=["short", "long"])
    n.set_defaults(fn=cmd_narration)

    r = sub.add_parser("render", help="render a track video via Remotion")
    r.add_argument("track_id")
    r.add_argument("--format", choices=["short", "long"], default=None)
    r.add_argument("--style", choices=["vector", "street", "satellite", "all"], default="vector")
    r.add_argument("--frame", type=int, default=None, help="render one still frame instead of a video")
    r.set_defaults(fn=cmd_render)

    b = sub.add_parser("batch", help="pick the top N animals in a study, build and render each")
    b.add_argument("slug")
    b.add_argument("--count", type=int, default=3)
    b.add_argument("--format", choices=["short", "long", "both"], default="short")
    b.add_argument("--style", choices=["vector", "street", "satellite", "all"], default="vector")
    b.add_argument("--animal", action="append", help="render this specific animal instead of the top-N (repeatable)")
    b.add_argument("--min-fixes", type=int, default=50)
    b.add_argument("--dry-run", action="store_true", help="just show which animals would be picked")
    b.set_defaults(fn=cmd_batch)

    rn = sub.add_parser("run", help="one command: DOI or CSV -> pick -> build -> render")
    rn.add_argument("source", help="Movebank DOI/handle URL, or a path to a CSV of fixes")
    rn.add_argument("--slug", required=True, help="folder name under data/studies/")
    rn.add_argument("--count", type=int, default=3)
    rn.add_argument("--format", choices=["short", "long", "both"], default="short")
    rn.add_argument("--style", choices=["vector", "street", "satellite", "all"], default="vector")
    rn.add_argument("--animal", action="append", help="render this specific animal instead of the top-N (repeatable)")
    rn.add_argument("--license", help="licence label for CSV imports, e.g. 'own data' or 'CC-BY 4.0'")
    rn.add_argument("--credit", help="credit line for CSV imports, shown in video end card")
    rn.add_argument("--min-fixes", type=int, default=50)
    rn.add_argument("--title", help="study title for CSV imports")
    rn.set_defaults(fn=cmd_run)

    st = sub.add_parser("status", help="list tracks, videos and review state")
    st.set_defaults(fn=cmd_status)

    ap = sub.add_parser("approve", help="set review state for a track")
    ap.add_argument("track_id")
    ap.add_argument("state", choices=REVIEW_STATES)
    ap.set_defaults(fn=cmd_approve)

    d = sub.add_parser("dashboard", help="local review dashboard (watch videos, set state)")
    d.add_argument("--port", type=int, default=8570)
    d.set_defaults(fn=lambda a: _dashboard(a.port))

    si = sub.add_parser("site", help="build a static website of videos into docs/ (GitHub Pages ready)")
    si.set_defaults(fn=lambda a: _site())

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
