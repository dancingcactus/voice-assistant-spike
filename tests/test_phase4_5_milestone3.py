"""
End-to-End Tests for Phase 4.5 Milestone 3: Inter-Character Dialogue System

Tests handoff generation, dialogue synthesis, and character relationship awareness.
"""

import pytest
from pathlib import Path
import sys

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from core.dialogue_synthesizer import DialogueSynthesizer
from core.character_system import CharacterSystem
from models.character_plan import CharacterPlan, CharacterTask
from models.dialogue import DialogueFragment, SynthesizedDialogue


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def dialogue_synthesizer():
    """Create a DialogueSynthesizer instance for testing."""
    return DialogueSynthesizer()


@pytest.fixture
def character_system():
    """Create a CharacterSystem instance for testing."""
    return CharacterSystem()


@pytest.fixture
def sample_character_plan():
    """Create a sample character plan with multiple tasks."""
    return CharacterPlan(
        tasks=[
            CharacterTask(
                character="delilah",
                task_description="Set timer for 30 minutes",
                intent="cooking",
                confidence=0.9,
                requires_handoff=False,  # First task doesn't have handoff_from
                handoff_from=None,
                estimated_duration_ms=1500,
            ),
            CharacterTask(
                character="hank",
                task_description="Add flour to shopping list",
                intent="household",
                confidence=0.85,
                requires_handoff=True,  # Hank receives handoff from Delilah
                handoff_from="delilah",
                estimated_duration_ms=1200,
            ),
        ],
        execution_mode="sequential",
        total_confidence=0.875,
        estimated_total_duration_ms=2700,
    )


# ============================================================================
# Test Handoff Generation
# ============================================================================

