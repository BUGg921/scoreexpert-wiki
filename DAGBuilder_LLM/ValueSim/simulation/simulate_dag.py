from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

try:
    from .collective_models import estimate_allgather, estimate_allreduce, estimate_reducescatter
    from .compute_models import estimate_tp_compute
    from .p2p_models import estimate_pp_p2p
    from .payload_models import compute_payload, dp_node_payload_bytes, pp_activation_bytes, tp_activation_bytes
except ImportError:  # pragma: no cover - supports direct script execution.
    from collective_models import estimate_allgather, estimate_allreduce, estimate_reducescatter
    from compute_models import estimate_tp_compute
    from p2p_models import estimate_pp_p2p
    from payload_models import compute_payload, dp_node_payload_bytes, pp_activation_bytes, tp_activation_bytes


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "config.py"


def load_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".py":
        spec = importlib.util.spec_from_file_location("dagbuilder_config", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load config: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "get_config"):
            return copy.deepcopy(module.get_config())
        if hasattr(module, "CONFIG"):
            return copy.deepcopy(module.CONFIG)
        raise ValueError("Python config must define CONFIG or get_config().")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_value_sim_config(config: dict[str, Any]) -> None:
    value_sim = config.get("value_sim_config")
    if not isinstance(value_sim, dict):
        raise ValueError("config.value_sim_config is required for ValueSim.")

    domains = config["domains"]
    tp_size = int(domains["tp_size"])
    tp_limit = int(value_sim.get("tp_size_limit", 8))
    if tp_size > tp_limit:
        raise ValueError(f"TP size {tp_size} exceeds ValueSim tp_size_limit {tp_limit}.")

    pp_link_type = value_sim.get("pp_link_type", "roce")
    if pp_link_type != "roce":
        raise ValueError("ValueSim Ascend profile expects pp_link_type='roce' unless explicitly redesigned.")

    model = value_sim.get("dp_collective_model", "hierarchical")
    if model not in {"simple", "hierarchical", "algorithmic"}:
        raise ValueError(f"Unsupported dp_collective_model: {model}")

    rank_map = value_sim.get("rank_to_affinity_group")
    if rank_map is not None and len(rank_map) != int(domains["num_gpus"]):
        raise ValueError("value_sim_config.rank_to_affinity_group length must match domains.num_gpus.")


def timing_for_node(config: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    task_kind = node["task_kind"]
    if task_kind in {"control"}:
        return {"duration_s": 0.0, "flops": 0.0, "payload_bytes": 0.0, "value_sim_detail": {"model": "zero_duration"}}
    if task_kind in {"forward", "backward"}:
        payload = compute_payload(config, node)
        timing = estimate_tp_compute(config, node, payload.flops, tp_activation_bytes(config))
    elif task_kind in {"pp_forward_send", "pp_backward_send", "pp_forward_recv", "pp_backward_recv"}:
        timing = estimate_pp_p2p(config, pp_activation_bytes(config))
    elif task_kind in {"dp_allreduce", "zero01_g_ar"}:
        timing = estimate_allreduce(config, dp_node_payload_bytes(config, node))
    elif task_kind in {"dp_reducescatter", "reduce_scatter", "zero01_g_rs"}:
        timing = estimate_reducescatter(config, dp_node_payload_bytes(config, node))
    elif task_kind in {"dp_allgather", "allgather", "zero01_p_ag"}:
        timing = estimate_allgather(config, dp_node_payload_bytes(config, node))
    else:
        raise ValueError(f"Unsupported task_kind for ValueSim: {task_kind}")
    return {
        "duration_s": timing.duration_s,
        "flops": timing.flops,
        "payload_bytes": timing.payload_bytes,
        "value_sim_detail": timing.detail,
    }


def simulate_dag(dag: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_value_sim_config(config)
    original_node_count = len(dag.get("nodes", []))
    original_edge_count = len(dag.get("edges", []))
    weighted = copy.deepcopy(dag)
    timing_rows: list[dict[str, Any]] = []
    for node in weighted["nodes"]:
        timing = timing_for_node(config, node)
        node.update(timing)
        timing_rows.append(
            {
                "node_id": node["node_id"],
                "label": node.get("label"),
                "task_kind": node["task_kind"],
                "duration_s": node["duration_s"],
                "flops": node["flops"],
                "payload_bytes": node["payload_bytes"],
                "resource": node.get("stream_type"),
                "value_sim_detail": node.get("value_sim_detail", {}),
            }
        )

    if len(weighted.get("nodes", [])) != original_node_count or len(weighted.get("edges", [])) != original_edge_count:
        raise RuntimeError("ValueSim changed DAG topology; this is not allowed.")

    weighted["value_sim"] = {
        "node_count": original_node_count,
        "edge_count": original_edge_count,
        "duration_field": "duration_s",
        "topology_unchanged": True,
    }
    return weighted, timing_rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill DAG nodes with ValueSim timing fields.")
    parser.add_argument("--dag", required=True, type=Path)
    parser.add_argument("--config", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timing-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dag = load_json(args.dag)
    config = load_config(args.config)
    output = args.output or args.dag.with_name("weighted_dag.json")
    timing_output = args.timing_output or args.dag.with_name("node_timing_table.json")
    weighted, timing_rows = simulate_dag(dag, config)
    write_json(output, weighted)
    write_json(timing_output, timing_rows)
    print(f"Wrote {output}")
    print(f"Wrote {timing_output}")


if __name__ == "__main__":
    main()
