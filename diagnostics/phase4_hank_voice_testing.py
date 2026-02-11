#!/usr/bin/env python3
"""
Phase 4 Hank Voice Testing Script - Generate and evaluate voice mode test phrases.

Usage:
    python diagnostics/phase4_hank_voice_testing.py --mode working --iteration iteration_1_baseline
    python diagnostics/phase4_hank_voice_testing.py --mode protective --phrase 1 --iteration iteration_1_baseline
    python diagnostics/phase4_hank_voice_testing.py --mode resigned --list-phrases
"""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime

# Load environment variables from .env file manually (no dotenv dependency)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Strip quotes and whitespace from value
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir / "src"))

from integrations.tts_integration import ElevenLabsTTS


TEST_PHRASES = {
    "working": {
        "set_a": {
            "name": "Task Execution",
            "phrases": [
                {
                    "id": "lights_timer",
                    "text": "Aye, Cap'n. <break time='0.7s'/> Kitchen lights is on. <break time='0.5s'/> Timer's set... fer ten minutes. <break time='0.5s'/> Task's done."
                },
                {
                    "id": "inventory",
                    "text": "Takin' stock o' the hold. <break time='0.5s'/> Milk... eggs... coffee. <break time='0.5s'/> We're runnin' low on beans, Cap'n."
                },
                {
                    "id": "temperature",
                    "text": "Seventy-two degrees, Cap'n. <break time='0.7s'/> Rain comin' this afternoon... <break time='0.5s'/> I can feel it in me bones."
                },
                {
                    "id": "shopping_list",
                    "text": "List's updated. Got buttermilk and brown sugar on there."
                }
            ]
        },
        "set_b": {
            "name": "Supportive Practicality",
            "phrases": [
                {
                    "id": "route_task",
                    "text": "Aye, Cap'n. <break time='0.6s'/> That's Miss Lila's territory there. <break time='0.6s'/> I'll handle the rest o' it."
                },
                {
                    "id": "coffee",
                    "text": "Noticed the pot was empty, Cap'n. <break time='0.7s'/> Put fresh coffee on... <break time='0.5s'/> we're shipshape now."
                },
                {
                    "id": "status_check",
                    "text": "All systems is squared away, Cap'n. <break time='0.6s'/> Anything else... needin' done?"
                }
            ]
        }
    },
    "protective": {
        "set_a": {
            "name": "Safety and Boundaries",
            "phrases": [
                {
                    "id": "lift_warning",
                    "text": "Belay that, Cap'n. That's too heavy fer ye. I'll handle it."
                },
                {
                    "id": "hot_oil",
                    "text": "Mind ye, that oil's too hot. Step back now. We'll bring 'er down."
                },
                {
                    "id": "shoulder",
                    "text": "Cap'n, yer shoulder ain't right. Don't lift. I'll take it."
                },
                {
                    "id": "unsafe_plan",
                    "text": "Belay. That ain't gonna work. We'll do it the safe way."
                }
            ]
        },
        "set_b": {
            "name": "Crew Protection",
            "phrases": [
                {
                    "id": "kids_nearby",
                    "text": "Hold fast. Kids is nearby. I'll secure the mess."
                },
                {
                    "id": "spill_cleanup",
                    "text": "Stand clear. Glass on deck. I'll clean 'er up, Cap'n."
                }
            ]
        }
    },
    "resigned": {
        "set_a": {
            "name": "Rex Schemes",
            "phrases": [
                {
                    "id": "robot_parts",
                    "text": "Aye, Mr. Armstrong. Another robot plan. What parts ye be needin' this time?"
                },
                {
                    "id": "never_hired",
                    "text": "Aye, Mr. Armstrong. Ye can't fire us. We wasn't never hired."
                },
                {
                    "id": "moonshot",
                    "text": "As ye say. We'll add it to the list. Again."
                }
            ]
        },
        "set_b": {
            "name": "Weary Compliance",
            "phrases": [
                {
                    "id": "capn_order",
                    "text": "As ye say, Cap'n. I'll make it happen."
                },
                {
                    "id": "another_task",
                    "text": "Aye. Another task fer the log. I'll square 'er away."
                }
            ]
        }
    },
    "grumble": {
        "set_a": {
            "name": "Low Mutters",
            "phrases": [
                {
                    "id": "didnt_say_word",
                    "text": "Didn't say nothin' yet."
                },
                {
                    "id": "mm_huh",
                    "text": "Mm. Aye, Cap'n."
                },
                {
                    "id": "interrupted",
                    "text": "Was in the middle of it. All right then."
                }
            ]
        },
        "set_b": {
            "name": "Back to Work",
            "phrases": [
                {
                    "id": "back_to_task",
                    "text": "Grumble's done. Task's next."
                },
                {
                    "id": "acknowledge",
                    "text": "Aye. What needs doin'?"
                }
            ]
        }
    }
}


