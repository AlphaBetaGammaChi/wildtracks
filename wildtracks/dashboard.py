"""Local review dashboard: `python -m wildtracks dashboard` then open http://localhost:8570

Lists every track package, embeds rendered MP4s for watching, shows the narration
script, and persists review state (new/reviewed/approved/published) to status.json.
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .cli import REVIEW_STATES, _load_status, _set_state
from .paths import TRACKS_DIR

PORT = 8570

PAGE = """<!doctype html><meta charset=utf-8><title>WildTracks review</title>
<style>
body{font-family:-apple-system,Avenir Next,sans-serif;background:#0b1420;color:#eee;max-width:1100px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.6rem}.track{background:#12202f;border:1px solid #22344a;border-radius:12px;padding:1.2rem;margin:1rem 0}
.track h2{margin:0 0 .4rem;font-size:1.15rem}.state{font-weight:700;text-transform:uppercase;letter-spacing:.05em}
.new{color:#94a3b8}.rendered{color:#7cc7ff}.reviewed{color:#fbbf24}.approved{color:#34d399}.published{color:#a78bfa}
video{max-width:100%;max-height:420px;border-radius:8px;margin:.4rem .6rem .4rem 0;background:#000;vertical-align:top}
video.short{max-width:240px}pre{white-space:pre-wrap;background:#0d1826;border-radius:8px;padding:.8rem;font-size:.85rem;color:#cbd5e1}
button,.btn{cursor:pointer;border:1px solid #33455e;background:#1a2a3d;color:#eee;border-radius:7px;padding:.35rem .8rem;margin-right:.4rem;font-size:.85rem}
button:hover{background:#22364d}.muted{color:#8aa0b8;font-size:.85rem}a{color:#7cc7ff}
h3{font-size:.95rem;margin:.8rem 0 .3rem;color:#9db4ca}
</style>
<h1>WildTracks — review dashboard</h1>
<p class=muted>Watch each render, then set the state. Nothing uploads automatically.</p>
__TRACKS__
<script>
async function setState(id,s){await fetch('/state',{method:'POST',body:JSON.stringify({track:id,state:s})});location.reload()}
</script>"""


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def track_card(d: Path, status: dict) -> str:
    entry = status.get(d.name, {})
    state = entry.get("state", "new")
    facts = {}
    fp = d / "facts.json"
    if fp.exists():
        facts = json.loads(fp.read_text())
    title = f"{_esc(facts.get('animal', d.name))} — {_esc(facts.get('species', {}).get('common', ''))}"
    j = facts.get("journey", {})
    summary = f"{j.get('days', '?')} days · at least {j.get('km', '?')} km · {' → '.join([j['countries'][0], j['countries'][-1]]) if j.get('countries') else ''}"
    vids = ""
    out = d / "out"
    if out.exists():
        for v in sorted(out.glob("*.mp4")):
            cls = "short" if "short" in v.name else "long"
            vids += f'<video class="{cls}" controls preload="metadata" src="/files/{d.name}/{urllib.parse.quote(v.name)}"></video>'
        vids = vids or '<p class=muted>No videos yet.</p>'
    narr = ""
    for fmt in ("short", "long"):
        p = d / f"narration_{fmt}.txt"
        if p.exists():
            narr += f"<h3>narration_{fmt}.txt</h3><pre>{_esc(p.read_text())}</pre>"
    creds = facts.get("study", {}).get("data_citation", "")
    buttons = "".join(
        f'<button onclick="setState(\'{d.name}\',\'{s}\')">{s}</button>' for s in ("reviewed", "approved", "published")
    )
    return f"""<div class=track>
<h2>{title} <span class="state {state}">[{state}]</span></h2>
<p class=muted>{_esc(summary)}</p>
{vids}
<p>{buttons}</p>
{narr}
<p class=muted>{_esc(creds)}</p>
</div>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body=b"", ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if isinstance(body, str):
            body = body.encode()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            status = _load_status()
            cards = "".join(
                track_card(d, status) for d in sorted(TRACKS_DIR.iterdir()) if d.is_dir()
            ) or "<p>No tracks yet.</p>"
            self._send(PAGE.replace("__TRACKS__", cards))
            return
        m = self.path.removeprefix("/files/")
        if m != self.path:
            parts = urllib.parse.unquote(m).split("/", 1)
            f = TRACKS_DIR / parts[0] / "out" / parts[1]
            if f.exists() and f.suffix == ".mp4" and f.resolve().is_relative_to(TRACKS_DIR.resolve()):
                self._send(f.read_bytes(), "video/mp4")
                return
        self._send("not found", "text/plain", 404)

    def do_POST(self):
        if self.path == "/state":
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if data.get("state") in REVIEW_STATES and (TRACKS_DIR / data.get("track", "")).is_dir():
                _set_state(data["track"], data["state"])
                self._send("{}", "application/json")
                return
        self._send("bad request", "text/plain", 400)

    def log_message(self, *a):
        pass


def serve(port: int = PORT):
    print(f"WildTracks dashboard -> http://localhost:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
