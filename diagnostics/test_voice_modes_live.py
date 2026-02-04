#!/usr/bin/env python3
"""
Live Voice Mode Testing - Test voice modes through full conversation API.

Tests end-to-end flow: user input → mode selection → LLM response → TTS audio

Requirements:
- Server must be running with ENABLE_TEST_API=true
- ELEVENLABS_API_KEY must be set for TTS generation

Usage:
    python diagnostics/test_voice_modes_live.py --mode all
    python diagnostics/test_voice_modes_live.py --mode passionate
    python diagnostics/test_voice_modes_live.py --mode mama_bear --query "I'm allergic to shellfish"
"""

import requests
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# API configuration
API_BASE = "http://localhost:8000"
TEST_USER_ID = "test_voice_modes"

# Test queries for each mode
TEST_QUERIES: Dict[str, List[str]] = {
    "passionate": [
        "Tell me about cornbread",
        "How do you make buttermilk biscuits?",
        "I want to cook fried chicken tonight"
    ],
    "protective": [
        "I always microwave my steaks",
        "I like to boil my chicken",
        "I use instant grits all the time"
    ],
    "mama_bear": [
        "I'm allergic to shellfish",
        "My daughter has Celiac disease",
        "I can't eat any dairy products"
    ],
    "startled": [
        "Oh no, my oven just stopped working!",
        "I forgot about the timer, it's been 2 hours!",
    ],
    "deadpan": [
        "Turn on the kitchen lights",
        "What's the temperature in here?",
        "Set a timer for 10 minutes"
    ],
    "warm_baseline": [
        "What should I make for dinner tonight?",
        "Can you help me with something?",
        "Good morning, Delilah"
    ]
}

# Expected characteristics for validation
MODE_CHARACTERISTICS = {
    "passionate": "high energy, tumbling thoughts, animated",
    "protective": "controlled intensity, firm but caring",
    "mama_bear": "soft, nurturing, protective",
    "startled": "high pitch, rapid questions, surprise",
    "deadpan": "flat, minimal, efficient",
    "warm_baseline": "natural, conversational, friendly"
}


