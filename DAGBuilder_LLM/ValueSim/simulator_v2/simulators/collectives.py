from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from ..topology import LinkProfile, Topology
from .common import TimingResult


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _dominant_link(
    topology: Topology,
    ranks: tuple[int, ...],
    forced: str | None = None,
    payload_bytes: float = 0.0,
    pairs: list[tuple[int, int]] | None = None,
) -> LinkProfile:
    if pairs is not None:
        return topology.critical_link_for_pairs(
            pairs,
            payload_bytes=payload_bytes,
            default_profile_kind=forced,
        )
    if forced:
        return topology.critical_link(
            ranks,
            payload_bytes=payload_bytes,
            default_profile_kind=forced,
        )
    return topology.critical_link(ranks, payload_bytes=payload_bytes)


def _ring_pairs(ranks: tuple[int, ...]) -> list[tuple[int, int]]:
    return [(rank, ranks[(index + 1) % len(ranks)]) for index, rank in enumerate(ranks)]


def _nhr_pair_rounds(ranks: tuple[int, ...]) -> list[list[tuple[int, int]]]:
    rounds: list[list[tuple[int, int]]] = []
    for step in range(int(math.log2(len(ranks)))):
        distance = 1 << step
        rounds.append(
            [(rank, ranks[index ^ distance]) for index, rank in enumerate(ranks)]
        )
    return rounds


def _nhr_round_bytes(full_bytes: float, size: int, collective: str) -> list[float]:
    if size <= 1:
        return []
    if not _is_power_of_two(size):
        raise ValueError("NHR requires a power-of-two communication domain")
    values = [full_bytes / size * (2**step) for step in range(int(math.log2(size)))]
    if collective == "reduce_scatter":
        values.reverse()
    if collective == "all_reduce":
        return list(reversed(values)) + values
    return values


def _flat_collective(
    *,
    category: str,
    collective: str,
    algorithm: str,
    domain: str,
    ranks: tuple[int, ...],
    logical_bytes: float,
    local_bytes: float,
    payload_scope: str,
    bucket_count: int,
    topology: Topology,
    forced_link: str | None,
) -> TimingResult:
    size = len(ranks)
    if size <= 1 or logical_bytes == 0:
        return TimingResult(
            duration_s=0.0,
            source="numerical",
            category=category,
            algorithm=algorithm,
            collective=collective,
            domain=domain,
            rank_group=ranks,
            payload_scope=payload_scope,
            logical_payload_bytes=logical_bytes,
            local_payload_bytes=local_bytes,
            bucket_count=bucket_count,
        )
    bucket_bytes = logical_bytes / bucket_count
    if algorithm == "ring":
        if collective == "all_reduce":
            step_values = [bucket_bytes / size] * (2 * (size - 1))
        elif collective in {"all_gather", "reduce_scatter"}:
            step_values = [bucket_bytes / size] * (size - 1)
        else:
            raise ValueError(f"Ring does not support collective {collective}")
        pair_rounds = [_ring_pairs(ranks)] * len(step_values)
    elif algorithm == "nhr":
        step_values = _nhr_round_bytes(bucket_bytes, size, collective)
        base_pair_rounds = _nhr_pair_rounds(ranks)
        if collective == "reduce_scatter":
            pair_rounds = list(reversed(base_pair_rounds))
        elif collective == "all_reduce":
            pair_rounds = list(reversed(base_pair_rounds)) + base_pair_rounds
        else:
            pair_rounds = base_pair_rounds
    elif algorithm == "recursive_doubling":
        if collective != "all_reduce":
            raise ValueError("recursive_doubling is only supported for all_reduce")
        logical_rounds = int(math.ceil(math.log2(size)))
        step_values = [bucket_bytes] * (2 * logical_rounds)
        base_pair_rounds = _nhr_pair_rounds(ranks)
        pair_rounds = base_pair_rounds + list(reversed(base_pair_rounds))
    else:
        raise ValueError(f"Unsupported flat collective algorithm: {algorithm}")
    round_links = [
        _dominant_link(
            topology,
            ranks,
            forced_link,
            payload_bytes=value,
            pairs=pairs,
        )
        for value, pairs in zip(step_values, pair_rounds)
    ]
    one_bucket_wire = sum(step_values)
    wire_bytes = one_bucket_wire * bucket_count
    transfer = sum(
        value / link.bandwidth_bytes_s for value, link in zip(step_values, round_links)
    ) * bucket_count
    steps = len(step_values) * bucket_count
    latency = sum(link.latency_s for link in round_links) * bucket_count
    dominant = max(
        round_links,
        key=lambda link: link.latency_s + max(step_values, default=0.0) / link.bandwidth_bytes_s,
    )
    return TimingResult(
        duration_s=transfer + latency,
        source="numerical",
        category=category,
        algorithm=algorithm,
        collective=collective,
        domain=domain,
        rank_group=ranks,
        payload_scope=payload_scope,
        logical_payload_bytes=logical_bytes,
        local_payload_bytes=local_bytes,
        wire_bytes_per_rank=wire_bytes,
        logical_steps=steps,
        bucket_count=bucket_count,
        transfer_time_s=transfer,
        latency_time_s=latency,
        detail={
            "link_kind": dominant.kind,
            "physical_link_kind": dominant.physical_kind,
            "link_status": dominant.status,
            "link_override_scope": dominant.override_scope,
            "link_override_endpoints": dominant.override_endpoints,
            "link_note": dominant.note,
            "bandwidth_bytes_s": dominant.bandwidth_bytes_s,
            "latency_per_step_s": dominant.latency_s,
            "steps_per_bucket": len(step_values),
            "round_payload_bytes_per_bucket": step_values,
            "round_links": [
                {
                    "round": index,
                    "link_kind": link.kind,
                    "physical_link_kind": link.physical_kind,
                    "status": link.status,
                    "override_scope": link.override_scope,
                    "override_endpoints": link.override_endpoints,
                    "bandwidth_bytes_s": link.bandwidth_bytes_s,
                    "latency_s": link.latency_s,
                }
                for index, link in enumerate(round_links)
            ],
            "bucket_bytes": bucket_bytes,
        },
    )


