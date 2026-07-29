from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .config import ScenarioConfig
from .strategy import Strategy, communication_groups, rank_mapping


def _ensure_repo_importable(config: ScenarioConfig) -> None:
    value = str(config.repository_root)
    if value not in sys.path:
        sys.path.insert(0, value)


def estimate_memory_gb(strategy: Strategy, config: ScenarioConfig) -> dict[str, float]:
    model, workload = config.model, config.workload
    max_layers = int(model["num_layers"]) // strategy.pp
    h, ffn = int(model["hidden_size"]), int(model["ffn_hidden_size"])
    per_layer = 4 * h * h + 2 * h * ffn
    param = max_layers * per_layer * int(model["gradient_dtype_bytes"]) / strategy.tp
    micro_bs = int(workload["global_batch_size"]) / strategy.dp / strategy.micro_batch_num
    live = min(strategy.micro_batch_num, 2 if strategy.schedule == "1f1b" else strategy.pp)
    activations = (
        micro_bs * int(workload["sequence_length"]) * h * int(model["dtype_bytes"])
        * max_layers * float(workload["activation_multiplier"]) * max(1, live) / strategy.tp
    )
    total = param * (2 + float(workload["optimizer_state_multiplier"])) + activations
    return {
        "params_gb": param / 1e9,
        "activations_gb": activations / 1e9,
        "estimated_total_gb": total / 1e9,
        "capacity_gb": float(config.memory["device_capacity_gb"]),
        "oom": total / 1e9 > float(config.memory["device_capacity_gb"]),
    }


def _trim_topology(strategy: Strategy, config: ScenarioConfig) -> dict[str, Any]:
    active = set(range(strategy.active_gpus))
    affinities = []
    for affinity in config.topology["affinity_groups"]:
        servers = []
        for server in affinity["servers"]:
            ranks = [int(rank) for rank in server["ranks"] if int(rank) in active]
            if ranks:
                servers.append({"server_id": int(server["server_id"]), "ranks": ranks})
        if servers:
            affinities.append(
                {"affinity_group_id": int(affinity["affinity_group_id"]), "servers": servers}
            )
    groups = communication_groups(strategy)
    topology = {
        "total_devices": strategy.active_gpus,
        "default_compute_tflops": float(config.topology["default_compute_tflops"]),
        "affinity_groups": affinities,
        "domains": {
            name: {"size": len(values[0]), "groups": values}
            for name, values in groups.items()
        },
        "device_overrides": {
            int(rank): copy.deepcopy(value)
            for rank, value in config.topology.get("device_overrides", {}).items()
            if int(rank) in active
        },
        "link_overrides": copy.deepcopy(config.topology.get("link_overrides", [])),
    }
    return topology


def _generator_config(strategy: Strategy, config: ScenarioConfig, artifact_dir: Path) -> dict[str, Any]:
    model, workload = config.model, config.workload
    network = config.network
    dp_name = (
        "naive_allreduce_after_backward"
        if strategy.dp_communication == "allreduce"
        else "reduce_scatter_allgather_after_backward"
    )
    return {
        "dag_id": strategy.signature,
        "model_para": {
            "num_layers": int(model["num_layers"]),
            "hidden_size": int(model["hidden_size"]),
            "ffn_hidden_size": int(model["ffn_hidden_size"]),
            "precision_factors": {"tp": 16, "dp": 32, "pp": 16, "ep": 16, "sp": 16},
        },
        "parallelism_config": {
            "global_batch_size": int(workload["global_batch_size"]),
            "seq_len": int(workload["sequence_length"]),
            "dp_size": strategy.dp,
            "tp_size": strategy.tp,
            "pp_size": strategy.pp,
            "vpp_size": 1,
            "sp_ce_size": 1,
            "sp_me_size": 1,
            "microbatch_num": strategy.micro_batch_num,
            "microbatch_size": int(workload["global_batch_size"]) / strategy.dp / strategy.micro_batch_num,
            "pp_strategy": strategy.schedule,
            "dp_strategy": dp_name,
            "dp_allreduce_granularity": "stage",
        },
        "network_config": {
            "npu_innode_static_delay_s": float(network["hccs_intra_server"]["latency_s"]),
            "roce_static_delay_s": float(network["roce"]["latency_s"]),
            "npu_innode_bandwidth_gbps": float(network["hccs_intra_server"]["bandwidth_gbps"]),
            "hccs_bandwidth_gbps": float(network["hccs_inter_server"]["bandwidth_gbps"]),
            "roce_bandwidth_gbps": float(network["roce"]["bandwidth_gbps"]),
            "bandwidth_utilization_ratio": float(network["roce"]["efficiency"]),
            "hccs_bandwidth_utilization_ratio": float(network["hccs_inter_server"]["efficiency"]),
            "die_num_per_node": 16,
            "alltoall_concurrency": 16,
            "hbm_bandwidth_gbps": float(network["hbm"]["bandwidth_gbps"]),
            "npu_memory_gb": float(config.memory["device_capacity_gb"]),
        },
        "immutable_config_sections": ["model_para", "network_config"],
        "domains": {
            "num_gpus": strategy.active_gpus,
            "dp_size": strategy.dp,
            "tp_size": strategy.tp,
            "pp_size": strategy.pp,
            "num_layers": int(model["num_layers"]),
            "num_microbatches": strategy.micro_batch_num,
        },
        "strategies": {
            "pp_strategy": strategy.schedule,
            "dp_strategy": dp_name,
            "dp_allreduce_granularity": "stage",
        },
        "color_theme": {
            "forward_node_color": "#D7E7F5", "backward_node_color": "#FCE4CC",
            "pp_comm_node_color": "#ECE4FF", "dp_comm_node_color": "#DDF3DD",
            "control_node_color": "#F2F2F2", "data_dependency_edge_color": "#2F6FB3",
            "resource_dependency_edge_color": "#2E8B57", "control_edge_color": "#333333",
        },
        "outputs": {
            "base_dir": str(artifact_dir), "html_filename": "dag.html", "json_filename": "dag.json"
        },
    }


