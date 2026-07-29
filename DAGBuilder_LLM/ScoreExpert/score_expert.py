from __future__ import annotations

import ast
import inspect
import math
from dataclasses import asdict
from types import FunctionType
from typing import Any
from typing import Callable

from .evaluator import (
    check_strategy_rules,
    finite_or_reject,
    static_check_source,
    strategy_metrics,
)
from .island_store import ISLANDS, load_score_source, update_leaders
from .strategy_space import (
    Strategy,
    config_to_cluster,
    config_to_model,
    config_to_profile,
    config_to_workload,
    enumerate_strategies,
    scenario_list,
    search_config,
    strategy_to_dict,
    workload_for_strategy,
)


ScoreStrategy = Callable[..., float]


def score_candidates(config: dict[str, Any], top_k: int | None = None, *, update_files: bool = True) -> dict[str, Any]:
    requested_top_k = int(top_k if top_k is not None else search_config(config).get("top_k", 3))
    candidate_pool_per_island = max(64, int(search_config(config).get("candidate_pool_per_island", 64)))
    island_results: dict[str, list[dict[str, Any]]] = {}
    island_candidate_pool: dict[str, list[dict[str, Any]]] = {}

    for island in ISLANDS:
        pool = score_island(config, island, top_n=max(4, candidate_pool_per_island))
        leaders = pool[:4]
        island_results[island] = leaders
        island_candidate_pool[island] = pool
        if update_files:
            update_leaders(island, leaders)

    selected = round_robin_candidates(island_candidate_pool, requested_top_k)
    return {
        "status": "pass" if selected else "fail",
        "scoring_mode": "score_expert",
        "island_top4": island_results,
        "island_candidates": island_candidate_pool,
        "top_candidates": selected,
        "candidate_count": len(selected),
    }


def score_island(config: dict[str, Any], island: str, top_n: int = 4) -> list[dict[str, Any]]:
    source = load_score_source(island)
    sandbox = static_check_source(source, int(search_config(config).get("sandbox", {}).get("max_program_chars", 6000)))
    if not sandbox.get("valid"):
        raise ValueError(f"{island} score_strategy failed safety check: {sandbox.get('reason')}")

    score_fn = compile_score_strategy(source)
    model = config_to_model(config)
    workload = config_to_workload(config)
    profile = config_to_profile(config)
    rows: list[dict[str, Any]] = []

    for scenario in scenario_list(config):
        cluster = config_to_cluster(config, scenario)
        for strategy in enumerate_strategies(config, scenario):
            metrics = strategy_metrics(strategy, model, cluster, workload)
            rule_check = check_strategy_rules(strategy, metrics, model, cluster)
            if rule_check["status"] != "pass":
                continue
            try:
                island_score = finite_or_reject(call_score_strategy(score_fn, strategy, model, cluster, workload, profile))
            except Exception:
                continue
            rows.append(
                {
                    "island": island,
                    "pp_size": strategy.pp_size,
                    "micro_batch_num": strategy.micro_batch_num,
                    "tp_size": strategy.tp_size,
                    "dp_size": strategy.dp_size,
                    "active_gpus": strategy.active_gpus,
                    "idle_gpus": strategy.idle_gpus,
                    "island_score": float(island_score),
                    "scenario": str(scenario.get("name", "target")),
                    "rule_check": rule_check,
                    "metrics": compact_metrics(asdict(metrics)),
                }
            )

    rows.sort(key=lambda item: float(item["island_score"]), reverse=True)
    return rows[:top_n]


def round_robin_candidates(island_results: dict[str, list[dict[str, Any]]], top_k: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    max_depth = max((len(items) for items in island_results.values()), default=0)
    for rank in range(max_depth):
        for island in ISLANDS:
            leaders = island_results.get(island, [])
            if rank >= len(leaders):
                continue
            item = dict(leaders[rank])
            item["island_rank"] = rank + 1
            selected.append(item)
            if len(selected) >= top_k:
                return selected
    return selected


def unique_strategy_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int, int]] = set()
    for item in sorted(candidates, key=lambda row: float(row["island_score"]), reverse=True):
        key = (
            int(item["pp_size"]),
            int(item["tp_size"]),
            int(item["dp_size"]),
            int(item["micro_batch_num"]),
        )
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
    return selected


def compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "estimated_total_gb",
        "memory_pressure",
        "pipeline_bubble_ratio",
        "estimated_iteration_time_s",
        "derived_microbatch_size",
        "tp_cross_affinity_groups",
        "dp_cross_affinity_groups",
        "pp_cross_affinity_links",
        "layer_imbalance",
    )
    result = {key: metrics[key] for key in keys if key in metrics}
    if "estimated_iteration_time_s" in result:
        result["estimated_latency_proxy_s"] = result.pop("estimated_iteration_time_s")
    return result


def compile_score_strategy(source: str) -> ScoreStrategy:
    sandbox = static_check_source(source)
    if not sandbox["valid"]:
        raise ValueError(str(sandbox["reason"]))
    namespace: dict[str, Any] = {
        "__builtins__": {
            "Exception": Exception,
            "abs": abs,
            "dict": dict,
            "float": float,
            "int": int,
            "len": len,
            "max": max,
            "min": min,
            "range": range,
            "sum": sum,
        },
        "math": math,
    }
    exec(compile(ast.parse(source), "<score_expert_program>", "exec"), namespace, namespace)
    fn = namespace.get("score_strategy")
    if not isinstance(fn, FunctionType):
        raise ValueError("score_strategy was not defined.")
    return fn  # type: ignore[return-value]


def call_score_strategy(
    fn: ScoreStrategy,
    strategy: Strategy,
    model: dict[str, Any],
    cluster: dict[str, Any],
    workload: dict[str, Any],
    profile: dict[str, Any],
) -> float:
    params = list(inspect.signature(fn).parameters)
    if params == ["strategy", "model_cfg", "topo_cfg", "profile_cfg"]:
        return float(fn(strategy_to_dict(strategy), model, cluster, profile))
    if params == ["pp", "tp", "dp", "model", "cluster", "workload"]:
        return float(fn(strategy.pp_size, strategy.tp_size, strategy.dp_size, model, cluster, workload_for_strategy(workload, strategy)))
    raise ValueError("unsupported score_strategy signature")
