#!/usr/bin/env python3
"""
video_prep.py
Unified Command-Line Interface (CLI) for the Wildlife Video Production Pipeline.

Usage:
  python video_prep.py parse                 # Ingests and parses all local ringing & benchmark datasets
  python video_prep.py generate [--id ID]    # Generates scripts, voiceovers, and map exports (GPX/KML/GeoJSON)
  python video_prep.py status                # Displays tickable progress checklist for all tracks
  python video_prep.py tick <id> <step>      # Ticks off a milestone as completed
  python video_prep.py untick <id> <step>    # Unticks a milestone
  python video_prep.py import <file_path>    # Imports ANY new track (Movebank CSV, GPX, GeoJSON, TXT)
  python video_prep.py serve [--port PORT]   # Launches local web server for video_tracker.html
"""

import os
import sys
import argparse
import webbrowser
import http.server
import socketserver
from typing import Optional

from track_parser import load_all_known_tracks, ingest_any_track, Track
from video_generator import generate_video_package_for_track
from status_manager import StatusManager, PIPELINE_STEPS

def cmd_parse(args):
    print("⏳ Scanning datasets and parsing tracks...")
    tracks = load_all_known_tracks()
    sm = StatusManager()
    sm.sync_tracks(tracks)
    print(f"✅ Successfully ingested {len(tracks)} tracks across all datasets.")
    sm.print_status_table()

def cmd_generate(args):
    print("🎬 Generating video production packages (Short-form, Long-form, GPX, KML, GeoJSON)...")
    tracks = load_all_known_tracks()
    if args.id:
        tracks = [t for t in tracks if t.track_id == args.id]
        if not tracks:
            print(f"❌ Error: Track ID '{args.id}' not found.")
            return

    sm = StatusManager()
    for t in tracks:
        res = generate_video_package_for_track(t)
        print(f"  ✨ [{t.track_id}] {t.common_name} -> {res['target_dir']}")
        
    sm.sync_tracks(tracks, mark_exports_ready=True)
    print(f"\n✅ Finished generating packages for {len(tracks)} track(s).")
    sm.print_status_table()

def cmd_status(args):
    sm = StatusManager()
    if not sm.data["tracks"]:
        print("ℹ️ Database empty. Loading known tracks...")
        tracks = load_all_known_tracks()
        sm.sync_tracks(tracks)
    sm.print_status_table()

def cmd_tick(args):
    sm = StatusManager()
    step = args.step.lower()
    valid_keys = [k for k, _ in PIPELINE_STEPS]
    
    if step not in valid_keys:
        print(f"❌ Invalid step key '{args.step}'. Valid step keys are:")
        for k, desc in PIPELINE_STEPS:
            print(f"   - {k:<20} ({desc})")
        return
        
    success = sm.tick(args.id, step)
    if success:
        print(f"✅ Ticked '{step}' as COMPLETE for [{args.id}].")
        sm.print_status_table()
    else:
        print(f"❌ Could not find track ID '{args.id}'.")

def cmd_untick(args):
    sm = StatusManager()
    step = args.step.lower()
    success = sm.untick(args.id, step)
    if success:
        print(f"⬜ Unticked '{step}' for [{args.id}].")
        sm.print_status_table()
    else:
        print(f"❌ Could not find track ID '{args.id}' or step '{step}'.")

def cmd_import(args):
    filepath = args.file_path
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
        
    print(f"📥 Ingesting new track from '{filepath}'...")
    imported_tracks = ingest_any_track(filepath)
    if not imported_tracks:
        print(f"❌ Could not parse any valid tracks from {filepath}.")
        return
        
    print(f"✅ Extracted {len(imported_tracks)} track(s):")
    sm = StatusManager()
    for t in imported_tracks:
        print(f"  - [{t.track_id}] {t.common_name} ({t.animal_id}): {len(t.waypoints)} waypoints, {t.total_distance_km} km")
        # Automatically generate video package
        res = generate_video_package_for_track(t)
        print(f"    Generated assets in: {res['target_dir']}")
        
    sm.sync_tracks(imported_tracks, mark_exports_ready=True)
    print("\n✅ New track(s) imported and added to the tickable tracking database!")
    sm.print_status_table()

def cmd_serve(args):
    port = args.port
    print(f"🌐 Launching Wildlife Video Studio Dashboard at http://localhost:{port}/video_tracker.html")
    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
            
    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}/video_tracker.html"
        print(f"🚀 Server running on port {port}. Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")

def main():
    parser = argparse.ArgumentParser(description="Wildlife Migration Video Production Pipeline & Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # parse
    sub_parse = subparsers.add_parser("parse", help="Ingest and parse all datasets")
    sub_parse.set_defaults(func=cmd_parse)
    
    # generate
    sub_gen = subparsers.add_parser("generate", help="Generate scripts, voiceovers, and map files")
    sub_gen.add_argument("--id", help="Optional specific track ID to generate")
    sub_gen.set_defaults(func=cmd_generate)
    
    # status
    sub_status = subparsers.add_parser("status", help="Show tickable completion progress table")
    sub_status.set_defaults(func=cmd_status)
    
    # tick
    sub_tick = subparsers.add_parser("tick", help="Tick a step as complete")
    sub_tick.add_argument("id", help="Track ID")
    sub_tick.add_argument("step", help="Step key (e.g. voiceover_ready, video_assembled)")
    sub_tick.set_defaults(func=cmd_tick)
    
    # untick
    sub_untick = subparsers.add_parser("untick", help="Untick a step")
    sub_untick.add_argument("id", help="Track ID")
    sub_untick.add_argument("step", help="Step key")
    sub_untick.set_defaults(func=cmd_untick)
    
    # import
    sub_import = subparsers.add_parser("import", help="Import ANY new track file (CSV, GPX, GeoJSON, TXT)")
    sub_import.add_argument("file_path", help="Path to file")
    sub_import.set_defaults(func=cmd_import)
    
    # serve
    sub_serve = subparsers.add_parser("serve", help="Launch interactive web dashboard")
    sub_serve.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    sub_serve.set_defaults(func=cmd_serve)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
