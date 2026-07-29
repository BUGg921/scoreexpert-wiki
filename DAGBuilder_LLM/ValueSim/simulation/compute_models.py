from __future__ import annotations

from typing import Any

try:
    from .collective_models import TimingResult, effective_bandwidth_bytes_per_s
except ImportError:  # pragma: no cover - supports direct script execution.
    from collective_models import TimingResult, effective_bandwidth_bytes_per_s


def _tp_link_profile(config: dict[str, Any], link_type: str) -> tuple[float, float]:
    network = config["network_config"]
    if link_type in {"hccs", "innode"}:
        bandwidth_gbps = float(network["hccs_bandwidth_gbps"])
        efficiency = float(network["hccs_bandwidth_utilization_ratio"])
        latency_s = float(network["npu_innode_static_delay_s"])
    elif link_type == "roce":
        bandwidth_gbps = float(network["roce_bandwidth_gbps"])
        efficiency = float(network["bandwidth_utilization_ratio"])
        latency_s = float(network["roce_static_delay_s"])
    else:
        raise ValueError(f"Unsupported TP link type: {link_type}")
    return effective_bandwidth_bytes_per_s(bandwidth_gbps, efficiency), latency_s


def _tp_ranks_for_node(config: dict[str, Any], node: dict[str, Any]) -> list[int]:
    domains = config["domains"]
    pp_size = int(domains["pp_size"])
    tp_size = int(domains["tp_size"])
    dp_rank = int(node.get("dp_rank") or 0)
    pp_stage = int(node.get("pp_stage_id") or 0)
    base = (dp_rank * pp_size * tp_size) + (pp_stage * tp_size)
    return [base + tp_rank for tp_rank in range(tp_size)]


def _tp_domain_crosses_affinity(config: dict[str, Any], node: dict[str, Any]) -> bool:
    rank_map = config.get("value_sim_config", {}).get("rank_to_affinity_group")
    if not rank_map:
        return False
    ranks = _tp_ranks_for_node(config, node)
    groups = {rank_map[rank] for rank in ranks if rank < len(rank_map)}
    return len(groups) > 1


def _estimate_tp_ring_comm(
    config: dict[str, Any],
    node: dict[str, Any],
    full_payload_bytes: float,
    collective_count: int,
) -> TimingResult:
    tp_size = int(config["domains"].get("tp_size", 1))
    if tp_size <= 1 or full_payload_bytes <= 0 or collective_count <= 0:
        return TimingResult(
            duration_s=0.0,
            payload_bytes=0.0,
            detail={
                "model": "tp_ring",
                "tp_size": tp_size,
                "collective_count": collective_count,
                "full_activation_bytes": full_payload_bytes,
                "local_shard_payload_bytes": full_payload_bytes,
                "wire_bytes": 0.0,
            },
        )

    value_sim = config.get("value_sim_config", {})
    crosses_affinity = _tp_domain_crosses_affinity(config, node)
    link_type = (
        value_sim.get("tp_cross_affinity_link_type", "roce")
        if crosses_affinity
        else value_sim.get("tp_intra_affinity_link_type", "hccs")
    )
    bandwidth, latency_s = _tp_link_profile(config, link_type)
    local_payload_bytes = full_payload_bytes / tp_size
    steps_per_collective = 2 * (tp_size - 1)
    wire_bytes_per_collective = 2 * local_payload_bytes * (tp_size - 1) / tp_size
    duration_per_collective = (steps_per_collective * latency_s) + (wire_bytes_per_collective / bandwidth)
    duration = duration_per_collective * collective_count
    return TimingResult(
        duration_s=duration,
        payload_bytes=wire_bytes_per_collective * collective_count,
        detail={
            "model": "tp_ring",
            "tp_size": tp_size,
            "collective_count": collective_count,
            "full_activation_bytes": full_payload_bytes,
            "local_shard_payload_bytes": local_payload_bytes,
            "payload_bytes_per_collective": local_payload_bytes,
            "wire_bytes_per_collective": wire_bytes_per_collective,
            "wire_bytes": wire_bytes_per_collective * collective_count,
            "steps_per_collective": steps_per_collective,
            "latency_s": latency_s,
            "effective_bandwidth_bytes_per_s": bandwidth,
            "link_type": link_type,
            "crosses_affinity": crosses_affinity,
        },
    )


def estimate_tp_compute(config: dict[str, Any], node: dict[str, Any], flops: float, payload_bytes: float) -> TimingResult:
    value_sim = config.get("value_sim_config", {})
    peak_flops = float(value_sim["device_peak_flops"])
    efficiency = float(value_sim["compute_efficiency"])
    tp_size = int(config["domains"].get("tp_size", 1))
    if peak_flops <= 0:
        raise ValueError("value_sim_config.device_peak_flops must be positive.")
    if not 0 < efficiency <= 1:
        raise ValueError("value_sim_config.compute_efficiency must be within (0, 1].")
    if tp_size <= 0:
        raise ValueError("domains.tp_size must be positive.")
    effective_flops = peak_flops * efficiency
    sharded_flops = flops / tp_size if value_sim.get("tp_compute_sharding_enabled", True) else flops
    compute_duration = sharded_flops / effective_flops

    task_kind = node["task_kind"]
    if task_kind == "forward":
        collective_count = int(value_sim.get("tp_forward_collectives_per_layer", 2))
    elif task_kind == "backward":
        collective_count = int(value_sim.get("tp_backward_collectives_per_layer", 2))
    else:
        collective_count = 0

    if value_sim.get("tp_comm_enabled", True):
        comm_model = value_sim.get("tp_comm_model", "ring")
        if comm_model != "ring":
            raise ValueError(f"Unsupported tp_comm_model: {comm_model}")
        comm = _estimate_tp_ring_comm(config, node, payload_bytes, collective_count)
    else:
        comm = TimingResult(
            duration_s=0.0,
            payload_bytes=0.0,
            detail={"model": "disabled", "tp_size": tp_size, "collective_count": collective_count},
        )

    overlap_ratio = float(value_sim.get("tp_comm_overlap_ratio", 0.0))
    if not 0.0 <= overlap_ratio <= 1.0:
        raise ValueError("value_sim_config.tp_comm_overlap_ratio must be within [0, 1].")
    non_overlapped_comm = comm.duration_s * (1.0 - overlap_ratio)
    duration = compute_duration + non_overlapped_comm
    return TimingResult(
        duration_s=duration,
        payload_bytes=comm.payload_bytes,
        flops=sharded_flops,
        detail={
            "model": "tp_supernode_sharded_compute_plus_comm",
            "tp_size": tp_size,
            "original_flops": flops,
            "sharded_flops": sharded_flops,
            "effective_flops": effective_flops,
            "local_compute_s": compute_duration,
            "full_activation_bytes": payload_bytes,
            "local_shard_payload_bytes": payload_bytes / tp_size,
            "tp_comm_s": comm.duration_s,
            "tp_comm_non_overlapped_s": non_overlapped_comm,
            "tp_comm_overlap_ratio": overlap_ratio,
            "tp_comm": comm.detail,
        },
    )
