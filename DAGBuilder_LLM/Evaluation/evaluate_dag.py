from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def evaluate_longest_path(weighted_dag: dict[str, Any]) -> dict[str, Any]:
    nodes = weighted_dag.get("nodes", [])
    edges = weighted_dag.get("edges", [])
    node_by_id = {node["node_id"]: node for node in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in node_by_id}
    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        if src not in node_by_id or dst not in node_by_id:
            raise ValueError(f"Edge references unknown node: {edge}")
        outgoing[src].append(dst)
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
    predecessor: dict[str, str | None] = {}
    for node_id in topo:
        best_start = 0.0
        best_pred: str | None = None
        for edge in edges:
            if edge["dst"] != node_id:
                continue
            src = edge["src"]
            if finish[src] > best_start:
                best_start = finish[src]
                best_pred = src
        duration = float(node_by_id[node_id].get("duration_s", 0.0) or 0.0)
        finish[node_id] = best_start + duration
        predecessor[node_id] = best_pred

    end_node = weighted_dag.get("layout", {}).get("end_node")
    if end_node in finish:
        final_node = str(end_node)
    else:
        final_node = max(finish, key=finish.get)

    path: list[str] = []
    cursor: str | None = final_node
    while cursor is not None:
        path.append(cursor)
        cursor = predecessor[cursor]
    path.reverse()

    return {
        "dag_id": weighted_dag.get("dag_id", "dag"),
        "status": "pass",
        "duration_field": "duration_s",
        "longest_path_time_s": finish[final_node],
        "longest_path_node_count": len(path),
        "critical_path_node_ids": path,
        "critical_path_preview": [
            {
                "node_id": node_id,
                "label": node_by_id[node_id].get("label"),
                "task_kind": node_by_id[node_id].get("task_kind"),
                "duration_s": float(node_by_id[node_id].get("duration_s", 0.0) or 0.0),
            }
            for node_id in path[:25]
        ],
    }


def evaluate_baseline_and_overlap(
    baseline_dag: dict[str, Any],
    overlapped_dag: dict[str, Any] | None = None,
    overlap_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline = evaluate_longest_path(baseline_dag)
    baseline_latency = float(baseline["longest_path_time_s"])
    baseline["baseline_latency_s"] = baseline_latency
    if overlapped_dag is None:
        return baseline

    overlap_eval = evaluate_longest_path(overlapped_dag)
    overlap_latency = float(overlap_eval["longest_path_time_s"])
    saved_s = max(0.0, baseline_latency - overlap_latency)
    baseline["overlap_evaluation"] = {
        "status": overlap_eval["status"],
        "overlap_latency_s": overlap_latency,
        "overlap_saved_s": saved_s,
        "overlap_saved_ratio": saved_s / baseline_latency if baseline_latency > 0 else 0.0,
        "overlapped_dag_id": overlap_eval["dag_id"],
        "critical_path_node_ids": overlap_eval["critical_path_node_ids"],
        "critical_path_preview": overlap_eval["critical_path_preview"],
        "overlap_plan": [] if overlap_report is None else overlap_report.get("overlap_plan", []),
        "overlap_report": overlap_report,
    }
    return baseline


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 评估结果: {report['status'].upper()}",
        "",
        f"- DAG: `{report['dag_id']}`",
        f"- 最长路径时间: {report['longest_path_time_s']:.9f} s",
        f"- 关键路径节点数: {report['longest_path_node_count']}",
        "",
        "## 关键路径预览",
        "",
    ]
    for node in report["critical_path_preview"]:
        lines.append(
            f"- {node['node_id']} ({node['task_kind']}): {node['duration_s']:.9f} s"
        )
    overlap = report.get("overlap_evaluation")
    if overlap:
        lines.extend(
            [
                "",
                "## Overlap Evaluation",
                "",
                f"- Baseline latency: {report['baseline_latency_s']:.9f} s",
                f"- Overlap latency: {overlap['overlap_latency_s']:.9f} s",
                f"- Saved latency: {overlap['overlap_saved_s']:.9f} s",
                f"- Saved ratio: {overlap['overlap_saved_ratio']:.4%}",
                f"- Applied overlap rules: {len(overlap.get('overlap_plan', []))}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate weighted DAG longest path latency.")
    parser.add_argument("--weighted-dag", required=True, type=Path)
    parser.add_argument("--overlapped-weighted-dag", type=Path)
    parser.add_argument("--overlap-report", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    overlap_report = load_json(args.overlap_report) if args.overlap_report else None
    overlapped_dag = load_json(args.overlapped_weighted_dag) if args.overlapped_weighted_dag else None
    report = evaluate_baseline_and_overlap(load_json(args.weighted_dag), overlapped_dag, overlap_report)
    json_path = args.report_json or args.weighted_dag.with_name("evaluation_report.json")
    md_path = args.report_md or args.weighted_dag.with_name("evaluation_report.md")
    write_json(json_path, report)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
