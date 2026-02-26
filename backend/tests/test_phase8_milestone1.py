"""
Tests for Phase 8 Milestone 1: Scenario Library & Data Model.

Covers:
- ScenarioLoader loads all YAML files in alphabetical order
- ScenarioLoader validates required fields via Pydantic
- ScenarioLoader raises on malformed YAML
- ScenarioLoader raises on unknown scenario IDs in load_by_ids
- load_by_ids returns correct subset in alphabetical order
- Group A files have required_chapter=1 and no setup_steps
- Group B files have required_chapter=2
- SetupStep validation: set_chapter requires chapter field
- SetupStep validation: trigger_beat requires beat_id field
- All 11 initial scenario IDs are present and unique
- Each scenario has at least one user_turn
- TestRunResult serialises to and from JSON without data loss
"""

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scenario_loader import load_all, load_by_ids, SCENARIOS_DIR
from models.test_run_models import (
    CapturedEffect,
    Scenario,
    ScenarioResult,
    SetupStep,
    TestRunRequest,
    TestRunResult,
    TestRunSummary,
    TurnResult,
    WatchForEffect,
)

# ---------------------------------------------------------------------------
# Expected scenario IDs for the initial suite
# ---------------------------------------------------------------------------

EXPECTED_IDS = {
    "ch1_beat_discovery",
    "delilah_solo_dinner_plan",
    "delilah_solo_allergy",
    "delilah_solo_wrong_food",
    "ch2_beat_hank_arrival",
    "hank_solo_shopping",
    "hank_solo_reminder",
    "hank_solo_philosophy",
    "coord_dinner_to_list",
    "coord_list_to_recipe",
    "coord_multiturn_plan",
}


# ===========================================================================
# load_all — basic loading
# ===========================================================================


class TestLoadAll:
    def test_returns_non_empty_list(self):
        scenarios = load_all()
        assert len(scenarios) > 0

    def test_returns_eleven_scenarios(self):
        scenarios = load_all()
        assert len(scenarios) == 11

    def test_all_expected_ids_present(self):
        ids = {s.id for s in load_all()}
        assert ids == EXPECTED_IDS

    def test_ids_are_unique(self):
        ids = [s.id for s in load_all()]
        assert len(ids) == len(set(ids))

    def test_alphabetical_order_matches_group_order(self):
        scenarios = load_all()
        ids = [s.id for s in scenarios]
        # Group A (a_ prefix) comes before Group B (b_ prefix) comes before C (c_ prefix)
        group_a_ids = [s.id for s in scenarios if s.required_chapter == 1]
        group_bc_ids = [s.id for s in scenarios if s.required_chapter == 2]
        # All Group A should appear before Group B/C in load order
        last_a_index = max(ids.index(i) for i in group_a_ids)
        first_bc_index = min(ids.index(i) for i in group_bc_ids)
        assert last_a_index < first_bc_index

    def test_count_matches_files_on_disk(self):
        yaml_files = list(SCENARIOS_DIR.glob("*.yaml"))
        assert len(load_all()) == len(yaml_files)


# ===========================================================================
# load_all — scenario field correctness
# ===========================================================================