def _rank(stage: int, dp_rank: int, tp_rank: int, strategy: Strategy) -> int:
    return ((stage * strategy.dp) + dp_rank) * strategy.tp + tp_rank


def _annotate_dag(dag: dict[str, Any], strategy: Strategy, config: ScenarioConfig) -> None:
    model, workload = config.model, config.workload
    layers_per_stage = int(model["num_layers"]) // strategy.pp
    h, ffn = int(model["hidden_size"]), int(model["ffn_hidden_size"])
    micro_bs = int(workload["global_batch_size"]) / strategy.dp / strategy.micro_batch_num
    tokens = micro_bs * int(workload["sequence_length"])
    forward_flops = 8.0 * tokens * h * h + 4.0 * tokens * h * ffn
    activation_bytes = tokens * h * int(model["dtype_bytes"])
    stage_param_elements = layers_per_stage * (4 * h * h + 2 * h * ffn)
    groups = communication_groups(strategy)
    for node in dag["nodes"]:
        task = str(node.get("task_kind") or "")
        stage = int(node.get("pp_stage_id") or 0)
        dp_rank = int(node.get("dp_rank") or 0)
        if task in {"forward", "backward"}:
            node["ranks"] = [_rank(stage, dp_rank, lane, strategy) for lane in range(strategy.tp)]
            node["flops"] = forward_flops * (
                float(workload["backward_flop_multiplier"]) if task == "backward" else 1.0
            )
            node["tp_payload_bytes"] = activation_bytes
            node["tp_communication"] = {
                "collective": "all_reduce",
                "algorithm": "ring",
                "domain": "tp",
                "payload_bytes": activation_bytes,
                "payload_scope": "replicated",
                "collective_count": 2,
            }
        elif task in {"pp_forward_send", "pp_backward_send"}:
            target_stage = stage - 1 if "backward" in task else stage + 1
            node["src_ranks"] = [_rank(stage, dp_rank, lane, strategy) for lane in range(strategy.tp)]
            node["dst_ranks"] = [_rank(target_stage, dp_rank, lane, strategy) for lane in range(strategy.tp)]
            node["payload_scope"] = "per_rank_send"
            node["payload_bytes"] = activation_bytes / strategy.tp
        elif task.startswith("dp_"):
            node["domain"] = "dp"
            node["rank_groups"] = [
                group for index, group in enumerate(groups["dp"]) if index // strategy.tp == stage
            ]
            node["payload_scope"] = "full_tensor"
            node["payload_elements"] = stage_param_elements
            node["dtype_bytes"] = int(model["gradient_dtype_bytes"])
            node["bucket_count"] = 1
    dag["rank_mapping"] = rank_mapping(strategy)
    dag["communication_groups"] = groups


