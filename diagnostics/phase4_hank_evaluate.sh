#!/bin/bash
# Phase 4 Hank Voice Evaluation Helper
# Plays all phrases for a given mode and iteration, allowing easy comparison

cd "$(dirname "$0")/.." || exit

MODE="${1:-working}"
ITERATION="${2:-iteration_1_baseline}"

AUDIO_DIR="diagnostics/phase4_audio"
PYTHON="python"

interrupted=0

trap 'interrupted=$((interrupted + 1)); if [ $interrupted -ge 2 ]; then echo ""; echo "Exiting..."; exit 0; else echo ""; echo "Skipping to next phrase..."; pkill -P $$ afplay 2>/dev/null; fi' INT

echo "=== Phase 4 Hank Voice Evaluation ==="
echo "Mode: $MODE"
echo "Iteration: $ITERATION"
echo ""
echo "Playing all phrases. Press Ctrl+C to skip to next phrase."
echo "Press Ctrl+C twice quickly to exit."
echo ""

count=1
for file in "$AUDIO_DIR/${MODE}_${ITERATION}"_*.mp3; do
    if [ -f "$file" ]; then
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

        if [ "$MODE" = "working" ]; then
            read -p "Clearness (1-5) - Are you able to understand what he is saying: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Color (1-5) - How colorful is the language: " c2
            read -p "Calm (1-5) - How calm is Hank: " c3
            read -p "Pacing (1-5) - Is his pace deliberate without being slow: " c4
            read -p "Character (1-5) - Does this feel like Hank: " c5

            total=$((c1 + c2 + c3 + c4 + c5))
            detailed_notes="Clearness:${c1}/5, Color:${c2}/5, Calm:${c3}/5, Pacing:${c4}/5, Character:${c5}/5"

        elif [ "$MODE" = "protective" ]; then
            read -p "Firmness (1-5) - Direct and decisive: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Protective Intent (1-5) - Clear concern for safety: " c2
            read -p "Calm Control (1-5) - Firm without yelling: " c3
            read -p "Clarity (1-5) - Safety direction is obvious: " c4
            read -p "Character Fit (1-5) - Still Hank, not another voice: " c5

            total=$((c1 + c2 + c3 + c4 + c5))
            detailed_notes="Firm:${c1}/5, Protect:${c2}/5, Calm:${c3}/5, Clear:${c4}/5, Character:${c5}/5"

        elif [ "$MODE" = "resigned" ]; then
            read -p "Weary Acceptance (1-5) - Sighing compliance: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Dry Humor (1-5) - Subtle, not sarcastic: " c2
            read -p "Not Annoyed (1-5) - Weary but still helpful: " c3
            read -p "Pacing (1-5) - Slightly slower, deliberate: " c4
            read -p "Character Fit (1-5) - Feels like Hank: " c5

            total=$((c1 + c2 + c3 + c4 + c5))
            detailed_notes="Weary:${c1}/5, DryHumor:${c2}/5, Helpful:${c3}/5, Pacing:${c4}/5, Character:${c5}/5"

        elif [ "$MODE" = "grumble" ]; then
            read -p "Low Mutter (1-5) - Feels under the breath: " c1
            if [ -z "$c1" ]; then
                echo "Skipping evaluation for this phrase."
                echo ""
                count=$((count + 1))
                continue
            fi
            read -p "Brevity (1-5) - Very short: " c2
            read -p "Not Rude (1-5) - Irritated but not mean: " c3
            read -p "Back to Work (1-5) - Returns to task quickly: " c4
            read -p "Character Fit (1-5) - Still Hank: " c5

            total=$((c1 + c2 + c3 + c4 + c5))
            detailed_notes="Mutter:${c1}/5, Brevity:${c2}/5, NotRude:${c3}/5, BackToWork:${c4}/5, Character:${c5}/5"

        else
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

            total=$((c1 + c2 + c3 + c4 + c5))
            detailed_notes="C1:${c1}/5, C2:${c2}/5, C3:${c3}/5, C4:${c4}/5, C5:${c5}/5"
        fi

        echo ""
        read -p "Additional Notes (optional): " notes

        avg=$(echo "scale=1; $total / 5" | bc)

        echo "Average rating: $avg/5"
        if [ -n "$notes" ]; then
            detailed_notes="${detailed_notes} | ${notes}"
        fi

        rating_out_of_10=$(printf "%.0f" "$(echo "$avg * 2" | bc -l)")

        $PYTHON diagnostics/phase4_hank_voice_testing.py \
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
