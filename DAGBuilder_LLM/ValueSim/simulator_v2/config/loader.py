from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any


CATEGORIES = ("dp", "pp", "ep", "tp", "compute", "optimizer", "other")
SOURCES = {0, 1}
PAYLOAD_SCOPES = {"full_tensor", "local_shard", "replicated", "per_rank_send"}


def load_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".py":
        raise ValueError("simulator_v2 currently accepts Python config files only")
    spec = importlib.util.spec_from_file_location(f"valuesim_v2_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load config: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "get_config"):
        config = module.get_config()
    elif hasattr(module, "CONFIG"):
        config = module.CONFIG
    else:
        raise ValueError("Python config must define CONFIG or get_config()")
    result = copy.deepcopy(config)
    validate_config(result)
    return result


def _require_mapping(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"config.{key} must be a dictionary")
    return value


def validate_config(config: dict[str, Any]) -> None:
    for section in ("model", "topology", "network", "parallel", "simulation_flags", "algorithms", "profiling"):
        _require_mapping(config, section)
    flags = config["simulation_flags"]
    missing = [category for category in CATEGORIES if category not in flags]
    if missing:
        raise ValueError(f"simulation_flags is missing categories: {missing}")
    invalid = {key: value for key, value in flags.items() if key in CATEGORIES and value not in SOURCES}
    if invalid:
        raise ValueError(f"simulation_flags values must be 0 or 1: {invalid}")
    overrides = config.get("simulation_overrides", {})
    for section in ("node_id", "op_name"):
        values = overrides.get(section, {})
        if not isinstance(values, dict) or any(value not in SOURCES for value in values.values()):
            raise ValueError(f"simulation_overrides.{section} must map names to 0 or 1")

    topology = config["topology"]
    for key in ("total_devices", "default_compute_tflops", "domains"):
        if key not in topology:
            raise ValueError(f"topology.{key} is required")
    if "affinity_groups" not in topology:
        for key in ("devices_per_server", "servers_per_affinity_group"):
            if key not in topology:
                raise ValueError(
                    f"topology.{key} is required when affinity_groups is not explicitly configured"
                )
    for key in ("hccs_intra_server", "hccs_inter_server", "roce", "hbm"):
        if key not in config["network"]:
            raise ValueError(f"network.{key} is required")

    algorithm_specs = list(config["algorithms"].get("operations", {}).items())
    algorithm_specs.extend(config["algorithms"].get("task_kinds", {}).items())
    for operation, spec in algorithm_specs:
        if "payload_scope" in spec and spec["payload_scope"] not in PAYLOAD_SCOPES:
            raise ValueError(f"Unsupported payload scope for {operation}: {spec['payload_scope']}")
        if "domain" in spec and spec["domain"] not in topology["domains"]:
            raise ValueError(f"Operation {operation} references unknown domain {spec['domain']}")
        if int(spec.get("bucket_count", 1)) <= 0:
            raise ValueError(f"Operation {operation} bucket_count must be positive")
        if "bucket_sizes_bytes" in spec:
            values = spec["bucket_sizes_bytes"]
            if not isinstance(values, list) or not values or any(float(value) <= 0 for value in values):
                raise ValueError(f"Operation {operation} bucket_sizes_bytes must be a positive list")

    model = config["model"]
    for key in ("num_layers", "hidden_size", "ffn_hidden_size", "microbatch_size", "sequence_length"):
        if key not in model or float(model[key]) <= 0:
            raise ValueError(f"model.{key} must be positive")
    parallel = config["parallel"]
    for key in ("tp_size", "pp_size", "dp_size", "ep_size", "cp_size"):
        if key not in parallel or int(parallel[key]) <= 0:
            raise ValueError(f"parallel.{key} must be positive")

    profiling = config["profiling"]
    if profiling.get("enabled", True) is False:
        return
    for key in ("path", "sheet", "columns", "duration_unit"):
        if key not in profiling:
            raise ValueError(f"profiling.{key} is required")
    if profiling["duration_unit"] not in {"s", "ms", "us", "ns"}:
        raise ValueError("profiling.duration_unit must be one of s/ms/us/ns")
