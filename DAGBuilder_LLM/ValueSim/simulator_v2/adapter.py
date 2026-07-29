"""Adapter from DAGBuilder's runtime config to the simulator_v2 engine."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .engine import SimulationEngine


def _precision_bytes(config: dict[str, Any], domain: str) -> float:
    bits = float(config["model_para"]["precision_factors"][domain])
    if bits <= 0:
        raise ValueError(f"model_para.precision_factors.{domain} must be positive")
    return bits / 8.0


def _microbatch_tokens(config: dict[str, Any]) -> float:
    parallel = config["parallelism_config"]
    return float(parallel["microbatch_size"]) * int(parallel["seq_len"])


def _compute_payload(config: dict[str, Any], node: dict[str, Any]) -> tuple[float, float]:
    model = config["model_para"]
    tokens = _microbatch_tokens(config)
    hidden = int(model["hidden_size"])
    ffn = int(model["ffn_hidden_size"])
    flops = 8.0 * tokens * hidden * hidden + 4.0 * tokens * hidden * ffn
    if node["task_kind"] == "backward":
        flops *= float(config["value_sim_config"].get("backward_flop_multiplier", 2.0))
    payload_bytes = flops * _precision_bytes(config, "tp") / 8.0
    return flops, payload_bytes


def _pp_activation_bytes(config: dict[str, Any]) -> float:
    full_activation = (
        _microbatch_tokens(config)
        * int(config["model_para"]["hidden_size"])
        * _precision_bytes(config, "pp")
    )
    return full_activation / int(config["domains"]["tp_size"])


def _tp_activation_bytes(config: dict[str, Any]) -> float:
    return (
        _microbatch_tokens(config)
        * int(config["model_para"]["hidden_size"])
        * _precision_bytes(config, "tp")
    )


def _stage_layer_count(config: dict[str, Any], stage_id: int) -> int:
    num_layers = int(config["domains"]["num_layers"])
    pp_size = int(config["domains"]["pp_size"])
    if not 0 <= stage_id < pp_size:
        raise ValueError(f"pp_stage_id {stage_id} is out of range for pp_size {pp_size}")
    base, remainder = divmod(num_layers, pp_size)
    return base + (1 if stage_id < remainder else 0)


def _dp_payload_bytes(config: dict[str, Any], node: dict[str, Any]) -> float:
    legacy = config["value_sim_config"]
    tp_size = int(config["domains"]["tp_size"])
    for key in ("payload_bytes", "bucket_bytes"):
        if node.get(key) not in (None, 0):
            payload = float(node[key])
            return payload if legacy.get("dp_explicit_payload_already_tp_sharded", False) else payload / tp_size
    stage_id = node.get("pp_stage_id")
    if stage_id is not None:
        model = config["model_para"]
        hidden = int(model["hidden_size"])
        ffn = int(model["ffn_hidden_size"])
        layer_parameters = 4 * hidden * hidden + 2 * hidden * ffn
        return (
            _stage_layer_count(config, int(stage_id))
            * layer_parameters
            * _precision_bytes(config, "dp")
            / tp_size
        )
    if legacy.get("dp_bucket_size_bytes") is not None:
        return float(legacy["dp_bucket_size_bytes"])
    raise ValueError(f"Cannot derive DP payload for node {node.get('node_id')}")


def _explicit_hierarchy(
    total_devices: int,
    ranks_per_server: int,
    rank_to_affinity: list[int],
) -> list[dict[str, Any]]:
    affinity_servers: dict[int, list[dict[str, Any]]] = {}
    server_id = 0
    for start in range(0, total_devices, ranks_per_server):
        ranks = list(range(start, min(start + ranks_per_server, total_devices)))
        affinity_ids = {rank_to_affinity[rank] for rank in ranks}
        if len(affinity_ids) != 1:
            raise ValueError(
                "simulator_v2 requires every server to belong to exactly one affinity group"
            )
        affinity_id = affinity_ids.pop()
        affinity_servers.setdefault(affinity_id, []).append(
            {"server_id": server_id, "ranks": ranks}
        )
        server_id += 1
    return [
        {"affinity_group_id": affinity_id, "servers": servers}
        for affinity_id, servers in sorted(affinity_servers.items())
    ]


def _parallel_groups(total_devices: int, pp_size: int, tp_size: int, dp_size: int) -> dict[str, Any]:
    tp_groups = [
        list(range(start, start + tp_size))
        for start in range(0, total_devices, tp_size)
    ]
    dp_groups = [
        [(dp_rank * pp_size + stage) * tp_size + lane for dp_rank in range(dp_size)]
        for stage in range(pp_size)
        for lane in range(tp_size)
    ]
    return {
        "tp": {"size": tp_size, "groups": tp_groups},
        "dp": {"size": dp_size, "groups": dp_groups},
    }


def config_from_dagbuilder(config: dict[str, Any]) -> dict[str, Any]:
    """Translate the active DAGBuilder config into a numerical simulator_v2 config."""
    domains = config["domains"]
    model = config["model_para"]
    parallelism = config["parallelism_config"]
    network = config["network_config"]
    legacy = config["value_sim_config"]

    total_devices = int(domains["num_gpus"])
    pp_size = int(domains["pp_size"])
    tp_size = int(domains["tp_size"])
    dp_size = int(domains["dp_size"])
    if pp_size * tp_size * dp_size != total_devices:
        raise ValueError("pp_size * tp_size * dp_size must equal domains.num_gpus")

    ranks_per_server = min(int(legacy.get("ranks_per_node", total_devices)), total_devices)
    if total_devices % ranks_per_server:
        raise ValueError("domains.num_gpus must be divisible by value_sim_config.ranks_per_node")
    rank_to_affinity = [
        int(value)
        for value in legacy.get(
            "rank_to_affinity_group",
            [rank // max(1, int(legacy.get("affinity_group_size", total_devices))) for rank in range(total_devices)],
        )
    ]
    if len(rank_to_affinity) != total_devices:
        raise ValueError("value_sim_config.rank_to_affinity_group length must match domains.num_gpus")
    device_overrides = {
        int(rank): copy.deepcopy(value)
        for rank, value in legacy.get("device_overrides", {}).items()
    }

    return {
        "model": {
            "name": str(config.get("model_name", "DAGBuilder model")),
            "num_layers": int(model["num_layers"]),
            "hidden_size": int(model["hidden_size"]),
            "ffn_hidden_size": int(model["ffn_hidden_size"]),
            "microbatch_size": float(parallelism["microbatch_size"]),
            "sequence_length": int(parallelism["seq_len"]),
        },
        "topology": {
            "total_devices": total_devices,
            "default_compute_tflops": float(legacy["device_peak_flops"]) / 1e12,
            "affinity_groups": _explicit_hierarchy(
                total_devices,
                ranks_per_server,
                rank_to_affinity,
            ),
            "domains": _parallel_groups(total_devices, pp_size, tp_size, dp_size),
            "device_overrides": device_overrides,
        },
        "network": {
            "bandwidth_unit_bits": 1e9,
            "hccs_intra_server": {
                "bandwidth_gbps": float(network["npu_innode_bandwidth_gbps"]),
                "efficiency": float(network["bandwidth_utilization_ratio"]),
                "latency_s": float(network["npu_innode_static_delay_s"]),
            },
            "hccs_inter_server": {
                "bandwidth_gbps": float(network["hccs_bandwidth_gbps"]),
                "efficiency": float(network["hccs_bandwidth_utilization_ratio"]),
                "latency_s": float(network["npu_innode_static_delay_s"]),
            },
            "roce": {
                "bandwidth_gbps": float(network["roce_bandwidth_gbps"]),
                "efficiency": float(network["bandwidth_utilization_ratio"]),
                "latency_s": float(network["roce_static_delay_s"]),
            },
            "hbm": {
                "bandwidth_gbps": float(network["hbm_bandwidth_gbps"]),
                "efficiency": 1.0,
                "latency_s": 0.0,
            },
        },
        "parallel": {
            "tp_size": tp_size,
            "pp_size": pp_size,
            "dp_size": dp_size,
            "ep_size": 1,
            "cp_size": 1,
        },
        "simulation_flags": {
            "dp": 1,
            "pp": 1,
            "ep": 0,
            "tp": 0,
            "compute": 1,
            "optimizer": 0,
            "other": 0,
        },
        "simulation_overrides": {"node_id": {}, "op_name": {}},
        "algorithms": {
            "operations": {},
            "task_kinds": {
                "pp_forward_send": {"category": "pp", "algorithm": "p2p", "payload_scope": "per_rank_send"},
                "pp_backward_send": {"category": "pp", "algorithm": "p2p", "payload_scope": "per_rank_send"},
                "pp_forward_recv": {"category": "pp", "algorithm": "p2p", "payload_scope": "per_rank_send"},
                "pp_backward_recv": {"category": "pp", "algorithm": "p2p", "payload_scope": "per_rank_send"},
                "dp_allreduce": {
                    "category": "dp",
                    "collective": "all_reduce",
                    "domain": "dp",
                    "algorithm": "ring",
                    "payload_scope": "full_tensor",
                },
                "dp_reducescatter": {
                    "category": "dp",
                    "collective": "reduce_scatter",
                    "domain": "dp",
                    "algorithm": "ring",
                    "payload_scope": "full_tensor",
                },
                "dp_allgather": {
                    "category": "dp",
                    "collective": "all_gather",
                    "domain": "dp",
                    "algorithm": "ring",
                    "payload_scope": "full_tensor",
                },
            },
            "compute": {
                "efficiency": float(legacy["compute_efficiency"]),
                "flops_scope": "global",
                "backward_flop_multiplier": float(legacy.get("backward_flop_multiplier", 2.0)),
                "operation_flops": {},
                "tp_communication": {
                    "enabled": bool(legacy.get("tp_comm_enabled", True)),
                    "algorithm": str(legacy.get("tp_comm_model", "ring")),
                    "forward_collectives": int(
                        legacy.get("tp_forward_collectives_per_layer", 2)
                    ),
                    "backward_collectives": int(
                        legacy.get("tp_backward_collectives_per_layer", 2)
                    ),
                    "overlap_ratio": float(legacy.get("tp_comm_overlap_ratio", 0.0)),
                },
            },
        },
        "profiling": {"enabled": False},
    }


def _prepare_dag(dag: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(dag)
    tp_size = int(config["domains"]["tp_size"])
    for node in prepared.get("nodes", []):
        task_kind = str(node.get("task_kind") or "")
        if task_kind in {"forward", "backward"}:
            flops, payload_bytes = _compute_payload(config, node)
            node["flops"] = flops
            node["payload_bytes"] = payload_bytes
            node["tp_payload_bytes"] = _tp_activation_bytes(config)
        elif task_kind in {"pp_forward_send", "pp_backward_send", "pp_forward_recv", "pp_backward_recv"}:
            node["payload_bytes"] = _pp_activation_bytes(config)
            node["payload_scope"] = "per_rank_send"
        elif task_kind in {"dp_allreduce", "dp_reducescatter", "dp_allgather"}:
            node["payload_bytes"] = _dp_payload_bytes(config, node)
            node["payload_scope"] = "full_tensor"
            stage_id = int(node.get("pp_stage_id") or 0)
            node["domain"] = "dp"
            node["domain_group_index"] = stage_id * tp_size
    return prepared


def simulate_dag(
    dag: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run a DAGBuilder DAG through simulator_v2 while preserving the old call shape."""
    v2_config = config_from_dagbuilder(config)
    engine = SimulationEngine(v2_config)
    weighted, timing_rows, _critical = engine.simulate(_prepare_dag(dag, config))
    return weighted, timing_rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
