from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ScoreExpert import score_candidates as score_expert_candidates  # noqa: E402
from ScoreExpert.evaluator import strategy_metrics  # noqa: E402
from ScoreExpert.strategy_space import (  # noqa: E402
    Strategy,
    config_to_cluster,
    config_to_model,
    config_to_workload,
    default_target_scenario,
)
from ScoreExpert.topology_model import global_rank  # noqa: E402


def candidate_without_matrix(candidate: dict[str, Any]) -> dict[str, Any]:
    result = dict(candidate)
    result.pop("placement", None)
    return result


def score_candidates(config: dict[str, Any]) -> dict[str, Any]:
    score_result = score_expert_candidates(config)
    scenario = default_target_scenario(config)
    model = config_to_model(config)
    cluster = config_to_cluster(config, scenario)
    workload = config_to_workload(config)

    candidates: list[dict[str, Any]] = []
    island_candidates = score_result.get("island_candidates") or score_result.get("island_top4", {})
    for island, leaders in island_candidates.items():
        for island_rank, leader in enumerate(leaders, start=1):
            strategy = strategy_from_dict(leader)
            metrics = strategy_metrics(strategy, model, cluster, workload)
            metrics_payload = asdict(metrics)
            metrics_payload["estimated_latency_proxy_s"] = metrics_payload.pop("estimated_iteration_time_s")
            candidate = {
                "island": island,
                "source_islands": [island],
                "source_island_ranks": {island: island_rank},
                "island_rank": island_rank,
                "pp_size": strategy.pp_size,
                "micro_batch_num": strategy.micro_batch_num,
                "tp_size": strategy.tp_size,
                "dp_size": strategy.dp_size,
                "active_gpus": strategy.active_gpus,
                "idle_gpus": strategy.idle_gpus,
                "island_score": float(leader["island_score"]),
                "score": float(leader["island_score"]),
                "scoring_mode": "score_expert",
                "score_status": "score_expert_candidate",
                "rule_check": leader.get("rule_check", {}),
                "metrics": metrics_payload,
                "risk_labels": list((leader.get("rule_check") or {}).get("risk_labels", [])),
                "signature": strategy_signature(strategy),
                "candidate_name": candidate_name(island, strategy),
                "placement": build_placement(
                    config,
                    strategy.pp_size,
                    strategy.micro_batch_num,
                    strategy.tp_size,
                    strategy.dp_size,
                    strategy.active_gpus,
                    strategy.idle_gpus,
                    cluster,
                ),
                "memory_estimate_gb": {
                    "estimated_total_gb": metrics.estimated_total_gb,
                    "global_batch_size": metrics.global_batch_size,
                    "local_minibatch_size": metrics.local_minibatch_size,
                    "derived_microbatch_size": metrics.derived_microbatch_size,
                },
            }
            candidates.append(candidate)

    candidates.sort(key=lambda item: (item["island"], int(item.get("island_rank", 999)), item["signature"]))
    return {
        "status": "pass" if candidates else "fail",
        "scoring_mode": "score_expert",
        "score_expert_result": score_result,
        "top_candidates": candidates,
        "candidate_count": len(candidates),
    }


def strategy_key(strategy: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(strategy["pp_size"]),
        int(strategy.get("micro_batch_num", 1)),
        int(strategy["tp_size"]),
        int(strategy["dp_size"]),
    )


def strategy_from_dict(strategy: dict[str, Any]) -> Strategy:
    pp_size, micro_batch_num, tp_size, dp_size = strategy_key(strategy)
    active_gpus = int(strategy.get("active_gpus", pp_size * tp_size * dp_size))
    idle_gpus = int(strategy.get("idle_gpus", 0))
    return Strategy(pp_size, tp_size, dp_size, micro_batch_num, active_gpus, idle_gpus)


def strategy_signature(strategy: Strategy) -> str:
    return f"pp{strategy.pp_size}|mbn{strategy.micro_batch_num}|tp{strategy.tp_size}|dp{strategy.dp_size}"


def candidate_name(island: str, strategy: Strategy) -> str:
    return f"{island}_pp{strategy.pp_size}_mbn{strategy.micro_batch_num}_tp{strategy.tp_size}_dp{strategy.dp_size}"


def build_placement(
    config: dict[str, Any],
    pp_size: int,
    micro_batch_num: int,
    tp_size: int,
    dp_size: int,
    active_gpus: int,
    idle_gpus: int,
    cluster: dict[str, Any],
) -> dict[str, Any]:
    total_gpus = active_gpus + idle_gpus
    num_layers = int(config["model_para"]["num_layers"])
    layers_per_stage = num_layers // pp_size
    layer_ranges = [
        list(range(stage * layers_per_stage, (stage + 1) * layers_per_stage))
        for stage in range(pp_size)
    ]
    assignments: list[dict[str, Any]] = []
    mode = str(cluster.get("rank_mapping_mode", "pp_major_huawei"))
    for dp_rank in range(dp_size):
        for pp_stage in range(pp_size):
            layers = layer_ranges[pp_stage]
            for tp_rank in range(tp_size):
                rank = global_rank(dp_rank, pp_stage, tp_rank, pp_size, tp_size, dp_size, mode)
                assignments.append(
                    {
                        "global_rank": rank,
                        "dp_rank": dp_rank,
                        "pp_stage": pp_stage,
                        "tp_rank": tp_rank,
                        "first_layer": layers[0],
                        "last_layer": layers[-1],
                    }
                )
    active_ranks = {item["global_rank"] for item in assignments}
    matrix = [
        [1 if rank in active_ranks else 0 for _ in range(num_layers)]
        for rank in range(total_gpus)
    ]
    return {
        "matrix_value": "binary",
        "total_gpus": total_gpus,
        "active_gpus": active_gpus,
        "idle_gpus": idle_gpus,
        "num_layers": num_layers,
        "pp_size": pp_size,
        "micro_batch_num": micro_batch_num,
        "tp_size": tp_size,
        "dp_size": dp_size,
        "global_rank_order": list(range(total_gpus)),
        "layer_ranges_by_pp_stage": layer_ranges,
        "assignments": assignments,
        "matrix": matrix,
    }


def write_score_outputs(scoring_result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    return {}
