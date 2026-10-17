"""Build scene-by-scene narration from a fact sheet. Sentences only use values from the facts."""

import math
from datetime import datetime

import pandas as pd

from . import facts as F
from . import geo

WORDS_PER_SECOND = 2.5
SHORT_MAX_SECONDS = 60.0

# Natural Earth names parts of the Sahara separately; viewers know them as "the Sahara".
SAHARA_PARTS = {
    "Western Desert", "Libyan Desert", "Nubian Desert", "Ténéré", "Grand Erg Oriental", "Grand Erg Occidental",
    "‘Erg Chech", "El Djouf", "Hamada du Drâa", "Idhän Murzuq", "Tassili oua-n-Ahaggar", "Tassili-n-Ajjer",
    "Sarïr Kalanshiyu ar Ramli al Kabi",
}


def fmt_date(iso: str, with_year: bool = True) -> str:
    d = datetime.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')}" + (f" {d.year}" if with_year else "")


def at_least_km(km: float) -> str:
    step = 100 if km >= 1000 else 10
    return f"{int(math.floor(km / step) * step):,}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def join_list(items: list) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def where(place: dict) -> str:
    if place.get("country"):
        return f"near {place['town']} in {place['country']}" if place.get("town") else f"in {place['country']}"
    return f"over the {place['sea']}" if place.get("sea") else "over open water"


def destination(place: dict) -> str:
    if place.get("country"):
        return f"{place['country']}, near {place['town']}" if place.get("town") else place["country"]
    return f"the {place['sea']}" if place.get("sea") else "open water"


def label_for(facts: dict) -> str:
    return facts["name"] if facts["has_nickname"] else facts["animal"].split()[-1]


def estimate_seconds(text: str, minimum: float = 3.0) -> float:
    return round(max(minimum, len(text.split()) / WORDS_PER_SECOND + 0.6), 2)


def _segment(df: pd.DataFrame, t0: str, t1: str) -> dict:
    seg = df[(df.timestamp >= pd.Timestamp(t0)) & (df.timestamp <= pd.Timestamp(t1))]
    return F.segment_facts(seg)


def _km_at(df: pd.DataFrame, iso: str) -> float:
    after = df[df.timestamp >= pd.Timestamp(iso)]
    return float(after.cum_km.iloc[0] if len(after) else df.cum_km.iloc[-1])


def _legs(facts: dict, df: pd.DataFrame, n_legs: int, min_stay_days: int) -> list:
    """Split the journey at stopovers. Picks the longest stops, or evenly spaced ones when there are many."""
    j0, j1 = facts["journey_window"]
    stays = [s for s in facts["stays"] if j0 < s["start"] and s["end"] < j1 and s["days"] >= min_stay_days]
    if len(stays) > n_legs - 1:
        k0, k1 = _km_at(df, j0), _km_at(df, j1)
        targets = [k0 + (k1 - k0) * (i + 1) / n_legs for i in range(n_legs - 1)]
        chosen = []
        for target in targets:
            free = [s for s in stays if s not in chosen]
            chosen.append(min(free, key=lambda s: abs(_km_at(df, s["start"]) - target) / max(s["days"], 1) ** 0.5))
        stays = chosen
    stays = sorted(stays, key=lambda s: s["start"])
    legs, t = [], j0
    for s in stays:
        legs.append({"t0": t, "t1": s["start"], "stay": s})
        t = s["end"]
    legs.append({"t0": t, "t1": j1, "stay": None})
    for leg in legs:
        leg["facts"] = _segment(df, leg["t0"], leg["t1"])
    return [l for l in legs if l["facts"]]


class _Told:
    """Remembers what has already been said so the script never repeats itself."""

    def __init__(self, start_country):
        self.countries = {start_country} if start_country else set()
        self.deserts, self.ranges, self.seas = set(), set(), set()

    def new(self, items, seen):
        fresh = [i for i in items if i not in seen]
        seen.update(fresh)
        return fresh


