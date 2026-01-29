"""Character access layer for observability dashboard."""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from core.character_system import CharacterSystem
from models.character import Character, VoiceMode, VoiceModeSelection
from models.user_state import Memory

logger = logging.getLogger(__name__)


class CharacterAccessLayer:
    """
    Data access layer for character definitions and system prompts.
    Wraps CharacterSystem to provide observability-specific functionality.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize character access layer.

        Args:
            project_root: Path to project root (defaults to auto-detection)
        """
        if project_root is None:
            # Auto-detect: go up from backend/src/observability to project root
            project_root = Path(__file__).parent.parent.parent.parent

        self.project_root = Path(project_root)
        self.characters_dir = self.project_root / "story" / "characters"

        # Initialize character system
        self.character_system = CharacterSystem(characters_dir=str(self.characters_dir))

        logger.info(f"CharacterAccessLayer initialized with {len(self.character_system.characters)} characters")

    def list_characters(self) -> List[Dict]:
        """
        List all available characters with basic info.

        Returns:
            List of character summaries
        """
        characters = []
        for char_id, character in self.character_system.characters.items():
            characters.append({
                "id": character.id,
                "name": character.name,
                "nickname": character.nickname,
                "role": character.role,
                "description": character.description,
                "num_voice_modes": len(character.voice_modes),
                "num_capabilities": len(character.capabilities),
                "has_story_arc": character.story_arc is not None,
                "has_tool_instructions": character.tool_instructions is not None,
            })
        return characters

    def get_character(self, character_id: str) -> Optional[Character]:
        """
        Get full character definition.

        Args:
            character_id: Character identifier

        Returns:
            Character object or None if not found
        """
        return self.character_system.get_character(character_id)

    def get_voice_modes(self, character_id: str) -> Optional[List[VoiceMode]]:
        """
        Get all voice modes for a character.

        Args:
            character_id: Character identifier

        Returns:
            List of voice modes or None if character not found
        """
        character = self.character_system.get_character(character_id)
        if character:
            return character.voice_modes
        return None

    def test_voice_mode_selection(
        self, character_id: str, user_input: str, context: Optional[Dict] = None
    ) -> Optional[VoiceModeSelection]:
        """
        Test voice mode selection for a character with given input.

        Args:
            character_id: Character identifier
            user_input: Test user input
            context: Optional context information

        Returns:
            VoiceModeSelection or None if character not found
        """
        return self.character_system.select_voice_mode(character_id, user_input, context)

    def build_system_prompt(
        self,
        character_id: str,
        voice_mode_id: Optional[str] = None,
        memory_context: Optional[Dict[str, List[Memory]]] = None,
    ) -> Optional[str]:
        """
        Build system prompt for a character.

        Args:
            character_id: Character identifier
            voice_mode_id: Optional specific voice mode ID
            memory_context: Optional memory context grouped by category

        Returns:
            System prompt string or None if character not found
        """
        character = self.character_system.get_character(character_id)
        if not character:
            return None

        # Get voice mode if specified
        voice_mode = None
        if voice_mode_id:
            voice_mode = character.get_voice_mode(voice_mode_id)

        return self.character_system.build_system_prompt(
            character_id, voice_mode=voice_mode, memory_context=memory_context
        )

    def get_character_statistics(self, character_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get usage statistics for a character.

        Args:
            character_id: Character identifier
            user_id: Optional user ID to filter stats

        Returns:
            Statistics dict or None if character not found
        """
        character = self.character_system.get_character(character_id)
        if not character:
            return None

        # Placeholder for now - would integrate with tool_call_access.py
        # to get actual interaction statistics
        return {
            "character_id": character_id,
            "character_name": character.name,
            "total_interactions": 0,  # TODO: Query from tool_call_access
            "most_used_voice_mode": "warm_baseline",  # TODO: Calculate from logs
            "average_response_length": 0,  # TODO: Calculate from logs
        }

    def get_tool_instructions(self, character_id: str, tool_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get tool usage instructions for a character.

        Args:
            character_id: Character identifier
            tool_name: Optional specific tool name (returns all if not specified)

        Returns:
            Tool instructions dict or None if character not found
        """
        character = self.character_system.get_character(character_id)
        if not character or not character.tool_instructions:
            return None

        if tool_name:
            return character.tool_instructions.get(tool_name)

        return character.tool_instructions

    def count_prompt_tokens(self, prompt: str) -> int:
        """
        Estimate token count for a prompt.

        Args:
            prompt: The prompt text

        Returns:
            Estimated token count (rough approximation)
        """
        # Rough estimation: ~4 characters per token for English text
        # Claude uses a more sophisticated tokenizer, but this is good enough
        # for observability purposes
        return len(prompt) // 4

    def get_prompt_breakdown(
        self,
        character_id: str,
        voice_mode_id: Optional[str] = None,
        memory_context: Optional[Dict[str, List[Memory]]] = None,
    ) -> Optional[Dict]:
        """
        Get detailed breakdown of system prompt sections with token counts.

        Args:
            character_id: Character identifier
            voice_mode_id: Optional voice mode ID
            memory_context: Optional memory context

        Returns:
            Dict with sections and token counts or None if character not found
        """
        character = self.character_system.get_character(character_id)
        if not character:
            return None

        # Build different sections separately to count tokens
        sections = {}

        # Base character info
        base_parts = [
            f"You are {character.name}",
            f"Role: {character.role}",
        ]
        if character.description:
            base_parts.append(character.description)
        base_text = "\n".join(base_parts)
        sections["base_character"] = {
            "text": base_text,
            "token_estimate": self.count_prompt_tokens(base_text),
        }

        # Personality
        personality_parts = ["## Core Personality"]
        for trait in character.personality.core_traits:
            personality_parts.append(f"- {trait}")
        personality_parts.append("\n## Speech Patterns")
        for pattern in character.personality.speech_patterns:
            personality_parts.append(f"- {pattern}")
        personality_text = "\n".join(personality_parts)
        sections["personality"] = {
            "text": personality_text,
            "token_estimate": self.count_prompt_tokens(personality_text),
        }

        # Voice modes
        voice_mode = None
        if voice_mode_id:
            voice_mode = character.get_voice_mode(voice_mode_id)

        if voice_mode:
            voice_parts = [
                f"## Current Voice Mode: {voice_mode.name}",
                voice_mode.response_style,
                "\nMode Characteristics:",
            ]
            for char in voice_mode.characteristics:
                voice_parts.append(f"- {char}")
            voice_text = "\n".join(voice_parts)
        else:
            voice_parts = ["## Voice Modes"]
            for mode in character.voice_modes:
                voice_parts.append(f"\n### {mode.name}")
                voice_parts.append(f"Style: {mode.response_style}")
            voice_text = "\n".join(voice_parts)

        sections["voice_modes"] = {
            "text": voice_text,
            "token_estimate": self.count_prompt_tokens(voice_text),
        }

        # Memory context
        if memory_context:
            memory_parts = ["## What You Know About This User"]
            for category, memories in memory_context.items():
                memory_parts.append(f"\n### {category.replace('_', ' ').title()}")
                for memory in memories:
                    memory_parts.append(f"- {memory.content}")
            memory_text = "\n".join(memory_parts)
            sections["memory_context"] = {
                "text": memory_text,
                "token_estimate": self.count_prompt_tokens(memory_text),
            }

        # Tool instructions
        if character.tool_instructions:
            tool_parts = ["## Tool Usage Guidelines"]
            for tool_name in character.tool_instructions.keys():
                tool_parts.append(f"\n### {tool_name}")
            tool_text = "\n".join(tool_parts)
            sections["tool_instructions"] = {
                "text": tool_text[:500] + "..." if len(tool_text) > 500 else tool_text,
                "token_estimate": self.count_prompt_tokens(tool_text),
            }

        # Calculate totals
        total_tokens = sum(section["token_estimate"] for section in sections.values())

        return {
            "character_id": character_id,
            "character_name": character.name,
            "sections": sections,
            "total_token_estimate": total_tokens,
        }
