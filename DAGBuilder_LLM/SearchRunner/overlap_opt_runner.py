from __future__ import annotations

from pathlib import Path
from typing import Any


def run_overlap_second_loop(
    *,
    base_config: dict[str, Any],
    candidate_results: list[dict[str, Any]],
    rules_path: Path,
    run_dir: Path,
    top_k: int = 3,
    max_iterations: int = 1,
) -> dict[str, Any]:
    evaluated_count = sum(1 for result in candidate_results if result.get("evaluation"))
    if not bool(base_config.get("search_config", {}).get("overlapopt", {}).get("enabled", True)):
        return {
            "status": "disabled",
            "reason": "overlapopt_disabled",
            "selected_count": 0,
        }
    return {
        "status": "static_rules_only",
        "reason": "second_loop_removed_static_rules_applied_per_candidate",
        "selected_count": min(int(top_k), evaluated_count),
        "evaluated_count": evaluated_count,
        "max_iterations_ignored": int(max_iterations),
    }
