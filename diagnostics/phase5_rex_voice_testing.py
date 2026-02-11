#!/usr/bin/env python3
"""
Phase 5 Rex Voice Testing Skeleton

This diagnostics scaffold matches the Phase 4 Hank workflow and provides a
place to collect Rex-specific test phrases, iteration settings, and a
generation harness. Fill `TEST_PHRASES` and `ITERATION_SETTINGS` then run
the script to generate evaluation artifacts.

Usage examples:
  python diagnostics/phase5_rex_voice_testing.py --mode default --list-phrases
  python diagnostics/phase5_rex_voice_testing.py --mode default --iteration iteration_1_baseline

"""

import argparse
from pathlib import Path
import json
from datetime import datetime
import os
import sys

# Add backend src to path so integrations can be imported when running locally
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir / "src"))

try:
    from integrations.tts_integration import ElevenLabsTTS
except Exception:
    ElevenLabsTTS = None

# Minimal Rex test phrases (populate with real lines later)
TEST_PHRASES = {
    "default": {
        "set_a": {
            "name": "Rex Short Announcements",
            "phrases": [
                {"id": "greeting", "text": "All systems go. Initiating protocol."},
                {"id": "idea", "text": "SCIENCE time. Here's the plan: bigger, louder, faster."}
            ]
        }
    }
}

ITERATION_SETTINGS = {
    "default": {
        "iteration_1_baseline": {
            "stability": 0.6,
            "similarity_boost": 0.7,
            "style": 0.5,
            "use_speaker_boost": True,
            "notes": "Energetic, grandiose delivery; prioritize enthusiasm"
        }
    }
}


class RexVoiceTester:
    """Skeleton tester for Rex voice diagnostics."""

    def __init__(self, output_dir: str = "diagnostics/phase5_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "evaluation_results.json"
        self.results = self._load_results()

        self.tts = None
        if ElevenLabsTTS:
            try:
                self.tts = ElevenLabsTTS()
                rex_voice_id = os.getenv("ELEVENLABS_REX_VOICE_ID", "").strip()
                if rex_voice_id:
                    self.tts.voice_mapping["rex"] = rex_voice_id
            except Exception:
                self.tts = None

    def _load_results(self):
        if self.results_file.exists():
            with open(self.results_file) as f:
                return json.load(f)
        return {}

    def list_phrases(self, mode: str):
        if mode not in TEST_PHRASES:
            print(f"Mode '{mode}' not found")
            return

        for set_name, set_data in TEST_PHRASES[mode].items():
            print(f"{set_data['name']}:")
            for i, phrase in enumerate(set_data['phrases'], start=1):
                print(f"  {i}. {phrase['id']} - {phrase['text']}")


def main():
    parser = argparse.ArgumentParser(description="Phase 5 Rex Voice Testing - Skeleton")
    parser.add_argument("--mode", required=True, choices=list(TEST_PHRASES.keys()))
    parser.add_argument("--list-phrases", action="store_true")
    args = parser.parse_args()

    tester = RexVoiceTester()
    if args.list_phrases:
        tester.list_phrases(args.mode)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
