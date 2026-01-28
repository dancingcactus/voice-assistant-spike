"""Character System - loads and manages character personalities and voice modes."""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from models.character import Character, VoiceMode, VoiceModeSelection

logger = logging.getLogger(__name__)


class CharacterSystem:
    """
    Manages character loading and voice mode selection.
    Responsible for building character-aware system prompts.
    """

    def __init__(self, characters_dir: Optional[str] = None):
        """
        Initialize the Character System.

        Args:
            characters_dir: Path to directory containing character JSON files
                           Defaults to project_root/story/characters
        """
        if characters_dir is None:
            # Default: go up from backend/src to project root, then to story/characters
            project_root = Path(__file__).parent.parent.parent.parent
            characters_dir = project_root / "story" / "characters"

        self.characters_dir = Path(characters_dir)
        self.characters: Dict[str, Character] = {}
        self._load_characters()

    def _load_characters(self) -> None:
        """Load all character definitions from the characters directory."""
        if not self.characters_dir.exists():
            logger.warning(f"Characters directory not found: {self.characters_dir}")
            return

        for char_file in self.characters_dir.glob("*.json"):
            try:
                with open(char_file, "r") as f:
                    char_data = json.load(f)
                character = Character(**char_data)
                self.characters[character.id] = character
                logger.info(f"Loaded character: {character.name} ({character.id})")
            except Exception as e:
                logger.error(f"Failed to load character from {char_file}: {e}")

    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID."""
        return self.characters.get(character_id)

    def select_voice_mode(
        self, character_id: str, user_input: str, context: Optional[Dict] = None
    ) -> Optional[VoiceModeSelection]:
        """
        Select the appropriate voice mode for a character based on user input.

        Args:
            character_id: ID of the character
            user_input: The user's message
            context: Optional context information (allergies, active tasks, etc.)

        Returns:
            VoiceModeSelection with the chosen mode and reasoning, or None if character not found
        """
        character = self.get_character(character_id)
        if not character:
            logger.warning(f"Character not found: {character_id}")
            return None

        user_lower = user_input.lower()

        # High-priority keyword checks for specific modes
        # These override the generic trigger matching

        # Mama Bear: allergies and dietary restrictions
        mama_bear_keywords = ['allerg', 'dietary', 'restriction', 'cant eat', "can't eat", 'health concern']
        if any(kw in user_lower for kw in mama_bear_keywords):
            mode = character.get_voice_mode("mama_bear")
            if mode:
                return VoiceModeSelection(
                    mode=mode,
                    confidence=0.95,
                    reasoning=f"Selected '{mode.name}' due to allergy/dietary concern"
                )

        # Startled: unexpected changes, surprises
        startled_keywords = ['oh no', 'oh my', 'unexpected', 'surprise', 'suddenly', 'went wrong', 'what happened', 'what just', 'what in']
        if any(kw in user_lower for kw in startled_keywords):
            mode = character.get_voice_mode("startled")
            if mode:
                return VoiceModeSelection(
                    mode=mode,
                    confidence=0.9,
                    reasoning=f"Selected '{mode.name}' due to unexpected event"
                )

        # Use the character's built-in trigger matching
        selected_mode = character.find_matching_voice_mode(user_input)

        # Build reasoning
        reasoning = f"Selected '{selected_mode.name}'"
        if selected_mode.id == "warm_baseline":
            reasoning += " (default/fallback)"
        else:
            # Find which trigger matched
            for trigger in selected_mode.triggers:
                trigger_lower = trigger.lower()
                trigger_words = trigger_lower.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
                for word in trigger_words:
                    if len(word) > 3 and word in user_lower:
                        reasoning += f" due to keyword: '{word}'"
                        break

        return VoiceModeSelection(
            mode=selected_mode,
            confidence=0.8,  # Simple trigger matching has moderate confidence
            reasoning=reasoning,
        )

    def build_system_prompt(
        self, character_id: str, voice_mode: Optional[VoiceMode] = None
    ) -> str:
        """
        Build a comprehensive system prompt for the character.

        Args:
            character_id: ID of the character
            voice_mode: Specific voice mode to use (optional)

        Returns:
            System prompt string for the LLM
        """
        character = self.get_character(character_id)
        if not character:
            return "You are a helpful AI assistant."

        # Build character identity
        prompt_parts = [
            f"You are {character.name}",
        ]

        if character.nickname:
            prompt_parts.append(f'(nickname: "{character.nickname}")')

        prompt_parts.append(f"\nRole: {character.role}")

        if character.description:
            prompt_parts.append(f"\n{character.description}")

        # Add personality
        prompt_parts.append("\n\n## Core Personality")
        for trait in character.personality.core_traits:
            prompt_parts.append(f"- {trait}")

        # Add speech patterns
        prompt_parts.append("\n\n## Speech Patterns")
        for pattern in character.personality.speech_patterns:
            prompt_parts.append(f"- {pattern}")

        # Add mannerisms if present
        if character.personality.mannerisms:
            prompt_parts.append("\n\n## Mannerisms")
            for mannerism in character.personality.mannerisms:
                prompt_parts.append(f"- {mannerism}")

        # Add story arc context if present
        if character.story_arc:
            prompt_parts.append("\n\n## Current Story Context (Chapter 1)")
            if character.story_arc.chapter_1:
                prompt_parts.append(f"{character.story_arc.chapter_1}")
            if character.story_arc.internal_conflict:
                prompt_parts.append(
                    f"\nInternal Conflict: {character.story_arc.internal_conflict}"
                )
            if character.story_arc.coping_mechanism:
                prompt_parts.append(
                    f"Coping Mechanism: {character.story_arc.coping_mechanism}"
                )

        # Add voice mode instructions
        if voice_mode:
            prompt_parts.append(f"\n\n## Current Voice Mode: {voice_mode.name}")
            prompt_parts.append(f"\n{voice_mode.response_style}")

            prompt_parts.append("\n\nMode Characteristics:")
            for characteristic in voice_mode.characteristics:
                prompt_parts.append(f"- {characteristic}")

            prompt_parts.append("\n\nExample Phrases:")
            for example in voice_mode.example_phrases[:2]:  # Limit to 2 examples
                prompt_parts.append(f'- "{example}"')

        else:
            # Include all voice modes for reference
            prompt_parts.append("\n\n## Voice Modes")
            prompt_parts.append(
                "You have multiple voice modes. Respond in the appropriate mode based on context:\n"
            )

            for mode in character.voice_modes:
                prompt_parts.append(f"\n### {mode.name}")
                prompt_parts.append("Triggers:")
                for trigger in mode.triggers[:3]:  # Limit triggers
                    prompt_parts.append(f"- {trigger}")
                prompt_parts.append(f"\nStyle: {mode.response_style}")

        # Add capabilities
        prompt_parts.append("\n\n## Your Capabilities")
        for capability in character.capabilities:
            prompt_parts.append(f"- {capability}")

        # Add response guidelines
        prompt_parts.append("\n\n## Response Guidelines")
        prompt_parts.append(
            "- Stay in character at all times"
        )
        prompt_parts.append(
            "- Keep responses concise (1-3 sentences for simple queries)"
        )
        prompt_parts.append(
            "- Use your voice mode's characteristics consistently"
        )
        prompt_parts.append(
            "- Show personality through word choice and phrasing"
        )
        prompt_parts.append(
            "- Be helpful while maintaining character authenticity"
        )

        return "\n".join(prompt_parts)

    def list_characters(self) -> Dict[str, str]:
        """Get a dict of character IDs to names."""
        return {char_id: char.name for char_id, char in self.characters.items()}
