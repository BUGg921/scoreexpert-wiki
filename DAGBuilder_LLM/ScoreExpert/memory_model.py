from __future__ import annotations

from typing import Any

from .strategy_space import derived_microbatch_size, global_batch_size, local_minibatch_size


def distribute_layers(num_layers: int, pp_size: int) -> list[list[int]]:
    if pp_size <= 0:
        raise ValueError("pp_size must be positive.")
    base = num_layers // pp_size
    remainder = num_layers % pp_size
    ranges: list[list[int]] = []
    cursor = 0
    for stage in range(pp_size):
        count = base + (1 if stage < remainder else 0)
        ranges.append(list(range(cursor, cursor + count)))
        cursor += count
    return ranges


def precision_bytes(model: dict[str, Any], domain: str) -> float:
    return float(model["precision_factors"][domain]) / 8.0


def transformer_layer_param_count(model: dict[str, Any]) -> int:
    hidden = int(model["hidden_size"])
    ffn = int(model["ffn_hidden_size"])
    return (4 * hidden * hidden) + (2 * hidden * ffn)


def estimate_memory_gb(model: dict[str, Any], workload: dict[str, Any], pp_size: int, tp_size: int, dp_size: int) -> dict[str, float]:
    layer_ranges = distribute_layers(int(model["num_layers"]), pp_size)
    max_layers = max(len(item) for item in layer_ranges)
    param_bytes = max_layers * transformer_layer_param_count(model) * precision_bytes(model, "dp") / max(1, tp_size)
    gradient_bytes = param_bytes
    optimizer_multiplier = float(workload.get("optimizer_state_multiplier", workload.get("optimizer_multiplier", 2.0)))
    optimizer_bytes = param_bytes * optimizer_multiplier

    micro_bs = derived_microbatch_size(workload, dp_size)
    tokens_per_microbatch = micro_bs * int(workload["seq_len"])
    activation_multiplier = float(workload.get("activation_multiplier", workload.get("search_config", {}).get("activation_multiplier", 8.0)))
    pp_strategy = str(workload.get("pp_strategy", "gpipe")).lower()
    if pp_strategy in {"1f1b", "interleaved_1f1b", "dualpipe"}:
        default_live = min(int(workload["microbatch_num"]), 2)
    else:
        default_live = min(int(workload["microbatch_num"]), max(1, pp_size))
    live_microbatches = int(workload.get("live_microbatches_per_stage", workload.get("search_config", {}).get("live_microbatches_per_stage", default_live)))
    live_microbatches = max(1, min(int(workload["microbatch_num"]), live_microbatches))
    activation_bytes = (
        tokens_per_microbatch
        * int(model["hidden_size"])
        * precision_bytes(model, "pp")
        * max_layers
        * activation_multiplier
        * live_microbatches
        / max(1, tp_size)
    )
    total_bytes = param_bytes + gradient_bytes + optimizer_bytes + activation_bytes
    return {
        "params_gb": param_bytes / 1e9,
        "gradients_gb": gradient_bytes / 1e9,
        "optimizer_gb": optimizer_bytes / 1e9,
        "activations_gb": activation_bytes / 1e9,
        "estimated_total_gb": total_bytes / 1e9,
        "global_batch_size": global_batch_size(workload),
        "local_minibatch_size": local_minibatch_size(workload, dp_size),
        "derived_microbatch_size": micro_bs,
        "live_microbatches_per_stage": float(live_microbatches),
        "activation_multiplier": activation_multiplier,
    }


def layer_imbalance(num_layers: int, pp_size: int) -> int:
    counts = [len(item) for item in distribute_layers(num_layers, pp_size)]
    return max(counts) - min(counts)
