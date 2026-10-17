from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STUDIES_DIR = DATA_DIR / "studies"
NATURAL_EARTH_DIR = DATA_DIR / "naturalearth"
TRACKS_DIR = ROOT / "tracks"
RENDERER_DIR = ROOT / "renderer"
STATUS_FILE = ROOT / "status.json"