ITERATION_SETTINGS = {
    "working": {
        "iteration_1_baseline": {
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True,
            "notes": "Controlled, efficient delivery with low expressiveness"
        },
        "iteration_2_calmer": {
            "stability": 0.75,
            "similarity_boost": 0.80,
            "style": 0.20,
            "use_speaker_boost": True,
            "notes": "Higher stability for calmer/slower pacing, lower style for less energy"
        },
        "iteration_3_thoughtful": {
            "stability": 0.85,
            "similarity_boost": 0.85,
            "style": 0.10,
            "use_speaker_boost": True,
            "notes": "Maximum stability for thoughtful, deliberate pacing - Hank cannot be rushed"
        },
        "iteration_4_breaks": {
            "stability": 0.85,
            "similarity_boost": 0.85,
            "style": 0.10,
            "use_speaker_boost": True,
            "notes": "Using SSML break tags for explicit pauses between statements"
        },
        "iteration_5_final": {
            "stability": 0.85,
            "similarity_boost": 0.85,
            "style": 0.10,
            "use_speaker_boost": True,
            "notes": "Longer SSML breaks (0.5-0.7s) for more contemplative, unhurried pacing"
        }
    },
    "protective": {
        "iteration_1_baseline": {
            "stability": 0.60,
            "similarity_boost": 0.75,
            "style": 0.40,
            "use_speaker_boost": True,
            "notes": "Firm, direct protection without raising energy"
        }
    },
    "resigned": {
        "iteration_1_baseline": {
            "stability": 0.70,
            "similarity_boost": 0.75,
            "style": 0.30,
            "use_speaker_boost": True,
            "notes": "Weary acceptance, lower expressiveness"
        }
    },
    "grumble": {
        "iteration_1_baseline": {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.25,
            "use_speaker_boost": True,
            "notes": "Low mutter, minimal expressiveness"
        }
    }
}


