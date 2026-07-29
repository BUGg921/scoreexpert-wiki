from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TimingResult:
    duration_s: float
    payload_bytes: float
    flops: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)


def gbps_to_bytes_per_s(gbps: float) -> float:
    return float(gbps) * 1e9 / 8.0


def effective_bandwidth_bytes_per_s(bandwidth_gbps: float, efficiency: float) -> float:
    if bandwidth_gbps <= 0:
        raise ValueError("bandwidth_gbps must be positive.")
    if not 0 < efficiency <= 1:
        raise ValueError("efficiency must be within (0, 1].")
    return gbps_to_bytes_per_s(bandwidth_gbps) * efficiency


def _layered_collective_time(
    *,
    total_data_size: float,
    domain_size: int,
    ranks_per_node: int,
    affinity_group_size: int,
    hccs_bandwidth_bytes_per_s: float,
    roce_bandwidth_bytes_per_s: float,
    layer1_latency_s: float,
    layer2_latency_s: float,
    layer3_latency_s: float,
    direction: str,
) -> TimingResult:
    if total_data_size < 0:
        raise ValueError("total_data_size must be non-negative.")
    if domain_size <= 0 or ranks_per_node <= 0 or affinity_group_size <= 0:
        raise ValueError("domain_size, ranks_per_node, and affinity_group_size must be positive.")

    n1 = min(int(ranks_per_node), int(domain_size))
    n2 = min(int(affinity_group_size), max(1, int(math.ceil(domain_size / n1))))
    n3 = max(1, int(math.ceil(domain_size / (n1 * n2))))
    details: list[dict[str, Any]] = []

    def add_steps(layer: str, steps: int, bandwidth: float, latency: float, base_bytes: float) -> float:
        total = 0.0
        for step in range(max(0, steps)):
            step_bytes = base_bytes * (2 ** step)
            transfer = 0.0 if bandwidth <= 0 else step_bytes / bandwidth
            step_time = latency + transfer
            total += step_time
            details.append(
                {
                    "layer": layer,
                    "step": step,
                    "payload_bytes": step_bytes,
                    "transfer_s": transfer,
                    "latency_s": latency,
                    "duration_s": step_time,
                }
            )
        return total

    per_rank_bytes = total_data_size / domain_size if domain_size else 0.0
    layer1_steps = n1 - 1 if n1 > 1 else 0
    layer2_steps = int(math.ceil(math.log2(n2))) if n2 > 1 else 0
    layer3_steps = int(math.ceil(math.log2(n3))) if n3 > 1 else 0

    duration = 0.0
    duration += add_steps("intra_node", layer1_steps, hccs_bandwidth_bytes_per_s, layer1_latency_s, per_rank_bytes)
    duration += add_steps("affinity_group", layer2_steps, hccs_bandwidth_bytes_per_s, layer2_latency_s, per_rank_bytes)
    duration += add_steps("inter_node_roce", layer3_steps, roce_bandwidth_bytes_per_s, layer3_latency_s, per_rank_bytes)

    return TimingResult(
        duration_s=duration,
        payload_bytes=total_data_size,
        detail={
            "direction": direction,
            "domain_size": domain_size,
            "ranks_per_node": ranks_per_node,
            "affinity_group_size": affinity_group_size,
            "shard_bytes": total_data_size / domain_size if domain_size else 0.0,
            "steps": details,
        },
    )


def _collective_inputs(config: dict[str, Any]) -> dict[str, Any]:
    network = config["network_config"]
    domains = config["domains"]
    value_sim = config.get("value_sim_config", {})
    model = value_sim.get("dp_collective_model", "hierarchical")
    if model not in {"simple", "hierarchical", "algorithmic"}:
        raise ValueError(f"Unsupported dp_collective_model: {model}")
    ranks_per_node = int(value_sim.get("ranks_per_node", network.get("die_num_per_node", domains["dp_size"])))
    affinity_group_size = int(value_sim.get("affinity_group_size", 1))
    if model == "simple":
        affinity_group_size = 1
        ranks_per_node = int(domains["dp_size"])
    return {
        "domain_size": int(domains["dp_size"]),
        "ranks_per_node": ranks_per_node,
        "affinity_group_size": affinity_group_size,
        "hccs_bandwidth_bytes_per_s": effective_bandwidth_bytes_per_s(
            float(network["hccs_bandwidth_gbps"]),
            float(network["hccs_bandwidth_utilization_ratio"]),
        ),
        "roce_bandwidth_bytes_per_s": effective_bandwidth_bytes_per_s(
            float(network["roce_bandwidth_gbps"]),
            float(network["bandwidth_utilization_ratio"]),
        ),
        "layer1_latency_s": float(network["npu_innode_static_delay_s"]),
        "layer2_latency_s": float(network["npu_innode_static_delay_s"]),
        "layer3_latency_s": float(network["roce_static_delay_s"]),
    }


def estimate_allgather(config: dict[str, Any], payload_bytes: float) -> TimingResult:
    return _layered_collective_time(
        total_data_size=payload_bytes,
        direction="allgather",
        **_collective_inputs(config),
    )


def estimate_reducescatter(config: dict[str, Any], payload_bytes: float) -> TimingResult:
    return _layered_collective_time(
        total_data_size=payload_bytes,
        direction="reducescatter",
        **_collective_inputs(config),
    )


def estimate_allreduce(config: dict[str, Any], payload_bytes: float) -> TimingResult:
    value_sim = config.get("value_sim_config", {})
    mode = value_sim.get("allreduce_mode", "monolithic")
    if mode == "decomposed":
        rs = estimate_reducescatter(config, payload_bytes)
        ag = estimate_allgather(config, payload_bytes)
        return TimingResult(
            duration_s=rs.duration_s + ag.duration_s,
            payload_bytes=payload_bytes,
            detail={"mode": mode, "reducescatter": rs.detail, "allgather": ag.detail},
        )
    if mode != "monolithic":
        raise ValueError(f"Unsupported allreduce_mode: {mode}")

    value_sim = config.get("value_sim_config", {})
    if value_sim.get("dp_collective_model", "hierarchical") == "hierarchical":
        rs = estimate_reducescatter(config, payload_bytes)
        ag = estimate_allgather(config, payload_bytes)
        return TimingResult(
            duration_s=rs.duration_s + ag.duration_s,
            payload_bytes=payload_bytes,
            detail={
                "mode": mode,
                "collective_model": "hierarchical",
                "algorithm": value_sim.get("dp_collective_algorithm", "abstract_layered"),
                "reducescatter": rs.detail,
                "allgather": ag.detail,
            },
        )

    domain_size = int(config["domains"]["dp_size"])
    if domain_size <= 1:
        return TimingResult(duration_s=0.0, payload_bytes=payload_bytes, detail={"mode": mode})
    network = config["network_config"]
    bandwidth = effective_bandwidth_bytes_per_s(
        float(network["hccs_bandwidth_gbps"]),
        float(network["hccs_bandwidth_utilization_ratio"]),
    )
    latency = float(network["npu_innode_static_delay_s"])
    steps = 2 * (domain_size - 1)
    ring_bytes = 2 * payload_bytes * (domain_size - 1) / domain_size
    duration = steps * latency + ring_bytes / bandwidth
    return TimingResult(
        duration_s=duration,
        payload_bytes=payload_bytes,
        detail={"mode": mode, "algorithm": "ring_alpha_beta", "steps": steps, "wire_bytes": ring_bytes},
    )
