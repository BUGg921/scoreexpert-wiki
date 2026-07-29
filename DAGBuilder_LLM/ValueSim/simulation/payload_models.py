from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def bits_to_bytes(bits: float) -> float:
    if bits <= 0:
        raise ValueError("precision bits must be positive.")
    return bits / 8.0


def precision_bytes(config: dict[str, Any], domain: str) -> float:
    model = config["model_para"]
    precision = model["precision_factors"][domain]
    return bits_to_bytes(float(precision))


def microbatch_tokens(config: dict[str, Any]) -> float:
    parallelism = config["parallelism_config"]
    return float(parallelism["microbatch_size"]) * int(parallelism["seq_len"])


def full_activation_bytes(config: dict[str, Any], precision_domain: str) -> float:
    model = config["model_para"]
    tokens = microbatch_tokens(config)
    dtype_bytes = precision_bytes(config, precision_domain)
    return tokens * int(model["hidden_size"]) * dtype_bytes


def tp_sharded_activation_bytes(config: dict[str, Any], precision_domain: str) -> float:
    tp_size = int(config["domains"].get("tp_size", 1))
    if tp_size <= 0:
        raise ValueError("domains.tp_size must be positive.")
    return full_activation_bytes(config, precision_domain) / tp_size


def pp_activation_bytes(config: dict[str, Any]) -> float:
    return tp_sharded_activation_bytes(config, "pp")


def tp_activation_bytes(config: dict[str, Any]) -> float:
    return full_activation_bytes(config, "tp")


def transformer_layer_param_count(config: dict[str, Any]) -> int:
    model = config["model_para"]
    hidden_size = int(model["hidden_size"])
    ffn_hidden_size = int(model["ffn_hidden_size"])
    attention_params = 4 * hidden_size * hidden_size
    mlp_params = 2 * hidden_size * ffn_hidden_size
    return attention_params + mlp_params


def layer_param_bytes(config: dict[str, Any]) -> float:
    return transformer_layer_param_count(config) * precision_bytes(config, "dp")


def layers_for_stage(config: dict[str, Any], stage_id: int) -> list[int]:
    domains = config["domains"]
    num_layers = int(domains["num_layers"])
    pp_size = int(domains["pp_size"])
    if not 0 <= stage_id < pp_size:
        raise ValueError(f"stage_id {stage_id} is out of range for pp_size {pp_size}.")
    base = num_layers // pp_size
    remainder = num_layers % pp_size
    cursor = 0
    for current_stage in range(pp_size):
        count = base + (1 if current_stage < remainder else 0)
        layer_ids = list(range(cursor, cursor + count))
        if current_stage == stage_id:
            return layer_ids
        cursor += count
    raise ValueError(f"Could not resolve layers for stage_id {stage_id}.")


def stage_gradient_bytes(config: dict[str, Any], stage_id: int) -> float:
    tp_size = int(config["domains"].get("tp_size", 1))
    return len(layers_for_stage(config, stage_id)) * layer_param_bytes(config) / tp_size


def dp_node_payload_bytes(config: dict[str, Any], node: dict[str, Any]) -> float:
    value_sim = config.get("value_sim_config", {})
    explicit_bucket = value_sim.get("dp_bucket_size_bytes")
    if "payload_bytes" in node and node["payload_bytes"] not in (None, 0):
        explicit = float(node["payload_bytes"])
        if value_sim.get("dp_explicit_payload_already_tp_sharded", False):
            return explicit
        tp_size = int(config["domains"].get("tp_size", 1))
        if tp_size <= 0:
            raise ValueError("domains.tp_size must be positive.")
        return explicit / tp_size
    if "bucket_bytes" in node and node["bucket_bytes"] not in (None, 0):
        explicit = float(node["bucket_bytes"])
        if value_sim.get("dp_explicit_payload_already_tp_sharded", False):
            return explicit
        tp_size = int(config["domains"].get("tp_size", 1))
        if tp_size <= 0:
            raise ValueError("domains.tp_size must be positive.")
        return explicit / tp_size
    stage_id = node.get("pp_stage_id")
    if stage_id is not None:
        return stage_gradient_bytes(config, int(stage_id))
    if explicit_bucket is not None:
        return float(explicit_bucket)
    return layer_param_bytes(config)


@dataclass(frozen=True)
class ComputePayload:
    flops: float
    payload_bytes: float


def layer_forward_flops(config: dict[str, Any], layer_id: int | None = None) -> float:
    value_sim = config.get("value_sim_config", {})
    explicit = value_sim.get("layer_forward_flops")
    if isinstance(explicit, list) and layer_id is not None:
        return float(explicit[layer_id])
    if explicit is not None and not isinstance(explicit, list):
        return float(explicit)

    model = config["model_para"]
    tokens = microbatch_tokens(config)
    hidden_size = int(model["hidden_size"])
    ffn_hidden_size = int(model["ffn_hidden_size"])
    attention_flops = 8 * tokens * hidden_size * hidden_size
    mlp_flops = 4 * tokens * hidden_size * ffn_hidden_size
    return float(attention_flops + mlp_flops)


def compute_payload(config: dict[str, Any], node: dict[str, Any]) -> ComputePayload:
    task_kind = node["task_kind"]
    layer_id = node.get("global_layer_id")
    forward_flops = layer_forward_flops(config, int(layer_id)) if layer_id is not None else layer_forward_flops(config)
    if task_kind == "forward":
        flops = forward_flops
    elif task_kind == "backward":
        multiplier = float(config.get("value_sim_config", {}).get("backward_flop_multiplier", 2.0))
        flops = forward_flops * multiplier
    else:
        raise ValueError(f"Unsupported compute task_kind for payload: {task_kind}")
    payload = flops * precision_bytes(config, "tp") / 8.0
    return ComputePayload(flops=flops, payload_bytes=payload)
