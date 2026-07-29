from __future__ import annotations

from typing import Any

from ..topology import Topology
from .collectives import estimate_collective
from .common import TimingResult, operation_config, resolve_payload


def _collective_name(node: dict[str, Any], spec: dict[str, Any]) -> str:
    explicit = str(spec.get("collective") or "").lower().replace("-", "_")
    mapping = {
        "allgather": "all_gather",
        "all_gather": "all_gather",
        "reducescatter": "reduce_scatter",
        "reduce_scatter": "reduce_scatter",
        "allreduce": "all_reduce",
        "all_reduce": "all_reduce",
        "alltoall": "all_to_all",
        "all_to_all": "all_to_all",
        "alltoallv": "all_to_all_v",
        "all_to_all_v": "all_to_all_v",
    }
    if explicit in mapping:
        return mapping[explicit]
    task = str(node.get("task_kind") or "").lower()
    if "alltoall" in task:
        return "all_to_all_v" if "metadata" in task or spec.get("variable_payload", False) else "all_to_all"
    if "allgather" in task:
        return "all_gather"
    if "reducescatter" in task:
        return "reduce_scatter"
    if "allreduce" in task:
        return "all_reduce"
    raise ValueError(f"Cannot determine EP collective for {node.get('node_id')}")


def _alltoall(
    node: dict[str, Any],
    spec: dict[str, Any],
    topology: Topology,
    domain: str,
    ranks: tuple[int, ...],
    collective: str,
) -> TimingResult:
    algorithm = str(spec["algorithm"]).lower()
    if algorithm not in {"pairwise", "hierarchical_pairwise"}:
        raise ValueError(f"{collective} supports pairwise or hierarchical_pairwise, not {algorithm}")
    logical, local, scope = resolve_payload(node, spec, len(ranks), collective)
    if scope != "per_rank_send":
        raise ValueError(f"{collective} requires payload_scope='per_rank_send'")
    size = len(ranks)
    if size <= 1 or local == 0:
        return TimingResult(
            duration_s=0.0,
            source="numerical",
            category="ep",
            algorithm=algorithm,
            collective=collective,
            domain=domain,
            rank_group=ranks,
            payload_scope=scope,
            logical_payload_bytes=logical,
            local_payload_bytes=local,
        )

    raw_matrix = spec.get("peer_payload_matrix") or node.get("peer_payload_matrix")
    raw_vector = spec.get("peer_payload_bytes") or node.get("peer_payload_bytes")
    if raw_matrix is not None:
        matrix = [[float(value) for value in row] for row in raw_matrix]
        if len(matrix) != size or any(len(row) != size for row in matrix):
            raise ValueError("peer_payload_matrix must be a square EP-size matrix")
        if any(value < 0 for row in matrix for value in row):
            raise ValueError("peer_payload_matrix values must be non-negative")
        if any(abs(sum(row) - local) > max(1e-6, local * 1e-9) for row in matrix):
            raise ValueError("Every peer_payload_matrix row must sum to the per-rank send payload")
    elif raw_vector is not None:
        vector = [float(value) for value in raw_vector]
        if len(vector) != size or any(value < 0 for value in vector):
            raise ValueError("peer_payload_bytes must contain one non-negative value per EP rank")
        if abs(sum(vector) - local) > max(1e-6, local * 1e-9):
            raise ValueError("peer_payload_bytes must sum to the per-rank send payload")
        matrix = [list(vector) for _ in range(size)]
    else:
        matrix = [[local / size] * size for _ in range(size)]

    forced = spec.get("link_kind")
    rank_times: list[float] = []
    rank_details: list[dict[str, Any]] = []
    for source_index, source in enumerate(ranks):
        vector = matrix[source_index]
        steps: list[dict[str, Any]] = []
        total = 0.0
        for offset in range(1, size):
            target_index = (source_index + offset) % size
            target = ranks[target_index]
            link = topology.link(
                source,
                target,
                str(forced) if algorithm == "pairwise" and forced else None,
            )
            payload = vector[target_index]
            duration = link.latency_s + payload / link.bandwidth_bytes_s
            total += duration
            steps.append(
                {
                    "step": offset - 1,
                    "source_rank": source,
                    "target_rank": target,
                    "payload_bytes": payload,
                    "link_kind": link.kind,
                    "physical_link_kind": link.physical_kind,
                    "link_status": link.status,
                    "link_override_scope": link.override_scope,
                    "link_override_endpoints": link.override_endpoints,
                    "bandwidth_bytes_s": link.bandwidth_bytes_s,
                    "latency_s": link.latency_s,
                    "duration_s": duration,
                }
            )
        rank_times.append(total)
        rank_details.append({"rank": source, "duration_s": total, "steps": steps})
    duration = max(rank_times, default=0.0)
    critical_index = rank_times.index(duration) if rank_times else 0
    critical_steps = rank_details[critical_index]["steps"] if rank_details else []
    transfer = sum(step["payload_bytes"] / step["bandwidth_bytes_s"] for step in critical_steps)
    latency = sum(step["latency_s"] for step in critical_steps)
    critical_source_index = ranks.index(rank_details[critical_index]["rank"]) if rank_details else 0
    wire = local - matrix[critical_source_index][critical_source_index] if rank_details else 0.0
    return TimingResult(
        duration_s=duration,
        source="numerical",
        category="ep",
        algorithm=algorithm,
        collective=collective,
        domain=domain,
        rank_group=ranks,
        payload_scope=scope,
        logical_payload_bytes=logical,
        local_payload_bytes=local,
        wire_bytes_per_rank=wire,
        logical_steps=size - 1,
        transfer_time_s=transfer,
        latency_time_s=latency,
        detail={
            "critical_rank": rank_details[critical_index]["rank"],
            "critical_steps": critical_steps,
            "rank_durations_s": rank_times,
            "uniform_payload": raw_vector is None and raw_matrix is None,
            "variable_payload_matrix": raw_matrix is not None,
        },
    )


def simulate_ep(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> TimingResult:
    spec = operation_config(config, node)
    domain = str(spec.get("domain") or node.get("domain") or "ep")
    ranks = topology.resolve_group(domain, node)
    collective = _collective_name(node, spec)
    if collective in {"all_to_all", "all_to_all_v"}:
        return _alltoall(node, spec, topology, domain, ranks, collective)
    logical, local, scope = resolve_payload(node, spec, len(ranks), collective)
    return estimate_collective(
        category="ep",
        collective=collective,
        algorithm=str(spec["algorithm"]),
        domain=domain,
        ranks=ranks,
        logical_bytes=logical,
        local_bytes=local,
        payload_scope=scope,
        bucket_count=int(spec.get("bucket_count") or node.get("bucket_count") or 1),
        topology=topology,
        spec=spec,
    )