def _deserts(names: list) -> list:
    out = ["Sahara" if n in SAHARA_PARTS else n for n in names]
    return list(dict.fromkeys(out))


def _leg_text(i: int, leg: dict, facts: dict, label: str, told: _Told, style: str) -> str:
    """style: 'long' (everything), 'short' or 'tight' (short without the extras)."""
    lf, verb = leg["facts"], facts["species"]["verb"]
    days = max(1, round(lf["days"]))
    parts = [f"On {fmt_date(lf['start'])}, {label} set off {lf['heading']}." if i == 0
             else f"On {fmt_date(lf['start'], with_year=False)} it moved on, heading {lf['heading']}."]

    new_countries = told.new(lf["countries"], told.countries)
    if style == "long" or len(new_countries) <= 3:
        through = join_list(new_countries)
    else:
        through = f"{', '.join(new_countries[:2])} and {len(new_countries) - 3} more countries, all the way to {new_countries[-1]}"
    km = at_least_km(lf["km"])
    parts.append(f"In {plural(days, 'day')} it {verb} at least {km} kilometres" + (f", through {through}." if through else "."))

    open_water = told.new([s["name"] for s in lf["seas"] if s["open_water"]], told.seas)
    if open_water:
        parts.append(f"It crossed open water over the {join_list(open_water)}.")
    coast = told.new([s["name"] for s in lf["seas"] if not s["open_water"]], told.seas)
    if coast and style == "long":
        parts.append(f"Like most storks it avoided open sea, keeping close to land along the {join_list(coast)}." if "stork" in facts["species"]["common"]
                     else f"It kept close to land along the {join_list(coast)}.")

    deserts = told.new(_deserts(lf["deserts"]), told.deserts)
    if deserts:
        parts.append(f"Its route crossed {join_list(['the ' + d for d in deserts])}.")
    ranges = told.new(lf["ranges"], told.ranges)
    if ranges and style == "long":
        parts.append(f"It passed over the {join_list(ranges)}.")

    best = facts["best_day"]
    if style != "tight" and lf["start"][:10] <= best["date"][:10] <= lf["end"][:10]:
        parts.append(f"On {fmt_date(best['date'], with_year=False)} alone it covered {best['km']} kilometres, its biggest day.")
    if leg["stay"]:
        rest = ["Then it stopped for", "Then it rested for", "Then it paused for"][i % 3]
        parts.append(f"{rest} {plural(leg['stay']['days'], 'day')} {where(leg['stay']['place'])}.")
    return " ".join(parts)