class TestScenarioFields:
    def test_each_scenario_has_at_least_one_user_turn(self):
        for s in load_all():
            assert len(s.user_turns) >= 1, f"{s.id} has no user_turns"

    def test_each_scenario_has_non_empty_name(self):
        for s in load_all():
            assert s.name.strip(), f"{s.id} has empty name"

    def test_each_scenario_has_non_empty_description(self):
        for s in load_all():
            assert s.description.strip(), f"{s.id} has empty description"

    def test_each_scenario_has_at_least_one_expected_character(self):
        for s in load_all():
            assert len(s.characters_expected) >= 1, f"{s.id} has no characters_expected"

    def test_each_scenario_has_at_least_one_tag(self):
        for s in load_all():
            assert len(s.tags) >= 1, f"{s.id} has no tags"

    def test_group_a_scenarios_have_required_chapter_1(self):
        group_a_ids = {
            "ch1_beat_discovery",
            "delilah_solo_dinner_plan",
            "delilah_solo_allergy",
            "delilah_solo_wrong_food",
        }
        for s in load_all():
            if s.id in group_a_ids:
                assert s.required_chapter == 1, f"{s.id} should have required_chapter=1"

    def test_group_a_scenarios_have_no_setup_steps(self):
        group_a_ids = {
            "ch1_beat_discovery",
            "delilah_solo_dinner_plan",
            "delilah_solo_allergy",
            "delilah_solo_wrong_food",
        }
        for s in load_all():
            if s.id in group_a_ids:
                assert s.setup_steps == [], f"{s.id} should have no setup_steps"

    def test_group_b_scenarios_have_required_chapter_2(self):
        group_b_ids = {
            "ch2_beat_hank_arrival",
            "hank_solo_shopping",
            "hank_solo_reminder",
            "hank_solo_philosophy",
        }
        for s in load_all():
            if s.id in group_b_ids:
                assert s.required_chapter == 2, f"{s.id} should have required_chapter=2"

    def test_group_c_scenarios_have_required_chapter_2(self):
        group_c_ids = {"coord_dinner_to_list", "coord_list_to_recipe", "coord_multiturn_plan"}
        for s in load_all():
            if s.id in group_c_ids:
                assert s.required_chapter == 2, f"{s.id} should have required_chapter=2"

    def test_hank_arrival_has_set_chapter_setup_step(self):
        scenarios_by_id = {s.id: s for s in load_all()}
        hank_arrival = scenarios_by_id["ch2_beat_hank_arrival"]
        chapter_steps = [st for st in hank_arrival.setup_steps if st.type == "set_chapter"]
        assert len(chapter_steps) == 1
        assert chapter_steps[0].chapter == 2

    def test_hank_arrival_has_trigger_beat_setup_step(self):
        scenarios_by_id = {s.id: s for s in load_all()}
        hank_arrival = scenarios_by_id["ch2_beat_hank_arrival"]
        beat_steps = [st for st in hank_arrival.setup_steps if st.type == "trigger_beat"]
        assert len(beat_steps) == 1
        assert beat_steps[0].beat_id == "hank_arrival"


# ===========================================================================
# load_by_ids
# ===========================================================================


class TestLoadByIds:
    def test_returns_single_matching_scenario(self):
        results = load_by_ids(["ch1_beat_discovery"])
        assert len(results) == 1
        assert results[0].id == "ch1_beat_discovery"

    def test_returns_multiple_matching_scenarios(self):
        ids = ["delilah_solo_dinner_plan", "hank_solo_shopping"]
        results = load_by_ids(ids)
        assert {s.id for s in results} == set(ids)

    def test_preserves_alphabetical_order(self):
        # Pass IDs in reverse alphabetical order; result should still be alphabetical
        ids = ["hank_solo_shopping", "ch1_beat_discovery"]
        results = load_by_ids(ids)
        result_ids = [s.id for s in results]
        # ch1_... sorts before hank_... alphabetically by filename
        assert result_ids.index("ch1_beat_discovery") < result_ids.index("hank_solo_shopping")

    def test_raises_on_unknown_id(self):
        with pytest.raises(ValueError, match="nonexistent_scenario"):
            load_by_ids(["nonexistent_scenario"])

    def test_raises_on_multiple_unknown_ids(self):
        with pytest.raises(ValueError):
            load_by_ids(["bad_id_1", "bad_id_2"])

    def test_raises_mentioning_unknown_id_in_message(self):
        with pytest.raises(ValueError, match="unknown_xyz"):
            load_by_ids(["unknown_xyz"])


# ===========================================================================
# Loader error handling
# ===========================================================================