def _hierarchy_shape(topology: Topology, ranks: tuple[int, ...]) -> tuple[int, int, int]:
    by_affinity: dict[int, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
    for rank in ranks:
        device = topology.device(rank)
        by_affinity[device.affinity_group_id][device.server_id].append(rank)
    affinity_groups = len(by_affinity)
    servers_per_affinity = {len(servers) for servers in by_affinity.values()}
    ranks_per_server = {len(values) for servers in by_affinity.values() for values in servers.values()}
    if len(servers_per_affinity) != 1 or len(ranks_per_server) != 1:
        raise ValueError("Hierarchical collective requires a symmetric rank placement")
    servers = next(iter(servers_per_affinity))
    local_ranks = next(iter(ranks_per_server))
    if affinity_groups * servers * local_ranks != len(ranks):
        raise ValueError("Hierarchical topology shape does not match domain size")
    if not _is_power_of_two(affinity_groups) or not _is_power_of_two(servers):
        raise ValueError("Hierarchical NHR levels must be powers of two")
    return local_ranks, servers, affinity_groups


def _hierarchy_pair_rounds(
    topology: Topology,
    ranks: tuple[int, ...],
) -> tuple[
    list[list[tuple[int, int]]],
    list[list[tuple[int, int]]],
    list[list[tuple[int, int]]],
]:
    by_affinity: dict[int, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
    for rank in ranks:
        device = topology.device(rank)
        by_affinity[device.affinity_group_id][device.server_id].append(rank)
    affinity_ids = sorted(by_affinity)
    for affinity_id in affinity_ids:
        for server_id in by_affinity[affinity_id]:
            by_affinity[affinity_id][server_id].sort()

    intra_edges: list[tuple[int, int]] = []
    for affinity_id in affinity_ids:
        for server_id in sorted(by_affinity[affinity_id]):
            server_ranks = tuple(by_affinity[affinity_id][server_id])
            intra_edges.extend(_ring_pairs(server_ranks))

    server_rounds: list[list[tuple[int, int]]] = []
    server_count = len(next(iter(by_affinity.values())))
    for step in range(int(math.log2(server_count))):
        edges: list[tuple[int, int]] = []
        for affinity_id in affinity_ids:
            server_ids = sorted(by_affinity[affinity_id])
            for server_index, server_id in enumerate(server_ids):
                peer_server_id = server_ids[server_index ^ (1 << step)]
                edges.extend(zip(by_affinity[affinity_id][server_id], by_affinity[affinity_id][peer_server_id]))
        server_rounds.append(edges)

    affinity_rounds: list[list[tuple[int, int]]] = []
    for step in range(int(math.log2(len(affinity_ids)))):
        edges = []
        for affinity_index, affinity_id in enumerate(affinity_ids):
            peer_affinity_id = affinity_ids[affinity_index ^ (1 << step)]
            source_servers = sorted(by_affinity[affinity_id])
            target_servers = sorted(by_affinity[peer_affinity_id])
            for source_server, target_server in zip(source_servers, target_servers):
                edges.extend(
                    zip(
                        by_affinity[affinity_id][source_server],
                        by_affinity[peer_affinity_id][target_server],
                    )
                )
        affinity_rounds.append(edges)
    return [intra_edges], server_rounds, affinity_rounds


def _hierarchical_collective(
    *,
    category: str,
    collective: str,
    algorithm: str,
    domain: str,
    ranks: tuple[int, ...],
    logical_bytes: float,
    local_bytes: float,
    payload_scope: str,
    bucket_count: int,
    topology: Topology,
    spec: dict[str, Any],
) -> TimingResult:
    if collective not in {"all_gather", "reduce_scatter"}:
        raise ValueError("Hierarchical model currently supports AllGather and ReduceScatter")
    local_ranks, servers, affinity_groups = _hierarchy_shape(topology, ranks)
    bucket_bytes = logical_bytes / bucket_count
    intra_pair_rounds, server_pair_rounds, affinity_pair_rounds = _hierarchy_pair_rounds(
        topology, ranks
    )
    intra_kind = str(spec.get("intra_server_link", "hccs_intra_server"))
    inter_server_kind = str(spec.get("inter_server_link", "hccs_inter_server"))
    cross_affinity_kind = str(spec.get("cross_affinity_link", "roce"))
    intra = topology.critical_link_for_pairs(
        intra_pair_rounds[0],
        payload_bytes=bucket_bytes / local_ranks,
        default_profile_kind=intra_kind,
    )
    inter_server_links = [
        topology.critical_link_for_pairs(
            pairs,
            payload_bytes=bucket_bytes / (local_ranks * servers),
            default_profile_kind=inter_server_kind,
        )
        for pairs in server_pair_rounds
    ]
    cross_affinity_links = [
        topology.critical_link_for_pairs(
            pairs,
            payload_bytes=bucket_bytes / len(ranks),
            default_profile_kind=cross_affinity_kind,
        )
        for pairs in affinity_pair_rounds
    ]
    inter_server = max(
        inter_server_links,
        key=lambda link: link.latency_s + bucket_bytes / (local_ranks * servers) / link.bandwidth_bytes_s,
        default=topology.link_profile(inter_server_kind),
    )
    cross_affinity = max(
        cross_affinity_links,
        key=lambda link: link.latency_s + bucket_bytes / len(ranks) / link.bandwidth_bytes_s,
        default=topology.link_profile(cross_affinity_kind),
    )
    hbm = topology.link_profile("hbm")
    step_details: list[dict[str, Any]] = []

    def append_steps(
        layer: str,
        algo: str,
        values: list[float],
        links: list[LinkProfile],
    ) -> None:
        for index, (value, link) in enumerate(zip(values, links)):
            step_details.append(
                {
                    "layer": layer,
                    "algorithm": algo,
                    "step": index,
                    "payload_bytes": value,
                    "link_kind": link.kind,
                    "physical_link_kind": link.physical_kind,
                    "link_status": link.status,
                    "link_override_scope": link.override_scope,
                    "link_override_endpoints": link.override_endpoints,
                    "link_note": link.note,
                    "bandwidth_bytes_s": link.bandwidth_bytes_s,
                    "transfer_time_s": value / link.bandwidth_bytes_s,
                    "latency_s": link.latency_s,
                }
            )

    staging_bytes_per_bucket = 0.0
    if collective == "all_gather":
        if bool(spec.get("include_local_staging", False)):
            staging_bytes_per_bucket = bucket_bytes / len(ranks)
        append_steps(
            "cross_affinity",
            "NHR",
            [bucket_bytes / len(ranks) * (2**step) for step in range(int(math.log2(affinity_groups)))],
            cross_affinity_links,
        )
        append_steps(
            "in_affinity_cross_server",
            "NHR",
            [bucket_bytes / (local_ranks * servers) * (2**step) for step in range(int(math.log2(servers)))],
            inter_server_links,
        )
        append_steps(
            "in_server",
            "RING",
            [bucket_bytes / local_ranks] * max(0, local_ranks - 1),
            [intra] * max(0, local_ranks - 1),
        )
    else:
        append_steps(
            "in_server",
            "RING",
            [bucket_bytes / local_ranks] * max(0, local_ranks - 1),
            [intra] * max(0, local_ranks - 1),
        )
        append_steps(
            "in_affinity_cross_server",
            "NHR",
            [
                bucket_bytes / (local_ranks * servers) * (2 ** (int(math.log2(servers)) - step - 1))
                for step in range(int(math.log2(servers)))
            ],
            list(reversed(inter_server_links)),
        )
        append_steps(
            "cross_affinity",
            "NHR",
            [
                bucket_bytes / len(ranks) * (2 ** (int(math.log2(affinity_groups)) - step - 1))
                for step in range(int(math.log2(affinity_groups)))
            ],
            list(reversed(cross_affinity_links)),
        )

    network_per_bucket = sum(step["transfer_time_s"] for step in step_details)
    latency_per_bucket = sum(step["latency_s"] for step in step_details)
    wire_per_bucket = sum(step["payload_bytes"] for step in step_details)
    local_copy_bytes_per_bucket = 0.0
    reduction_memory_bytes_per_bucket = 0.0
    local_copy_time = 0.0
    reduction_time = 0.0
    staging_time = 0.0
    staging_latency = 0.0
    if collective == "all_gather" and staging_bytes_per_bucket:
        staging_link = topology.critical_link_for_pairs(
            [pair for pairs in server_pair_rounds for pair in pairs],
            payload_bytes=staging_bytes_per_bucket,
            default_profile_kind=str(spec.get("local_staging_link", "hccs_inter_server")),
        )
        staging_time = staging_bytes_per_bucket / staging_link.bandwidth_bytes_s * bucket_count
        staging_latency = staging_link.latency_s * bucket_count
    if collective == "reduce_scatter" and bool(spec.get("include_executor_memory", False)):
        local_copy_bytes_per_bucket = bucket_bytes
        reduction_memory_accesses = int(spec.get("reduction_memory_accesses_per_byte", 4))
        if reduction_memory_accesses != 4:
            raise ValueError("The v2 ReduceScatter executor ledger requires exactly four HBM movements")
        reduction_memory_bytes_per_bucket = wire_per_bucket * reduction_memory_accesses
        local_copy_time = local_copy_bytes_per_bucket / hbm.bandwidth_bytes_s * bucket_count
        reduction_time = reduction_memory_bytes_per_bucket / hbm.bandwidth_bytes_s * bucket_count

    network_time = network_per_bucket * bucket_count
    latency = latency_per_bucket * bucket_count + staging_latency
    wire_bytes = wire_per_bucket * bucket_count
    transfer = network_time + staging_time + local_copy_time + reduction_time
    steps_per_bucket = len(step_details) + (1 if staging_bytes_per_bucket else 0)
    duration = transfer + latency
    return TimingResult(
        duration_s=duration,
        source="numerical",
        category=category,
        algorithm=algorithm,
        collective=collective,
        domain=domain,
        rank_group=ranks,
        payload_scope=payload_scope,
        logical_payload_bytes=logical_bytes,
        local_payload_bytes=local_bytes,
        wire_bytes_per_rank=wire_bytes,
        logical_steps=steps_per_bucket * bucket_count,
        bucket_count=bucket_count,
        transfer_time_s=transfer,
        latency_time_s=latency,
        local_copy_time_s=local_copy_time + staging_time,
        reduction_time_s=reduction_time,
        detail={
            "network_steps_per_bucket": len(step_details),
            "steps_per_bucket": steps_per_bucket,
            "network_transfer_time_s": network_time,
            "local_staging_time_s": staging_time,
            "local_staging_bytes_per_rank": staging_bytes_per_bucket * bucket_count,
            "local_copy_bytes_per_rank": local_copy_bytes_per_bucket * bucket_count,
            "reduction_memory_bytes_per_rank": reduction_memory_bytes_per_bucket * bucket_count,
            "reduction_memory_accesses_per_byte": 4 if reduction_memory_bytes_per_bucket else 0,
            "bucket_bytes": bucket_bytes,
            "hierarchy": {
                "ranks_per_server": local_ranks,
                "servers_per_affinity_group": servers,
                "affinity_group_count": affinity_groups,
            },
            "steps": step_details,
        },
    )


def estimate_collective(
    *,
    category: str,
    collective: str,
    algorithm: str,
    domain: str,
    ranks: tuple[int, ...],
    logical_bytes: float,
    local_bytes: float,
    payload_scope: str,
    bucket_count: int,
    topology: Topology,
    spec: dict[str, Any],
) -> TimingResult:
    explicit_buckets = spec.get("bucket_sizes_bytes")
    if explicit_buckets is not None:
        sizes = [float(value) for value in explicit_buckets]
        if not sizes or any(value <= 0 for value in sizes):
            raise ValueError("bucket_sizes_bytes must be a non-empty list of positive byte sizes")
        if abs(sum(sizes) - logical_bytes) > max(1e-6, logical_bytes * 1e-9):
            raise ValueError("bucket_sizes_bytes must sum to the logical collective payload")
        nested_spec = dict(spec)
        nested_spec.pop("bucket_sizes_bytes", None)
        buckets = [
            estimate_collective(
                category=category,
                collective=collective,
                algorithm=algorithm,
                domain=domain,
                ranks=ranks,
                logical_bytes=size,
                local_bytes=local_bytes * size / logical_bytes if logical_bytes else 0.0,
                payload_scope=payload_scope,
                bucket_count=1,
                topology=topology,
                spec=nested_spec,
            )
            for size in sizes
        ]
        return TimingResult(
            duration_s=sum(item.duration_s for item in buckets),
            source="numerical",
            category=category,
            algorithm=algorithm,
            collective=collective,
            domain=domain,
            rank_group=ranks,
            payload_scope=payload_scope,
            logical_payload_bytes=logical_bytes,
            local_payload_bytes=local_bytes,
            wire_bytes_per_rank=sum(item.wire_bytes_per_rank for item in buckets),
            logical_steps=sum(item.logical_steps for item in buckets),
            bucket_count=len(buckets),
            transfer_time_s=sum(item.transfer_time_s for item in buckets),
            latency_time_s=sum(item.latency_time_s for item in buckets),
            local_copy_time_s=sum(item.local_copy_time_s for item in buckets),
            reduction_time_s=sum(item.reduction_time_s for item in buckets),
            detail={
                "bucket_mode": "explicit",
                "bucket_sizes_bytes": sizes,
                "buckets": [item.to_dict() for item in buckets],
            },
        )
    normalized = algorithm.lower()
    if normalized in {"hierarchical", "hierarchical_nhr_ring", "hierarchical_ring_nhr"}:
        return _hierarchical_collective(
            category=category,
            collective=collective,
            algorithm=normalized,
            domain=domain,
            ranks=ranks,
            logical_bytes=logical_bytes,
            local_bytes=local_bytes,
            payload_scope=payload_scope,
            bucket_count=bucket_count,
            topology=topology,
            spec=spec,
        )
    return _flat_collective(
        category=category,
        collective=collective,
        algorithm=normalized,
        domain=domain,
        ranks=ranks,
        logical_bytes=logical_bytes,
        local_bytes=local_bytes,
        payload_scope=payload_scope,
        bucket_count=bucket_count,
        topology=topology,
        forced_link=spec.get("link_kind"),
    )
