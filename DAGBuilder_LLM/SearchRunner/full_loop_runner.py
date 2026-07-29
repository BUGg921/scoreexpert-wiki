from __future__ import annotations

import argparse
import copy
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "DagGenerator") not in sys.path:
    sys.path.insert(0, str(ROOT / "DagGenerator"))
if str(ROOT / "SearchRunner") not in sys.path:
    sys.path.insert(0, str(ROOT / "SearchRunner"))

from generate_dag import load_config  # noqa: E402
from SearchRunner.evolution_runner import evolve_one_island, is_enabled, make_evolution_dir, render_evolution_report, summarize_evaluation_feedback  # noqa: E402
from SearchRunner.run_two_stage_search import output_root_from_config, run_two_stage_search  # noqa: E402
from ScoreExpert.island_store import ISLANDS  # noqa: E402


def run_full_loop(config_path: Path, rules_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    if output_root is None:
        output_root = output_root_from_config(config)
    run_root = make_full_loop_dir(output_root)
    outer = dict(config.get("search_config", {}).get("full_loop", {}))
    evolution = dict(config.get("search_config", {}).get("evolution", {}))
    overlap = dict(config.get("search_config", {}).get("overlapopt", {}))
    outer_rounds = int(outer.get("outer_rounds", 5))
    score_rounds = int(outer.get("score_rounds", evolution.get("max_rounds", 5)))
    overlap_iterations = int(outer.get("overlap_iterations", overlap.get("max_iterations", 5)))

    rounds: list[dict[str, Any]] = []
    feedback: dict[str, Any] = {"status": "initial", "summary": "", "suggestions": []}
    for outer_index in range(outer_rounds):
        score_events = []
        for score_index in range(score_rounds):
            island = ISLANDS[(outer_index * score_rounds + score_index) % len(ISLANDS)]
            try:
                result = evolve_one_island(island, feedback, config)
            except Exception as exc:  # noqa: BLE001
                result = {"status": "fail", "reason": str(exc)}
            score_events.append({"score_round": score_index, "island": island, "result": result})

        round_config = copy.deepcopy(config)
        round_config.setdefault("search_config", {}).setdefault("overlapopt", {})["max_iterations"] = overlap_iterations
        temp_config_path = run_root / f"outer_{outer_index:04d}_config.py"
        write_config_module(temp_config_path, round_config)
        search_report = run_two_stage_search(
            temp_config_path,
            rules_path,
            run_root / f"outer_{outer_index:04d}",
            write_markdown_report=False,
        )
        try:
            feedback = summarize_evaluation_feedback(search_report.get("candidate_results", []), config)
        except Exception as exc:  # noqa: BLE001
            feedback = {"status": "fail", "reason": str(exc), "summary": "", "suggestions": []}
        rounds.append(
            {
                "outer_round": outer_index,
                "score_events": score_events,
                "search_status": search_report.get("status"),
                "search_run_dir": search_report.get("run_dir"),
                "overlap_second_loop": search_report.get("overlap_second_loop", {}),
                "feedback": sanitize_feedback(feedback),
            }
        )

    summary = {
        "status": "pass",
        "run_root": str(run_root.as_posix()),
        "deepseek_enabled": is_enabled(config),
        "outer_rounds": outer_rounds,
        "score_rounds_per_outer": score_rounds,
        "overlap_iterations_per_outer": overlap_iterations,
        "rounds": rounds,
    }
    report_path = run_root / "full_loop_report.md"
    report_path.write_text(render_full_loop_report(summary), encoding="utf-8")
    summary["full_loop_report_md"] = str(report_path.as_posix())
    return summary


def write_config_module(path: Path, config: dict[str, Any]) -> None:
    path.write_text("CONFIG = " + repr(config) + "\n", encoding="utf-8")


def make_full_loop_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"full_loop_{timestamp}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = output_root / f"full_loop_{timestamp}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def sanitize_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(feedback)
    result.pop("raw", None)
    return result


def render_full_loop_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# Full Loop Report: {str(summary['status']).upper()}",
        "",
        f"- Run root: `{summary['run_root']}`",
        f"- DeepSeek enabled: `{summary['deepseek_enabled']}`",
        f"- Outer rounds: {summary['outer_rounds']}",
        f"- Score rounds per outer: {summary['score_rounds_per_outer']}",
        f"- Overlap iterations per outer: {summary['overlap_iterations_per_outer']}",
        "",
        "## Rounds",
        "",
    ]
    for item in summary.get("rounds", []):
        overlap = item.get("overlap_second_loop", {})
        lines.extend(
            [
                f"### Outer Round {item.get('outer_round')}",
                "",
                f"- Search status: `{item.get('search_status')}`",
                f"- Search run directory: `{item.get('search_run_dir')}`",
                f"- Overlap mode: `{overlap.get('status', '')}`",
                f"- Overlap reason: `{overlap.get('reason', '')}`",
                "- Score evolution:",
            ]
        )
        for event in item.get("score_events", []):
            result = event.get("result", {})
            lines.append(
                f"  - score_round={event.get('score_round')}, island={event.get('island')}, status={result.get('status')}, program={result.get('program_id', '')}, score={result.get('island_score', '')}"
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run outer ScoreExpert + OverlapOPT optimization loop.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_full_loop(args.config, args.rules, args.output_root)
    print(f"Full loop status: {summary['status']}")
    print(f"Run root: {summary['run_root']}")
    print(f"DeepSeek enabled: {summary['deepseek_enabled']}")
    print(f"Report: {summary.get('full_loop_report_md', '')}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