def _make_scenes(facts: dict, df: pd.DataFrame, fmt: str, style: str, n_legs: int) -> list:
    label = label_for(facts)
    common = facts["species"]["common"]
    young = (facts.get("life_stage") or "").lower() == "juvenile"
    whole, journey = facts["whole"], facts["journey"]
    j0, j1 = facts["journey_window"]
    scenes = []

    def add(kind, text, t0, t1, camera="follow", min_s=3.0):
        scenes.append({"id": f"s{len(scenes) + 1}", "kind": kind, "text": text, "t0": t0, "t1": t1,
                       "camera": camera, "seconds": estimate_seconds(text, min_s) if text else min_s})

    cs = journey["countries"]
    if len(cs) >= 2:
        add("hook", f"This {'young ' if young else ''}{common} {facts['species']['verb']} from {cs[0]} to {cs[-1]}. This is its real GPS track.",
            j0, j1, camera="overview", min_s=3.5)
    month = datetime.fromisoformat(whole["start"]).strftime("%B %Y")
    intro_name = f"Its name: {label}." if facts["has_nickname"] else f"Its code: {label}."
    tagged_at = where(whole["start_place"]) if fmt == "long" else f"in {whole['start_place'].get('country') or 'the wild'}"
    subject = "it" if scenes else f"a {'young ' if young else ''}{common}"
    add("intro", f"In {month}, researchers put a GPS tag on {subject} {tagged_at}. {intro_name}",
        whole["start"], j0, camera="start", min_s=4.0)

    told = _Told(whole["start_place"].get("country"))
    for i, leg in enumerate(_legs(facts, df, n_legs, min_stay_days=4 if fmt == "long" else 6)):
        add("leg", _leg_text(i, leg, facts, label, told, style), leg["t0"], leg["t1"])

    first = "On its very first migration, " if young else ""
    if fmt == "long":
        arrival = (f"{first}{label} reached {destination(journey['end_place'])} on {fmt_date(j1)}, "
                   f"{journey['straight_km']:,} kilometres from where it was tagged. "
                   f"That is at least {at_least_km(journey['km'])} kilometres in {round(journey['days'])} days.")
    else:
        arrival = (f"{first}{label} reached {journey['end_place'].get('country') or 'its destination'} on {fmt_date(j1)}: "
                   f"at least {at_least_km(journey['km'])} kilometres in {round(journey['days'])} days.")
    add("arrival", arrival, j1, j1, camera="overview", min_s=5.0)

    if fmt == "long" and whole["end"] > j1:
        after = _segment(df, j1, whole["end"])
        back = geo.haversine_km(df.lat.iloc[-1], df.lon.iloc[-1], df.lat.iloc[0], df.lon.iloc[0])
        months = round((datetime.fromisoformat(whole["end"]) - datetime.fromisoformat(j1)).days / 30.4)
        text = (f"The data follows {label} for {plural(months, 'more month')}, until {fmt_date(whole['end'])}. "
                f"In that time it {facts['species']['verb']} at least another {at_least_km(after['km'])} kilometres, "
                f"and its last recorded position was {where(after['end_place'])}")
        text += f", just {round(back):,} kilometres from where it started." if back < 0.25 * facts["farthest"]["km_from_start"] else "."
        add("after", text, j1, whole["end"])

    if facts.get("outcome") == "died":
        add("outcome", f"Researchers later confirmed that {label} had died. Many young {common}s do not survive their first year.",
            whole["end"], whole["end"], camera="overview", min_s=4.0)

    add("credits", "", whole["end"], whole["end"], camera="overview", min_s=4.0)
    return scenes


def build_scenes(facts: dict, df: pd.DataFrame, fmt: str) -> dict:
    """fmt is 'short' or 'long'."""
    if fmt == "long":
        scenes = _make_scenes(facts, df, fmt, "long", n_legs=8)
    else:
        for style, n in (("short", 3), ("tight", 3), ("tight", 2), ("tight", 1)):
            scenes = _make_scenes(facts, df, fmt, style, n)
            if sum(s["seconds"] for s in scenes) <= SHORT_MAX_SECONDS:
                break
    label, common = label_for(facts), facts["species"]["common"]
    return {
        "format": fmt,
        "label": label,
        "title": f"{label} the {common}" if facts["has_nickname"] else f"{common.capitalize()} {label}",
        "subtitle": f"{facts['journey']['countries'][0] if facts['journey']['countries'] else ''} to {facts['journey']['countries'][-1] if facts['journey']['countries'] else ''}".strip(" to"),
        "scenes": scenes,
        "credits": {
            "data": facts["study"]["data_citation"],
            "license": facts["study"]["license"],
            "doi": facts["study"]["doi"],
        },
    }


def narration_text(scenes: dict) -> str:
    lines = [f"# {scenes['title']} ({scenes['format']})",
             "# Read each [scene] as written, leaving a short pause between scenes.",
             "# To change the wording, edit scenes_<format>.json and run `wildtracks narration <track>`.", ""]
    for s in scenes["scenes"]:
        if s["text"]:
            lines += [f"[{s['id']}]", s["text"], ""]
    return "\n".join(lines)
