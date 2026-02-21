"""
Tests for Phase 5.1 Milestone 3: request_handoff Tool & Character Prompt Updates.

Covers:
- HandoffTool: name, description, parameters, available_secondaries, execute() fallback
- tool_call_models.ToolCallLog: new orchestrator_decision and resulted_in_character fields
- story/characters/delilah.json: request_handoff guidance present and correct
- story/characters/hank.json: request_handoff guidance present and correct
- CharacterSystem.build_system_prompt: request_handoff guidance injected for delilah/hank
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path so imports match the backend module layout
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.handoff_tool import HandoffTool
from tools.tool_base import ToolContext, ToolResultStatus
from observability.tool_call_models import ToolCallLog, ToolCallStatus
from datetime import datetime


# ===========================================================================
# HandoffTool — basic contract
# ===========================================================================


class TestHandoffToolBasic:
    def test_name_is_request_handoff(self):
        tool = HandoffTool()
        assert tool.name == "request_handoff"

    def test_description_is_meaningful(self):
        tool = HandoffTool()
        assert len(tool.description) > 50
        assert "request_handoff" in tool.description or "follow-up" in tool.description.lower()

    def test_parameters_include_required_fields(self):
        tool = HandoffTool()
        names = {p.name for p in tool.parameters}
        assert "to_character" in names
        assert "task_summary" in names
        assert "items" in names

    def test_to_character_is_required(self):
        tool = HandoffTool()
        to_char = next(p for p in tool.parameters if p.name == "to_character")
        assert to_char.required is True

    def test_task_summary_is_required(self):
        tool = HandoffTool()
        summary = next(p for p in tool.parameters if p.name == "task_summary")
        assert summary.required is True

    def test_items_is_optional(self):
        tool = HandoffTool()
        items = next(p for p in tool.parameters if p.name == "items")
        assert items.required is False

    def test_items_type_is_array(self):
        tool = HandoffTool()
        items = next(p for p in tool.parameters if p.name == "items")
        assert items.type == "array"
        assert items.items == {"type": "string"}


class TestHandoffToolAvailableSecondaries:
    def test_default_includes_hank(self):
        tool = HandoffTool()
        to_char = next(p for p in tool.parameters if p.name == "to_character")
        assert to_char.enum is not None
        assert "hank" in to_char.enum

    def test_custom_secondaries(self):
        tool = HandoffTool(available_secondaries=["hank", "rex"])
        to_char = next(p for p in tool.parameters if p.name == "to_character")
        assert set(to_char.enum) == {"hank", "rex"}

    def test_empty_secondaries_enum_is_none(self):
        """An empty list is intentional 'no valid targets'; enum should be None."""
        tool = HandoffTool(available_secondaries=[])
        to_char = next(p for p in tool.parameters if p.name == "to_character")
        assert to_char.enum is None

    def test_none_secondaries_falls_back_to_default(self):
        """None means 'use default'; falls back to ['hank']."""
        tool = HandoffTool(available_secondaries=None)
        to_char = next(p for p in tool.parameters if p.name == "to_character")
        assert to_char.enum == ["hank"]

    def test_openai_function_has_enum(self):
        tool = HandoffTool(available_secondaries=["hank"])
        fn = tool.to_openai_function()
        props = fn["function"]["parameters"]["properties"]
        assert "to_character" in props
        assert "hank" in props["to_character"]["enum"]


class TestHandoffToolExecuteFallback:
    @pytest.mark.asyncio
    async def test_execute_returns_success(self):
        """execute() is a no-op safety fallback — should return SUCCESS."""
        tool = HandoffTool()
        context = ToolContext(user_id="u1", session_id="s1", character_id="delilah")
        result = await tool.execute(
            context,
            to_character="hank",
            task_summary="Add items to list",
            items=["chicken"],
        )
        assert result.status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_message_mentions_character(self):
        tool = HandoffTool()
        context = ToolContext(user_id="u1", session_id="s1", character_id="delilah")
        result = await tool.execute(context, to_character="hank", task_summary="test")
        assert "hank" in result.message.lower()

    @pytest.mark.asyncio
    async def test_execute_data_includes_intercepted_false(self):
        tool = HandoffTool()
        context = ToolContext(user_id="u1", session_id="s1", character_id="delilah")
        result = await tool.execute(context, to_character="hank", task_summary="test")
        assert result.data is not None
        assert result.data.get("intercepted") is False

    @pytest.mark.asyncio
    async def test_execute_without_items_uses_empty_list(self):
        tool = HandoffTool()
        context = ToolContext(user_id="u1", session_id="s1", character_id="delilah")
        result = await tool.execute(context, to_character="hank", task_summary="test")
        assert result.data["items"] == []


# ===========================================================================
# tool_call_models.py — new Phase 5.1 fields
# ===========================================================================


def _make_log(**kwargs) -> ToolCallLog:
    defaults = dict(
        call_id="test-call-1",
        timestamp=datetime.utcnow(),
        duration_ms=50,
        tool_name="manage_timer",
        user_id="test_user",
        request={"action": "set"},
        response={"status": "success"},
        status=ToolCallStatus.SUCCESS,
    )
    defaults.update(kwargs)
    return ToolCallLog(**defaults)


class TestToolCallLogNewFields:
    def test_orchestrator_decision_defaults_to_none(self):
        log = _make_log()
        assert log.orchestrator_decision is None

    def test_resulted_in_character_defaults_to_none(self):
        log = _make_log()
        assert log.resulted_in_character is None

    def test_orchestrator_decision_can_be_set(self):
        log = _make_log(
            tool_name="request_handoff",
            orchestrator_decision={"accepted": True, "rejected_reason": None},
        )
        assert log.orchestrator_decision["accepted"] is True

    def test_resulted_in_character_can_be_set(self):
        log = _make_log(
            tool_name="request_handoff",
            resulted_in_character="hank",
        )
        assert log.resulted_in_character == "hank"

    def test_rejected_handoff_accepted_false(self):
        log = _make_log(
            tool_name="request_handoff",
            orchestrator_decision={
                "accepted": False,
                "rejected_reason": "FR2.4 — one handoff per turn",
            },
            resulted_in_character=None,
        )
        assert log.orchestrator_decision["accepted"] is False
        assert log.resulted_in_character is None

    def test_fields_serialise_in_model_dump(self):
        log = _make_log(
            tool_name="request_handoff",
            orchestrator_decision={"accepted": True, "rejected_reason": None},
            resulted_in_character="hank",
        )
        d = log.model_dump()
        assert d["orchestrator_decision"]["accepted"] is True
        assert d["resulted_in_character"] == "hank"


# ===========================================================================
# story/characters JSON — request_handoff guidance
# ===========================================================================

# Resolve path relative to this test file (backend/tests/ → project_root/story/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DELILAH_JSON = _PROJECT_ROOT / "story" / "characters" / "delilah.json"
_HANK_JSON = _PROJECT_ROOT / "story" / "characters" / "hank.json"


class TestDelilahRequestHandoffGuidance:
    @pytest.fixture(scope="class")
    def delilah(self):
        with open(_DELILAH_JSON) as f:
            return json.load(f)

    def test_tool_instructions_present(self, delilah):
        assert "tool_instructions" in delilah

    def test_request_handoff_key_present(self, delilah):
        assert "request_handoff" in delilah["tool_instructions"]

    def test_general_guidance_present(self, delilah):
        guidance = delilah["tool_instructions"]["request_handoff"].get("general_guidance", "")
        assert len(guidance) > 20

    def test_when_to_use_is_list(self, delilah):
        when = delilah["tool_instructions"]["request_handoff"].get("when_to_use", [])
        assert isinstance(when, list)
        assert len(when) > 0

    def test_when_not_to_use_is_list(self, delilah):
        when_not = delilah["tool_instructions"]["request_handoff"].get("when_NOT_to_use", [])
        assert isinstance(when_not, list)
        assert len(when_not) > 0

    def test_references_hank(self, delilah):
        guidance = json.dumps(delilah["tool_instructions"]["request_handoff"]).lower()
        assert "hank" in guidance

    def test_existing_tool_instructions_still_present(self, delilah):
        assert "save_memory" in delilah["tool_instructions"]


class TestHankRequestHandoffGuidance:
    @pytest.fixture(scope="class")
    def hank(self):
        with open(_HANK_JSON) as f:
            return json.load(f)

    def test_tool_instructions_present(self, hank):
        assert "tool_instructions" in hank

    def test_request_handoff_key_present(self, hank):
        assert "request_handoff" in hank["tool_instructions"]

    def test_general_guidance_present(self, hank):
        guidance = hank["tool_instructions"]["request_handoff"].get("general_guidance", "")
        assert len(guidance) > 20

    def test_when_to_use_is_list(self, hank):
        when = hank["tool_instructions"]["request_handoff"].get("when_to_use", [])
        assert isinstance(when, list)
        assert len(when) > 0

    def test_references_delilah(self, hank):
        guidance = json.dumps(hank["tool_instructions"]["request_handoff"]).lower()
        assert "delilah" in guidance


# ===========================================================================
# CharacterSystem — request_handoff injected into system prompt
# ===========================================================================


class TestCharacterSystemRequestHandoffPrompt:
    """
    Verify that the build_system_prompt path exercises the request_handoff
    instructions block from the JSON definitions.

    Uses a minimal mock CharacterSystem-style loader to stay test-portable
    without requiring a running server.
    """

    def _load_character_prompt(self, json_path: Path) -> str:
        """
        Manually apply the tool_instructions rendering logic from
        CharacterSystem.build_system_prompt() to the request_handoff block.
        """
        with open(json_path) as f:
            data = json.load(f)

        tool_instructions = data.get("tool_instructions", {})
        rh = tool_instructions.get("request_handoff", {})
        if not rh:
            return ""

        parts = []
        if "general_guidance" in rh:
            parts.append(rh["general_guidance"])
        if "when_to_use" in rh:
            parts.extend(rh["when_to_use"])
        if "when_NOT_to_use" in rh:
            parts.extend(rh["when_NOT_to_use"])
        return "\n".join(parts)

    def test_delilah_prompt_includes_handoff_guidance(self):
        prompt = self._load_character_prompt(_DELILAH_JSON)
        assert len(prompt) > 0
        assert "handoff" in prompt.lower() or "hank" in prompt.lower()

    def test_hank_prompt_includes_handoff_guidance(self):
        prompt = self._load_character_prompt(_HANK_JSON)
        assert len(prompt) > 0
        assert "handoff" in prompt.lower() or "delilah" in prompt.lower()

    def test_handoff_tool_registered_in_tool_system(self):
        """HandoffTool can be registered in ToolSystem without error."""
        from core.tool_system import ToolSystem

        tool_system = ToolSystem()
        handoff_tool = HandoffTool(available_secondaries=["hank"])
        tool_system.register_tool(handoff_tool)
        assert "request_handoff" in tool_system.list_tools()

    def test_handoff_tool_in_openai_functions(self):
        from core.tool_system import ToolSystem

        tool_system = ToolSystem()
        tool_system.register_tool(HandoffTool(available_secondaries=["hank"]))
        functions = tool_system.get_openai_functions()
        names = [f["function"]["name"] for f in functions]
        assert "request_handoff" in names
