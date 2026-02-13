"""Character System - loads and manages character personalities and voice modes."""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any

from models.character import Character, VoiceMode, VoiceModeSelection
from models.user_state import Memory

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
        self,
        character_id: str,
        voice_mode: Optional[VoiceMode] = None,
        memory_context: Optional[Dict[str, List[Memory]]] = None
    ) -> str:
        """
        Build a comprehensive system prompt for the character.

        Args:
            character_id: ID of the character
            voice_mode: Specific voice mode to use (optional)
            memory_context: Dict of memory lists grouped by category (optional)

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

        # Add memory context section
        if memory_context:
            prompt_parts.append("\n\n## What You Know About This User")

            # Dietary Restrictions (CRITICAL - always show first)
            dietary = memory_context.get("dietary_restrictions", [])
            if dietary:
                prompt_parts.append("\n### ⚠️  DIETARY RESTRICTIONS (CRITICAL)")
                for memory in dietary:
                    prompt_parts.append(f"- {memory.content}")
                prompt_parts.append(
                    "**IMPORTANT**: ALWAYS consider these restrictions in ANY food recommendation. "
                    "If uncertain, ask before suggesting."
                )

            # Preferences
            prefs = memory_context.get("preferences", [])
            if prefs:
                prompt_parts.append("\n### Preferences")
                for memory in sorted(prefs, key=lambda m: m.importance, reverse=True):
                    prompt_parts.append(f"- {memory.content}")

            # Relationships
            relationships = memory_context.get("relationships", [])
            if relationships:
                prompt_parts.append("\n### Family & Relationships")
                for memory in relationships:
                    prompt_parts.append(f"- {memory.content}")

            # Facts
            facts = memory_context.get("facts", [])
            if facts:
                prompt_parts.append("\n### Facts About User")
                for memory in sorted(facts, key=lambda m: m.importance, reverse=True)[:5]:
                    prompt_parts.append(f"- {memory.content}")

            # Events (only show upcoming/recent)
            events = memory_context.get("events", [])
            if events:
                prompt_parts.append("\n### Upcoming Events & Schedule")
                for memory in sorted(events, key=lambda m: m.importance, reverse=True)[:3]:
                    prompt_parts.append(f"- {memory.content}")

        # Add tool instructions if present
        if character.tool_instructions:
            prompt_parts.append("\n\n## Tool Usage Guidelines")

            for tool_name, instructions in character.tool_instructions.items():
                prompt_parts.append(f"\n### Using the '{tool_name}' Tool")

                if 'general_guidance' in instructions:
                    prompt_parts.append(f"\n{instructions['general_guidance']}")

                if 'when_to_use' in instructions:
                    prompt_parts.append("\n**When to use this tool:**")
                    for condition in instructions['when_to_use']:
                        prompt_parts.append(f"- {condition}")

                if 'when_NOT_to_use' in instructions:
                    prompt_parts.append("\n**When NOT to use:**")
                    for condition in instructions['when_NOT_to_use']:
                        prompt_parts.append(f"- {condition}")

                if 'examples' in instructions and len(instructions['examples']) > 0:
                    prompt_parts.append("\n**Examples:**")
                    for i, ex in enumerate(instructions['examples'][:3], 1):  # Show first 3
                        prompt_parts.append(f"\n{i}. User: \"{ex['user_says']}\"")
                        prompt_parts.append(f"   Action: {ex['action']}")
                        if 'calls' in ex and len(ex['calls']) > 0:
                            call = ex['calls'][0]  # Show first call as example
                            prompt_parts.append(
                                f"   Example call: category=\"{call['category']}\", "
                                f"importance={call['importance']}"
                            )

                if 'importance_guidelines' in instructions:
                    prompt_parts.append("\n**Importance Ratings:**")
                    guidelines = instructions['importance_guidelines']
                    for level in ['10', '9', '8', '7', '5', '3']:
                        if level in guidelines:
                            prompt_parts.append(f"- {level}: {guidelines[level]}")

                if 'mama_bear_mode_integration' in instructions:
                    prompt_parts.append(f"\n**Special Note:** {instructions['mama_bear_mode_integration']}")

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

    def inject_character_awareness(
        self,
        prompt: str,
        character_id: str,
        other_characters: List[str],
    ) -> str:
        """
        Inject awareness of other characters into a system prompt.
        
        Adds relationship context so characters can naturally reference
        each other and coordinate during multi-character interactions.
        
        Args:
            prompt: The base system prompt
            character_id: ID of the character receiving the prompt
            other_characters: List of other character IDs that are active
        
        Returns:
            Enhanced prompt with character relationship context
        """
        if not other_characters:
            return prompt
        
        # Load relationship data
        relationships_file = self.characters_dir / "relationships.json"
        if not relationships_file.exists():
            return prompt
        
        try:
            with open(relationships_file, "r") as f:
                relationships_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load relationships: {e}")
            return prompt
        
        # Get relationships for this character
        char_relationships = relationships_data.get(character_id, {})
        
        relationship_context = ["\n\n## Other Characters Present"]
        
        for other_char_id in other_characters:
            if other_char_id == character_id:
                continue
            
            other_char = self.get_character(other_char_id)
            if not other_char:
                continue
            
            rel_data = char_relationships.get(other_char_id, {})
            
            relationship_context.append(f"\n### {other_char.name}")
            relationship_context.append(f"Role: {other_char.role}")
            
            if rel_data:
                rel_type = rel_data.get("relationship_type", "colleague")
                relationship_context.append(f"Relationship: {rel_type}")
                
                descriptors = rel_data.get("descriptors", [])
                if descriptors:
                    relationship_context.append("How you see them:")
                    for desc in descriptors[:3]:  # Limit to 3
                        relationship_context.append(f"- {desc}")
                
                dialogue_style = rel_data.get("dialogue_style", [])
                if dialogue_style:
                    relationship_context.append("When interacting:")
                    for style in dialogue_style[:3]:  # Limit to 3
                        relationship_context.append(f"- {style}")
        
        # Append relationship context to prompt
        if len(relationship_context) > 1:  # More than just the header
            return prompt + "\n".join(relationship_context)
        
        return prompt
    
    def get_character_relationship(
        self,
        character_id: str,
        other_character_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get relationship information between two characters.
        
        Args:
            character_id: Primary character ID
            other_character_id: Other character ID
        
        Returns:
            Relationship data dict or None if no relationship exists
        """
        relationships_file = self.characters_dir / "relationships.json"
        if not relationships_file.exists():
            return None
        
        try:
            with open(relationships_file, "r") as f:
                relationships_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load relationships: {e}")
            return None
        
        char_relationships = relationships_data.get(character_id, {})
        return char_relationships.get(other_character_id, None)