def _simulator_config(strategy: Strategy, config: ScenarioConfig) -> dict[str, Any]:
    model, workload = config.model, config.workload
    common_dp = {
        "domain": "dp", "algorithm": "ring", "payload_scope": "full_tensor", "bucket_count": 1
    }
    return {
        "model": {
            "num_layers": int(model["num_layers"]), "hidden_size": int(model["hidden_size"]),
            "ffn_hidden_size": int(model["ffn_hidden_size"]),
            "microbatch_size": int(workload["global_batch_size"]) / strategy.dp / strategy.micro_batch_num,
            "sequence_length": int(workload["sequence_length"]),
        },
        "topology": _trim_topology(strategy, config),
        "network": copy.deepcopy(config.network),
        "parallel": {
            "tp_size": strategy.tp, "pp_size": strategy.pp, "dp_size": strategy.dp,
            "ep_size": 1, "cp_size": 1,
        },
        "simulation_flags": {
            "dp": 1, "pp": 1, "ep": 1, "tp": 1, "compute": 1, "optimizer": 1, "other": 1,
        },
        "simulation_overrides": {"node_id": {}, "op_name": {}},
        "algorithms": {
            "operations": {},
            "task_kinds": {
                "dp_allreduce": common_dp | {"collective": "all_reduce"},
                "dp_reducescatter": common_dp | {"collective": "reduce_scatter"},
                "dp_allgather": common_dp | {"collective": "all_gather"},
                "pp_forward_send": {"payload_scope": "per_rank_send"},
                "pp_backward_send": {"payload_scope": "per_rank_send"},
            },
            "compute": {
                "efficiency": float(workload["compute_efficiency"]),
                "flops_scope": "global",
                "backward_flop_multiplier": float(workload["backward_flop_multiplier"]),
                "tp_communication": {
                    "enabled": strategy.tp > 1,
                    "algorithm": "ring",
                    "forward_collectives": 2,
                    "backward_collectives": 2,
                    "overlap_ratio": 0.0,
                },
            },
        },
        "profiling": {"enabled": False},
    }


class StrategyEvaluator:
    def __init__(self, config: ScenarioConfig, run_dir: Path) -> None:
        _ensure_repo_importable(config)
        self.config = config
        self.run_dir = run_dir
        self.cache_dir = run_dir / "simulation_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_path(self, strategy: Strategy) -> Path:
        key = hashlib.sha256(
            f"{self.config.fingerprint()}:{strategy.cache_key}".encode("utf-8")
        ).hexdigest()[:20]
        return self.cache_dir / f"{key}.json"

    def cached(self, strategy: Strategy) -> dict[str, Any] | None:
        path = self.cache_path(strategy)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def evaluate(self, strategy: Strategy) -> dict[str, Any]:
        cached = self.cached(strategy)
        if cached is not None:
            return cached
        artifact_dir = self.run_dir / "candidates" / strategy.signature
        artifact_dir.mkdir(parents=True, exist_ok=True)
        memory = estimate_memory_gb(strategy, self.config)
        result: dict[str, Any] = {
            "strategy": strategy.to_dict(), "status": "failed", "memory": memory,
            "artifact_dir": str(artifact_dir),
        }
        try:
            if memory["oom"]:
                raise MemoryError(
                    f"estimated {memory['estimated_total_gb']:.3f} GB > {memory['capacity_gb']:.3f} GB"
                )
            from DagGenerator.generate_dag import build_dag
            from RuleCheck.check_dag import DEFAULT_RULES, RuleChecker
            from ValueSim.simulator_v2.engine import SimulationEngine, write_json

            dag = build_dag(
                _generator_config(strategy, self.config, artifact_dir),
                Path("DAGBuilder_Evolve/scenario"),
                artifact_dir / "dag.html",
                artifact_dir / "dag.json",
            )
            _annotate_dag(dag, strategy, self.config)
            write_json(artifact_dir / "dag.json", dag)
            rules = json.loads(Path(DEFAULT_RULES).read_text(encoding="utf-8"))
            rule_report = RuleChecker(dag, rules, artifact_dir / "dag.json").run()
            write_json(artifact_dir / "rule_check.json", rule_report)
            if int(rule_report["summary"]["errors"]):
                raise ValueError(f"RuleCheck failed with {rule_report['summary']['errors']} error(s)")
            simulator_config = _simulator_config(strategy, self.config)
            write_json(artifact_dir / "resolved_simulator_config.json", simulator_config)
            engine = SimulationEngine(simulator_config)
            weighted, rows, critical = engine.simulate(dag)
            write_json(artifact_dir / "weighted_dag.json", weighted)
            write_json(artifact_dir / "node_timings.json", rows)
            write_json(artifact_dir / "critical_path.json", critical)
            category: dict[str, float] = {}
            critical_ids = set(critical["node_ids"])
            for row in rows:
                if row["node_id"] in critical_ids:
                    name = str(row["category"])
                    duration = float(row["duration_s"])
                    if name == "compute":
                        detail = row.get("detail", {})
                        tp_duration = float(
                            detail.get("tp_duration_s")
                            or detail.get("tp_comm_non_overlapped_s")
                            or 0.0
                        )
                        category["tp"] = category.get("tp", 0.0) + tp_duration
                        duration -= tp_duration
                    category[name] = category.get(name, 0.0) + duration
            result.update(
                {
                    "status": "pass", "latency_s": float(critical["duration_s"]),
                    "critical_path": critical, "critical_path_category_s": category,
                    "node_count": len(dag["nodes"]), "edge_count": len(dag["edges"]),
                    "rank_mapping": dag["rank_mapping"],
                }
            )
        except Exception as exc:
            result["error_type"] = type(exc).__name__
            result["error"] = str(exc)
        self.cache_path(strategy).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return result