class TestHandoffGeneration:
    """Test handoff phrase generation between characters."""

    def test_delilah_to_hank_handoff(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test generating a handoff from Delilah to Hank."""
        handoff = dialogue_synthesizer.synthesize_handoff("delilah", "hank")
        
        # Check that handoff is generated
        assert handoff is not None
        assert len(handoff) > 0
        
        # Check that it contains character-appropriate language
        # Delilah should use warm, Southern terms
        assert any(term in handoff.lower() for term in [
            "hank", "deary", "sugar", "honey", "sweetheart", "can you"
        ])
        
        print(f"✓ Delilah→Hank handoff: {handoff}")

    def test_hank_to_delilah_handoff(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test generating a handoff from Hank to Delilah."""
        handoff = dialogue_synthesizer.synthesize_handoff("hank", "delilah")
        
        # Check that handoff is generated
        assert handoff is not None
        assert len(handoff) > 0
        
        # Check that it contains character-appropriate language
        # Hank should use gruff, maritime-influenced terms
        assert any(term in handoff.lower() for term in [
            "miss lila", "lila", "aye", "cap'n", "recipe", "cookin'", "kitchen"
        ])
        
        print(f"✓ Hank→Delilah handoff: {handoff}")

    def test_handoff_template_variety(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test that handoff templates rotate to avoid repetition."""
        handoffs = []
        
        # Generate 5 handoffs from Delilah to Hank
        for _ in range(5):
            handoff = dialogue_synthesizer.synthesize_handoff("delilah", "hank")
            handoffs.append(handoff)
        
        # Check that not all handoffs are identical
        unique_handoffs = set(handoffs)
        assert len(unique_handoffs) > 1, "All handoffs are identical - no variety"
        
        # Check that immediate repeats are rare (allow 1 repeat in 5)
        immediate_repeats = sum(
            1 for i in range(len(handoffs) - 1) if handoffs[i] == handoffs[i + 1]
        )
        assert immediate_repeats <= 1, f"Too many immediate repeats: {immediate_repeats}"
        
        print(f"✓ Generated {len(unique_handoffs)} unique handoffs out of 5")
        for i, handoff in enumerate(handoffs, 1):
            print(f"  {i}. {handoff}")


# ============================================================================
# Test Response Combining
# ============================================================================

class TestResponseCombining:
    """Test combining multiple character responses into dialogue."""

    def test_combine_two_character_responses(
        self,
        dialogue_synthesizer: DialogueSynthesizer,
        sample_character_plan: CharacterPlan
    ):
        """Test combining responses from Delilah and Hank."""
        responses = [
            {
                "character": "delilah",
                "text": "Sugar, timer's set for 30 minutes!",
                "voice_mode": "passionate",
            },
            {
                "character": "hank",
                "text": "Aye, flour's on the list, Cap'n.",
                "voice_mode": "working",
            },
        ]
        
        dialogue = dialogue_synthesizer.combine_responses(responses, sample_character_plan)
        
        # Check dialogue structure
        assert isinstance(dialogue, SynthesizedDialogue)
        assert len(dialogue.fragments) == 2
        assert dialogue.total_characters == 2
        assert dialogue.includes_handoffs
        
        # Check first fragment (Delilah)
        delilah_fragment = dialogue.fragments[0]
        assert delilah_fragment.character == "delilah"
        assert delilah_fragment.includes_handoff
        assert delilah_fragment.handoff_to == "hank"
        # Check that handoff was appended
        assert "hank" in delilah_fragment.text.lower()
        
        # Check second fragment (Hank)
        hank_fragment = dialogue.fragments[1]
        assert hank_fragment.character == "hank"
        assert not hank_fragment.includes_handoff  # Last fragment has no handoff
        
        # Check full text
        assert "delilah" in dialogue.full_text.lower() or "timer" in dialogue.full_text.lower()
        assert "hank" in dialogue.full_text.lower() or "flour" in dialogue.full_text.lower()
        
        print(f"✓ Combined dialogue: {dialogue.full_text}")

    def test_single_character_no_handoff(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test that single-character responses have no handoffs."""
        responses = [
            {
                "character": "delilah",
                "text": "Sugar, timer's set for 30 minutes!",
                "voice_mode": "passionate",
            },
        ]
        
        plan = CharacterPlan(
            tasks=[
                CharacterTask(
                    character="delilah",
                    task_description="Set timer",
                    intent="cooking",
                    confidence=0.9,
                    requires_handoff=False,
                    handoff_from=None,
                    estimated_duration_ms=1500,
                )
            ],
            execution_mode="single",
            total_confidence=0.9,
            estimated_total_duration_ms=1500,
        )
        
        dialogue = dialogue_synthesizer.combine_responses(responses, plan)
        
        assert len(dialogue.fragments) == 1
        assert not dialogue.includes_handoffs
        assert not dialogue.fragments[0].includes_handoff
        
        print(f"✓ Single-character response (no handoff): {dialogue.full_text}")


# ============================================================================
# Test Character Relationships
# ============================================================================

class TestCharacterRelationships:
    """Test character relationship awareness."""

    def test_get_character_relationship(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test retrieving relationship data between characters."""
        # Test Delilah's view of Hank
        rel = dialogue_synthesizer.get_character_relationship("delilah", "hank")
        
        assert rel is not None
        assert rel.other_character == "hank"
        assert rel.relationship_type in ["colleague", "friend"]
        assert 0.0 <= rel.trust_level <= 1.0
        assert len(rel.descriptors) > 0
        assert len(rel.dialogue_style) > 0
        
        print(f"✓ Delilah's view of Hank: {rel.relationship_type}, trust={rel.trust_level}")
        print(f"  Descriptors: {rel.descriptors}")
        
        # Test Hank's view of Delilah
        rel = dialogue_synthesizer.get_character_relationship("hank", "delilah")
        
        assert rel is not None
        assert rel.other_character == "delilah"
        assert rel.relationship_type in ["colleague", "friend"]
        
        print(f"✓ Hank's view of Delilah: {rel.relationship_type}, trust={rel.trust_level}")

    def test_inject_character_awareness(self, character_system: CharacterSystem):
        """Test injecting character awareness into system prompts."""
        base_prompt = "You are Delilah, a Southern cook."
        
        enhanced_prompt = character_system.inject_character_awareness(
            prompt=base_prompt,
            character_id="delilah",
            other_characters=["hank"],
        )
        
        # Check that prompt was enhanced
        assert len(enhanced_prompt) > len(base_prompt)
        
        # Check that Hank is mentioned
        assert "hank" in enhanced_prompt.lower()
        
        # Check that relationship context is included
        assert any(term in enhanced_prompt.lower() for term in [
            "relationship", "colleague", "reliable", "efficient"
        ])
        
        print(f"✓ Enhanced prompt includes relationship context")
        print(f"  Original length: {len(base_prompt)} chars")
        print(f"  Enhanced length: {len(enhanced_prompt)} chars")


# ============================================================================
# Test Sign-Up Phrases
# ============================================================================

class TestSignUpPhrases:
    """Test sign-up phrases for multi-domain queries."""

    def test_delilah_claims_cooking(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test Delilah claiming cooking work."""
        phrase = dialogue_synthesizer.get_sign_up_phrases("delilah", "cooking")
        
        assert phrase is not None
        assert len(phrase) > 0
        
        # Should sound enthusiastic and character-appropriate
        assert any(term in phrase.lower() for term in [
            "sugar", "honey", "darlin'", "sweetheart", "i", "me", "let"
        ])
        
        print(f"✓ Delilah claims cooking: {phrase}")

    def test_hank_claims_logistics(self, dialogue_synthesizer: DialogueSynthesizer):
        """Test Hank claiming logistics work."""
        phrase = dialogue_synthesizer.get_sign_up_phrases("hank", "logistics")
        
        assert phrase is not None
        assert len(phrase) > 0
        
        # Should sound efficient and character-appropriate
        assert any(term in phrase.lower() for term in [
            "aye", "list", "i'll", "cap'n", "handle", "logistics"
        ])
        
        print(f"✓ Hank claims logistics: {phrase}")


# ============================================================================
# Integration Tests
# ============================================================================

class TestDialogueIntegration:
    """Test full dialogue synthesis workflow."""

    def test_full_multi_character_workflow(
        self,
        dialogue_synthesizer: DialogueSynthesizer,
        sample_character_plan: CharacterPlan
    ):
        """Test complete workflow: handoffs → combine → result."""
        # Simulate multi-character responses
        responses = [
            {
                "character": "delilah",
                "text": "Timer's set, sugar!",
                "voice_mode": "passionate",
            },
            {
                "character": "hank",
                "text": "Flour's on the list.",
                "voice_mode": "working",
            },
        ]
        
        # Combine responses (should inject handoffs)
        dialogue = dialogue_synthesizer.combine_responses(responses, sample_character_plan)
        
        # Verify complete dialogue structure
        assert dialogue.total_characters == 2
        assert dialogue.includes_handoffs
        assert len(dialogue.fragments) == 2
        
        # Delilah's fragment should have handoff injected
        assert "hank" in dialogue.fragments[0].text.lower()
        
        # Full text should be coherent
        full_text = dialogue.full_text
        assert "timer" in full_text.lower()
        assert "flour" in full_text.lower()
        assert "hank" in full_text.lower()
        
        print(f"✓ Full multi-character dialogue:")
        for i, fragment in enumerate(dialogue.fragments, 1):
            print(f"  {i}. [{fragment.character}] {fragment.text}")
        print(f"  Full: {full_text}")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
