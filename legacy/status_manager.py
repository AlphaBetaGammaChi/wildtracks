#!/usr/bin/env python3
"""
status_manager.py
Persistent tracking & checklist database for video production workflows.
Manages tracks_status.json with tickable milestones for each animal track.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from track_parser import Track

STATUS_FILE = "video_production/tracks_status.json"

PIPELINE_STEPS = [
    ("data_parsed", "Data Parsed & Validated"),
    ("map_exported", "GPX/KML/GeoJSON Exported"),
    ("short_script_ready", "Short-Form Script Ready"),
    ("long_script_ready", "Long-Form Script Ready"),
    ("voiceover_ready", "Voiceover Audio Generated (ElevenLabs)"),
    ("map_rendered", "3D Map Animation Rendered (TravelBoast/Earth Studio)"),
    ("video_assembled", "Final Video Edited & Captioned"),
    ("published_shorts", "Published on Shorts/TikTok"),
    ("published_long", "Published on YouTube Long-Form"),
    ("monetized", "Monetization & Analytics Logged")
]

class StatusManager:
    def __init__(self, filepath: str = STATUS_FILE):
        self.filepath = filepath
        self.data: Dict[str, Any] = {"tracks": {}, "last_updated": ""}
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not read {self.filepath}, starting fresh: {e}")
                self.data = {"tracks": {}, "last_updated": ""}
        else:
            self.data = {"tracks": {}, "last_updated": ""}

    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def sync_tracks(self, tracks: List[Track], mark_exports_ready: bool = False):
        """Synchronizes tracked animals with the database, preserving any user-ticked progress."""
        for t in tracks:
            tid = t.track_id
            if tid not in self.data["tracks"]:
                # Initialize new track record
                self.data["tracks"][tid] = {
                    "track_id": tid,
                    "common_name": t.common_name,
                    "scientific_name": t.scientific_name,
                    "display_id": getattr(t, 'display_id', t.animal_id),
                    "animal_id": t.animal_id,
                    "category": t.category,
                    "dataset_source": t.dataset_source,
                    "total_distance_km": t.total_distance_km,
                    "total_duration_days": t.total_duration_days,
                    "waypoints_count": len(t.waypoints),
                    "record_highlight": t.record_highlight,
                    "steps": {step_key: False for step_key, _ in PIPELINE_STEPS},
                    "notes": "",
                    "created_at": datetime.now().isoformat()
                }
            
            rec = self.data["tracks"][tid]
            # Update basic metadata
            rec["common_name"] = t.common_name
            rec["display_id"] = getattr(t, 'display_id', t.animal_id)
            rec["total_distance_km"] = t.total_distance_km
            rec["total_duration_days"] = t.total_duration_days
            rec["waypoints_count"] = len(t.waypoints)
            rec["record_highlight"] = t.record_highlight
            
            # Auto-tick data_parsed if valid waypoints exist
            if len(t.waypoints) >= 2:
                rec["steps"]["data_parsed"] = True
            if mark_exports_ready:
                rec["steps"]["map_exported"] = True
                rec["steps"]["short_script_ready"] = True
                rec["steps"]["long_script_ready"] = True
                
        self.save()

    def tick(self, track_id: str, step_key: str) -> bool:
        """Ticks off a step as complete."""
        if track_id in self.data["tracks"]:
            if step_key in self.data["tracks"][track_id]["steps"]:
                self.data["tracks"][track_id]["steps"][step_key] = True
                self.save()
                return True
        return False

    def untick(self, track_id: str, step_key: str) -> bool:
        """Unticks a step."""
        if track_id in self.data["tracks"]:
            if step_key in self.data["tracks"][track_id]["steps"]:
                self.data["tracks"][track_id]["steps"][step_key] = False
                self.save()
                return True
        return False

    def set_notes(self, track_id: str, notes: str):
        if track_id in self.data["tracks"]:
            self.data["tracks"][track_id]["notes"] = notes
            self.save()

    def get_progress(self, track_id: str) -> (int, int, float):
        """Returns (completed_steps, total_steps, percentage)."""
        if track_id not in self.data["tracks"]:
            return 0, len(PIPELINE_STEPS), 0.0
        steps = self.data["tracks"][track_id]["steps"]
        completed = sum(1 for v in steps.values() if v)
        total = len(PIPELINE_STEPS)
        pct = round((completed / total) * 100.0, 1)
        return completed, total, pct

    def get_overall_stats(self) -> Dict[str, Any]:
        tracks = list(self.data["tracks"].values())
        total_tracks = len(tracks)
        if total_tracks == 0:
            return {"total_tracks": 0, "total_km": 0, "overall_pct": 0, "published": 0}
            
        total_km = sum(t.get("total_distance_km", 0) for t in tracks)
        all_completed = 0
        all_possible = total_tracks * len(PIPELINE_STEPS)
        published_count = 0
        
        for t in tracks:
            steps = t.get("steps", {})
            all_completed += sum(1 for v in steps.values() if v)
            if steps.get("published_shorts") or steps.get("published_long"):
                published_count += 1
                
        pct = round((all_completed / max(1, all_possible)) * 100.0, 1)
        return {
            "total_tracks": total_tracks,
            "total_km": round(total_km, 1),
            "overall_pct": pct,
            "published": published_count
        }

    def print_status_table(self):
        """Prints an attractive CLI table showing tickable completion for all tracks."""
        stats = self.get_overall_stats()
        print("\n" + "=" * 95)
        print(f" 🦅 WILDLIFE TRACK VIDEO PRODUCTION PIPELINE | OVERALL PROGRESS: {stats['overall_pct']}% ")
        print(f" Tracks: {stats['total_tracks']} | Total Migration Distance: {stats['total_km']:,} km | Published: {stats['published']}")
        print("=" * 95)
        
        # Header
        hdr = f"{'Track ID':<22} | {'Subject':<24} | {'Dist (km)':<9} | {'Progress':<12} | Checkpoints"
        print(hdr)
        print("-" * 95)
        
        for tid, t in sorted(self.data["tracks"].items()):
            comp, tot, pct = self.get_progress(tid)
            subj = f"{t.get('common_name', '')} ({t.get('display_id', '')})"[:24]
            dist = f"{int(t.get('total_distance_km', 0)):,}"
            bar_len = int(comp / tot * 8)
            bar = "█" * bar_len + "░" * (8 - bar_len)
            prog_str = f"[{bar}] {comp}/{tot}"
            
            # Compact symbols for 10 steps
            # 1: Data, 2: Map, 3: Short, 4: Long, 5: Voice, 6: Anim, 7: Edit, 8: Shorts, 9: LongPub, 10: $
            step_icons = []
            steps = t.get("steps", {})
            keys = [k for k, _ in PIPELINE_STEPS]
            for k in keys:
                step_icons.append("✅" if steps.get(k) else "⬜")
            icons_str = "".join(step_icons)
            
            print(f"{tid:<22} | {subj:<24} | {dist:<9} | {prog_str:<12} | {icons_str}")
            
        print("-" * 95)
        print("Legend: [1:Parsed 2:MapExport 3:ShortScript 4:LongScript 5:Voiceover 6:3DMap 7:VideoEdit 8:Shorts 9:LongPub 10:Monetized]")
        print("=" * 95 + "\n")

if __name__ == '__main__':
    from track_parser import load_all_known_tracks
    sm = StatusManager()
    tracks = load_all_known_tracks()
    sm.sync_tracks(tracks, mark_exports_ready=True)
    sm.print_status_table()