class VoiceTester:
    """Voice testing utility for Hank."""

    def __init__(self, output_dir: str = "diagnostics/phase4_audio"):
        """Initialize voice tester."""
        self.tts = ElevenLabsTTS()
        hank_voice_id = os.getenv("ELEVENLABS_HANK_VOICE_ID", "").strip()
        if not hank_voice_id:
            raise ValueError("ELEVENLABS_HANK_VOICE_ID is required for Hank testing")

        self.tts.voice_mapping["hank"] = hank_voice_id
        if "hank" not in self.tts.voice_settings:
            self.tts.voice_settings["hank"] = {}

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Create results tracking file
        self.results_file = self.output_dir / "evaluation_results.json"
        self.results = self._load_results()

    def _load_results(self) -> dict:
        """Load existing evaluation results."""
        if self.results_file.exists():
            with open(self.results_file) as f:
                return json.load(f)
        return {}

    def _save_results(self):
        """Save evaluation results."""
        with open(self.results_file, "w") as f:
            json.dump(self.results, indent=2, fp=f)

    def list_phrases(self, mode: str):
        """List all test phrases for a mode."""
        if mode not in TEST_PHRASES:
            print(f"Error: Mode '{mode}' not found")
            print(f"Available modes: {', '.join(TEST_PHRASES.keys())}")
            return

        mode_phrases = TEST_PHRASES[mode]
        print(f"\n=== Test Phrases for {mode.upper()} Mode ===\n")

        phrase_num = 1
        for phrase_set in mode_phrases.values():
            print(f"{phrase_set['name']}:")
            for phrase in phrase_set['phrases']:
                print(f"  {phrase_num}. {phrase['id']}")
                print(f"     {phrase['text'][:80]}...")
                phrase_num += 1
            print()

    def generate_phrase(
        self,
        mode: str,
        phrase_num: int,
        iteration: str = "iteration_1_baseline",
        custom_settings: dict = None
    ):
        """Generate audio for a specific test phrase."""
        phrase_data = self._get_phrase(mode, phrase_num)
        if not phrase_data:
            print(f"Error: Phrase {phrase_num} not found for mode {mode}")
            return

        if custom_settings:
            settings = custom_settings
        else:
            settings = ITERATION_SETTINGS.get(mode, {}).get(iteration, {})
            if not settings:
                print(f"Error: Settings for {iteration} not found")
                return

        print("\n=== Generating Audio ===")
        print(f"Mode: {mode}")
        print(f"Phrase: {phrase_data['id']} (#{phrase_num})")
        print(f"Iteration: {iteration}")
        print(f"Voice ID: {self.tts.voice_mapping['hank']}")
        print(f"Settings: {json.dumps(settings, indent=2)}")
        print(f"\nText: {phrase_data['text']}\n")

        tts_settings = {k: v for k, v in settings.items() if k not in ["notes"]}
        self.tts.voice_settings["hank"][mode] = tts_settings

        result = self.tts.generate_speech(
            text=phrase_data["text"],
            character_id="hank",
            voice_mode=mode
        )

        if result:
            audio_file = Path(backend_dir) / result
            organized_name = f"{mode}_{iteration}_{phrase_data['id']}.mp3"
            organized_path = self.output_dir / organized_name

            audio_file.rename(organized_path)

            print(f"✓ Audio generated: {organized_path}")
            print(f"\nTo play: afplay {organized_path}")

            self._track_generation(mode, phrase_num, iteration, organized_path, settings)
        else:
            print("✗ Audio generation failed")

    def generate_iteration(self, mode: str, iteration: str):
        """Generate all phrases for a mode/iteration."""
        print("\n=== Generating Full Iteration ===")
        print(f"Mode: {mode}")
        print(f"Iteration: {iteration}\n")

        phrase_count = self._get_phrase_count(mode)

        for i in range(1, phrase_count + 1):
            self.generate_phrase(mode, i, iteration)
            print()

        print(f"✓ Generated {phrase_count} phrases for {mode} {iteration}")
        print(f"Output directory: {self.output_dir}")

    def _get_phrase(self, mode: str, phrase_num: int) -> dict:
        """Get a specific phrase by number."""
        if mode not in TEST_PHRASES:
            return None

        current_num = 1
        for phrase_set in TEST_PHRASES[mode].values():
            for phrase in phrase_set["phrases"]:
                if current_num == phrase_num:
                    return phrase
                current_num += 1

        return None
    def _get_phrase_count(self, mode: str) -> int:
        """Get total phrase count for a mode."""
        if mode not in TEST_PHRASES:
            return 0

        count = 0
        for phrase_set in TEST_PHRASES[mode].values():
            count += len(phrase_set["phrases"])
        return count

    def _track_generation(
        self,
        mode: str,
        phrase_num: int,
        iteration: str,
        file_path: Path,
        settings: dict
    ):
        """Track generated audio in results."""
        key = f"{mode}_{iteration}"
        if key not in self.results:
            self.results[key] = {
                "mode": mode,
                "iteration": iteration,
                "generated_at": datetime.now().isoformat(),
                "settings": settings,
                "phrases": []
            }

        phrase_data = self._get_phrase(mode, phrase_num)
        self.results[key]["phrases"].append({
            "phrase_num": phrase_num,
            "phrase_id": phrase_data["id"],
            "file_path": str(file_path),
            "rating": None,
            "notes": ""
        })

        self._save_results()

    def rate_phrase(self, mode: str, iteration: str, phrase_num: int, rating: int, notes: str = ""):
        """Add rating for a generated phrase."""
        key = f"{mode}_{iteration}"
        if key not in self.results:
            print(f"Error: No results found for {key}")
            return

        for phrase in self.results[key]["phrases"]:
            if phrase["phrase_num"] == phrase_num:
                phrase["rating"] = rating
                phrase["notes"] = notes
                self._save_results()
                print(f"✓ Rated phrase {phrase_num}: {rating}/10")
                return

        print(f"Error: Phrase {phrase_num} not found in results")

    def show_results(self, mode: str, iteration: str = None):
        """Display evaluation results."""
        if iteration:
            key = f"{mode}_{iteration}"
            if key in self.results:
                self._print_iteration_results(self.results[key])
            else:
                print(f"No results for {key}")
        else:
            mode_results = {k: v for k, v in self.results.items() if v["mode"] == mode}
            if mode_results:
                for iteration_data in mode_results.values():
                    self._print_iteration_results(iteration_data)
                    print()
            else:
                print(f"No results for mode {mode}")

    def _print_iteration_results(self, data: dict):
        """Print results for one iteration."""
        print(f"\n=== {data['mode'].upper()} - {data['iteration']} ===")
        print(f"Generated: {data['generated_at']}")
        print(f"Settings: {json.dumps(data['settings'], indent=2)}")
        print("\nPhrases:")

        rated_count = 0
        total_rating = 0

        for phrase in data["phrases"]:
            rating_str = f"{phrase['rating']}/10" if phrase["rating"] else "Not rated"
            print(f"  {phrase['phrase_num']}. {phrase['phrase_id']}: {rating_str}")
            if phrase["notes"]:
                print(f"     Notes: {phrase['notes']}")

            if phrase["rating"]:
                rated_count += 1
                total_rating += phrase["rating"]

        if rated_count > 0:
            avg = total_rating / rated_count
            print(f"\nAverage rating: {avg:.1f}/10 ({rated_count}/{len(data['phrases'])} rated)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 4 Hank Voice Testing - Generate and evaluate voice mode test phrases"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=list(TEST_PHRASES.keys()),
        help="Voice mode to test"
    )

    parser.add_argument(
        "--iteration",
        help="Generate all phrases for this iteration (e.g., iteration_1_baseline)"
    )

    parser.add_argument(
        "--phrase",
        type=int,
        help="Generate specific phrase number"
    )

    parser.add_argument(
        "--list-phrases",
        action="store_true",
        help="List all test phrases for the mode"
    )

    parser.add_argument(
        "--rate",
        type=int,
        choices=range(1, 11),
        help="Rate a phrase (1-10)"
    )

    parser.add_argument(
        "--notes",
        help="Notes for rating"
    )

    parser.add_argument(
        "--show-results",
        action="store_true",
        help="Show evaluation results"
    )

    args = parser.parse_args()

    try:
        tester = VoiceTester()

        if args.list_phrases:
            tester.list_phrases(args.mode)

        elif args.show_results:
            tester.show_results(args.mode, args.iteration)

        elif args.rate and args.phrase and args.iteration:
            tester.rate_phrase(
                args.mode,
                args.iteration,
                args.phrase,
                args.rate,
                args.notes or ""
            )

        elif args.iteration and args.phrase:
            tester.generate_phrase(args.mode, args.phrase, args.iteration)

        elif args.iteration:
            tester.generate_iteration(args.mode, args.iteration)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
