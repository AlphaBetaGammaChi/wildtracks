# WildTracks

Real animal tracks -> narrated map videos for YouTube (Shorts + long-form).
Every video follows genuine recorded telemetry — never invented routes.

## Layout

- `wildtracks/` — Python package (downloader, selector, facts, scripts, render glue, CLI)
- `renderer/` — Remotion (React/TS) video project: `Short` (1080x1920) and `Long` (1920x1080)
- `data/studies/<slug>/` — downloaded Movebank studies (gps.csv, reference.csv, study.json)
- `data/naturalearth/` — Natural Earth geojson used for country/sea/desert lookups
- `tracks/<study>--<animal>/` — per-animal package: facts.json, points.json,
  scenes_{short,long}.json, narration_{short,long}.txt, description.txt, out/*.mp4
- `legacy/` — old fabricated-track pipeline, kept for reference only
- `status.json` — review state per track (new/rendered/reviewed/approved/published)

## Commands

Use the venv: `.venv/bin/python -m wildtracks <cmd>`

- `fetch <doi-or-url> --slug <name>` — download a Movebank study (CC0/CC-BY only)
- `pick <slug>` — rank animals by story-worthiness
- `track <slug> "<animal>"` — build a track package (facts, points, scenes, narration)
- `script <track-id>` — rebuild scenes + narration after changing script.py
- `narration <track-id>` — rewrite narration txt from edited scenes_*.json
- `render <track-id> --format short|long --style vector|street|satellite|all [--frame N]`
- `status` — list tracks, videos, review state
- `approve <track-id> <state>` — set review state
- `dashboard [--port 8570]` — local review page: watch MP4s, set state
- tests: `.venv/bin/python -m pytest tests/`

## Voiceover sync

Record narration from `narration_<fmt>.txt`, save it as `audio_<fmt>.mp3` (or .wav/.m4a/.aac)
in the track folder, and re-render. Scene timings stretch to the audio length.
For exact sync, add `markers_<fmt>.txt`: one start time (seconds or m:ss) per spoken scene,
in order — each scene snaps to its marker.

## Map styles

- `vector` — offline Natural Earth, works anywhere
- `street` — OpenFreeMap tiles (needs network during render)
- `satellite` — MapTiler tiles; requires `export MAPTILER_KEY=...` and a licence check
  before monetised use

## Rules

- Only CC0/CC-BY studies. The downloader refuses anything else.
- Narration text may only contain numbers/claims present in facts.json.
- Videos are reviewed by a human (`approve`) before any YouTube upload; nothing auto-uploads.
- Don't commit API keys or audio containing secrets.

## Notes

- ffmpeg is not installed; Remotion handles mp4 encoding itself.
- MapLibre worker files (maplibre-gl-*.mjs) are copied into each track folder by
  `wildtracks.render` because Remotion's webpack can't bundle them — they're served
  via --public-dir.
