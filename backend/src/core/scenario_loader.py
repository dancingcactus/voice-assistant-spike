"""
Scenario loader for Phase 8: Experience Testing Suite.

Scans backend/data/test_scenarios/ for *.yaml files, parses them with PyYAML,
and validates them against the Scenario Pydantic model.

Group ordering (A → B → C) is enforced by filename prefix convention (a_, b_, c_)
so that alphabetical sort naturally produces the correct run order.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from models.test_run_models import Scenario

SCENARIOS_DIR = Path(__file__).parent.parent.parent / "data" / "test_scenarios"


def load_all() -> List[Scenario]:
    """Load all *.yaml scenario files, sorted alphabetically by filename."""
    scenarios: List[Scenario] = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            scenarios.append(Scenario.model_validate(raw))
        except Exception as exc:
            raise ValueError(f"Failed to load scenario file {path.name}: {exc}") from exc
    return scenarios


def load_by_ids(ids: List[str]) -> List[Scenario]:
    """Return scenarios matching *ids*, in load_all() (alphabetical) order."""
    all_scenarios = {s.id: s for s in load_all()}
    missing = [i for i in ids if i not in all_scenarios]
    if missing:
        raise ValueError(f"Unknown scenario IDs: {missing}")
    return [s for s in all_scenarios.values() if s.id in set(ids)]
