from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Strategy:
    pp_size: int
    tp_size: int
    dp_size: int
    micro_batch_num: int
    active_gpus: int
    idle_gpus: int


def load_config(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("dagbuilder_config", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load config: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "get_config"):
        return module.get_config()
    if hasattr(module, "CONFIG"):
        return module.CONFIG
    raise ValueError("Python config must define CONFIG or get_config().")


def search_config(config: dict[str, Any]) -> dict[str, Any]:
    return dict(config.get("search_config", {}))


def config_to_model(config: dict[str, Any]) -> dict[str, Any]:
    model = config["model_para"]
    parallelism = config.get("parallelism_config", {})
    return {
        "num_layers": int(model["num_layers"]),
        "hidden_size": int(model["hidden_size"]),
        "ffn_hidden_size": int(model["ffn_hidden_size"]),
        "precision_factors": dict(model["precision_factors"]),
        "seq_len": int(parallelism.get("seq_len", 1)),
        "global_batch_size": float(parallelism.get("global_batch_size", 1)),
    }


def default_target_scenario(config: dict[str, Any]) -> dict[str, Any]:
    scenarios = search_config(config).get("cluster_scenarios")
    if isinstance(scenarios, list) and scenarios:
        return dict(scenarios[0])
    total = int(config["domains"]["num_gpus"])
    return {
        "name": "target",
        "num_gpus": total,
        "affinity_groups": 1,
        "nodes_per_affinity_group": 1,
        "gpus_per_node": int(config["network_config"].get("die_num_per_node", total)),
        "weight": 1.0,
    }


def scenario_list(config: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = search_config(config).get("cluster_scenarios")
    if isinstance(scenarios, list) and scenarios:
        return [dict(item) for item in scenarios]
    return [default_target_scenario(config)]


def config_to_cluster(config: dict[str, Any], scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    network = config["network_config"]
    scenario = scenario or default_target_scenario(config)
    total = int(scenario.get("num_gpus", config["domains"]["num_gpus"]))
    gpus_per_node = int(scenario.get("gpus_per_node", network.get("die_num_per_node", total)))
    nodes_per_affinity = int(scenario.get("nodes_per_affinity_group", 1))
    return {
        "num_devices": total,
        "num_gpus": total,
        "gpus_per_node": gpus_per_node,
        "nodes_per_affinity_group": nodes_per_affinity,
        "affinity_groups": int(scenario.get("affinity_groups", max(1, total // max(1, gpus_per_node * nodes_per_affinity)))),
        "gpus_per_affinity_group": gpus_per_node * nodes_per_affinity,
        "npu_memory_gb": float(network["npu_memory_gb"]),
        "device_memory_gb": float(network["npu_memory_gb"]),
        "hccs_bandwidth_gbps": float(network["hccs_bandwidth_gbps"]),
        "roce_bandwidth_gbps": float(network["roce_bandwidth_gbps"]),
        "hccs_bandwidth_utilization_ratio": float(network["hccs_bandwidth_utilization_ratio"]),
        "bandwidth_utilization_ratio": float(network["bandwidth_utilization_ratio"]),
        "tp_size_limit": int(config.get("value_sim_config", {}).get("tp_size_limit", total)),
        "rank_mapping_mode": str(scenario.get("rank_mapping_mode", search_config(config).get("rank_mapping_mode", "pp_major_huawei"))),
    }


def config_to_workload(config: dict[str, Any]) -> dict[str, Any]:
    parallelism = config["parallelism_config"]
    dp_size = int(parallelism["dp_size"])
    microbatch_num = int(parallelism["microbatch_num"])
    global_batch = float(parallelism.get("global_batch_size", float(parallelism["microbatch_size"]) * microbatch_num * dp_size))
    return {
        "seq_len": int(parallelism["seq_len"]),
        "global_batch_size": global_batch,
        "microbatch_num": microbatch_num,
        "pp_strategy": parallelism.get("pp_strategy", "gpipe"),
        "search_config": search_config(config),
    }


def config_to_profile(config: dict[str, Any]) -> dict[str, Any]:
    profile = dict(config.get("profile_config", {}))
    profile["search_config"] = search_config(config)
    return profile


def strategy_to_dict(strategy: Strategy) -> dict[str, int]:
    return {
        "pp": strategy.pp_size,
        "tp": strategy.tp_size,
        "dp": strategy.dp_size,
        "micro_batch_num": strategy.micro_batch_num,
    }


def global_batch_size(workload: dict[str, Any]) -> float:
    return float(workload["global_batch_size"])


def local_minibatch_size(workload: dict[str, Any], dp_size: int) -> float:
    return global_batch_size(workload) / float(dp_size)


def derived_microbatch_size(workload: dict[str, Any], dp_size: int) -> float:
    return local_minibatch_size(workload, dp_size) / float(workload["microbatch_num"])


def workload_for_strategy(workload: dict[str, Any], strategy: Strategy) -> dict[str, Any]:
    result = dict(workload)
    result["microbatch_num"] = int(strategy.micro_batch_num)
    return result


def enumerate_strategies(config: dict[str, Any], scenario: dict[str, Any] | None = None) -> list[Strategy]:
    model = config_to_model(config)
    cluster = config_to_cluster(config, scenario)
    workload = config_to_workload(config)
    search = search_config(config)
    total_gpus = int(cluster["num_gpus"])
    allow_idle = bool(search.get("allow_idle_gpus", True))
    tp_limit = min(int(cluster["tp_size_limit"]), total_gpus)
    allowed_tp = search.get("allowed_tp_sizes") or [size for size in range(1, tp_limit + 1) if int(cluster["gpus_per_node"]) % size == 0]
    allowed_tp_sizes = sorted({int(size) for size in allowed_tp if 1 <= int(size) <= tp_limit})
    active_counts = search.get("allowed_active_gpu_counts") or [size for size in range(1, total_gpus + 1) if total_gpus % size == 0]
    allowed_active_counts = {int(size) for size in active_counts if 1 <= int(size) <= total_gpus}
    micro_batches = sorted({int(size) for size in search.get("micro_batch_candidates", [1, 2, 4, 8, 16, 32, 64]) if int(size) > 0})
    batch = int(global_batch_size(workload))
    strategies: list[Strategy] = []
    for pp_size in range(1, int(model["num_layers"]) + 1):
        if int(model["num_layers"]) % pp_size != 0:
            continue
        for tp_size in allowed_tp_sizes:
            if int(model["hidden_size"]) % tp_size != 0:
                continue
            for dp_size in range(1, total_gpus + 1):
                active = pp_size * tp_size * dp_size
                if active > total_gpus or active not in allowed_active_counts:
                    continue
                if not allow_idle and active != total_gpus:
                    continue
                if batch % dp_size != 0:
                    continue
                for micro_batch_num in micro_batches:
                    if batch % (dp_size * micro_batch_num) != 0:
                        continue
                    strategies.append(Strategy(pp_size, tp_size, dp_size, micro_batch_num, active, total_gpus - active))
    return strategies


def strategy_asdict(strategy: Strategy) -> dict[str, int]:
    return asdict(strategy)
