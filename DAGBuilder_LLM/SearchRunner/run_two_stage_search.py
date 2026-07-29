from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"

sys.path.insert(0, str(ROOT / "DagGenerator"))
sys.path.insert(0, str(ROOT / "SearchRunner"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Evaluation"))
sys.path.insert(0, str(ROOT / "ScoreExpert"))

from generate_dag import load_config  # noqa: E402
from run_dag_rulecheck import run_flow  # noqa: E402
from score_candidates import candidate_without_matrix, score_candidates  # noqa: E402
from ScoreExpert.strategy_space import config_to_cluster, config_to_workload, default_target_scenario, derived_microbatch_size, global_batch_size, local_minibatch_size  # noqa: E402
from evaluate_dag import evaluate_baseline_and_overlap, load_json as load_weighted_dag  # noqa: E402
from OverlapOPT.overlap_opt import run_overlap_opt  # noqa: E402


def sanitize_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value).strip("_")


def make_run_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"two_stage_{timestamp}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = output_root / f"two_stage_{timestamp}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def derive_candidate_config(base_config: dict[str, Any], candidate: dict[str, Any], candidate_dir: Path) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    pp_size = int(candidate["pp_size"])
    tp_size = int(candidate["tp_size"])
    dp_size = int(candidate["dp_size"])
    active_gpus = int(candidate["active_gpus"])
    microbatch_num = int(candidate.get("micro_batch_num", config["parallelism_config"]["microbatch_num"]))
    workload = config_to_workload(config)
    cluster = config_to_cluster(config, default_target_scenario(config))
    pp_strategy = str(config["strategies"]["pp_strategy"])
    dp_strategy = str(config["strategies"]["dp_strategy"])
    dp_granularity = str(config["strategies"]["dp_allreduce_granularity"])

    config["dag_id"] = f"{pp_strategy}_pp{pp_size}_dp{dp_size}_tp{tp_size}_mb{microbatch_num}_candidate"
    config["parallelism_config"]["pp_size"] = pp_size
    config["parallelism_config"]["tp_size"] = tp_size
    config["parallelism_config"]["dp_size"] = dp_size
    config["parallelism_config"]["global_batch_size"] = global_batch_size(workload)
    config["parallelism_config"]["local_minibatch_size"] = local_minibatch_size(workload, dp_size)
    candidate_workload = dict(workload)
    candidate_workload["microbatch_num"] = microbatch_num
    candidate_microbatch_size = derived_microbatch_size(candidate_workload, dp_size)
    config["parallelism_config"]["microbatch_num"] = microbatch_num
    config["parallelism_config"]["microbatch_size"] = candidate_microbatch_size
    config["parallelism_config"]["pp_strategy"] = pp_strategy
    config["parallelism_config"]["dp_strategy"] = dp_strategy
    config["parallelism_config"]["dp_allreduce_granularity"] = dp_granularity
    config["domains"]["num_gpus"] = active_gpus
    config["domains"]["pp_size"] = pp_size
    config["domains"]["tp_size"] = tp_size
    config["domains"]["dp_size"] = dp_size
    config["domains"]["num_layers"] = int(config["model_para"]["num_layers"])
    config["domains"]["num_microbatches"] = microbatch_num
    config["network_config"]["die_num_per_node"] = int(cluster["gpus_per_node"])
    config["strategies"]["pp_strategy"] = pp_strategy
    config["strategies"]["dp_strategy"] = dp_strategy
    config["strategies"]["dp_allreduce_granularity"] = dp_granularity

    value_sim = config.get("value_sim_config", {})
    affinity_group_size = max(1, int(cluster["gpus_per_affinity_group"]))
    value_sim["ranks_per_node"] = int(cluster["gpus_per_node"])
    value_sim["affinity_group_size"] = affinity_group_size
    value_sim["num_affinity_groups"] = max(1, active_gpus // affinity_group_size)
    value_sim["rank_to_affinity_group"] = [
        rank // affinity_group_size
        for rank in range(active_gpus)
    ]
    config["value_sim_config"] = value_sim
    config["candidate_metadata"] = {
        "original_total_gpus": int(candidate.get("placement", {}).get("total_gpus", active_gpus + int(candidate.get("idle_gpus", 0)))),
        "active_gpus": active_gpus,
        "idle_gpus": int(candidate["idle_gpus"]),
        "placement_matrix_path": candidate.get("placement_matrix_path", ""),
        "island_score": float(candidate["island_score"]),
        "source_islands": list(candidate.get("source_islands", [])),
        "micro_batch_num": microbatch_num,
    }
    config["outputs"] = {
        "base_dir": str(candidate_dir.as_posix()),
        "name_template": "dag_artifacts",
        "html_filename": "dag.html",
        "json_filename": "dag.json",
    }
    return config


def write_candidate_config(config: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def run_candidate(
    *,
    base_config: dict[str, Any],
    candidate: dict[str, Any],
    candidate_dir: Path,
    rules_path: Path,
    enable_overlap: bool = True,
) -> dict[str, Any]:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    config = derive_candidate_config(base_config, candidate, candidate_dir)
    config_path = candidate_dir / "candidate_config.json"
    write_candidate_config(config, config_path)

    flow_report = run_flow(
        config_path=config_path,
        rules_path=rules_path,
        html_output=candidate_dir / "dag.html",
        dag_json_output=candidate_dir / "dag.json",
        rule_report_json=candidate_dir / "rule_check_report.json",
        rule_report_md=candidate_dir / "rule_check_report.md",
        weighted_dag_output=candidate_dir / "weighted_dag.json",
        timing_output=candidate_dir / "node_timing_table.json",
        skip_valuesim=False,
        write_reports=False,
    )

    result: dict[str, Any] = {
        "candidate": candidate_without_matrix(candidate),
        "candidate_dir": str(candidate_dir.as_posix()),
        "config": str(config_path.as_posix()),
        "flow_status": flow_report["status"],
        "flow_report": flow_report,
        "overlap_opt": {
            "status": "skipped",
            "reason": "weighted_dag_not_ready",
        },
        "evaluation": None,
    }

    weighted_path = candidate_dir / "weighted_dag.json"
    if flow_report["status"] == "pass" and weighted_path.exists():
        if enable_overlap:
            overlap_report = run_overlap_opt(
                weighted_dag_path=weighted_path,
                overlapped_dag_output=candidate_dir / "overlapped_weighted_dag.json",
                write_reports=False,
            )
            result["overlap_opt"] = overlap_report
            evaluation = evaluate_baseline_and_overlap(
                load_weighted_dag(weighted_path),
                load_weighted_dag(candidate_dir / "overlapped_weighted_dag.json"),
                overlap_report,
            )
        else:
            evaluation = evaluate_baseline_and_overlap(load_weighted_dag(weighted_path))
            result["overlap_opt"] = {
                "status": "disabled",
                "reason": "scoreexpert_search_uses_total_latency_only",
            }
        total_latency = float(evaluation["baseline_latency_s"])
        result["candidate"]["evaluation_latency_s"] = float(evaluation["longest_path_time_s"])
        result["candidate"]["baseline_latency_s"] = float(evaluation["baseline_latency_s"])
        result["candidate"]["total_latency_s"] = total_latency
        overlap = evaluation.get("overlap_evaluation", {})
        result["candidate"]["overlap_latency_s"] = float(overlap.get("overlap_latency_s", total_latency))
        result["candidate"]["overlap_saved_s"] = float(overlap.get("overlap_saved_s", 0.0))
        result["candidate"]["overlap_saved_ratio"] = float(overlap.get("overlap_saved_ratio", 0.0))
        result["candidate"]["score_status"] = "evaluated_formula_candidate"
        result["candidate"]["evaluation_feedback"] = {
            "latency_s": total_latency,
            "total_latency_s": total_latency,
            "baseline_latency_s": float(evaluation["baseline_latency_s"]),
            "overlap_latency_s": float(overlap.get("overlap_latency_s", total_latency)),
            "overlap_saved_s": float(overlap.get("overlap_saved_s", 0.0)),
            "overlap_saved_ratio": float(overlap.get("overlap_saved_ratio", 0.0)),
            "feedback_metric": "total_latency_s",
            "island_score_preserved": float(result["candidate"]["island_score"]),
        }
        evaluation["strategy_scoring_feedback"] = result["candidate"]["evaluation_feedback"]
        result["evaluation"] = {
            **evaluation,
            "outputs": {},
        }
    return result


def build_formula_feedback(candidate_results: list[dict[str, Any]]) -> dict[str, Any]:
    island_results: list[dict[str, Any]] = []
    for result in candidate_results:
        candidate = result.get("candidate", {})
        evaluation = result.get("evaluation")
        if not evaluation:
            continue
        latency = float(evaluation["longest_path_time_s"])
        source_islands = candidate.get("source_islands") or [candidate.get("island")]
        for island in source_islands:
            if island is None:
                continue
            island_results.append(
                {
                    "island": island,
                    "latency_s": latency,
                    "baseline_latency_s": float(evaluation.get("baseline_latency_s", latency)),
                    "overlap_latency_s": float(evaluation.get("overlap_evaluation", {}).get("overlap_latency_s", latency)),
                    "overlap_saved_s": float(evaluation.get("overlap_evaluation", {}).get("overlap_saved_s", 0.0)),
                    "overlap_saved_ratio": float(evaluation.get("overlap_evaluation", {}).get("overlap_saved_ratio", 0.0)),
                    "pp_size": candidate.get("pp_size"),
                    "tp_size": candidate.get("tp_size"),
                    "dp_size": candidate.get("dp_size"),
                    "micro_batch_num": candidate.get("micro_batch_num"),
                    "island_score": candidate.get("island_score"),
                    "candidate_name": candidate.get("candidate_name"),
                    "formula_source": candidate.get("formula_source", ""),
                }
            )
    if not island_results:
        return {
            "status": "no_evaluation_feedback",
            "feedback_metric": "longest_path_latency_s",
            "island_results": [],
            "best_island": None,
            "replacement_actions": [],
        }

    best = min(island_results, key=lambda item: float(item["latency_s"]))
    replacements: list[dict[str, Any]] = []
    for entry in island_results:
        other_latencies = [
            float(item["latency_s"])
            for item in island_results
            if item["island"] != entry["island"]
        ]
        if other_latencies and float(entry["latency_s"]) > max(other_latencies):
            replacements.append(
                {
                    "target_island": entry["island"],
                    "replacement_source_island": best["island"],
                    "reason": "winner_latency_worse_than_all_other_island_winners",
                    "old_program_id": entry.get("program_id"),
                    "new_formula_source": best.get("formula_source", ""),
                    "mutation_operator_preserved": True,
                }
            )

    return {
        "status": "pass",
        "feedback_metric": "longest_path_latency_s",
        "island_results": island_results,
        "best_island": best["island"],
        "best_latency_s": best["latency_s"],
        "replacement_actions": replacements,
    }


def write_summary_json(path: Path, outputs: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(outputs, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def output_root_from_config(config: dict[str, Any]) -> Path:
    outputs = config.get("outputs", {})
    return Path(outputs.get("base_dir", ROOT / "outputs"))


def run_two_stage_search(
    config_path: Path,
    rules_path: Path,
    output_root: Path | None,
    *,
    write_markdown_report: bool = True,
) -> dict[str, Any]:
    base_config = load_config(config_path)
    if output_root is None:
        output_root = output_root_from_config(base_config)
    run_dir = make_run_dir(output_root)
    scoring_result = score_candidates(base_config)

    candidate_results: list[dict[str, Any]] = []
    for candidate in scoring_result["top_candidates"]:
        name = sanitize_name(str(candidate.get("candidate_name") or f"{candidate['island']}_pp{candidate['pp_size']}_mbn{candidate.get('micro_batch_num', 'na')}_tp{candidate['tp_size']}_dp{candidate['dp_size']}"))
        candidate_results.append(
            run_candidate(
                base_config=base_config,
                candidate=candidate,
                candidate_dir=run_dir / name,
                rules_path=rules_path,
            )
        )

    candidate_results.sort(
        key=lambda item: float((item.get("evaluation") or {}).get("longest_path_time_s", float("inf"))),
    )
    overlap_loop = run_overlap_loop_if_enabled(base_config, candidate_results, rules_path, run_dir)
    formula_feedback = build_formula_feedback(candidate_results)
    formula_feedback["applied_replacements"] = []
    formula_feedback["replacement_policy"] = "reported_only_for_funsearch_reset_or_copy"
    overlap_ranking = build_overlap_ranking(candidate_results)
    summary = {
        "status": "pass" if any(result.get("evaluation") for result in candidate_results) else "fail",
        "run_dir": str(run_dir.as_posix()),
        "source_config": str(config_path.as_posix()),
        "rules": str(rules_path.as_posix()),
        "scoring_outputs": {},
        "strategy_scorer_outputs": {},
        "formula_feedback": formula_feedback,
        "overlap_ranking": overlap_ranking,
        "overlap_second_loop": overlap_loop,
        "primary_ranking": "baseline_latency_s",
        "candidate_results": candidate_results,
    }
    if write_markdown_report:
        report_path = run_dir / "run_report.md"
        report_path.write_text(render_run_report(summary), encoding="utf-8")
        summary["run_report_md"] = str(report_path.as_posix())
    return summary


def run_overlap_loop_if_enabled(
    base_config: dict[str, Any],
    candidate_results: list[dict[str, Any]],
    rules_path: Path,
    run_dir: Path,
) -> dict[str, Any]:
    overlap_config = dict(base_config.get("search_config", {}).get("overlapopt", {}))
    if not bool(overlap_config.get("enabled", True)):
        return {"status": "disabled"}
    from overlap_opt_runner import run_overlap_second_loop

    return run_overlap_second_loop(
        base_config=base_config,
        candidate_results=candidate_results,
        rules_path=rules_path,
        run_dir=run_dir,
        top_k=int(overlap_config.get("top_k", 3)),
        max_iterations=int(overlap_config.get("max_iterations", 1)),
    )


def build_overlap_ranking(candidate_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranking: list[dict[str, Any]] = []
    for result in candidate_results:
        evaluation = result.get("evaluation")
        if not evaluation:
            continue
        candidate = result.get("candidate", {})
        overlap = evaluation.get("overlap_evaluation", {})
        ranking.append(
            {
                "candidate_dir": result.get("candidate_dir"),
                "pp_size": candidate.get("pp_size"),
                "tp_size": candidate.get("tp_size"),
                "dp_size": candidate.get("dp_size"),
                "micro_batch_num": candidate.get("micro_batch_num"),
                "baseline_latency_s": float(evaluation.get("baseline_latency_s", evaluation.get("longest_path_time_s"))),
                "overlap_latency_s": float(overlap.get("overlap_latency_s", evaluation.get("longest_path_time_s"))),
                "overlap_saved_s": float(overlap.get("overlap_saved_s", 0.0)),
                "overlap_saved_ratio": float(overlap.get("overlap_saved_ratio", 0.0)),
            }
        )
    ranking.sort(key=lambda item: float(item["overlap_latency_s"]))
    return ranking


def render_run_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# Two-Stage Search Report: {str(summary['status']).upper()}",
        "",
        f"- Run directory: `{summary['run_dir']}`",
        f"- Source config: `{summary['source_config']}`",
        f"- Rules: `{summary['rules']}`",
        f"- Primary ranking: `{summary['primary_ranking']}`",
        "",
        "## Candidate Results",
        "",
    ]
    candidates = summary.get("candidate_results", [])
    if not candidates:
        lines.append("No candidates were evaluated.")
        return "\n".join(lines) + "\n"
    for index, result in enumerate(candidates, start=1):
        candidate = result.get("candidate", {})
        evaluation = result.get("evaluation") or {}
        overlap = evaluation.get("overlap_evaluation", {}) if evaluation else {}
        lines.extend(
            [
                f"### {index}. {candidate.get('candidate_name', 'unknown')}",
                "",
                f"- Strategy: PP={candidate.get('pp_size')}, MBN={candidate.get('micro_batch_num')}, TP={candidate.get('tp_size')}, DP={candidate.get('dp_size')}",
                f"- Source islands: `{', '.join(candidate.get('source_islands', []))}`",
                f"- Island score: {float(candidate.get('island_score', 0.0)):.6f}",
                f"- Flow status: `{result.get('flow_status')}`",
                f"- Baseline latency: {float(evaluation.get('baseline_latency_s', float('nan'))):.9f} s" if evaluation else "- Baseline latency: unavailable",
                f"- Overlap latency: {float(overlap.get('overlap_latency_s', float('nan'))):.9f} s" if overlap else "- Overlap latency: unavailable",
                f"- Overlap saved ratio: {float(overlap.get('overlap_saved_ratio', 0.0)):.4%}" if overlap else "- Overlap saved ratio: unavailable",
                f"- Output directory: `{result.get('candidate_dir')}`",
                "",
            ]
        )
    overlap_loop = summary.get("overlap_second_loop", {})
    if overlap_loop:
        lines.extend(
            [
                "## OverlapOPT Static Rules",
                "",
                f"- Status: `{overlap_loop.get('status')}`",
                f"- Mode: static rules only",
                f"- Evaluated candidates: {overlap_loop.get('evaluated_count', overlap_loop.get('selected_count', 0))}",
                f"- Reason: `{overlap_loop.get('reason', '')}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run two-stage DAGBuilder strategy search.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-root", type=Path, help="Override config.outputs.base_dir.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_two_stage_search(args.config, args.rules, args.output_root)
    print(f"Two-stage status: {report['status']}")
    print(f"Run directory: {report['run_dir']}")
    print(f"Report: {report.get('run_report_md', '')}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
