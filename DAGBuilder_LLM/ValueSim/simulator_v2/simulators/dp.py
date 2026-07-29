from __future__ import annotations

from typing import Any

from ..topology import Topology
from .collectives import estimate_collective
from .common import TimingResult, operation_config, resolve_payload


_COLLECTIVE_NAMES = {
    "allgather": "all_gather",
    "all_gather": "all_gather",
    "reducescatter": "reduce_scatter",
    "reduce_scatter": "reduce_scatter",
    "allreduce": "all_reduce",
    "all_reduce": "all_reduce",
}


def simulate_dp(node: dict[str, Any], config: dict[str, Any], topology: Topology) -> TimingResult:
    spec = operation_config(config, node)
    domain = str(spec.get("domain") or node.get("domain") or "")
    if not domain:
        raise ValueError(f"DP node {node.get('node_id')} has no communication domain")
    ranks = topology.resolve_group(domain, node)
    raw_collective = str(spec.get("collective") or node.get("op_type") or "")
    collective = _COLLECTIVE_NAMES.get(raw_collective.lower())
    if collective is None:
        task_kind = str(node.get("task_kind") or "")
        if "allgather" in task_kind:
            collective = "all_gather"
        elif "reducescatter" in task_kind:
            collective = "reduce_scatter"
        elif "allreduce" in task_kind:
            collective = "all_reduce"
        else:
            raise ValueError(f"Cannot determine DP collective for {node.get('node_id')}")
    logical, local, scope = resolve_payload(node, spec, len(ranks), collective)
    return estimate_collective(
        category="dp",
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
