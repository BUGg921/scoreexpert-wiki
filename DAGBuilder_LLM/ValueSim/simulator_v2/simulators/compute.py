from __future__ import annotations

from typing import Any

from ..topology import Topology
from .collectives import estimate_collective
from .common import TimingResult


def _compute_ranks(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> tuple[int, ...]:
    explicit = node.get("ranks") or node.get("rank_group")
    if explicit:
        ranks = tuple(int(rank) for rank in explicit)
        for rank in ranks:
            topology.device(rank)
        return ranks
    parallel = config["parallel"]
    tp_size = int(parallel["tp_size"])
    pp_size = int(parallel["pp_size"])
    if node.get("dp_rank") is not None or node.get("pp_stage_id") is not None:
        dp_rank = int(node.get("dp_rank") or 0)
        stage = int(node.get("pp_stage_id") or 0)
        ranks = tuple((dp_rank * pp_size + stage) * tp_size + lane for lane in range(tp_size))
        for rank in ranks:
            topology.device(rank)
        return ranks
    if "tp" in topology.domains:
        return topology.group("tp", int(node.get("domain_group_index") or 0))
    return (0,)


def _derive_flops(node: dict[str, Any], config: dict[str, Any]) -> float:
    if node.get("flops") not in (None, 0):
        return float(node["flops"])
    compute_config = config["algorithms"].get("compute", {})
    node_id = str(node.get("node_id") or "")
    op_name = str(node.get("op_name") or "")
    for key in (node_id, op_name):
        if key in compute_config.get("operation_flops", {}):
            return float(compute_config["operation_flops"][key])

    model = config["model"]
    hidden = int(model["hidden_size"])
    ffn = int(model["ffn_hidden_size"])
    tokens = float(model["microbatch_size"]) * int(model["sequence_length"])
    task = str(node.get("task_kind") or "")
    label = f"{task} {op_name} {node_id}".lower()
    attention = 8.0 * tokens * hidden * hidden
    mlp = 4.0 * tokens * hidden * ffn
    if "attention" in label:
        flops = attention
    elif "expert" in label:
        expert_ffn = int(model.get("expert_ffn_hidden_size", ffn))
        top_k = int(model.get("top_k", 1))
        flops = 4.0 * tokens * hidden * expert_ffn * top_k
    elif "dense" in label or "mlp" in label:
        flops = mlp
    elif task in {"forward", "backward"}:
        flops = attention + mlp
        if "all_layers" in label:
            flops *= int(model["num_layers"])
    else:
        raise ValueError(f"Cannot derive FLOPs for compute node {node_id}; provide node.flops or operation_flops")
    if "backward" in label:
        flops *= float(compute_config.get("backward_flop_multiplier", 2.0))
    return flops


def simulate_compute(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> TimingResult:
    ranks = _compute_ranks(node, config, topology)
    flops = _derive_flops(node, config)
    compute_config = config["algorithms"].get("compute", {})
    efficiency = float(compute_config.get("efficiency", 1.0))
    if not 0 < efficiency <= 1:
        raise ValueError("algorithms.compute.efficiency must be within (0, 1]")
    scope = str(compute_config.get("flops_scope", "global"))
    if scope not in {"global", "per_rank"}:
        raise ValueError("algorithms.compute.flops_scope must be global or per_rank")
    local_flops = flops / len(ranks) if scope == "global" else flops
    rank_durations = {
        rank: local_flops / (topology.device(rank).compute_tflops * 1e12 * efficiency)
        for rank in ranks
    }
    critical_rank = max(rank_durations, key=rank_durations.get)
    compute_duration = rank_durations[critical_rank]

    tp_config = compute_config.get("tp_communication", {})
    tp_enabled = bool(tp_config.get("enabled", False))
    tp_collective_count = 0
    task_kind = str(node.get("task_kind") or "")
    if task_kind == "forward":
        tp_collective_count = int(tp_config.get("forward_collectives", 2))
    elif task_kind == "backward":
        tp_collective_count = int(tp_config.get("backward_collectives", 2))
    if tp_collective_count < 0:
        raise ValueError("algorithms.compute.tp_communication collective counts must be non-negative")

    tp_payload_bytes = float(node.get("tp_payload_bytes") or 0.0)
    tp_comm = None
    tp_comm_duration = 0.0
    if tp_enabled and len(ranks) > 1 and tp_collective_count > 0 and tp_payload_bytes > 0:
        algorithm = str(tp_config.get("algorithm", "ring")).lower()
        if algorithm != "ring":
            raise ValueError(f"Unsupported TP communication algorithm: {algorithm}")
        # DAGBuilder's legacy TP supernode model applies the ring to one
        # TP-local activation shard. Keeping that convention preserves the
        # established model while v2 resolves the actual physical links.
        local_activation_shard = tp_payload_bytes / len(ranks)
        tp_comm = estimate_collective(
            category="tp",
            collective="all_reduce",
            algorithm=algorithm,
            domain="tp",
            ranks=ranks,
            logical_bytes=local_activation_shard,
            local_bytes=local_activation_shard,
            payload_scope="replicated",
            bucket_count=1,
            topology=topology,
            spec={},
        )
        tp_comm_duration = tp_comm.duration_s * tp_collective_count

    overlap_ratio = float(tp_config.get("overlap_ratio", 0.0))
    if not 0.0 <= overlap_ratio <= 1.0:
        raise ValueError("algorithms.compute.tp_communication.overlap_ratio must be within [0, 1]")
    tp_comm_non_overlapped = tp_comm_duration * (1.0 - overlap_ratio)
    duration = compute_duration + tp_comm_non_overlapped
    algorithm = "flops_over_slowest_rank_rate"
    if tp_comm is not None:
        algorithm += "+tp_ring_allreduce"
    return TimingResult(
        duration_s=duration,
        source="numerical",
        category="compute",
        algorithm=algorithm,
        rank_group=ranks,
        logical_payload_bytes=tp_payload_bytes,
        local_payload_bytes=tp_payload_bytes / len(ranks),
        wire_bytes_per_rank=(
            tp_comm.wire_bytes_per_rank * tp_collective_count
            if tp_comm is not None
            else 0.0
        ),
        logical_steps=(
            tp_comm.logical_steps * tp_collective_count
            if tp_comm is not None
            else 0
        ),
        transfer_time_s=(
            tp_comm.transfer_time_s * tp_collective_count
            if tp_comm is not None
            else 0.0
        ),
        latency_time_s=(
            tp_comm.latency_time_s * tp_collective_count
            if tp_comm is not None
            else 0.0
        ),
        flops=flops,
        detail={
            "flops_scope": scope,
            "local_flops_per_rank": local_flops,
            "compute_efficiency": efficiency,
            "rank_compute_tflops": {str(rank): topology.device(rank).compute_tflops for rank in ranks},
            "rank_durations_s": {str(rank): value for rank, value in rank_durations.items()},
            "critical_rank": critical_rank,
            "local_compute_s": compute_duration,
            "tp_full_activation_bytes": tp_payload_bytes,
            "tp_local_activation_shard_bytes": tp_payload_bytes / len(ranks),
            "tp_collective_count": tp_collective_count,
            "tp_comm_s": tp_comm_duration,
            "tp_comm_non_overlapped_s": tp_comm_non_overlapped,
            "tp_comm_overlap_ratio": overlap_ratio,
            "tp_comm": tp_comm.to_dict() if tp_comm is not None else None,
        },
    )