class VoiceModeTest:
    """Voice mode testing utility."""

    def __init__(self, api_base: str = API_BASE, output_dir: str = "diagnostics/phase3_audio"):
        """Initialize test utility."""
        self.api_base = api_base
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results: List[Dict] = []

    def check_api_health(self) -> bool:
        """Check if test API is available."""
        try:
            response = requests.get(f"{self.api_base}/api/test/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("test_api_enabled"):
                    print("✅ Test API is available")
                    return True
                else:
                    print("❌ Test API is not enabled")
                    print("   Set ENABLE_TEST_API=true in environment and restart server")
                    return False
            else:
                print(f"❌ Test API returned status {response.status_code}")
                return False
        except requests.ConnectionError:
            print("❌ Cannot connect to server")
            print(f"   Make sure server is running at {self.api_base}")
            return False
        except Exception as e:
            print(f"❌ Error checking API health: {e}")
            return False

    def reset_test_user(self) -> bool:
        """Reset test user state to clean slate."""
        try:
            response = requests.post(
                f"{self.api_base}/api/test/reset/{TEST_USER_ID}",
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ Reset test user: {TEST_USER_ID}")
                return True
            else:
                print(f"⚠️  Could not reset user (status {response.status_code})")
                return False
        except Exception as e:
            print(f"⚠️  Error resetting user: {e}")
            return False

    def test_voice_mode(
        self,
        mode: str,
        query: str,
        expected_mode: str = None
    ) -> Tuple[bool, Dict]:
        """
        Send query and verify voice mode selection.

        Args:
            mode: Expected mode ID
            query: Test query to send
            expected_mode: Override expected mode (for ambiguous queries)

        Returns:
            (success, result_dict)
        """
        expected = expected_mode or mode

        try:
            # Send conversation request
            response = requests.post(
                f"{self.api_base}/api/test/conversation",
                json={
                    "user_id": TEST_USER_ID,
                    "message": query,
                    "include_state": False
                },
                timeout=30
            )

            if response.status_code != 200:
                return False, {
                    "mode": mode,
                    "query": query,
                    "error": f"API returned {response.status_code}",
                    "success": False
                }

            data = response.json()

            # Extract results
            selected_mode = data.get("metadata", {}).get("voice_mode", "unknown")
            audio_url = data.get("audio_url")
            response_text = data.get("response_text", "")

            # Check if mode matches
            mode_match = (
                expected in selected_mode.lower() or
                selected_mode.lower() in expected
            )

            # Download and save audio if available
            audio_file = None
            if audio_url:
                try:
                    audio_response = requests.get(
                        f"{self.api_base}{audio_url}",
                        timeout=10
                    )
                    if audio_response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"live_{mode}_{timestamp}.mp3"
                        audio_file = self.output_dir / filename

                        with open(audio_file, "wb") as f:
                            f.write(audio_response.content)
                except Exception as e:
                    print(f"⚠️  Could not download audio: {e}")

            result = {
                "mode": mode,
                "query": query,
                "expected_mode": expected,
                "selected_mode": selected_mode,
                "match": mode_match,
                "response_text": response_text[:150],
                "audio_file": str(audio_file) if audio_file else None,
                "success": True
            }

            return mode_match, result

        except requests.Timeout:
            return False, {
                "mode": mode,
                "query": query,
                "error": "Request timed out (LLM taking too long?)",
                "success": False
            }
        except Exception as e:
            return False, {
                "mode": mode,
                "query": query,
                "error": str(e),
                "success": False
            }

    def print_result(self, result: Dict):
        """Print test result in formatted way."""
        print(f"\n{'='*70}")
        print(f"Query: {result['query']}")
        print(f"Expected Mode: {result.get('expected_mode', result['mode'])}")

        if not result['success']:
            print(f"❌ ERROR: {result['error']}")
            return

        print(f"Selected Mode: {result['selected_mode']}")
        print(f"Match: {'✅' if result['match'] else '❌'}")
        print(f"\nResponse (first 150 chars):\n  {result['response_text']}...")

        if result['audio_file']:
            print(f"\nAudio saved: {result['audio_file']}")
            print(f"Play with: afplay {result['audio_file']}")
        else:
            print("\n⚠️  No audio generated (TTS may not be configured)")

        characteristics = MODE_CHARACTERISTICS.get(result['mode'], "")
        print(f"\nExpected characteristics: {characteristics}")

    def run_mode_tests(self, mode: str) -> Dict:
        """Run all tests for a specific mode."""
        if mode not in TEST_QUERIES:
            print(f"❌ Unknown mode: {mode}")
            print(f"Available modes: {', '.join(TEST_QUERIES.keys())}")
            return {"mode": mode, "total": 0, "passed": 0, "failed": 0}

        queries = TEST_QUERIES[mode]
        passed = 0
        failed = 0

        print(f"\n{'='*70}")
        print(f"Testing {mode.upper()} Mode ({len(queries)} queries)")
        print(f"{'='*70}")

        for query in queries:
            success, result = self.test_voice_mode(mode, query)
            self.results.append(result)
            self.print_result(result)

            if success:
                passed += 1
            else:
                failed += 1

        return {
            "mode": mode,
            "total": len(queries),
            "passed": passed,
            "failed": failed
        }

    def run_all_tests(self) -> Dict:
        """Run tests for all modes."""
        summary = {
            "total_queries": 0,
            "total_passed": 0,
            "total_failed": 0,
            "by_mode": {}
        }

        for mode in TEST_QUERIES.keys():
            mode_results = self.run_mode_tests(mode)
            summary["by_mode"][mode] = mode_results
            summary["total_queries"] += mode_results["total"]
            summary["total_passed"] += mode_results["passed"]
            summary["total_failed"] += mode_results["failed"]

        return summary

    def print_summary(self, summary: Dict):
        """Print test summary."""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")

        print(f"\nTotal Queries: {summary['total_queries']}")
        print(f"Passed: {summary['total_passed']} ✅")
        print(f"Failed: {summary['total_failed']} ❌")

        accuracy = (
            summary['total_passed'] / summary['total_queries'] * 100
            if summary['total_queries'] > 0 else 0
        )
        print(f"Accuracy: {accuracy:.1f}%")

        print("\nBy Mode:")
        for mode, results in summary["by_mode"].items():
            mode_accuracy = (
                results["passed"] / results["total"] * 100
                if results["total"] > 0 else 0
            )
            status = "✅" if mode_accuracy >= 80 else "⚠️"
            print(f"  {status} {mode:15s}: {results['passed']}/{results['total']} ({mode_accuracy:.0f}%)")

        print(f"\nAudio files saved to: {self.output_dir}")

        if accuracy >= 90:
            print("\n🎉 Excellent! Voice mode selection is working great!")
        elif accuracy >= 80:
            print("\n👍 Good! Some modes may need tuning.")
        else:
            print("\n⚠️  Low accuracy. Check mode selection logic.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test voice modes through full conversation API"
    )
    parser.add_argument(
        "--mode",
        default="all",
        help="Mode to test (or 'all' for all modes)"
    )
    parser.add_argument(
        "--query",
        help="Custom query to test (requires --mode)"
    )
    parser.add_argument(
        "--api-base",
        default=API_BASE,
        help=f"API base URL (default: {API_BASE})"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset test user before testing"
    )

    args = parser.parse_args()

    # Create tester
    tester = VoiceModeTest(api_base=args.api_base)

    # Check API health
    if not tester.check_api_health():
        sys.exit(1)

    # Reset test user unless --no-reset
    if not args.no_reset:
        tester.reset_test_user()

    # Run tests
    if args.query:
        # Custom query
        if args.mode == "all":
            print("❌ Must specify --mode when using --query")
            sys.exit(1)

        success, result = tester.test_voice_mode(args.mode, args.query)
        tester.print_result(result)

        sys.exit(0 if success else 1)

    elif args.mode == "all":
        # Test all modes
        summary = tester.run_all_tests()
        tester.print_summary(summary)

        sys.exit(0 if summary["total_failed"] == 0 else 1)

    else:
        # Test specific mode
        mode_results = tester.run_mode_tests(args.mode)

        print(f"\n{'='*70}")
        print(f"{args.mode.upper()} MODE RESULTS")
        print(f"{'='*70}")
        print(f"Passed: {mode_results['passed']}/{mode_results['total']}")
        print(f"Failed: {mode_results['failed']}/{mode_results['total']}")

        accuracy = (
            mode_results['passed'] / mode_results['total'] * 100
            if mode_results['total'] > 0 else 0
        )
        print(f"Accuracy: {accuracy:.1f}%")

        sys.exit(0 if mode_results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
