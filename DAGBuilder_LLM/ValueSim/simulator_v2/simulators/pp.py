from __future__ import annotations

from typing import Any

from ..topology import Topology
from .common import TimingResult, operation_config, resolve_payload


def _pp_pairs(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> list[tuple[int, int]]:
    source_ranks = node.get("src_ranks") or node.get("source_ranks")
    target_ranks = node.get("dst_ranks") or node.get("target_ranks")
    if source_ranks is not None or target_ranks is not None:
        if source_ranks is None or target_ranks is None or len(source_ranks) != len(target_ranks):
            raise ValueError("PP node explicit source/target rank lists must have equal length")
        pairs = [(int(source), int(target)) for source, target in zip(source_ranks, target_ranks)]
        for source, target in pairs:
            topology.device(source)
            topology.device(target)
        return pairs

    parallel = config["parallel"]
    tp_size = int(parallel["tp_size"])
    pp_size = int(parallel["pp_size"])
    dp_rank = int(node.get("dp_rank") or 0)
    stage = int(node.get("pp_stage_id") or 0)
    task = str(node.get("task_kind") or "")
    if "backward" in task:
        source_stage, target_stage = stage, stage - 1
    else:
        source_stage, target_stage = stage, stage + 1
    if not 0 <= source_stage < pp_size or not 0 <= target_stage < pp_size:
        raise ValueError(f"PP node {node.get('node_id')} references an invalid adjacent stage")
    pairs = []
    for lane in range(tp_size):
        source = (dp_rank * pp_size + source_stage) * tp_size + lane
        target = (dp_rank * pp_size + target_stage) * tp_size + lane
        topology.device(source)
        topology.device(target)
        pairs.append((source, target))
    return pairs


def simulate_pp(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> TimingResult:
    spec = operation_config(config, node)
    pairs = _pp_pairs(node, config, topology)
    logical, local, scope = resolve_payload(node, spec, len(pairs), "p2p")
    details: list[dict[str, Any]] = []
    for source, target in pairs:
        link = topology.link(source, target)
        transfer = local / link.bandwidth_bytes_s
        duration = link.latency_s + transfer
        details.append(
            {
                "source_rank": source,
                "target_rank": target,
                "link_kind": link.kind,
                "physical_link_kind": link.physical_kind,
                "link_status": link.status,
                "link_override_scope": link.override_scope,
                "link_override_endpoints": link.override_endpoints,
                "link_note": link.note,
                "payload_bytes": local,
                "transfer_time_s": transfer,
                "latency_s": link.latency_s,
                "duration_s": duration,
            }
        )
    critical = max(details, key=lambda item: item["duration_s"], default=None)
    rank_group = tuple(dict.fromkeys(rank for pair in pairs for rank in pair))
    return TimingResult(
        duration_s=float(critical["duration_s"] if critical else 0.0),
        source="numerical",
        category="pp",
        algorithm="p2p_parallel_lanes",
        collective="p2p",
        domain="pp",
        rank_group=rank_group,
        payload_scope=scope,
        logical_payload_bytes=logical,
        local_payload_bytes=local,
        wire_bytes_per_rank=local,
        logical_steps=1 if pairs else 0,
        transfer_time_s=float(critical["transfer_time_s"] if critical else 0.0),
        latency_time_s=float(critical["latency_s"] if critical else 0.0),
        detail={"parallel_lane_count": len(pairs), "critical_lane": critical, "lanes": details},
    )
