from __future__ import annotations

from typing import Any


def rank_node(rank: int, cluster: dict[str, Any]) -> int:
    return rank // int(cluster["gpus_per_node"])


def rank_affinity(rank: int, cluster: dict[str, Any]) -> int:
    return rank // int(cluster["gpus_per_affinity_group"])


def group_cross_count(ranks: list[int], cluster: dict[str, Any], kind: str) -> bool:
    if kind == "node":
        return len({rank_node(rank, cluster) for rank in ranks}) > 1
    if kind == "affinity":
        return len({rank_affinity(rank, cluster) for rank in ranks}) > 1
    raise ValueError(f"unsupported group kind: {kind}")


def global_rank(dp_rank: int, pp_stage: int, tp_rank: int, pp_size: int, tp_size: int, dp_size: int, mode: str = "pp_major_huawei") -> int:
    if mode == "dp_major":
        return dp_rank * pp_size * tp_size + pp_stage * tp_size + tp_rank
    if mode == "pp_major_huawei":
        return pp_stage * dp_size * tp_size + dp_rank * pp_size * tp_size + tp_rank
    if mode == "tp_pp_dp":
        return tp_rank * pp_size * dp_size + pp_stage * dp_size + dp_rank
    raise ValueError(f"unsupported rank mapping mode: {mode}")


def estimate_topology_metrics(pp_size: int, tp_size: int, dp_size: int, cluster: dict[str, Any]) -> dict[str, int]:
    tp_cross_node = 0
    tp_cross_affinity = 0
    pp_cross_node = 0
    pp_cross_affinity = 0
    dp_cross_node = 0
    dp_cross_affinity = 0
    mode = str(cluster.get("rank_mapping_mode", "pp_major_huawei"))
    for dp_rank in range(dp_size):
        for pp_stage in range(pp_size):
            ranks = [global_rank(dp_rank, pp_stage, tp_rank, pp_size, tp_size, dp_size, mode) for tp_rank in range(tp_size)]
            tp_cross_node += int(group_cross_count(ranks, cluster, "node"))
            tp_cross_affinity += int(group_cross_count(ranks, cluster, "affinity"))
    for dp_rank in range(dp_size):
        for pp_stage in range(pp_size - 1):
            ranks = [
                global_rank(dp_rank, pp_stage, 0, pp_size, tp_size, dp_size, mode),
                global_rank(dp_rank, pp_stage + 1, 0, pp_size, tp_size, dp_size, mode),
            ]
            pp_cross_node += int(group_cross_count(ranks, cluster, "node"))
            pp_cross_affinity += int(group_cross_count(ranks, cluster, "affinity"))
    for pp_stage in range(pp_size):
        for tp_rank in range(tp_size):
            ranks = [global_rank(dp_rank, pp_stage, tp_rank, pp_size, tp_size, dp_size, mode) for dp_rank in range(dp_size)]
            dp_cross_node += int(group_cross_count(ranks, cluster, "node"))
            dp_cross_affinity += int(group_cross_count(ranks, cluster, "affinity"))
    return {
        "tp_cross_node_groups": tp_cross_node,
        "tp_cross_affinity_groups": tp_cross_affinity,
        "pp_cross_node_links": pp_cross_node,
        "pp_cross_affinity_links": pp_cross_affinity,
        "dp_cross_node_groups": dp_cross_node,
        "dp_cross_affinity_groups": dp_cross_affinity,
    }
