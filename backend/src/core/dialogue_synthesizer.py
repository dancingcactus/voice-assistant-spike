"""
DialogueSynthesizer - Generates natural handoffs and inter-character dialogue.

This module provides functionality for creating natural handoffs between
characters and synthesizing multi-character dialogue responses.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from models.dialogue import (
    DialogueFragment,
    SynthesizedDialogue,
    HandoffTemplate,
    CharacterRelationship,
)
from models.character_plan import CharacterPlan, CharacterTask


class DialogueSynthesizer:
    """
    Synthesizes natural dialogue and handoffs between characters.
    
    Features:
    - Generates character-appropriate handoff phrases
    - Tracks template usage to avoid repetition
    - Combines multi-character responses seamlessly
    - Injects character references when appropriate
    - Logs coordination events for observability
    """
    
    def __init__(self, config_dir: Optional[Path] = None, coordination_tracker=None):
        """
        Initialize the DialogueSynthesizer.
        
        Args:
            config_dir: Directory containing handoff templates and relationships.
                       Defaults to backend/src/config
            coordination_tracker: Optional CoordinationTracker for logging events
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        
        self.config_dir = config_dir
        self.story_dir = Path(__file__).parent.parent.parent.parent / "story"
        self.coordination_tracker = coordination_tracker
        
        # Load handoff templates
        self.handoff_templates = self._load_handoff_templates()
        
        # Load character relationships
        self.character_relationships = self._load_character_relationships()
        
        # Track template usage to avoid repetition
        self.template_usage: Dict[str, List[int]] = {
            "delilah_to_hank": [],
            "hank_to_delilah": [],
        }
    
    def _load_handoff_templates(self) -> Dict[str, Any]:
        """Load handoff templates from JSON configuration."""
        template_path = self.config_dir / "handoff_templates.json"
        
        try:
            with open(template_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal defaults if file doesn't exist
            return {
                "delilah_to_hank": ["Hank, can you help with that?"],
                "hank_to_delilah": ["Miss Lila, that's for you."],
                "sign_up_at_beginning": {
                    "delilah_claims_cooking": ["I'll handle the cooking!"],
                    "hank_claims_logistics": ["I'll get the list."],
                },
            }
    
    def _load_character_relationships(self) -> Dict[str, Any]:
        """Load character relationship data from JSON."""
        relationship_path = self.story_dir / "characters" / "relationships.json"
        
        try:
            with open(relationship_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal defaults if file doesn't exist
            return {
                "delilah": {
                    "hank": {
                        "relationship_type": "colleague",
                        "trust_level": 0.7,
                        "descriptors": ["reliable", "efficient"],
                        "dialogue_style": ["Respectful", "Professional"],
                    }
                },
                "hank": {
                    "delilah": {
                        "relationship_type": "colleague",
                        "trust_level": 0.8,
                        "descriptors": ["warm", "expert"],
                        "dialogue_style": ["Protective", "Respectful"],
                    }
                },
            }
    
    def synthesize_handoff(
        self,
        from_character: str,
        to_character: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> str:
        """
        Generate a natural handoff phrase from one character to another.
        
        Args:
            from_character: Character handing off (e.g., "delilah")
            to_character: Character receiving handoff (e.g., "hank")
            context: Optional conversation context for context-aware handoffs
            user_id: Optional user ID for coordination tracking
            intent: Optional intent type that triggered handoff
        
        Returns:
            Natural handoff phrase appropriate for the characters
        """
        template_key = f"{from_character}_to_{to_character}"
        
        # Get available templates
        templates = self.handoff_templates.get(template_key, [])
        if not templates:
            # Fallback handoff
            fallback = f"...and {to_character.capitalize()}, can you help with that?"
            
            # Log handoff event
            if self.coordination_tracker and user_id:
                self.coordination_tracker.log_handoff(
                    user_id=user_id,
                    from_character=from_character,
                    to_character=to_character,
                    intent=intent or "unknown",
                    template_used="fallback",
                    success=True,
                    metadata={"type": "fallback"}
                )
            
            return fallback
        
        # Select template that hasn't been used recently
        template_idx, handoff = self._select_handoff_template(template_key, templates)
        
        # Log handoff event
        if self.coordination_tracker and user_id:
            self.coordination_tracker.log_handoff(
                user_id=user_id,
                from_character=from_character,
                to_character=to_character,
                intent=intent or "unknown",
                template_used=f"{template_key}_{template_idx}",
                success=True,
                metadata={
                    "template_idx": template_idx,
                    "template_text": handoff
                }
            )
        
        return handoff
    
    def _select_handoff_template(
        self,
        template_key: str,
        templates: List[str],
    ) -> tuple[int, str]:
        """
        Select a handoff template, avoiding recent usage.
        
        Uses a weighted selection algorithm that deprioritizes
        recently used templates to maintain variety.
        
        Args:
            template_key: Key for template type (e.g., "delilah_to_hank")
            templates: List of available templates
        
        Returns:
            Tuple of (template_index, template_string)
        """
        # Get recent usage for this template type
        recent_usage = self.template_usage.get(template_key, [])
        
        # If we have fewer than 3 templates, just rotate
        if len(templates) <= 3:
            # Simple rotation: pick next unused template
            for i, template in enumerate(templates):
                if i not in recent_usage[-2:]:  # Avoid last 2 uses
                    self.template_usage[template_key] = recent_usage[-5:] + [i]
                    return (i, template)
            # If all recently used, pick randomly
            selected_idx = random.randint(0, len(templates) - 1)
            self.template_usage[template_key] = recent_usage[-5:] + [selected_idx]
            return (selected_idx, templates[selected_idx])
        
        # For larger template sets, use weighted selection
        # Templates used recently get lower weights
        weights = []
        for i in range(len(templates)):
            if i in recent_usage[-1:]:  # Last use
                weights.append(0.1)
            elif i in recent_usage[-3:]:  # Recent use
                weights.append(0.5)
            else:  # Not recently used
                weights.append(1.0)
        
        # Weighted random selection
        selected_idx = random.choices(range(len(templates)), weights=weights, k=1)[0]
        
        # Track usage
        self.template_usage[template_key] = recent_usage[-5:] + [selected_idx]
        
        return (selected_idx, templates[selected_idx])
    
    def combine_responses(
        self,
        responses: List[Dict[str, Any]],
        character_plan: CharacterPlan,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SynthesizedDialogue:
        """
        Combine multiple character responses into a cohesive dialogue.
        
        Args:
            responses: List of character responses, each containing:
                      - character: str
                      - text: str
                      - voice_mode: str
            character_plan: Plan specifying task ordering and handoffs
            user_id: Optional user ID for coordination tracking
            query: Optional original user query for tracking
        
        Returns:
            SynthesizedDialogue with combined responses and handoff info
        """
        fragments: List[DialogueFragment] = []
        full_text_parts: List[str] = []
        includes_handoffs = False
        
        # Track characters involved for multi-task logging
        characters_involved = set()
        
        for i, response in enumerate(responses):
            character = response.get("character", "unknown")
            text = response.get("text", "")
            voice_mode = response.get("voice_mode", "default")
            
            characters_involved.add(character)
            
            # Determine if this response includes a handoff
            has_handoff = i < len(responses) - 1  # All except last
            handoff_to = None
            
            if has_handoff and i < len(character_plan.tasks) - 1:
                # Get next character from plan
                next_task = character_plan.tasks[i + 1]
                handoff_to = next_task.character
                includes_handoffs = True
                
                # Get intent for handoff tracking
                intent = None
                if i < len(character_plan.tasks):
                    intent = character_plan.tasks[i].intent
                
                # Generate handoff phrase (will be logged automatically)
                handoff_phrase = self.synthesize_handoff(
                    character,
                    handoff_to,
                    user_id=user_id,
                    intent=intent
                )
                
                # Append handoff to response text
                text = f"{text} {handoff_phrase}"
            
            # Create dialogue fragment
            fragment = DialogueFragment(
                character=character,
                text=text,
                voice_mode=voice_mode,
                includes_handoff=has_handoff,
                handoff_to=handoff_to,
            )
            fragments.append(fragment)
            full_text_parts.append(text)
        
        # Log multi-task completion if multiple characters involved
        if len(characters_involved) > 1 and self.coordination_tracker and user_id:
            self.coordination_tracker.log_multi_task(
                user_id=user_id,
                query=query or "",
                characters_involved=list(characters_involved),
                success=True,
                metadata={
                    "num_characters": len(characters_involved),
                    "num_handoffs": sum(1 for f in fragments if f.includes_handoff)
                }
            )
        
        # Create synthesized dialogue
        dialogue = SynthesizedDialogue(
            fragments=fragments,
            full_text=" ".join(full_text_parts),
            total_characters=len(responses),
            includes_handoffs=includes_handoffs,
        )
        
        return dialogue
    
    def inject_character_references(
        self,
        text: str,
        character: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Inject references to other characters when appropriate.
        
        This method is currently a placeholder for future functionality
        where characters might reference each other in single-character
        responses (e.g., "Hank would probably tell you to...").
        
        Args:
            text: Original response text
            character: Character generating the response
            context: Conversation context
        
        Returns:
            Text with character references injected (if appropriate)
        """
        # For now, return text unchanged
        # Future enhancement: detect opportunities for character references
        # and inject them naturally
        return text
    
    def get_character_relationship(
        self,
        character: str,
        other_character: str,
    ) -> Optional[CharacterRelationship]:
        """
        Get relationship information between two characters.
        
        Args:
            character: Primary character
            other_character: Character to get relationship with
        
        Returns:
            CharacterRelationship if relationship exists, None otherwise
        """
        char_data = self.character_relationships.get(character, {})
        rel_data = char_data.get(other_character, None)
        
        if rel_data is None:
            return None
        
        return CharacterRelationship(
            other_character=other_character,
            relationship_type=rel_data.get("relationship_type", "unknown"),
            trust_level=rel_data.get("trust_level", 0.5),
            descriptors=rel_data.get("descriptors", []),
            dialogue_style=rel_data.get("dialogue_style", []),
        )
    
    def get_sign_up_phrases(
        self,
        character: str,
        domain: str,
    ) -> Optional[str]:
        """
        Get a sign-up phrase for a character claiming work.
        
        Used when both characters need to respond to a multi-domain
        query (e.g., "What should I make for dinner and what's on my list?")
        
        Args:
            character: Character signing up (e.g., "delilah", "hank")
            domain: Domain being claimed (e.g., "cooking", "logistics")
        
        Returns:
            Sign-up phrase if available, None otherwise
        """
        sign_up_data = self.handoff_templates.get("sign_up_at_beginning", {})
        
        if character == "delilah" and domain == "cooking":
            phrases = sign_up_data.get("delilah_claims_cooking", [])
        elif character == "hank" and domain in ["logistics", "household"]:
            phrases = sign_up_data.get("hank_claims_logistics", [])
        else:
            return None
        
        if not phrases:
            return None
        
        # Select random phrase (these don't need rotation tracking)
        return random.choice(phrases)
