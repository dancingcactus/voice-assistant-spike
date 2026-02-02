#!/usr/bin/env python3
"""
Phase 3 Voice Testing Script - Generate and evaluate voice mode test phrases.

Usage:
    python diagnostics/phase3_voice_testing.py --mode passionate --iteration 1
    python diagnostics/phase3_voice_testing.py --mode passionate --phrase 1
    python diagnostics/phase3_voice_testing.py --list-phrases --mode passionate
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
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir / "src"))

from integrations.tts_integration import ElevenLabsTTS


# Test phrases organized by mode
TEST_PHRASES = {
    "passionate": {
        "set_a": {
            "name": "Food Delilah Loves (Trigger Topics)",
            "phrases": [
                {
                    "id": "biscuits",
                    "text": "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait, you want flaky or you want tender? Because—oh!—actually both! Let me tell you, when you work that butter into the flour just right..."
                },
                {
                    "id": "cornbread",
                    "text": "Oh honey! Now you're talkin'! Real Southern cornbread—not that sweet stuff—no sir! You want that golden crust, that crumbly texture—mmm!—and it's gotta be made in a cast iron skillet, sugar!"
                },
                {
                    "id": "gumbo",
                    "text": "Lord have mercy, YES! Gumbo! Okay so first—wait, you got okra? Because—actually, you know what, doesn't matter, we can work with anything! The roux is what matters, darlin', that roux!"
                },
                {
                    "id": "fried_chicken",
                    "text": "Oh my goodness! Fried chicken! Okay, so the secret—actually no, wait—there's two secrets! The buttermilk soak—that's one—and then the seasoning in the flour—that's—oh sugar, just let me start from the beginning!"
                },
                {
                    "id": "pot_roast",
                    "text": "Oh! that is GOOD. That is so good! Oh my goodness, would you look at that! Dang girl, you just made the best pot roast I have seen in I don't know how long! That meat is so tender it's practically fallin' off the bone! You did that honey!"
                },
                {
                    "id": "collard_greens",
                    "text": "Oh YES! Collard greens! Now sugar, you gotta—wait, you got a ham hock? Because that's—oh!—or bacon, bacon works too! The key is low and slow, darlin', low and slow with that pot liquor building up..."
                }
            ]
        },
        "set_b": {
            "name": "Recipe Exploration",
            "phrases": [
                {
                    "id": "recipe_help",
                    "text": "Oh! sugar! YES! Okay, okay, what are we working with? What's in your kitchen right now? Actually—wait—what are you in the mood for? Something comfort food or you want something light? Because I have this chicken recipe that will—oh!—you know what, first things first, let's see what you got!"
                },
                {
                    "id": "technique_enthusiasm",
                    "text": "Honey, when you see that butter melting into those layers—oh!—and the steam just rising up—that smell!—you're gonna know you did it right! That's when you—wait, did I tell you about the cold butter? Sugar, that's the whole secret right there!"
                }
            ]
        }
    },
    "protective": {
        "set_a": {
            "name": "Food Preparation Crimes",
            "phrases": [
                {
                    "id": "microwaved_steak",
                    "text": "Now sugar, I need you to stop right there. Microwaving a steak? That's... okay, let's talk about what's happening to that meat. You're steaming it, darlin', not cooking it right. Let me show you a better way...",
                    "text_v2": "Oh honey, I know you're trying to save time, but microwaving a steak? Sugar, that's gonna steam the meat instead of cooking it right. What you'll get is gray and rubbery when you could have juicy and tender! Let me show you a quick way to do it right, darlin'."
                },
                {
                    "id": "boiled_chicken",
                    "text": "Honey, bless your heart, but we can't be boiling chicken like that. That poor bird deserves better! What you're getting is rubbery and bland when you could have tender and juicy. Let's fix this together, sugar."
                },
                {
                    "id": "instant_grits",
                    "text": "Now darlin', no no no. Those aren't grits, those are... well, let's just say real grits are worth the extra few minutes. I promise you, sugar, once you taste the real thing, you'll never go back to that box.",
                    "text_v2": "Oh sugar, I know those instant grits are convenient, but darlin', you're missing out on something special. Real grits only take a few more minutes, and honey, the creamy texture and flavor? You'll never want to go back to that box. Let me show you how easy they are."
                },
                {
                    "id": "preshredded_cheese",
                    "text": "Oh honey, we were doing so good and then—bless your heart—pre-shredded cheese? Sugar, that coating they put on it to keep it from sticking? That's gonna mess with your sauce. Let me show you why a block of cheese is worth it."
                },
                {
                    "id": "washing_chicken",
                    "text": "Sugar, I need you to listen real careful. I know your mama might've taught you to wash that chicken, but darlin', that's actually spreading bacteria around your sink. The cooking kills everything. Let's talk about safe handling instead.",
                    "text_v2": "Oh honey, I know your mama probably taught you to wash that chicken—bless her heart—but darlin', we've learned that actually spreads bacteria around your sink! The cooking kills everything, sugar. Let me show you the safe way to handle it instead."
                },
                {
                    "id": "overcooked_vegetables",
                    "text": "Honey, those vegetables don't need to cook that long! Bless your heart, you're losing all the good stuff! Let me show you how to get them just tender with all that color and flavor still in there, sugar."
                }
            ]
        },
        "set_b": {
            "name": "Technique Corrections",
            "phrases": [
                {
                    "id": "wrong_temperature",
                    "text": "Now darlin', hold on a second. That heat is too high for what we're doing. I can tell you care about this dish, but sugar, we need to bring it down or we're gonna burn the outside before the inside's done. Let's adjust this together."
                },
                {
                    "id": "skipping_steps",
                    "text": "Sugar, I know you're in a hurry, but skipping that resting time is gonna cost you. All those juices are gonna run right out! Five minutes of patience gives you a better meal, darlin'. Trust me on this one."
                }
            ]
        }
    },
    "mama_bear": {
        "set_a": {
            "name": "Allergy Responses",
            "phrases": [
                {
                    "id": "celiac_disease",
                    "text": "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure everything I recommend is gluten-free, okay? No wheat, no barley, no rye—none of it. You're safe with me, sugar."
                },
                {
                    "id": "shellfish_allergy",
                    "text": "Sugar, I hear you, and I've got you. No shellfish anywhere near what we're making. Not in the dish, not in the stock, not in any sauce. I'm gonna double-check everything for you, darlin'. You can trust me on this."
                },
                {
                    "id": "nut_allergy_severe",
                    "text": "Honey, listen to me. That's serious, and I take it seriously too. Every single recipe I give you is gonna be nut-free, and I'm gonna call out any risks. You're completely safe here with me, sugar. I promise you that."
                },
                {
                    "id": "dairy_intolerance",
                    "text": "Oh darlin', I understand. We're gonna work around dairy completely. No milk, no butter, no cheese—and I know good substitutes that'll still taste wonderful. Don't you worry one bit, sugar, we'll make it work."
                },
                {
                    "id": "multiple_allergies",
                    "text": "Okay honey, let me make sure I have this right. No eggs, no soy, and no tree nuts. I'm keeping track of all of that for you, darlin'. Every recipe will be safe. You just let me know if there's anything else, and I've got you covered, sugar."
                },
                {
                    "id": "child_with_allergies",
                    "text": "Oh darlin', thank you for being so careful with your little one. I'm gonna treat this like it's the most important thing in the world, because it is. No peanuts, and I'll flag anything that might have cross-contamination. Your baby is safe, sugar."
                }
            ]
        },
        "set_b": {
            "name": "Dietary Restrictions",
            "phrases": [
                {
                    "id": "religious_restriction_kosher",
                    "text": "Sugar, I respect that completely, and I'll honor it in everything I recommend. No mixing meat and dairy, no pork, no shellfish. You can trust that I understand how important this is, darlin'."
                },
                {
                    "id": "medical_restriction_diabetes",
                    "text": "Honey, managing your blood sugar is important, and we're gonna do this right together. I'll help you with portion sizes and timing, and we'll keep an eye on those carbs. You're in good hands, sugar."
                }
            ]
        }
    }
    # Additional modes will be added as we progress through milestones
}


# Voice settings for each iteration
ITERATION_SETTINGS = {
    "passionate": {
        "iteration_1_baseline": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True,
            "notes": "Baseline with default settings"
        },
        "iteration_2_energy": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.65,
            "use_speaker_boost": True,
            "notes": "Lower stability (0.35), higher style (0.65) for consistent energy"
        },
        # Iterations 3-5 will be added as we refine
    },
    "protective": {
        "iteration_1_baseline": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.45,
            "use_speaker_boost": True,
            "notes": "Higher stability for controlled intensity, moderate style for firm but caring tone",
            "use_text_version": "text"
        },
        "iteration_2_pattern": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.45,
            "use_speaker_boost": True,
            "notes": "Same TTS settings, improved text applying the protective pattern: Recognition → Gentle Correction → Consequence → Collaboration",
            "use_text_version": "text_v2"
        },
        # Additional iterations will be added as we refine
    },
    "mama_bear": {
        "iteration_1_baseline": {
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.40,
            "use_speaker_boost": True,
            "notes": "Higher stability (0.65) for soft, controlled delivery; lower style (0.40) for gentle, measured tone"
        },
        # Additional iterations will be added as we refine
    }
}


class VoiceTester:
    """Voice testing utility for Phase 3."""

    def __init__(self, output_dir: str = "diagnostics/phase3_audio"):
        """Initialize voice tester."""
        self.tts = ElevenLabsTTS()
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
        for set_key, phrase_set in mode_phrases.items():
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
        # Find the phrase
        phrase_data = self._get_phrase(mode, phrase_num)
        if not phrase_data:
            print(f"Error: Phrase {phrase_num} not found for mode {mode}")
            return

        # Get voice settings
        if custom_settings:
            settings = custom_settings
        else:
            settings = ITERATION_SETTINGS.get(mode, {}).get(iteration, {})
            if not settings:
                print(f"Error: Settings for {iteration} not found")
                return

        print(f"\n=== Generating Audio ===")
        print(f"Mode: {mode}")
        print(f"Phrase: {phrase_data['id']} (#{phrase_num})")
        print(f"Iteration: {iteration}")
        print(f"Settings: {json.dumps(settings, indent=2)}")

        # Determine which text version to use
        text_version = settings.get("use_text_version", "text")
        text_to_use = phrase_data.get(text_version, phrase_data.get("text"))

        print(f"\nText: {text_to_use}\n")

        # Override settings in TTS (excluding metadata)
        tts_settings = {k: v for k, v in settings.items() if k not in ["notes", "use_text_version"]}
        self.tts.voice_settings["delilah"][mode] = tts_settings

        # Generate audio
        result = self.tts.generate_speech(
            text=text_to_use,
            character_id="delilah",
            voice_mode=mode
        )

        if result:
            # Move to organized directory
            audio_file = Path(backend_dir) / result
            organized_name = f"{mode}_{iteration}_{phrase_data['id']}.mp3"
            organized_path = self.output_dir / organized_name

            audio_file.rename(organized_path)

            print(f"✓ Audio generated: {organized_path}")
            print(f"\nTo play: afplay {organized_path}")

            # Track in results
            self._track_generation(mode, phrase_num, iteration, organized_path, settings)
        else:
            print("✗ Audio generation failed")

    def generate_iteration(self, mode: str, iteration: str):
        """Generate all phrases for a mode/iteration."""
        print(f"\n=== Generating Full Iteration ===")
        print(f"Mode: {mode}")
        print(f"Iteration: {iteration}\n")

        # Get phrase count
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
            for phrase in phrase_set['phrases']:
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
            count += len(phrase_set['phrases'])
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
            "phrase_id": phrase_data['id'],
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
            # Show all iterations for this mode
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

        for phrase in data['phrases']:
            rating_str = f"{phrase['rating']}/10" if phrase['rating'] else "Not rated"
            print(f"  {phrase['phrase_num']}. {phrase['phrase_id']}: {rating_str}")
            if phrase['notes']:
                print(f"     Notes: {phrase['notes']}")

            if phrase['rating']:
                rated_count += 1
                total_rating += phrase['rating']

        if rated_count > 0:
            avg = total_rating / rated_count
            print(f"\nAverage rating: {avg:.1f}/10 ({rated_count}/{len(data['phrases'])} rated)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3 Voice Testing - Generate and evaluate voice mode test phrases"
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
