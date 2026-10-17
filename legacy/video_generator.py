#!/usr/bin/env python3
"""
video_generator.py
Automated video asset & script generator for animal tracking data.
Generates:
1. Short-Form Video Package (YouTube Shorts / TikTok / Reels - 45-60s)
   - Dynamic viral hook based on real telemetry
   - Timed chronological telemetry milestones
   - TravelBoast & Google Earth Studio camera directions
   - Sound effects (SFX) & on-screen HUD overlay cues
   - Clean ElevenLabs-ready voiceover prompt text
2. Long-Form Video Package (YouTube Video Essay / Documentary - 6-10 min)
   - Act I: The Tagging & The Science
   - Act II: The Odyssey (Stage-by-stage obstacles & biology)
   - Act III: The Discovery & Conservation Legacy
   - Full B-roll cues and camera target guidelines
   - Clean ElevenLabs-ready voiceover prompt text
3. Map Animation Exports
   - .gpx (TravelBoast, Strava, QGIS)
   - .kml (Google Earth Studio 3D camera tracking)
   - .geojson (Mapbox, Leaflet, After Effects GEOlayers 3)
   - track_summary.json
"""

import os
import json
from typing import Dict, Any, List
from track_parser import Track

OUTPUT_DIR = "video_production/tracks"

