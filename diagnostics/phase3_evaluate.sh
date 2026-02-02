#!/bin/bash
# Phase 3 Voice Evaluation Helper
# Plays all phrases for a given mode and iteration, allowing easy comparison

# Navigate to project root
cd "$(dirname "$0")/.." || exit

MODE="${1:-passionate}"
ITERATION="${2:-iteration_1_baseline}"

AUDIO_DIR="diagnostics/phase3_audio"

# Python command (script loads .env automatically, no venv needed)
PYTHON="python"

# Track Ctrl+C presses for exit detection
interrupted=0

# Trap SIGINT (Ctrl+C) to allow skipping
trap 'interrupted=$((interrupted + 1)); if [ $interrupted -ge 2 ]; then echo ""; echo "Exiting..."; exit 0; else echo ""; echo "Skipping to next phrase..."; pkill -P $$ afplay 2>/dev/null; fi' INT

echo "=== Phase 3 Voice Evaluation ==="
echo "Mode: $MODE"
echo "Iteration: $ITERATION"
echo ""
echo "Playing all phrases. Press Ctrl+C to skip to next phrase."
echo "Press Ctrl+C twice quickly to exit."
echo ""

count=1
for file in "$AUDIO_DIR/${MODE}_${ITERATION}"_*.mp3; do
    if [ -f "$file" ]; then
        # Reset interrupt counter for each phrase
        interrupted=0

        filename=$(basename "$file")
        phrase_id=${filename#${MODE}_${ITERATION}_}
        phrase_id=${phrase_id%.mp3}

        echo "[$count] Playing: $phrase_id"
        echo "File: $filename"

        afplay "$file" &
        AFPLAY_PID=$!
        wait $AFPLAY_PID 2>/dev/null

        echo ""
        echo "=== Evaluation Criteria (1-5 scale) ==="
        echo ""

        # Mode-specific evaluation criteria
        if [ "$MODE" = "passionate" ]; then
            read -p "Southern Authenticity (1-5) - How well does this represent the Southern accent: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Character Fit (1-5) - How well does the phrasing fit the character: " c2
            read -p "Energy Matching Mode (1-5) - How well does the energy match the mode: " c3
            read -p "Followability (1-5) - How easily can you follow what she is saying: " c4
            read -p "Speed (1-5) - How well the speed matches the energy level she should have: " c5
            read -p "Timing and Emphasis (1-5) - Do the pauses and emphasis feel natural: " c6

            total=$((c1 + c2 + c3 + c4 + c5 + c6))
            detailed_notes="Southern:${c1}/5, Character:${c2}/5, Energy:${c3}/5, Followability:${c4}/5, Speed:${c5}/5, Timing:${c6}/5"

        elif [ "$MODE" = "protective" ]; then
            read -p "Southern Authenticity (1-5) - Maintains Southern warmth despite correction: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Character Fit (1-5) - Sounds like Delilah being protective, not mean: " c2
            read -p "Controlled Intensity (1-5) - Firm without being harsh or angry: " c3
            read -p "Caring Tone (1-5) - User feels guided, not scolded: " c4
            read -p "Bless Your Heart (1-5) - Endearment sounds genuine, not condescending: " c5
            read -p "Transition Quality (1-5) - Shock to education shift feels natural: " c6

            total=$((c1 + c2 + c3 + c4 + c5 + c6))
            detailed_notes="Southern:${c1}/5, Character:${c2}/5, Controlled:${c3}/5, Caring:${c4}/5, BlessYourHeart:${c5}/5, Transition:${c6}/5"

        else
            # Default generic criteria
            read -p "Criterion 1 (1-5): " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Criterion 2 (1-5): " c2
            read -p "Criterion 3 (1-5): " c3
            read -p "Criterion 4 (1-5): " c4
            read -p "Criterion 5 (1-5): " c5
            read -p "Criterion 6 (1-5): " c6

            total=$((c1 + c2 + c3 + c4 + c5 + c6))
            detailed_notes="C1:${c1}/5, C2:${c2}/5, C3:${c3}/5, C4:${c4}/5, C5:${c5}/5, C6:${c6}/5"
        fi

        echo ""
        read -p "Additional Notes (optional): " notes

        # Calculate average rating
        avg=$(echo "scale=1; $total / 6" | bc)

        echo "Average rating: $avg/5"
        if [ -n "$notes" ]; then
            detailed_notes="${detailed_notes} | ${notes}"
        fi

        # Convert 1-5 scale to 1-10 for storage (multiply by 2, round to integer)
        rating_out_of_10=$(printf "%.0f" "$(echo "$avg * 2" | bc -l)")

        $PYTHON diagnostics/phase3_voice_testing.py \
            --mode "$MODE" \
            --iteration "$ITERATION" \
            --phrase "$count" \
            --rate "$rating_out_of_10" \
            --notes "$detailed_notes"

        echo ""
        count=$((count + 1))
    fi
done

echo "=== Evaluation Complete ==="
echo ""
echo "To see results:"
echo "  $PYTHON diagnostics/phase3_voice_testing.py --mode $MODE --show-results"
