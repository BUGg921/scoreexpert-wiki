from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "SearchRunner") not in sys.path:
    sys.path.insert(0, str(ROOT / "SearchRunner"))
if str(ROOT / "DagGenerator") not in sys.path:
    sys.path.insert(0, str(ROOT / "DagGenerator"))

from generate_dag import load_config  # noqa: E402
from run_two_stage_search import output_root_from_config, run_two_stage_search  # noqa: E402
from SearchRunner.deepseek_client import evolve_program, is_enabled, summarize_evaluation_feedback  # noqa: E402
from ScoreExpert.evaluator import static_check_source  # noqa: E402
from ScoreExpert.island_store import (  # noqa: E402
    ISLANDS,
    append_program,
    load_active_program_id,
    load_instruction,
    load_program_bank,
    update_program_bank,
)
from ScoreExpert.score_expert import score_island  # noqa: E402


def run_evolution(config_path: Path, rules_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    evolution = evolution_config(config)
    if output_root is None:
        output_root = output_root_from_config(config)
    run_root = make_evolution_dir(output_root)
    max_rounds = int(evolution.get("max_rounds", 5))
    migration_interval = int(evolution.get("migration_interval", 3))

    rounds: list[dict[str, Any]] = []
    feedback: dict[str, Any] = {"status": "initial", "summary": "", "suggestions": []}
    for round_index in range(max_rounds):
        island = ISLANDS[round_index % len(ISLANDS)]
        round_output_root = run_root / f"round_{round_index:04d}"
        search_report = run_two_stage_search(config_path, rules_path, round_output_root, write_markdown_report=False)
        try:
            feedback = summarize_evaluation_feedback(search_report.get("candidate_results", []), config)
        except Exception as exc:  # noqa: BLE001
            feedback = {"status": "fail", "reason": str(exc), "summary": "", "suggestions": []}
        evolution_result = evolve_one_island(island, feedback, config)
        migration_result = None
        if migration_interval > 0 and (round_index + 1) % migration_interval == 0:
            migration_result = migrate_islands(search_report.get("candidate_results", []), config)
        round_report = {
            "round": round_index,
            "selected_island": island,
            "search_run_dir": search_report.get("run_dir"),
            "search_status": search_report.get("status"),
            "feedback": sanitize_feedback(feedback),
            "evolution": evolution_result,
            "migration": migration_result,
        }
        rounds.append(round_report)

    summary = {
        "status": "pass",
        "run_root": str(run_root.as_posix()),
        "deepseek_enabled": is_enabled(config),
        "rounds": rounds,
    }
    report_path = run_root / "evolution_report.md"
    report_path.write_text(render_evolution_report(summary), encoding="utf-8")
    summary["evolution_report_md"] = str(report_path.as_posix())
    return summary


def evolve_one_island(island: str, feedback: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    bank = load_program_bank(island)
    v0, v1 = select_program_pair(bank)
    if not is_enabled(config):
        return {
            "status": "skipped",
            "reason": "DEEPSEEK_API_KEY is not set",
            "v0": v0.get("program_id"),
            "v1": v1.get("program_id"),
        }
    try:
        source = evolve_program(
            island=island,
            instruction=load_instruction(island),
            v0=v0,
            v1=v1,
            feedback=feedback,
            config=config,
        )
    except Exception as exc:  # noqa: BLE001
        return {"status": "fail", "reason": str(exc), "v0": v0.get("program_id"), "v1": v1.get("program_id")}
    if not source:
        return {"status": "fail", "reason": "DeepSeek did not return source"}
    check = static_check_source(source)
    if not check.get("valid"):
        return {"status": "fail", "reason": check.get("reason"), "v0": v0.get("program_id"), "v1": v1.get("program_id")}

    next_id = next_program_id(bank)
    trial_program = {
        "program_id": next_id,
        "parent_ids": parent_ids(v0, v1),
        "source": source,
        "island_score": None,
        "evaluation": None,
        "origin": "deepseek_evolution",
        "feedback_summary": feedback.get("summary", ""),
    }
    updated = append_program(island, trial_program, activate=True)
    leaders = score_island(config, island, top_n=4)
    best_score = float(leaders[0]["island_score"]) if leaders else None
    bank = load_program_bank(island)
    for program in bank:
        if str(program.get("program_id")) == next_id:
            program["island_score"] = best_score
            break
    update_program_bank(island, bank, next_id)
    return {
        "status": "pass",
        "program_id": next_id,
        "parent_ids": trial_program["parent_ids"],
        "active_program_id": load_active_program_id(island),
        "island_score": best_score,
    }


def migrate_islands(candidate_results: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    metric = str(evolution_config(config).get("metric", "baseline_latency_s"))
    replace_fraction = float(evolution_config(config).get("replace_fraction", 0.5))
    island_scores = best_metric_by_island(candidate_results, metric)
    if len(island_scores) < 2:
        return {"status": "skipped", "reason": "not enough evaluated islands", "island_scores": island_scores}

    ranked = sorted(island_scores.items(), key=lambda item: float(item[1]))
    replace_count = max(1, math.floor(len(ranked) * replace_fraction))
    survivors = ranked[: len(ranked) - replace_count]
    targets = ranked[len(ranked) - replace_count :]
    if not survivors:
        return {"status": "skipped", "reason": "no surviving islands", "island_scores": island_scores}

    source_island = survivors[0][0]
    source_program = select_program_pair(load_program_bank(source_island))[0]
    actions: list[dict[str, Any]] = []
    for target_island, target_score in targets:
        if target_island == source_island:
            continue
        replacement_source = source_program.get("source", "")
        if is_enabled(config):
            try:
                adapted = evolve_program(
                    island=target_island,
                    instruction=load_instruction(target_island),
                    v0=source_program,
                    v1=source_program,
                    feedback={
                        "summary": "Cross-island migration. Adapt the source program to the target island instruction.",
                        "suggestions": [],
                    },
                    config=config,
                )
                if adapted and static_check_source(adapted).get("valid"):
                    replacement_source = adapted
            except Exception:
                replacement_source = source_program.get("source", "")
        program = {
            "program_id": "v0",
            "parent_ids": [source_program.get("program_id")],
            "source": replacement_source,
            "island_score": source_program.get("island_score"),
            "evaluation": None,
            "origin": f"migration_from_{source_island}",
        }
        update_program_bank(target_island, [program], "v0")
        actions.append(
            {
                "target_island": target_island,
                "source_island": source_island,
                "target_metric": target_score,
                "source_metric": island_scores[source_island],
            }
        )
    return {"status": "pass", "metric": metric, "island_scores": island_scores, "actions": actions}


def select_program_pair(bank: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not bank:
        raise ValueError("program bank is empty")
    ranked = sorted(bank, key=program_sort_key, reverse=True)
    if len(ranked) == 1:
        return ranked[0], ranked[0]
    return ranked[0], ranked[1]


def parent_ids(v0: dict[str, Any], v1: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for program in (v0, v1):
        program_id = str(program.get("program_id", ""))
        if program_id and program_id not in ids:
            ids.append(program_id)
    return ids


def program_sort_key(program: dict[str, Any]) -> tuple[int, float, int, int]:
    score = program.get("island_score")
    has_score = 1 if isinstance(score, (int, float)) else 0
    score_value = float(score) if has_score else float("-inf")
    source_len = len(str(program.get("source", "")))
    version = int(str(program.get("program_id", "v0")).lstrip("v") or 0) if str(program.get("program_id", "")).startswith("v") else 0
    return (has_score, score_value, -source_len, version)


def next_program_id(bank: list[dict[str, Any]]) -> str:
    max_version = -1
    for program in bank:
        value = str(program.get("program_id", ""))
        if value.startswith("v") and value[1:].isdigit():
            max_version = max(max_version, int(value[1:]))
    return f"v{max_version + 1}"


def best_metric_by_island(candidate_results: list[dict[str, Any]], metric: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for result in candidate_results:
        evaluation = result.get("evaluation") or {}
        value = evaluation.get(metric)
        if value is None:
            continue
        for island in result.get("candidate", {}).get("source_islands", []):
            value_f = float(value)
            if island not in scores or value_f < scores[island]:
                scores[island] = value_f
    return scores


def evolution_config(config: dict[str, Any]) -> dict[str, Any]:
    return dict(config.get("search_config", {}).get("evolution", {}))


def make_evolution_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"evolution_{timestamp}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = output_root / f"evolution_{timestamp}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def sanitize_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(feedback)
    result.pop("raw", None)
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_evolution_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# Evolution Report: {str(summary['status']).upper()}",
        "",
        f"- Run root: `{summary['run_root']}`",
        f"- DeepSeek enabled: `{summary['deepseek_enabled']}`",
        f"- Rounds: {len(summary.get('rounds', []))}",
        "",
        "## Rounds",
        "",
    ]
    for round_report in summary.get("rounds", []):
        evolution = round_report.get("evolution") or {}
        migration = round_report.get("migration") or {}
        feedback = round_report.get("feedback") or {}
        lines.extend(
            [
                f"### Round {round_report.get('round')}",
                "",
                f"- Selected island: `{round_report.get('selected_island')}`",
                f"- Search status: `{round_report.get('search_status')}`",
                f"- Search run directory: `{round_report.get('search_run_dir')}`",
                f"- Feedback status: `{feedback.get('status')}`",
                f"- Feedback summary: {feedback.get('summary', '')}",
                f"- Evolution status: `{evolution.get('status')}`",
                f"- Program id: `{evolution.get('program_id', '')}`",
                f"- Parent ids: `{', '.join(str(item) for item in evolution.get('parent_ids', []))}`",
                f"- Island score: {evolution.get('island_score', '')}",
                f"- Migration status: `{migration.get('status', 'not_run')}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FunSearch-style island evolution.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_evolution(args.config, args.rules, args.output_root)
    print(f"Evolution status: {summary['status']}")
    print(f"Run root: {summary['run_root']}")
    print(f"DeepSeek enabled: {summary['deepseek_enabled']}")
    print(f"Report: {summary.get('evolution_report_md', '')}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
