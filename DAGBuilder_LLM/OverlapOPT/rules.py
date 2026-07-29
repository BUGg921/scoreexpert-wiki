from __future__ import annotations

import copy
from collections import defaultdict, deque
from typing import Any


PP_FORWARD_KINDS = {"pp_forward_send", "pp_forward_recv"}
DP_RS_AG_KINDS = {"dp_reducescatter", "dp_allgather"}


def apply_overlap_rules(weighted_dag: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    overlapped = copy.deepcopy(weighted_dag)
    node_by_id = {node["node_id"]: node for node in overlapped.get("nodes", [])}
    baseline_latency = longest_path_latency(weighted_dag)

    pp_events = apply_pp_overlap(node_by_id)
    dp_events = apply_dp_overlap(node_by_id)
    applied_events = pp_events + dp_events

    overlapped["dag_id"] = f"{weighted_dag.get('dag_id', 'dag')}_overlapped"
    overlapped["overlap_opt"] = {
        "version": 1,
        "source_dag_id": weighted_dag.get("dag_id", "dag"),
        "model": "duration_reduction_without_dependency_removal",
        "applied_event_count": len(applied_events),
        "total_hidden_s": sum(float(event["hidden_s"]) for event in applied_events),
        "topology_unchanged": True,
    }

    overlap_latency = longest_path_latency(overlapped)
    saved_s = max(0.0, baseline_latency - overlap_latency)
    report = {
        "status": "pass",
        "source_dag_id": weighted_dag.get("dag_id", "dag"),
        "overlapped_dag_id": overlapped["dag_id"],
        "baseline_latency_s": baseline_latency,
        "overlap_latency_s": overlap_latency,
        "overlap_saved_s": saved_s,
        "overlap_saved_ratio": saved_s / baseline_latency if baseline_latency > 0 else 0.0,
        "overlap_plan": applied_events,
        "safety": {
            "original_topology_preserved": True,
            "data_dependencies_removed": 0,
            "dependency_edges_removed": 0,
            "derived_dag_acyclic": True,
            "duration_only_rewrite": True,
        },
    }
    return overlapped, report


def apply_pp_overlap(node_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    compute_by_key: dict[tuple[int | None, int | None, int | None], list[dict[str, Any]]] = defaultdict(list)
    for node in node_by_id.values():
        task_kind = str(node.get("task_kind"))
        if task_kind != "forward":
            continue
        key = (
            optional_int(node.get("dp_rank")),
            optional_int(node.get("pp_stage_id")),
            optional_int(node.get("microbatch_id")),
        )
        compute_by_key[key].append(node)

    events: list[dict[str, Any]] = []
    for node in node_by_id.values():
        task_kind = str(node.get("task_kind"))
        if task_kind not in PP_FORWARD_KINDS:
            continue

        microbatch_id = optional_int(node.get("microbatch_id"))
        if microbatch_id is None or microbatch_id <= 0:
            continue
        overlap_key = (
            optional_int(node.get("dp_rank")),
            optional_int(node.get("pp_stage_id")),
            microbatch_id - 1,
        )
        overlap_candidates = compute_by_key.get(overlap_key, [])
        available_compute_s = sum(float(item.get("duration_s", 0.0) or 0.0) for item in overlap_candidates)
        duration_s = float(node.get("duration_s", 0.0) or 0.0)
        hidden_s = min(duration_s, available_compute_s)
        if hidden_s <= 0:
            continue

        original_duration_s = duration_s
        node["duration_s"] = max(0.0, duration_s - hidden_s)
        aligned_with = [item["node_id"] for item in overlap_candidates]
        annotate_node(
            node,
            original_duration_s,
            hidden_s,
            "pp_forward_send_recv_previous_microbatch_compute",
            aligned_with,
        )
        if overlap_candidates and "column" in overlap_candidates[0]:
            node["overlap_column"] = overlap_candidates[0]["column"]
        events.append(
            {
                "rule": "pp_forward_send_recv_previous_microbatch_compute",
                "node_id": node["node_id"],
                "task_kind": task_kind,
                "hidden_s": hidden_s,
                "remaining_s": float(node["duration_s"]),
                "aligned_start_with": aligned_with,
                "overlap_with": aligned_with,
                "reason": "PP forward send/recv for microbatch n is modeled as overlappable with same-stage forward compute from microbatch n-1.",
            }
        )
    return events


def apply_dp_overlap(node_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    backward_by_stage: dict[int | None, list[dict[str, Any]]] = defaultdict(list)
    for node in node_by_id.values():
        if node.get("task_kind") == "backward":
            backward_by_stage[optional_int(node.get("pp_stage_id"))].append(node)

    events: list[dict[str, Any]] = []
    for node in node_by_id.values():
        if node.get("task_kind") not in DP_RS_AG_KINDS:
            continue
        duration_s = float(node.get("duration_s", 0.0) or 0.0)
        if duration_s <= 0:
            continue

        stage = optional_int(node.get("pp_stage_id"))
        backward_compute_s = sum(float(item.get("duration_s", 0.0) or 0.0) for item in backward_by_stage.get(stage, []))
        task_kind = str(node.get("task_kind"))
        hidden_ratio = 0.5 if task_kind == "dp_reducescatter" else 0.25
        # V1 is conservative: only part of stage-level DP communication can be hidden.
        hidden_s = min(duration_s * hidden_ratio, backward_compute_s)
        if hidden_s <= 0:
            continue

        original_duration_s = duration_s
        node["duration_s"] = max(0.0, duration_s - hidden_s)
        rule = f"{task_kind}_backward_overlap"
        aligned_with = [item["node_id"] for item in backward_by_stage.get(stage, [])]
        annotate_node(node, original_duration_s, hidden_s, rule, aligned_with)
        events.append(
            {
                "rule": rule,
                "node_id": node["node_id"],
                "task_kind": task_kind,
                "hidden_s": hidden_s,
                "remaining_s": float(node["duration_s"]),
                "aligned_start_with": aligned_with,
                "overlap_with_stage": stage,
                "reason": f"Stage-level {task_kind} is treated as shardable, with part of communication hidden by backward compute.",
            }
        )
    return events


def annotate_node(
    node: dict[str, Any],
    original_duration_s: float,
    hidden_s: float,
    rule: str,
    aligned_start_with: list[str],
) -> None:
    node["original_duration_s"] = original_duration_s
    node["overlap_hidden_s"] = hidden_s
    detail = dict(node.get("overlap_opt_detail") or {})
    detail.update(
        {
            "rule": rule,
            "overlap_rule": rule,
            "aligned_start_with": aligned_start_with,
            "original_duration_s": original_duration_s,
            "hidden_s": hidden_s,
            "remaining_duration_s": float(node.get("duration_s", 0.0) or 0.0),
        }
    )
    node["overlap_opt_detail"] = detail


def longest_path_latency(weighted_dag: dict[str, Any]) -> float:
    nodes = weighted_dag.get("nodes", [])
    edges = weighted_dag.get("edges", [])
    node_by_id = {node["node_id"]: node for node in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in node_by_id}
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        if src not in node_by_id or dst not in node_by_id:
            raise ValueError(f"Edge references unknown node: {edge}")
        outgoing[src].append(dst)
        incoming[dst].append(src)
        indegree[dst] += 1

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    topo: list[str] = []
    while queue:
        node_id = queue.popleft()
        topo.append(node_id)
        for dst in outgoing[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                queue.append(dst)
    if len(topo) != len(node_by_id):
        raise ValueError("Weighted DAG contains a cycle.")

    finish: dict[str, float] = {}
    for node_id in topo:
        start_s = max((finish[src] for src in incoming[node_id]), default=0.0)
        finish[node_id] = start_s + float(node_by_id[node_id].get("duration_s", 0.0) or 0.0)

    end_node = weighted_dag.get("layout", {}).get("end_node")
    if end_node in finish:
        return finish[str(end_node)]
    return max(finish.values(), default=0.0)


def optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