class TestLoaderErrorHandling:
    def test_raises_on_missing_required_field(self, tmp_path, monkeypatch):
        """A YAML file missing the required `id` field should raise ValueError."""
        bad_yaml = tmp_path / "bad_scenario.yaml"
        bad_yaml.write_text(
            textwrap.dedent("""\
                name: "Missing ID"
                description: "No id field"
                characters_expected: ["delilah"]
                user_turns:
                  - "Hello"
            """),
            encoding="utf-8",
        )
        monkeypatch.setattr("core.scenario_loader.SCENARIOS_DIR", tmp_path)
        with pytest.raises(ValueError, match="bad_scenario.yaml"):
            load_all()

    def test_raises_on_malformed_yaml(self, tmp_path, monkeypatch):
        """A file with invalid YAML syntax should raise ValueError."""
        bad_yaml = tmp_path / "broken.yaml"
        bad_yaml.write_text("id: [unclosed bracket\n", encoding="utf-8")
        monkeypatch.setattr("core.scenario_loader.SCENARIOS_DIR", tmp_path)
        with pytest.raises(ValueError, match="broken.yaml"):
            load_all()

    def test_returns_empty_list_for_empty_directory(self, tmp_path, monkeypatch):
        """An empty directory should return an empty list without raising."""
        monkeypatch.setattr("core.scenario_loader.SCENARIOS_DIR", tmp_path)
        result = load_all()
        assert result == []


# ===========================================================================
# SetupStep model validation
# ===========================================================================


class TestSetupStepValidation:
    def test_set_chapter_with_chapter_is_valid(self):
        step = SetupStep(type="set_chapter", chapter=2)
        assert step.chapter == 2

    def test_trigger_beat_with_beat_id_is_valid(self):
        step = SetupStep(type="trigger_beat", beat_id="hank_arrival")
        assert step.beat_id == "hank_arrival"

    def test_trigger_beat_default_variant_is_standard(self):
        step = SetupStep(type="trigger_beat", beat_id="hank_arrival")
        assert step.variant == "standard"

    def test_trigger_beat_custom_variant(self):
        step = SetupStep(type="trigger_beat", beat_id="hank_arrival", variant="urgent")
        assert step.variant == "urgent"


# ===========================================================================
# TestRunResult serialisation round-trip
# ===========================================================================


class TestTestRunResultSerialisation:
    def test_round_trips_minimal_result(self):
        run = TestRunResult(
            run_id="run_20260224_143022",
            run_label="Baseline",
            started_at="2026-02-24T14:30:22Z",
            status="pending",
            user_id="test_user_01",
        )
        json_str = run.model_dump_json()
        restored = TestRunResult.model_validate_json(json_str)
        assert restored.run_id == run.run_id
        assert restored.run_label == run.run_label
        assert restored.status == run.status
        assert restored.user_id == run.user_id

    def test_round_trips_with_scenario_results(self):
        effect = CapturedEffect(type="story_beat", label="beat advanced")
        turn = TurnResult(
            turn_index=0,
            user_message="Hello",
            character="delilah",
            response="Hi there, sugar!",
            turn_id="turn-abc",
            effects=[effect],
        )
        scenario_result = ScenarioResult(
            scenario_id="delilah_solo_dinner_plan",
            scenario_name="Delilah — Dinner planning",
            status="complete",
            duration_seconds=5.2,
            turns=[turn],
        )
        run = TestRunResult(
            run_id="run_x",
            run_label="Test",
            started_at="2026-02-24T14:00:00Z",
            status="complete",
            user_id="u1",
            scenario_results=[scenario_result],
        )
        json_str = run.model_dump_json()
        restored = TestRunResult.model_validate_json(json_str)
        assert len(restored.scenario_results) == 1
        assert restored.scenario_results[0].turns[0].effects[0].label == "beat advanced"

    def test_completed_at_defaults_to_none(self):
        run = TestRunResult(
            run_id="r",
            run_label="l",
            started_at="2026-02-24T14:00:00Z",
            status="pending",
            user_id="u",
        )
        assert run.completed_at is None

    def test_scenario_results_defaults_to_empty_list(self):
        run = TestRunResult(
            run_id="r",
            run_label="l",
            started_at="2026-02-24T14:00:00Z",
            status="pending",
            user_id="u",
        )
        assert run.scenario_results == []


# ===========================================================================
# TestRunSummary model
# ===========================================================================


class TestTestRunSummaryModel:
    def test_creates_correctly(self):
        summary = TestRunSummary(
            run_id="run_20260224_143022",
            run_label="After prompt v3",
            started_at="2026-02-24T14:30:22Z",
            status="complete",
            scenario_count=11,
            completed_count=11,
            user_id="test_user_01",
        )
        assert summary.scenario_count == 11
        assert summary.completed_count == 11
