"""Hand a track to the Remotion renderer."""

import json
import os
import subprocess
from pathlib import Path

from .paths import RENDERER_DIR

STYLES = ("vector", "street", "satellite")
COMPOSITIONS = {"short": "Short", "long": "Long"}
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".aac")


def find_audio(track: Path, fmt: str):
    for ext in AUDIO_EXTS:
        p = track / f"audio_{fmt}{ext}"
        if p.exists():
            return p.name
    return None


def read_markers(track: Path, fmt: str):
    """markers_<fmt>.txt: one start time per spoken scene, in seconds (e.g. 0, 6.2, 13.9 ...)."""
    p = track / f"markers_{fmt}.txt"
    if not p.exists():
        return None
    values = []
    for line in p.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            if ":" in line:
                m, s = line.split(":", 1)
                values.append(int(m) * 60 + float(s))
            else:
                values.append(float(line))
    return values


def build_props(track: Path, fmt: str, style: str) -> dict:
    facts = json.loads((track / "facts.json").read_text())
    scenes = json.loads((track / f"scenes_{fmt}.json").read_text())
    audio = find_audio(track, fmt)
    markers = read_markers(track, fmt)
    spoken = [s for s in scenes["scenes"] if s["text"]]
    if markers is not None and len(markers) != len(spoken):
        raise ValueError(f"markers_{fmt}.txt has {len(markers)} times but there are {len(spoken)} spoken scenes")
    return {
        "style": style,
        "title": scenes["title"],
        "subtitle": scenes.get("subtitle", ""),
        "label": scenes["label"],
        "species": facts["species"]["common"],
        "points": json.loads((track / "points.json").read_text()),
        "scenes": scenes["scenes"],
        "credits": scenes["credits"],
        "audio": audio,
        "markers": markers,
        "maptilerKey": os.environ.get("MAPTILER_KEY") or None,
    }


def _remotion(args: list):
    subprocess.run(["npx", "remotion", *args], cwd=RENDERER_DIR, check=True)


def _copy_maplibre_worker(track: Path):
    """MapLibre's worker can't be bundled by Remotion's webpack; serve it from the public dir."""
    import shutil

    dist = RENDERER_DIR / "node_modules" / "maplibre-gl" / "dist"
    for name in ("maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"):
        src = dist / name
        dst = track / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def render(track: Path, fmt: str, style: str, frame: int = None, concurrency: int = None) -> Path:
    if style == "satellite" and not os.environ.get("MAPTILER_KEY"):
        raise RuntimeError("Satellite style needs a MapTiler key: export MAPTILER_KEY=... (free account at maptiler.com)")
    if style != "vector":
        _copy_maplibre_worker(track)
    out_dir = track / "out"
    out_dir.mkdir(exist_ok=True)
    props_path = out_dir / f"props_{fmt}_{style}.json"
    props_path.write_text(json.dumps(build_props(track, fmt, style)))
    common = [f"--props={props_path}", f"--public-dir={track}", "--gl=angle", "--log=error"]
    if frame is not None:
        out = out_dir / f"still_{fmt}_{style}_{frame}.png"
        _remotion(["still", "src/index.ts", COMPOSITIONS[fmt], str(out), f"--frame={frame}", *common])
    else:
        out = out_dir / f"{fmt}_{style}.mp4"
        extra = [f"--concurrency={concurrency}"] if concurrency else []
        if style != "vector":
            extra = extra or ["--concurrency=2"]
        _remotion(["render", "src/index.ts", COMPOSITIONS[fmt], str(out), "--codec=h264", "--crf=18", *extra, *common])
    return out
