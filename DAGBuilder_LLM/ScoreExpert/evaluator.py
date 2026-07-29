from __future__ import annotations

import ast
import math
from dataclasses import asdict, dataclass
from typing import Any

from .memory_model import estimate_memory_gb, layer_imbalance
from .strategy_space import Strategy, workload_for_strategy
from .topology_model import estimate_topology_metrics


FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "__import__", "globals", "locals", "random"}
FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.ClassDef)


@dataclass(frozen=True)
class EvaluationMetrics:
    estimated_total_gb: float
    memory_overflow_gb: float
    memory_pressure: float
    pipeline_bubble_ratio: float
    tp_cross_node_groups: int
    tp_cross_affinity_groups: int
    pp_cross_node_links: int
    pp_cross_affinity_links: int
    dp_cross_node_groups: int
    dp_cross_affinity_groups: int
    layer_imbalance: int
    estimated_iteration_time_s: float
    global_batch_size: float
    local_minibatch_size: float
    derived_microbatch_size: float


def static_check_source(source: str, max_program_chars: int = 6000) -> dict[str, Any]:
    if len(source) > max_program_chars:
        return {"valid": False, "reason": "program_too_large"}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"valid": False, "reason": f"syntax_error: {exc}"}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "score_strategy"]
    if len(functions) != 1:
        return {"valid": False, "reason": "must_define_exactly_one_score_strategy"}
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            return {"valid": False, "reason": f"forbidden_syntax: {type(node).__name__}"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            return {"valid": False, "reason": f"forbidden_call: {node.func.id}"}
    params = [item.arg for item in functions[0].args.args]
    if params not in (
        ["strategy", "model_cfg", "topo_cfg", "profile_cfg"],
        ["pp", "tp", "dp", "model", "cluster", "workload"],
    ):
        return {"valid": False, "reason": "unsupported_signature"}
    if not has_unified_base_score(functions[0]):
        return {"valid": False, "reason": "score_strategy_must_initialize_score_to_1000"}
    return {"valid": True, "reason": "pass", "signature": params}


def has_unified_base_score(function: ast.FunctionDef) -> bool:
    for node in function.body:
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "score" not in targets:
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
                return float(value.value) == 1000.0
            return False
    return False


def finite_or_reject(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("score_strategy returned a non-finite score")
    return value


def pipeline_bubble_ratio(pp_size: int, micro_batch_num: int) -> float:
    if micro_batch_num <= 0:
        return 1.0
    return max(0.0, float(pp_size - 1) / float(micro_batch_num + pp_size - 1))


def estimated_iteration_time_s(metrics: dict[str, float], pp_size: int, dp_size: int) -> float:
    return (
        metrics["estimated_total_gb"] * 0.015
        + pipeline_bubble_ratio(pp_size, int(metrics["microbatch_num"])) * 2.0
        + math.log2(max(1, dp_size)) * 0.05
        + metrics["tp_cross_node_groups"] * 0.04
        + metrics["tp_cross_affinity_groups"] * 0.10
        + metrics["dp_cross_node_groups"] * 0.025
        + metrics["dp_cross_affinity_groups"] * 0.08
        + metrics["pp_cross_node_links"] * 0.015
        + metrics["pp_cross_affinity_links"] * 0.04
    )


def strategy_metrics(strategy: Strategy, model: dict[str, Any], cluster: dict[str, Any], workload: dict[str, Any]) -> EvaluationMetrics:
    derived_workload = workload_for_strategy(workload, strategy)
    memory = estimate_memory_gb(model, derived_workload, strategy.pp_size, strategy.tp_size, strategy.dp_size)
    topology = estimate_topology_metrics(strategy.pp_size, strategy.tp_size, strategy.dp_size, cluster)
    raw = {**memory, **topology, "microbatch_num": float(strategy.micro_batch_num)}
    raw["estimated_iteration_time_s"] = estimated_iteration_time_s(raw, strategy.pp_size, strategy.dp_size)
    overflow = max(0.0, memory["estimated_total_gb"] - float(cluster["npu_memory_gb"]))
    return EvaluationMetrics(
        estimated_total_gb=memory["estimated_total_gb"],
        memory_overflow_gb=overflow,
        memory_pressure=memory["estimated_total_gb"] / float(cluster["npu_memory_gb"]),
        pipeline_bubble_ratio=pipeline_bubble_ratio(strategy.pp_size, strategy.micro_batch_num),
        layer_imbalance=layer_imbalance(int(model["num_layers"]), strategy.pp_size),
        estimated_iteration_time_s=raw["estimated_iteration_time_s"],
        global_batch_size=memory["global_batch_size"],
        local_minibatch_size=memory["local_minibatch_size"],
        derived_microbatch_size=memory["derived_microbatch_size"],
        **topology,
    )


def check_strategy_rules(
    strategy: Strategy,
    metrics: EvaluationMetrics,
    model: dict[str, Any],
    cluster: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []
    warnings: list[str] = []

    if metrics.memory_pressure > 1.20:
        violations.append("memory_hard_overflow")
    elif metrics.memory_overflow_gb > 0:
        warnings.append("memory_soft_overflow")
    if metrics.derived_microbatch_size <= 0:
        violations.append("invalid_microbatch_size")
    if strategy.tp_size > int(cluster["gpus_per_node"]):
        violations.append("tp_larger_than_node")
    if int(cluster["gpus_per_node"]) % max(1, strategy.tp_size) != 0:
        violations.append("tp_not_divisible_by_gpus_per_node")
    if int(model["hidden_size"]) % max(1, strategy.tp_size) != 0:
        violations.append("tp_not_divisible_by_hidden_size")
    if strategy.active_gpus > int(cluster["num_gpus"]):
        violations.append("active_gpus_exceed_cluster")

    if metrics.tp_cross_affinity_groups > 0:
        warnings.append("tp_crosses_affinity_group")
    if metrics.tp_cross_node_groups > 0:
        warnings.append("tp_crosses_node")
    if metrics.layer_imbalance > 0:
        warnings.append("pipeline_layer_imbalance")

    return {
        "status": "pass" if not violations else "fail",
        "violations": violations,
        "warnings": warnings,
        "risk_labels": [warning for warning in warnings if warning.endswith("_overflow")],
    }


def metrics_to_dict(metrics: EvaluationMetrics) -> dict[str, Any]:
    return asdict(metrics)