def generate_short_form_script(track: Track) -> (str, str):
    """
    Generates short-form video package markdown and clean voiceover text.
    Returns (markdown_package, clean_voiceover_text).
    """
    dist_str = f"{int(track.total_distance_km):,} km"
    miles_str = f"{int(track.total_distance_km * 0.621371):,} miles"
    days_str = f"{int(track.total_duration_days)} days" if track.total_duration_days >= 1 else "several hours"
    
    subject_name = getattr(track, 'display_id', None) or track.animal_id or track.common_name

    # Dynamic hook generation based on species and feats
    if "Pacific" in " ".join(track.geo_features) or track.total_distance_km > 8000:
        hook = f"This tiny {track.common_name} just completed an impossible journey: {dist_str} non-stop across the open ocean without landing once."
        dilemma = "If its wings stop flapping for even ten seconds, it hits the water and drowns."
    elif "Sahara" in " ".join(track.geo_features):
        hook = f"Meet {subject_name}: the {track.common_name} that just flew non-stop across the scorching Sahara desert furnace."
        dilemma = "No water, no trees, and temperatures topping 45 degrees Celsius."
    elif track.category == "Marine":
        hook = f"In the pitch-black abyss of the open ocean, this {track.common_name} just swam {dist_str} in a dead straight line."
        dilemma = "How did it navigate thousands of miles with pinpoint precision? Satellite tracking revealed the truth."
    elif len(track.waypoints) > 20:
        hook = f"For years, this {track.common_name} was tracked across {len(track.waypoints)} verified sightings by citizen scientists."
        dilemma = f"Living a double life between wild fjords and bustling city harbors, here is the secret path of {subject_name}."
    else:
        hook = f"Scientists attached a tiny tracker to this {track.common_name}. What it did next stunned biologists."
        dilemma = f"A relentless trek spanning {dist_str} across hostile terrain."

    # Build chronological legs
    wps = track.waypoints
    num_wp = len(wps)
    
    start_wp = wps[0]
    mid_wp = wps[num_wp // 2] if num_wp > 2 else wps[0]
    end_wp = wps[-1]
    
    # Clean voiceover text
    clean_vo_lines = [
        hook,
        dilemma,
        f"It began at {start_wp.get('location_name', 'its starting coordinates')}.",
        f"Burning up to half its body mass as fuel, it pushed relentlessly forward, crossing {', '.join(track.geo_features) if track.geo_features else 'mountains, open water, and shifting winds'}.",
        f"Halfway through the journey at {mid_wp.get('location_name', 'the midpoint')}, the tracker recorded extreme endurance under grueling conditions.",
        f"Finally, after covering {dist_str}, {subject_name} touched down at {end_wp.get('location_name', 'its destination')}.",
        f"Could you survive a journey like this? Follow for more incredible wild tracking journeys."
    ]
    clean_vo = "\n\n".join(clean_vo_lines)
    
    # Formatted production markdown
    md = f"""# Short-Form Video Production Blueprint (YouTube Shorts / TikTok / Reels)
**Track ID:** `{track.track_id}`  
**Subject:** {track.common_name} (*{track.scientific_name}*) — {track.animal_id}  
**Format:** 9:16 Vertical Video (1080x1920) | Target Duration: 50–58 seconds  
**Total Distance:** {dist_str} ({miles_str}) | **Time Elapsed:** {days_str}  
**Geographic Obstacles:** {', '.join(track.geo_features) if track.geo_features else 'Regional Flyway Corridors'}  

---

## 🎬 Beat-by-Beat Timeline & Production Directives

### [0:00 – 0:08] The Viral Hook
* **Visual Direction:** [MAP] Dynamic high-altitude satellite globe view. Fast zoom directly into `{start_wp.get('location_name', 'Starting Point')}`. Animated path line begins pulsating with energy.
* **On-Screen HUD:** `🔴 RECORDING LIVE TELEMETRY` | `TAG: {track.animal_id}`
* **Sound Design:** [SFX] Deep bass sub-drop, followed by rushing wind and rapid heartbeat sound effect.
* **Voiceover:**
  > "{hook} {dilemma}"

---

### [0:08 – 0:22] Leg 1: Departure & The Fuel Burn
* **Visual Direction:** [MAP] Camera tilts to 45° perspective (TravelBoast style) tracking the {track.common_name} avatar travelling along the route. Satellite terrain swoops below.
* **On-Screen HUD:** `📍 Day 1: {start_wp.get('location_name', 'Departure')}` | `Distance: 0 km ➔ {int(track.total_distance_km * 0.35):,} km` | `Odometer Ticking Up Fast`
* **Sound Design:** [SFX] Fast rhythmic synth pulse, distant bird wing flaps or ocean surf.
* **Voiceover:**
  > "It began at {start_wp.get('location_name', 'its starting grounds')}. Burning up to half its body weight as fuel, it pushed relentlessly forward, braving {', '.join(track.geo_features) if track.geo_features else 'unforgiving winds and open terrain'}."

---

### [0:22 – 0:38] Leg 2: The Critical Obstacle & Climax
* **Visual Direction:** [MAP] Camera pulls into a dramatic close-up as the path crosses `{mid_wp.get('location_name', 'the midpoint')}`. Overlay weather satellite storm layers or desert topography.
* **On-Screen HUD:** `⚠️ EXTREME ENDURANCE ZONE` | `Halfway Point` | `Speed: {int(track.total_distance_km / max(1, track.total_duration_days * 24) * 2)} km/h`
* **Sound Design:** [SFX] Rising tension riser, wind howling or thunderstorm rumble.
* **Voiceover:**
  > "Halfway through the journey, near {mid_wp.get('location_name', 'the midpoint')}, the satellite tracker recorded extreme endurance. Every muscle was pushed to the absolute breaking point."

---

### [0:38 – 0:52] Leg 3: Touchdown & The Discovery
* **Visual Direction:** [MAP] Camera eases to a stop at `{end_wp.get('location_name', 'Destination')}`. Golden landing pin drops with ripple effect.
* **On-Screen HUD:** `🏁 TOUCHDOWN VERIFIED` | `Total: {dist_str}` | `Elapsed: {days_str}`
* **Sound Design:** [SFX] Satisfying mechanical lock chime, warm ambient resolution chord.
* **Voiceover:**
  > "Finally, after covering {dist_str}, {track.animal_id} made touchdown at {end_wp.get('location_name', 'its final destination')}. An awe-inspiring testament to the resilience of life on Earth."

---

### [0:52 – 0:58] The Call to Action
* **Visual Direction:** On-screen end card: *"Which animal journey should we track next?"* | Channel Subscribe Button.
* **Voiceover:**
  > "Could you survive a journey like this? Follow for more incredible wild tracking journeys."

---

## 🎙️ ElevenLabs Voice Prompt (Ready to Copy)
```
{clean_vo}
```
"""
    return md, clean_vo

def generate_long_form_script(track: Track) -> (str, str):
    """
    Generates long-form documentary script package markdown and clean narrator text.
    Returns (markdown_package, clean_voiceover_text).
    """
    dist_str = f"{int(track.total_distance_km):,} km"
    miles_str = f"{int(track.total_distance_km * 0.621371):,} miles"
    days_str = f"{int(track.total_duration_days)} days" if track.total_duration_days >= 1 else "several hours"
    wps = track.waypoints
    start_wp = wps[0] if wps else {}
    end_wp = wps[-1] if wps else {}

    # Build narrative sections
    act1_text = (
        f"For centuries, the seasonal disappearance of wildlife was shrouded in mystery. "
        f"Early naturalists once believed birds hibernated in mud at the bottom of lakes or transformed into different creatures during winter. "
        f"Today, tiny satellite transmitters and precision colour-marking schemes have revealed a reality far more astonishing than fiction. "
        f"This is the extraordinary story of {track.animal_id}, a {track.common_name} ({track.scientific_name or 'wild traveler'}) "
        f"that embarked on an expedition across {dist_str} ({miles_str}) of unforgiving planet Earth."
    )
    
    act2_text = (
        f"The expedition officially commenced at {start_wp.get('location_name', 'its origin point')}. "
        f"Before taking flight, these animals undergo profound physiological transformations. "
        f"Many species gorge themselves in a feeding frenzy known as hyperphagia, doubling their body mass in pure fat. "
        f"Some even shrink their non-essential digestive organs to save weight and maximize aerodynamic efficiency. "
        f"When {track.animal_id} launched into the sky, it was a biological missile engineered for one single purpose: endurance.\n\n"
        f"As the path unfolded across {', '.join(track.geo_features) if track.geo_features else 'diverse landscapes'}, "
        f"the telemetry fixes showed an astonishing navigational instinct. "
        f"Relying on polarized light, the Earth's geomagnetic field, and celestial cues, this traveler maintained an unwavering trajectory. "
        f"Navigating turbulent atmospheric fronts, sudden wind shears, and pitch-black nights, it continued hour after hour, covering thousands of kilometers without respite."
    )
    
    act3_text = (
        f"After {days_str} and {dist_str} of relentless movement, {track.animal_id} safely reached {end_wp.get('location_name', 'its destination')}. "
        f"This dataset, recorded through {track.dataset_source}, provides critical insights for global conservationists. "
        f"Every waypoint logged represents a vital ecological corridor that must be protected from habitat degradation, industrial development, and climate volatility. "
        f"When we look at this single golden line across the globe, we are not just looking at numbers on a screen; "
        f"we are looking at the heartbeat of our living planet."
    )
    
    clean_vo = f"{act1_text}\n\n{act2_text}\n\n{act3_text}\n\nThank you for watching. If you want to explore more remarkable migration journeys from around the world, subscribe to the channel and leave a comment with the species you want to see mapped next."
    
    md = f"""# Long-Form Documentary Production Script (YouTube 6–10 Minutes)
**Title Concept:** The Impossible Journey of {track.animal_id} | {dist_str} Wildlife Odyssey  
**Subject:** {track.common_name} (*{track.scientific_name}*)  
**Dataset Reference:** {track.dataset_source}  
**Total Distance:** {dist_str} ({miles_str}) | **Total Duration:** {days_str}  
**Total Waypoints:** {len(track.waypoints)}  

---

## 📽️ ACT I: The Mystery & The Mission [0:00 – 2:30]
* **Visual Directives:**
  * [B-ROLL] Archival footage of historical bird banding expeditions, high-magnification close-ups of color rings and satellite solar packs.
  * [MAP] Google Earth Studio wide orbit around Earth with cloud layers. The camera drops smoothly into `{start_wp.get('location_name', 'Origin')}`.
  * [GRAPHIC] Species Profile Card: Common Name, Scientific Name, Wing Chord, Weight, Ring/Tag ID.
* **Music:** Ambient, mysterious strings that slowly build in tempo.
* **Narrator:**
  > "{act1_text}"

---

## 🧭 ACT II: The Odyssey Across the Globe [2:30 – 6:30]
* **Visual Directives:**
  * [MAP] Google Earth Studio 3D camera tracking: Low-angle 3D flyover following the KML path over topographic mountain ranges, coastlines, and open bodies of water.
  * [HUD CALLOUT] Interactive data overlays showing speed, altitude, days elapsed, and heart-rate telemetry.
  * [B-ROLL] Aerial drone footage of stormy cloud tops, expansive deserts, and crashing ocean waves.
* **Key Telemetry Milestones:**
"""
    # Detail up to 5 key milestones in Act II
    step = max(1, len(track.waypoints) // 5)
    for wp in track.waypoints[::step]:
        loc_display = wp.get('location_name') or f"{wp['lat']}, {wp['lng']}"
        notes_display = wp.get('notes') or "Position logged via satellite telemetry."
        md += f"  * **Waypoint {wp['index']} ({wp['timestamp']}):** `{loc_display}` — *{notes_display}*\n"

    md += f"""
* **Music:** Propulsive, cinematic orchestral soundtrack with deep percussion and driving rhythm.
* **Narrator:**
  > "{act2_text}"

---

## 🌍 ACT III: The Discovery & The Science of Survival [6:30 – 8:30]
* **Visual Directives:**
  * [MAP] Final smooth camera deceleration into `{end_wp.get('location_name', 'Destination')}`. The complete route illuminates across the entire globe.
  * [GRAPHIC] Global Flyway Map showing international borders and conservation stopover reserves.
  * [B-ROLL] High-speed telephoto lens footage of the species resting, feeding, and reuniting with breeding flocks.
* **Music:** Warm, triumphant resolution melody.
* **Narrator:**
  > "{act3_text}"

---

## 🎙️ ElevenLabs Complete Narration Transcript
```
{clean_vo}
```
"""
    return md, clean_vo

def generate_video_package_for_track(track: Track, output_root: str = OUTPUT_DIR) -> Dict[str, str]:
    """
    Generates all video scripts, audio prompts, and map data formats for a given track.
    Returns a dict of generated file paths.
    """
    # Clean directory name
    safe_name = f"{track.track_id}_{track.common_name.replace(' ', '_')}".replace('/', '_').replace(':', '_')
    target_dir = os.path.join(output_root, safe_name)
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. Short-form package
    short_md, short_vo = generate_short_form_script(track)
    short_script_path = os.path.join(target_dir, "short_script.md")
    short_vo_path = os.path.join(target_dir, "short_voiceover.txt")
    with open(short_script_path, 'w', encoding='utf-8') as f:
        f.write(short_md)
    with open(short_vo_path, 'w', encoding='utf-8') as f:
        f.write(short_vo)
        
    # 2. Long-form package
    long_md, long_vo = generate_long_form_script(track)
    long_script_path = os.path.join(target_dir, "long_script.md")
    long_vo_path = os.path.join(target_dir, "long_voiceover.txt")
    with open(long_script_path, 'w', encoding='utf-8') as f:
        f.write(long_md)
    with open(long_vo_path, 'w', encoding='utf-8') as f:
        f.write(long_vo)
        
    # 3. Map exports
    gpx_path = os.path.join(target_dir, "route.gpx")
    with open(gpx_path, 'w', encoding='utf-8') as f:
        f.write(track.to_gpx())
        
    kml_path = os.path.join(target_dir, "route.kml")
    with open(kml_path, 'w', encoding='utf-8') as f:
        f.write(track.to_kml())
        
    geojson_path = os.path.join(target_dir, "route.geojson")
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(track.to_geojson(), f, indent=2)
        
    summary_path = os.path.join(target_dir, "track_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(track.to_dict(), f, indent=2)
        
    return {
        "track_id": track.track_id,
        "target_dir": target_dir,
        "short_script": short_script_path,
        "short_voiceover": short_vo_path,
        "long_script": long_script_path,
        "long_voiceover": long_vo_path,
        "route_gpx": gpx_path,
        "route_kml": kml_path,
        "route_geojson": geojson_path,
        "summary": summary_path
    }

if __name__ == '__main__':
    from track_parser import load_all_known_tracks
    tracks = load_all_known_tracks()
    print(f"Generating packages for {len(tracks)} tracks...")
    for t in tracks:
        res = generate_video_package_for_track(t)
        print(f"Generated package for {t.track_id} -> {res['target_dir']}")
