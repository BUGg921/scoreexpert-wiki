from __future__ import annotations

import argparse
import copy
import html
import importlib.util
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "config.py"


DP_STRATEGY_SHORT_NAMES = {
    "naive_allreduce_after_backward": "naive_ar",
    "reduce_scatter_allgather_after_backward": "rs_ag",
    "zero_01": "zero01",
}


def load_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".py":
        config = load_python_config(path)
    elif path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    else:
        raise ValueError(f"Unsupported config format: {path}. Use .py or .json.")
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a mapping object: {path}")
    return config


def load_python_config(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("dagbuilder_config", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load Python config: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "get_config"):
        config = module.get_config()
    elif hasattr(module, "CONFIG"):
        config = module.CONFIG
    elif hasattr(module, "DAG_GENERATOR_CONFIG"):
        config = module.DAG_GENERATOR_CONFIG
    else:
        raise ValueError("Python config must define CONFIG, DAG_GENERATOR_CONFIG, or get_config().")
    return copy.deepcopy(config)


def distribute_layers(num_layers: int, pp_size: int) -> list[list[int]]:
    if pp_size <= 0:
        raise ValueError("pp_size must be positive.")
    ranges: list[list[int]] = []
    base = num_layers // pp_size
    remainder = num_layers % pp_size
    cursor = 0
    for stage_id in range(pp_size):
        count = base + (1 if stage_id < remainder else 0)
        if count <= 0:
            raise ValueError("num_layers must be at least pp_size for the first-stage generator.")
        ranges.append(list(range(cursor, cursor + count)))
        cursor += count
    return ranges


def resolve_domains(domains: dict[str, Any]) -> dict[str, int]:
    pp_size = int(domains["pp_size"])
    dp_size = int(domains["dp_size"])
    num_layers = int(domains["num_layers"])
    num_microbatches = int(domains["num_microbatches"])
    num_gpus = int(domains.get("num_gpus", pp_size * dp_size * int(domains.get("tp_size", 1))))

    raw_tp_size = domains.get("tp_size", "auto")
    if raw_tp_size == "auto" or raw_tp_size is None:
        denominator = pp_size * dp_size
        if num_gpus % denominator != 0:
            raise ValueError("num_gpus must be divisible by pp_size * dp_size when tp_size is auto.")
        tp_size = num_gpus // denominator
    else:
        tp_size = int(raw_tp_size)

    if min(num_gpus, pp_size, dp_size, tp_size, num_layers, num_microbatches) <= 0:
        raise ValueError("num_gpus, pp_size, dp_size, tp_size, num_layers, and num_microbatches must be positive.")
    if pp_size * dp_size * tp_size != num_gpus:
        raise ValueError(
            f"Invalid parallel domains: pp_size * dp_size * tp_size must equal num_gpus "
            f"({pp_size} * {dp_size} * {tp_size} != {num_gpus})."
        )
    if num_layers < pp_size:
        raise ValueError("num_layers must be at least pp_size for the first-stage generator.")

    return {
        "num_gpus": num_gpus,
        "dp_size": dp_size,
        "tp_size": tp_size,
        "pp_size": pp_size,
        "num_layers": num_layers,
        "num_microbatches": num_microbatches,
    }


def node(
    *,
    node_id: str,
    label: str,
    task_kind: str,
    stream_type: str,
    row: str,
    column: float,
    dp_rank: int | None = None,
    pp_stage_id: int | None = None,
    tp_domain_id: int | None = None,
    global_layer_id: int | None = None,
    microbatch_id: int | None = None,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "label": label,
        "task_kind": task_kind,
        "stream_type": stream_type,
        "dp_rank": dp_rank,
        "pp_stage_id": pp_stage_id,
        "tp_domain_id": tp_domain_id,
        "global_layer_id": global_layer_id,
        "microbatch_id": microbatch_id,
        "row": row,
        "column": column,
    }


def edge(src: str, dst: str, edge_kind: str, color_role: str) -> dict[str, str]:
    return {
        "src": src,
        "dst": dst,
        "edge_kind": edge_kind,
        "color_role": color_role,
    }


def layer_node_id(kind: str, dp_rank: int, layer_id: int, microbatch_id: int) -> str:
    prefix = "F" if kind == "forward" else "B"
    return f"{prefix}_dp{dp_rank}_l{layer_id}_mb{microbatch_id}"


def pp_forward_node_id(dp_rank: int, stage_id: int, microbatch_id: int) -> str:
    return f"PPF_dp{dp_rank}_s{stage_id}_to_s{stage_id + 1}_mb{microbatch_id}"


def pp_backward_node_id(dp_rank: int, stage_id: int, microbatch_id: int) -> str:
    return f"PPB_dp{dp_rank}_s{stage_id}_to_s{stage_id - 1}_mb{microbatch_id}"


def dp_reducescatter_node_id(stage_id: int) -> str:
    return f"DP_RS_s{stage_id}"


def dp_allgather_node_id(stage_id: int) -> str:
    return f"DP_AG_s{stage_id}"


def stage_task_base_column(
    schedule_columns: dict[tuple[str, int, int], int],
    task_kind: str,
    stage_id: int,
    microbatch_id: int,
    stage_span: int,
) -> int:
    logical_column = schedule_columns[(task_kind, stage_id, microbatch_id)]
    return 1 + ((logical_column - 1) * stage_span)


def compute_schedule_columns(
    pp_strategy: str,
    pp_size: int,
    num_microbatches: int,
) -> dict[tuple[str, int, int], int]:
    if pp_strategy == "gpipe":
        forward_span = num_microbatches + pp_size - 1
        backward_offset = forward_span + 1
        return {
            **{
                ("forward", stage_id, microbatch_id): microbatch_id + stage_id + 1
                for stage_id in range(pp_size)
                for microbatch_id in range(num_microbatches)
            },
            **{
                ("backward", stage_id, microbatch_id): (
                    backward_offset + microbatch_id + (pp_size - 1 - stage_id)
                )
                for stage_id in range(pp_size)
                for microbatch_id in range(num_microbatches)
            },
        }
    if pp_strategy == "1f1b":
        return compute_1f1b_schedule_columns(pp_size, num_microbatches)
    raise ValueError(f"Unsupported pp_strategy for first-stage DagGenerator: {pp_strategy}")


def compute_1f1b_schedule_columns(
    pp_size: int,
    num_microbatches: int,
) -> dict[tuple[str, int, int], int]:
    total_tasks = pp_size * num_microbatches * 2
    completed: set[tuple[str, int, int]] = set()
    scheduled: dict[tuple[str, int, int], int] = {}
    next_forward = [0 for _ in range(pp_size)]
    next_backward = [0 for _ in range(pp_size)]
    time_index = 1

    while len(completed) < total_tasks:
        stage_choices: list[tuple[int, tuple[str, int, int]]] = []
        for stage_id in range(pp_size):
            backward_mb = next_backward[stage_id]
            if backward_mb < num_microbatches and is_backward_ready(
                stage_id,
                backward_mb,
                pp_size,
                completed,
            ):
                stage_choices.append((stage_id, ("backward", stage_id, backward_mb)))
                continue

            forward_mb = next_forward[stage_id]
            if forward_mb < num_microbatches and is_forward_ready(
                stage_id,
                forward_mb,
                completed,
            ):
                stage_choices.append((stage_id, ("forward", stage_id, forward_mb)))

        if not stage_choices:
            raise ValueError("1F1B scheduler made no progress; check dependency rules.")

        for stage_id, task_key in stage_choices:
            scheduled[task_key] = time_index
            completed.add(task_key)
            if task_key[0] == "forward":
                next_forward[stage_id] += 1
            else:
                next_backward[stage_id] += 1
        time_index += 1

    return scheduled


def is_forward_ready(
    stage_id: int,
    microbatch_id: int,
    completed: set[tuple[str, int, int]],
) -> bool:
    if stage_id == 0:
        return True
    return ("forward", stage_id - 1, microbatch_id) in completed


def is_backward_ready(
    stage_id: int,
    microbatch_id: int,
    pp_size: int,
    completed: set[tuple[str, int, int]],
) -> bool:
    if ("forward", stage_id, microbatch_id) not in completed:
        return False
    if stage_id == pp_size - 1:
        return True
    return ("backward", stage_id + 1, microbatch_id) in completed


def build_dag(config: dict[str, Any], source_config: Path, html_output: Path, json_output: Path) -> dict[str, Any]:
    domains = config["domains"]
    strategies = config["strategies"]
    color_theme = config["color_theme"]
    validate_model_parameters(config)
    validate_parallelism_config(config)
    validate_network_config(config)
    pp_strategy = strategies.get("pp_strategy", "gpipe")
    dp_strategy = strategies.get("dp_strategy", "naive_allreduce_after_backward")
    dp_granularity = strategies.get("dp_allreduce_granularity", "stage")

    if pp_strategy not in {"gpipe", "1f1b"}:
        raise ValueError("First-stage DagGenerator currently implements pp_strategy='gpipe' and '1f1b'.")
    if dp_strategy not in {"naive_allreduce_after_backward", "reduce_scatter_allgather_after_backward"}:
        raise ValueError("First-stage DagGenerator currently implements dp_strategy='naive_allreduce_after_backward' and 'reduce_scatter_allgather_after_backward'.")
    if dp_granularity != "stage":
        raise ValueError("First-stage DagGenerator currently implements dp_allreduce_granularity='stage'.")

    resolved_domains = resolve_domains(domains)
    num_gpus = resolved_domains["num_gpus"]
    dp_size = resolved_domains["dp_size"]
    tp_size = resolved_domains["tp_size"]
    pp_size = resolved_domains["pp_size"]
    num_layers = resolved_domains["num_layers"]
    num_microbatches = resolved_domains["num_microbatches"]
    layer_ranges = distribute_layers(num_layers, pp_size)
    max_layers_per_stage = max(len(layer_ids) for layer_ids in layer_ranges)
    stage_span = max_layers_per_stage + 1

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    rows = ["Control"]
    for dp_rank in range(dp_size):
        for stage_id in range(pp_size):
            rows.append(f"DP{dp_rank} / Stage {stage_id + 1} / Comp")
            rows.append(f"DP{dp_rank} / Stage {stage_id + 1} / Comm")
    rows.append("DP Comm")

    nodes.append(node(node_id="start", label="Start", task_kind="control", stream_type="control", row="Control", column=0.0))

    schedule_columns = compute_schedule_columns(pp_strategy, pp_size, num_microbatches)
    dp_offset = 1 + ((max(schedule_columns.values()) - 1) * stage_span) + max_layers_per_stage + 2

    for dp_rank in range(dp_size):
        for stage_id, layer_ids in enumerate(layer_ranges):
            for microbatch_id in range(num_microbatches):
                forward_column = stage_task_base_column(
                    schedule_columns,
                    "forward",
                    stage_id,
                    microbatch_id,
                    stage_span,
                )
                for layer_order, layer_id in enumerate(layer_ids):
                    nodes.append(
                        node(
                            node_id=layer_node_id("forward", dp_rank, layer_id, microbatch_id),
                            label=f"F({layer_id},{microbatch_id})",
                            task_kind="forward",
                            stream_type="comp",
                            row=f"DP{dp_rank} / Stage {stage_id + 1} / Comp",
                            column=forward_column + layer_order,
                            dp_rank=dp_rank,
                            pp_stage_id=stage_id,
                            tp_domain_id=0,
                            global_layer_id=layer_id,
                            microbatch_id=microbatch_id,
                        )
                    )

                backward_column = stage_task_base_column(
                    schedule_columns,
                    "backward",
                    stage_id,
                    microbatch_id,
                    stage_span,
                )
                for layer_order, layer_id in enumerate(reversed(layer_ids)):
                    nodes.append(
                        node(
                            node_id=layer_node_id("backward", dp_rank, layer_id, microbatch_id),
                            label=f"B({layer_id},{microbatch_id})",
                            task_kind="backward",
                            stream_type="comp",
                            row=f"DP{dp_rank} / Stage {stage_id + 1} / Comp",
                            column=backward_column + layer_order,
                            dp_rank=dp_rank,
                            pp_stage_id=stage_id,
                            tp_domain_id=0,
                            global_layer_id=layer_id,
                            microbatch_id=microbatch_id,
                        )
                    )

    for dp_rank in range(dp_size):
        for stage_id in range(pp_size - 1):
            for microbatch_id in range(num_microbatches):
                nodes.append(
                    node(
                        node_id=pp_forward_node_id(dp_rank, stage_id, microbatch_id),
                        label=f"P2P-F(S{stage_id + 1}->S{stage_id + 2},m{microbatch_id})",
                        task_kind="pp_forward_send",
                        stream_type="comm",
                        row=f"DP{dp_rank} / Stage {stage_id + 1} / Comm",
                        column=stage_task_base_column(
                            schedule_columns,
                            "forward",
                            stage_id,
                            microbatch_id,
                            stage_span,
                        ) + len(layer_ranges[stage_id]),
                        dp_rank=dp_rank,
                        pp_stage_id=stage_id,
                        tp_domain_id=0,
                        microbatch_id=microbatch_id,
                    )
                )
        for stage_id in range(pp_size - 1, 0, -1):
            for microbatch_id in range(num_microbatches):
                nodes.append(
                    node(
                        node_id=pp_backward_node_id(dp_rank, stage_id, microbatch_id),
                        label=f"P2P-B(S{stage_id + 1}->S{stage_id},m{microbatch_id})",
                        task_kind="pp_backward_send",
                        stream_type="comm",
                        row=f"DP{dp_rank} / Stage {stage_id + 1} / Comm",
                        column=stage_task_base_column(
                            schedule_columns,
                            "backward",
                            stage_id,
                            microbatch_id,
                            stage_span,
                        ) + len(layer_ranges[stage_id]),
                        dp_rank=dp_rank,
                        pp_stage_id=stage_id,
                        tp_domain_id=0,
                        microbatch_id=microbatch_id,
                    )
                )

    for stage_id in range(pp_size):
        if dp_strategy == "naive_allreduce_after_backward":
            nodes.append(
                node(
                    node_id=f"DP_AR_s{stage_id}",
                    label=f"DP-AR(S{stage_id + 1})",
                    task_kind="dp_allreduce",
                    stream_type="dp_comm",
                    row="DP Comm",
                    column=dp_offset + stage_id,
                    pp_stage_id=stage_id,
                    tp_domain_id=0,
                )
            )
        else:
            nodes.append(
                node(
                    node_id=dp_reducescatter_node_id(stage_id),
                    label=f"DP-RS(S{stage_id + 1})",
                    task_kind="dp_reducescatter",
                    stream_type="dp_comm",
                    row="DP Comm",
                    column=dp_offset + (stage_id * 2),
                    pp_stage_id=stage_id,
                    tp_domain_id=0,
                )
            )
            nodes.append(
                node(
                    node_id=dp_allgather_node_id(stage_id),
                    label=f"DP-AG(S{stage_id + 1})",
                    task_kind="dp_allgather",
                    stream_type="dp_comm",
                    row="DP Comm",
                    column=dp_offset + (stage_id * 2) + 1,
                    pp_stage_id=stage_id,
                    tp_domain_id=0,
                )
            )
    end_column = dp_offset + (pp_size * 2 if dp_strategy == "reduce_scatter_allgather_after_backward" else pp_size) + 1
    nodes.append(node(node_id="end", label="End", task_kind="control", stream_type="control", row="Control", column=end_column))

    for dp_rank in range(dp_size):
        first_layer = layer_ranges[0][0]
        edges.append(edge("start", layer_node_id("forward", dp_rank, first_layer, 0), "control", "control"))

    for dp_rank in range(dp_size):
        for microbatch_id in range(num_microbatches):
            for stage_id, layer_ids in enumerate(layer_ranges):
                for left, right in zip(layer_ids, layer_ids[1:]):
                    edges.append(edge(layer_node_id("forward", dp_rank, left, microbatch_id), layer_node_id("forward", dp_rank, right, microbatch_id), "model_forward_dependency", "data_dependency"))
                    edges.append(edge(layer_node_id("backward", dp_rank, right, microbatch_id), layer_node_id("backward", dp_rank, left, microbatch_id), "model_backward_dependency", "data_dependency"))
                for layer_id in layer_ids:
                    edges.append(edge(layer_node_id("forward", dp_rank, layer_id, microbatch_id), layer_node_id("backward", dp_rank, layer_id, microbatch_id), "intra_layer_dependency", "data_dependency"))

            for stage_id in range(pp_size - 1):
                src_layer = layer_ranges[stage_id][-1]
                dst_layer = layer_ranges[stage_id + 1][0]
                ppf = pp_forward_node_id(dp_rank, stage_id, microbatch_id)
                edges.append(edge(layer_node_id("forward", dp_rank, src_layer, microbatch_id), ppf, "pp_forward_send_dependency", "data_dependency"))
                edges.append(edge(ppf, layer_node_id("forward", dp_rank, dst_layer, microbatch_id), "pp_forward_recv_dependency", "data_dependency"))

            for stage_id in range(pp_size - 1, 0, -1):
                src_layer = layer_ranges[stage_id][0]
                dst_layer = layer_ranges[stage_id - 1][-1]
                ppb = pp_backward_node_id(dp_rank, stage_id, microbatch_id)
                edges.append(edge(layer_node_id("backward", dp_rank, src_layer, microbatch_id), ppb, "pp_backward_send_dependency", "data_dependency"))
                edges.append(edge(ppb, layer_node_id("backward", dp_rank, dst_layer, microbatch_id), "pp_backward_recv_dependency", "data_dependency"))

    by_row: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in nodes:
        if item["stream_type"] in {"comp", "comm", "dp_comm"}:
            by_row[item["row"]].append(item)
    for row_nodes in by_row.values():
        ordered = sorted(row_nodes, key=lambda item: (item["column"], item["node_id"]))
        for left, right in zip(ordered, ordered[1:]):
            edges.append(edge(left["node_id"], right["node_id"], "resource_dependency", "resource_dependency"))

    for stage_id, layer_ids in enumerate(layer_ranges):
        for dp_rank in range(dp_size):
            last_backward = layer_node_id("backward", dp_rank, layer_ids[0], num_microbatches - 1)
            if dp_strategy == "naive_allreduce_after_backward":
                edges.append(edge(last_backward, f"DP_AR_s{stage_id}", "dp_allreduce_trigger_dependency", "data_dependency"))
            else:
                edges.append(edge(last_backward, dp_reducescatter_node_id(stage_id), "dp_reducescatter_trigger_dependency", "data_dependency"))
        if dp_strategy == "naive_allreduce_after_backward":
            edges.append(edge(f"DP_AR_s{stage_id}", "end", "control", "control"))
        else:
            edges.append(edge(dp_reducescatter_node_id(stage_id), dp_allgather_node_id(stage_id), "dp_allgather_after_reducescatter_dependency", "data_dependency"))
            edges.append(edge(dp_allgather_node_id(stage_id), "end", "control", "control"))

    node_ids = {item["node_id"] for item in nodes}
    edge_pairs = set()
    deduped_edges = []
    for item in edges:
        key = (item["src"], item["dst"], item["edge_kind"], item["color_role"])
        if item["src"] not in node_ids or item["dst"] not in node_ids:
            raise ValueError(f"Edge references unknown node: {item}")
        if key not in edge_pairs:
            edge_pairs.add(key)
            deduped_edges.append(item)

    columns = sorted({item["column"] for item in nodes})
    dag = {
        "dag_id": config.get("dag_id", "dag"),
        "source_config": str(source_config.as_posix()),
        "selected_rules": {
            "pp_strategy": pp_strategy,
            "dp_strategy": dp_strategy,
            "pp_rule_source": f"DagGenerator/rules/pp_strategies.md#{pp_strategy}",
            "dp_rule_source": f"DagGenerator/rules/dp_strategies.md#{dp_strategy}",
        },
        "domains": {
            "num_gpus": num_gpus,
            "dp_size": dp_size,
            "tp_size": tp_size,
            "pp_size": pp_size,
            "num_microbatches": num_microbatches,
            "num_layers": num_layers,
        },
        "model_para": copy.deepcopy(config.get("model_para", {})),
        "parallelism_config": copy.deepcopy(config.get("parallelism_config", {})),
        "network_config": copy.deepcopy(config.get("network_config", {})),
        "immutable_config_sections": list(config.get("immutable_config_sections", [])),
        "color_theme": color_theme,
        "nodes": sorted(nodes, key=lambda item: (item["column"], item["row"], item["node_id"])),
        "edges": deduped_edges,
        "layout": {
            "rows": rows,
            "columns": columns,
            "start_node": "start",
            "end_node": "end",
            "stage_span_columns": stage_span,
        },
        "invariants": {
            "start_reaches_end": reaches(deduped_edges, "start", "end"),
            "same_stage_compute_serialization": True,
            "pp_send_receive_dependency": True,
            "dp_allreduce_trigger_rule": "after all backward tasks in each stage complete",
        },
        "outputs": {
            "html": str(html_output.as_posix()),
            "json": str(json_output.as_posix()),
        },
    }
    return dag


def validate_model_parameters(config: dict[str, Any]) -> None:
    model_para = config.get("model_para")
    if model_para is None:
        return
    if not isinstance(model_para, dict):
        raise ValueError("model_para must be a mapping when provided.")
    required = {
        "num_layers",
        "hidden_size",
        "ffn_hidden_size",
        "precision_factors",
    }
    missing = sorted(required - set(model_para))
    if missing:
        raise ValueError(f"model_para is missing required fields: {', '.join(missing)}")
    model_layers = int(model_para["num_layers"])
    domain_layers = int(config["domains"]["num_layers"])
    if model_layers != domain_layers:
        raise ValueError(
            f"model_para.num_layers must equal domains.num_layers "
            f"({model_layers} != {domain_layers})."
        )
    for key in ("num_layers", "hidden_size", "ffn_hidden_size"):
        if int(model_para[key]) <= 0:
            raise ValueError(f"model_para.{key} must be positive.")
    precision_factors = model_para["precision_factors"]
    if not isinstance(precision_factors, dict):
        raise ValueError("model_para.precision_factors must be a mapping.")
    for key in ("tp", "dp", "pp", "ep", "sp"):
        if key not in precision_factors:
            raise ValueError(f"model_para.precision_factors.{key} is required.")
        if int(precision_factors[key]) <= 0:
            raise ValueError(f"model_para.precision_factors.{key} must be positive.")


def validate_parallelism_config(config: dict[str, Any]) -> None:
    parallelism = config.get("parallelism_config")
    if parallelism is None:
        return
    if not isinstance(parallelism, dict):
        raise ValueError("parallelism_config must be a mapping when provided.")
    required = {
        "global_batch_size",
        "seq_len",
        "dp_size",
        "tp_size",
        "pp_size",
        "vpp_size",
        "sp_ce_size",
        "sp_me_size",
        "microbatch_num",
        "microbatch_size",
        "pp_strategy",
        "dp_strategy",
        "dp_allreduce_granularity",
    }
    missing = sorted(required - set(parallelism))
    if missing:
        raise ValueError(f"parallelism_config is missing required fields: {', '.join(missing)}")
    for key in ("global_batch_size", "seq_len", "dp_size", "tp_size", "pp_size", "vpp_size", "sp_ce_size", "sp_me_size", "microbatch_num"):
        if int(parallelism[key]) <= 0:
            raise ValueError(f"parallelism_config.{key} must be positive.")
    if float(parallelism["microbatch_size"]) <= 0:
        raise ValueError("parallelism_config.microbatch_size must be positive.")
    domains = config["domains"]
    strategies = config["strategies"]
    mirrors = {
        "dp_size": ("domains", int(domains["dp_size"])),
        "tp_size": ("domains", int(domains["tp_size"])),
        "pp_size": ("domains", int(domains["pp_size"])),
        "microbatch_num": ("domains.num_microbatches", int(domains["num_microbatches"])),
        "pp_strategy": ("strategies", strategies["pp_strategy"]),
        "dp_strategy": ("strategies", strategies["dp_strategy"]),
        "dp_allreduce_granularity": ("strategies", strategies["dp_allreduce_granularity"]),
    }
    for key, (target, value) in mirrors.items():
        if parallelism[key] != value:
            raise ValueError(f"parallelism_config.{key} must match {target} value ({parallelism[key]!r} != {value!r}).")


def validate_network_config(config: dict[str, Any]) -> None:
    network = config.get("network_config")
    if network is None:
        return
    if not isinstance(network, dict):
        raise ValueError("network_config must be a mapping when provided.")
    required = {
        "npu_innode_static_delay_s",
        "roce_static_delay_s",
        "npu_innode_bandwidth_gbps",
        "hccs_bandwidth_gbps",
        "roce_bandwidth_gbps",
        "bandwidth_utilization_ratio",
        "hccs_bandwidth_utilization_ratio",
        "die_num_per_node",
        "alltoall_concurrency",
        "hbm_bandwidth_gbps",
        "npu_memory_gb",
    }
    missing = sorted(required - set(network))
    if missing:
        raise ValueError(f"network_config is missing required fields: {', '.join(missing)}")
    positive_fields = required - {"npu_innode_static_delay_s", "roce_static_delay_s"}
    for key in positive_fields:
        if float(network[key]) <= 0:
            raise ValueError(f"network_config.{key} must be positive.")
    for key in ("npu_innode_static_delay_s", "roce_static_delay_s"):
        if float(network[key]) < 0:
            raise ValueError(f"network_config.{key} must be non-negative.")
    for key in ("bandwidth_utilization_ratio", "hccs_bandwidth_utilization_ratio"):
        value = float(network[key])
        if not 0 < value <= 1:
            raise ValueError(f"network_config.{key} must be within (0, 1].")


def reaches(edges: list[dict[str, str]], src: str, dst: str) -> bool:
    outgoing: dict[str, list[str]] = defaultdict(list)
    for item in edges:
        outgoing[item["src"]].append(item["dst"])
    queue = deque([src])
    visited = {src}
    while queue:
        node_id = queue.popleft()
        if node_id == dst:
            return True
        for child in outgoing[node_id]:
            if child not in visited:
                visited.add(child)
                queue.append(child)
    return False


def write_json(dag: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(dag, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def render_html(dag: dict[str, Any], output: Path) -> None:
    color_theme = dag["color_theme"]
    row_to_y = {row: 120 + (index * 96) for index, row in enumerate(dag["layout"]["rows"])}
    col_scale = 180
    left_margin = 280
    width = int(left_margin + (max(dag["layout"]["columns"]) * col_scale) + 320)
    height = int(max(row_to_y.values()) + 180)
    node_payload = []
    for item in dag["nodes"]:
        row = item["row"]
        x = left_margin + (float(item["column"]) * col_scale)
        y = row_to_y[row]
        task_kind = item["task_kind"]
        fill = {
            "forward": color_theme["forward_node_color"],
            "backward": color_theme["backward_node_color"],
            "pp_forward_send": color_theme["pp_comm_node_color"],
            "pp_backward_send": color_theme["pp_comm_node_color"],
            "dp_allreduce": color_theme["dp_comm_node_color"],
            "dp_reducescatter": color_theme["dp_comm_node_color"],
            "dp_allgather": color_theme["dp_comm_node_color"],
            "control": color_theme["control_node_color"],
        }.get(task_kind, "#FFFFFF")
        node_payload.append(
            {
                **item,
                "x": x,
                "y": y,
                "width": 126 if task_kind not in {"control"} else 90,
                "height": 42 if task_kind not in {"control"} else 32,
                "fill": fill,
                "tooltip": "\n".join(f"{key}={value}" for key, value in item.items()),
            }
        )

    edge_payload = []
    for item in dag["edges"]:
        color = {
            "control": color_theme["control_edge_color"],
            "data_dependency": color_theme["data_dependency_edge_color"],
            "resource_dependency": color_theme["resource_dependency_edge_color"],
        }[item["color_role"]]
        edge_payload.append({**item, "color": color, "dashed": item["color_role"] == "resource_dependency"})

    labels_html = "\n".join(
        f'<div class="row-label" style="top:{y + 12}px">{html.escape(row)}</div>'
        for row, y in row_to_y.items()
    )
    html_text = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(dag["dag_id"])}</title>
  <style>
    body {{ margin: 0; background: #FBFBFC; font-family: Arial, sans-serif; }}
    #canvas {{ position: relative; width: {width}px; height: {height}px; }}
    #edges {{ position: absolute; left: 0; top: 0; width: {width}px; height: {height}px; overflow: visible; }}
    .title {{ position: absolute; left: 32px; top: 28px; font-size: 20px; font-weight: 600; }}
    .row-label {{ position: absolute; left: 32px; color: #333; font-size: 14px; }}
    .node {{
      position: absolute; border: 2px solid #345; border-radius: 12px; box-sizing: border-box;
      display: flex; align-items: center; justify-content: center; text-align: center;
      font-size: 14px; cursor: move; user-select: none; box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    }}
  </style>
</head>
<body>
  <div id="canvas">
    <svg id="edges" viewBox="0 0 {width} {height}"></svg>
    <div class="title">{html.escape(dag["dag_id"])}</div>
    {labels_html}
  </div>
  <script>
    const nodes = {json.dumps(node_payload)};
    const edges = {json.dumps(edge_payload)};
    const canvas = document.getElementById("canvas");
    const svg = document.getElementById("edges");
    const nodeMap = new Map();

    function renderNodes() {{
      for (const node of nodes) {{
        const div = document.createElement("div");
        div.className = "node";
        div.textContent = node.label;
        div.title = node.tooltip;
        div.style.left = node.x + "px";
        div.style.top = node.y + "px";
        div.style.width = node.width + "px";
        div.style.height = node.height + "px";
        div.style.background = node.fill;
        canvas.appendChild(div);
        node.element = div;
        nodeMap.set(node.node_id, node);
        let dragging = false, offsetX = 0, offsetY = 0;
        div.addEventListener("mousedown", (event) => {{
          dragging = true;
          offsetX = event.clientX - node.x;
          offsetY = event.clientY - node.y;
        }});
        window.addEventListener("mousemove", (event) => {{
          if (!dragging) return;
          node.x = event.clientX - offsetX;
          node.y = event.clientY - offsetY;
          div.style.left = node.x + "px";
          div.style.top = node.y + "px";
          renderEdges();
        }});
        window.addEventListener("mouseup", () => dragging = false);
      }}
    }}

    function renderEdges() {{
      svg.innerHTML = "";
      for (const edge of edges) {{
        const src = nodeMap.get(edge.src);
        const dst = nodeMap.get(edge.dst);
        if (!src || !dst) continue;
        const x1 = src.x + src.width;
        const y1 = src.y + src.height / 2;
        const x2 = dst.x;
        const y2 = dst.y + dst.height / 2;
        const mid = (x1 + x2) / 2;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", `M ${{x1}} ${{y1}} L ${{mid}} ${{y1}} L ${{mid}} ${{y2}} L ${{x2}} ${{y2}}`);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", edge.color);
        path.setAttribute("stroke-width", "2");
        if (edge.dashed) path.setAttribute("stroke-dasharray", "8 6");
        svg.appendChild(path);
      }}
    }}

    renderNodes();
    renderEdges();
  </script>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")


def output_paths_from_config(
    config: dict[str, Any],
    *,
    html_override: Path | None,
    json_override: Path | None,
) -> tuple[Path, Path]:
    outputs = config.get("outputs", {})
    if html_override is not None and json_override is not None:
        return html_override, json_override

    if "html" in outputs and "json" in outputs:
        html_output = html_override or Path(outputs["html"])
        json_output = json_override or Path(outputs["json"])
        return html_output, json_output

    domains = config["domains"]
    resolved_domains = resolve_domains(domains)
    strategies = config["strategies"]
    pp_strategy = strategies.get("pp_strategy", "gpipe")
    dp_strategy = strategies.get("dp_strategy", "naive_allreduce_after_backward")
    values = {
        "num_gpus": resolved_domains["num_gpus"],
        "pp_size": resolved_domains["pp_size"],
        "dp_size": resolved_domains["dp_size"],
        "tp_size": resolved_domains["tp_size"],
        "num_microbatches": resolved_domains["num_microbatches"],
        "num_layers": resolved_domains["num_layers"],
        "pp_strategy": pp_strategy,
        "dp_strategy": dp_strategy,
        "dp_strategy_short": DP_STRATEGY_SHORT_NAMES.get(dp_strategy, sanitize_name(dp_strategy)),
        "dag_id": sanitize_name(str(config.get("dag_id", "dag"))),
    }
    base_dir = Path(outputs.get("base_dir", "outputs"))
    name_template = outputs.get(
        "name_template",
        "pp{pp_size}_{pp_strategy}_dp{dp_size}_{dp_strategy_short}",
    )
    folder = sanitize_path_fragment(name_template.format(**values))
    html_filename = outputs.get("html_filename", "dag.html")
    json_filename = outputs.get("json_filename", "dag.json")
    html_output = html_override or base_dir / folder / html_filename
    json_output = json_override or base_dir / folder / json_filename
    return html_output, json_output


def sanitize_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value).strip("_")


def sanitize_path_fragment(value: str) -> str:
    return sanitize_name(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate first-stage logical DAG HTML and JSON artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--html-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    html_output, json_output = output_paths_from_config(
        config,
        html_override=args.html_output,
        json_override=args.json_output,
    )
    dag = build_dag(config, args.config, html_output, json_output)
    render_html(dag, html_output)
    write_json(dag, json_output)
    print(f"Wrote {html_output}")
    print(f"Wrote {json_output}")


if __name__ == "__main__":
    main()
