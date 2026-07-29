from __future__ import annotations

import argparse
import copy
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"
DEFAULT_OUTPUT = ROOT / "EVALUATION_DATABASE.md"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DagGenerator"))
sys.path.insert(0, str(ROOT / "RuleCheck"))

from DagGenerator.generate_dag import build_dag, load_config  # noqa: E402
from OverlapOPT.rules import apply_overlap_rules, longest_path_latency  # noqa: E402
from RuleCheck.check_dag import RuleChecker, load_json  # noqa: E402
from ScoreExpert.strategy_space import Strategy, enumerate_strategies  # noqa: E402
from ValueSim.simulator_v2.adapter import simulate_dag  # noqa: E402


STRATEGY_PAIRS = (
    ("gpipe", "naive_allreduce_after_backward"),
    ("1f1b", "reduce_scatter_allgather_after_backward"),
)


def main() -> int:
    args = parse_args()
    clean_generated_outputs(ROOT)

    base_config = load_config(args.config)
    rules = load_json(args.rules)
    scenario = base_config.get("search_config", {}).get("cluster_scenarios", [{}])[0]
    base_strategies = enumerate_strategies(base_config, scenario)

    attempted = 0
    skipped = 0
    rows: list[dict[str, Any]] = []
    skipped_rulecheck_for_size = 0
    for strategy in base_strategies:
        for pp_strategy, dp_strategy in STRATEGY_PAIRS:
            attempted += 1
            try:
                row, rulecheck_skipped = evaluate_strategy_pair(
                    base_config,
                    rules,
                    strategy,
                    pp_strategy,
                    dp_strategy,
                    args.rulecheck_node_limit,
                )
                if rulecheck_skipped:
                    skipped_rulecheck_for_size += 1
            except Exception:  # noqa: BLE001 - skipped by design to keep generation fast.
                skipped += 1
                continue
            if row is None:
                skipped += 1
                continue
            rows.append(row)
            if len(rows) % args.write_every == 0:
                rows.sort(key=lambda item: (float(item["overlap_latency_s"]), float(item["baseline_latency_s"])))
                args.output.write_text(
                    render_markdown(
                        rows=rows,
                        config_path=args.config,
                        attempted=attempted,
                        skipped=skipped,
                        base_strategy_count=len(base_strategies),
                        skipped_rulecheck_for_size=skipped_rulecheck_for_size,
                        partial=True,
                    ),
                    encoding="utf-8",
                )
                print(f"Progress: attempted={attempted}, succeeded={len(rows)}, skipped={skipped}", flush=True)

    rows.sort(key=lambda item: (float(item["overlap_latency_s"]), float(item["baseline_latency_s"])))
    args.output.write_text(
        render_markdown(
            rows=rows,
            config_path=args.config,
            attempted=attempted,
            skipped=skipped,
            base_strategy_count=len(base_strategies),
            skipped_rulecheck_for_size=skipped_rulecheck_for_size,
            partial=False,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    print(f"Attempted: {attempted}, succeeded: {len(rows)}, skipped: {skipped}")
    return 0


def evaluate_strategy_pair(
    base_config: dict[str, Any],
    rules: dict[str, Any],
    strategy: Strategy,
    pp_strategy: str,
    dp_strategy: str,
    rulecheck_node_limit: int,
) -> tuple[dict[str, Any] | None, bool]:
    config = config_for_strategy_pair(base_config, strategy, pp_strategy, dp_strategy)
    dag_id = str(config["dag_id"])
    dummy_html = ROOT / "outputs" / "_database_in_memory" / f"{dag_id}.html"
    dummy_json = ROOT / "outputs" / "_database_in_memory" / f"{dag_id}.json"

    dag = build_dag(config, DEFAULT_CONFIG, dummy_html, dummy_json)
    rulecheck_skipped = len(dag.get("nodes", [])) > rulecheck_node_limit
    if not rulecheck_skipped:
        rule_report = RuleChecker(dag, rules, dummy_json).run()
        if int(rule_report.get("summary", {}).get("errors", 0)) > 0:
            return None, rulecheck_skipped

    weighted_dag, _timing_rows = simulate_dag(dag, config)
    overlapped_dag, overlap_report = apply_overlap_rules(weighted_dag)
    baseline_latency_s = longest_path_latency(weighted_dag)
    overlap_latency_s = longest_path_latency(overlapped_dag)
    saved_latency_s = max(0.0, baseline_latency_s - overlap_latency_s)
    overlap_ratio = saved_latency_s / baseline_latency_s if baseline_latency_s > 0 else 0.0
    overlap_plan = overlap_report.get("overlap_plan", [])

    return {
        "dag_id": dag_id,
        "pp_size": strategy.pp_size,
        "tp_size": strategy.tp_size,
        "dp_size": strategy.dp_size,
        "microbatch_num": strategy.micro_batch_num,
        "active_gpus": strategy.active_gpus,
        "idle_gpus": strategy.idle_gpus,
        "pp_strategy": pp_strategy,
        "dp_strategy": dp_strategy,
        "baseline_latency_s": float(baseline_latency_s),
        "overlap_latency_s": float(overlap_latency_s),
        "saved_latency_s": float(saved_latency_s),
        "overlap_ratio": float(overlap_ratio),
        "overlap_event_count": len(overlap_plan),
        "rulecheck_status": "skipped_size_limit" if rulecheck_skipped else "pass",
    }, rulecheck_skipped


def config_for_strategy_pair(
    base_config: dict[str, Any],
    strategy: Strategy,
    pp_strategy: str,
    dp_strategy: str,
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    microbatch_size = float(config["parallelism_config"]["global_batch_size"]) / float(strategy.dp_size * strategy.micro_batch_num)
    dp_short = "rs_ag" if dp_strategy == "reduce_scatter_allgather_after_backward" else "naive_ar"
    config["dag_id"] = (
        f"{pp_strategy}_pp{strategy.pp_size}_dp{strategy.dp_size}_tp{strategy.tp_size}_"
        f"mb{strategy.micro_batch_num}_{dp_short}"
    )

    config["domains"]["num_gpus"] = int(strategy.active_gpus)
    config["domains"]["pp_size"] = int(strategy.pp_size)
    config["domains"]["tp_size"] = int(strategy.tp_size)
    config["domains"]["dp_size"] = int(strategy.dp_size)
    config["domains"]["num_microbatches"] = int(strategy.micro_batch_num)

    parallelism = config["parallelism_config"]
    parallelism["pp_size"] = int(strategy.pp_size)
    parallelism["tp_size"] = int(strategy.tp_size)
    parallelism["dp_size"] = int(strategy.dp_size)
    parallelism["microbatch_num"] = int(strategy.micro_batch_num)
    parallelism["microbatch_size"] = microbatch_size
    parallelism["pp_strategy"] = pp_strategy
    parallelism["dp_strategy"] = dp_strategy
    parallelism["dp_allreduce_granularity"] = "stage"

    config["strategies"]["pp_strategy"] = pp_strategy
    config["strategies"]["dp_strategy"] = dp_strategy
    config["strategies"]["dp_allreduce_granularity"] = "stage"

    value_sim = config["value_sim_config"]
    affinity_group_size = int(value_sim.get("affinity_group_size", 16))
    active_gpus = int(strategy.active_gpus)
    value_sim["num_affinity_groups"] = max(1, math.ceil(active_gpus / max(1, affinity_group_size)))
    value_sim["rank_to_affinity_group"] = [rank // max(1, affinity_group_size) for rank in range(active_gpus)]
    value_sim["ranks_per_node"] = min(int(value_sim.get("ranks_per_node", affinity_group_size)), active_gpus)
    return config


def clean_generated_outputs(root: Path) -> None:
    for dirname in ("outputs", "tests"):
        target = (root / dirname).resolve()
        expected = (root / dirname).resolve()
        if target != expected or target.parent != root.resolve():
            raise RuntimeError(f"Refusing to clean unexpected path: {target}")
        target.mkdir(exist_ok=True)
        for child in target.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def render_markdown(
    *,
    rows: list[dict[str, Any]],
    config_path: Path,
    attempted: int,
    skipped: int,
    base_strategy_count: int,
    skipped_rulecheck_for_size: int,
    partial: bool,
) -> str:
    generated_at = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# Evaluation Latency Database",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Config source: `{config_path}`",
        f"- Base parallel combinations: `{base_strategy_count}`",
        f"- Strategy-pair attempts: `{attempted}`",
        f"- Succeeded: `{len(rows)}`",
        f"- Skipped: `{skipped}`",
        f"- RuleCheck skipped for large DAGs: `{skipped_rulecheck_for_size}`",
        f"- Partial file: `{partial}`",
        "- Strategy pairs: `gpipe + naive_allreduce_after_backward`, `1f1b + reduce_scatter_allgather_after_backward`",
        "- Ranking: sorted by overlap optimized latency ascending",
        "",
        "| Rank | PP | TP | DP | MB | Active GPUs | Idle GPUs | PP Strategy | DP Strategy | Baseline Latency (s) | Overlap Latency (s) | Saved (s) | Overlap Ratio | Events | RuleCheck | DAG ID |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for rank, row in enumerate(rows, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(row["pp_size"]),
                    str(row["tp_size"]),
                    str(row["dp_size"]),
                    str(row["microbatch_num"]),
                    str(row["active_gpus"]),
                    str(row["idle_gpus"]),
                    escape_cell(str(row["pp_strategy"])),
                    escape_cell(str(row["dp_strategy"])),
                    f"{float(row['baseline_latency_s']):.9f}",
                    f"{float(row['overlap_latency_s']):.9f}",
                    f"{float(row['saved_latency_s']):.9f}",
                    f"{float(row['overlap_ratio']):.6%}",
                    str(row["overlap_event_count"]),
                    escape_cell(str(row["rulecheck_status"])),
                    escape_cell(str(row["dag_id"])),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the root Markdown Evaluation latency database.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rulecheck-node-limit", type=int, default=20000)
    parser.add_argument("--write-every", type=int, default=25)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
