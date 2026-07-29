from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import load_config, validate_config
from .simulators.common import TimingResult, operation_key
from .simulators.compute import simulate_compute
from .simulators.dp import simulate_dp
from .simulators.ep import simulate_ep
from .simulators.pp import simulate_pp
from .simulators.profiling import ProfileEntry, ProfilingStore
from .topology import Topology


DP_TASKS = {"dp_allreduce", "dp_reducescatter", "dp_allgather", "zero3_allgather", "zero3_reducescatter"}
PP_TASKS = {"pp_forward_send", "pp_backward_send", "pp_forward_recv", "pp_backward_recv"}
COMPUTE_TASKS = {
    "compute",
    "forward",
    "backward",
    "attention_compute",
    "dense_compute",
    "expert_compute",
    "route_table_local",
    "local_grad_merge",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _edge_endpoints(edge: dict[str, Any]) -> tuple[str, str]:
    source = edge.get("src", edge.get("source", edge.get("source_node_id")))
    target = edge.get("dst", edge.get("target", edge.get("target_node_id")))
    if source is None or target is None:
        raise ValueError(f"DAG edge has no recognized endpoints: {edge}")
    return str(source), str(target)


def longest_path(dag: dict[str, Any]) -> dict[str, Any]:
    nodes = dag.get("nodes", [])
    node_by_id = {str(node["node_id"]): node for node in nodes}
    if len(node_by_id) != len(nodes):
        raise ValueError("DAG contains duplicate node_id values")
    successors: dict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in node_by_id}
    for edge in dag.get("edges", []):
        source, target = _edge_endpoints(edge)
        if source not in node_by_id or target not in node_by_id:
            raise ValueError(f"DAG edge references an unknown node: {source} -> {target}")
        successors[source].append(target)
        indegree[target] += 1
    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    distance = {node_id: float(node_by_id[node_id].get("duration_s") or 0.0) for node_id in queue}
    previous: dict[str, str] = {}
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in successors[source]:
            candidate = distance[source] + float(node_by_id[target].get("duration_s") or 0.0)
            if candidate > distance.get(target, float("-inf")):
                distance[target] = candidate
                previous[target] = source
            indegree[target] -= 1
            if indegree[target] == 0:
                distance.setdefault(target, float(node_by_id[target].get("duration_s") or 0.0))
                queue.append(target)
    if visited != len(nodes):
        raise ValueError("DAG contains a cycle; longest path is undefined")
    if not distance:
        return {"duration_s": 0.0, "node_ids": [], "nodes": []}
    end = max(distance, key=distance.get)
    path = [end]
    while end in previous:
        end = previous[end]
        path.append(end)
    path.reverse()
    return {
        "duration_s": distance[path[-1]],
        "node_ids": path,
        "nodes": [
            {
                "node_id": node_id,
                "duration_s": float(node_by_id[node_id].get("duration_s") or 0.0),
                "duration_source": node_by_id[node_id].get("duration_source"),
            }
            for node_id in path
        ],
    }


class SimulationEngine:
    def __init__(self, config: dict[str, Any], *, config_path: Path | None = None) -> None:
        validate_config(config)
        self.config = copy.deepcopy(config)
        self.config_path = config_path
        self.topology = Topology(self.config["topology"], self.config["network"])
        config_dir = config_path.parent if config_path is not None else None
        self.profiling = (
            ProfilingStore(self.config["profiling"], config_dir=config_dir)
            if self.config["profiling"].get("enabled", True)
            else None
        )

    def category(self, node: dict[str, Any]) -> str:
        task = str(node.get("task_kind") or "")
        if task == "control":
            return "control"
        operation = operation_key(node)
        operations = self.config["algorithms"].get("operations", {})
        spec = None
        for key in (str(node.get("node_id") or ""), str(node.get("op_name") or "")):
            if key and key in operations:
                spec = operations[key]
                break
        if spec and spec.get("category"):
            return str(spec["category"])
        domain = str(node.get("domain") or "")
        if task == "optimizer":
            return "optimizer"
        if task in DP_TASKS or domain in {"dp", "dp_cp", "dp_ep"} or operation.startswith("zero3_"):
            return "dp"
        if task in PP_TASKS:
            return "pp"
        if task.startswith("ep_"):
            return "ep"
        if task.startswith("tp_") or task.startswith("tp_sp_"):
            return "tp"
        if task in {"forward", "backward"} and "tp_" in operation:
            return "tp"
        if task in COMPUTE_TASKS:
            return "compute"
        return "other"

    def numerical_enabled(self, node: dict[str, Any], category: str) -> bool:
        overrides = self.config.get("simulation_overrides", {})
        node_id = str(node.get("node_id") or "")
        op_name = str(node.get("op_name") or "")
        if node_id in overrides.get("node_id", {}):
            return bool(overrides["node_id"][node_id])
        if op_name in overrides.get("op_name", {}):
            return bool(overrides["op_name"][op_name])
        return bool(self.config["simulation_flags"][category])

    def _validate_profile_coverage(self, nodes: list[dict[str, Any]]) -> None:
        missing: list[str] = []
        for node in nodes:
            category = self.category(node)
            if category == "control" or self.numerical_enabled(node, category):
                continue
            if self.profiling is None:
                missing.append(
                    f"{node.get('node_id')} [{category}] profiling is disabled"
                )
                continue
            if self.profiling.find(node) is None:
                candidates = ", ".join(self.profiling.candidate_keys(node))
                missing.append(f"{node.get('node_id')} [{category}] candidates=({candidates})")
        if missing:
            raise ValueError("Missing exact profiling entries:\n- " + "\n- ".join(missing))

    @staticmethod
    def _control_timing() -> TimingResult:
        return TimingResult(
            duration_s=0.0,
            source="zero_control",
            category="control",
            algorithm="zero_duration",
        )

    def _numerical_timing(self, node: dict[str, Any], category: str) -> TimingResult:
        if category == "dp":
            return simulate_dp(node, self.config, self.topology)
        if category == "pp":
            return simulate_pp(node, self.config, self.topology)
        if category == "ep":
            return simulate_ep(node, self.config, self.topology)
        if category == "compute":
            return simulate_compute(node, self.config, self.topology)
        raise ValueError(
            f"Category {category} has simulation flag 1, but simulator_v2 has no numerical provider for it"
        )

    def timing_for_node(self, node: dict[str, Any]) -> tuple[TimingResult, ProfileEntry | None]:
        category = self.category(node)
        if category == "control":
            return self._control_timing(), None
        if self.numerical_enabled(node, category):
            profile = self.profiling.find(node) if self.profiling is not None else None
            return self._numerical_timing(node, category), profile
        if self.profiling is None:
            raise ValueError(
                f"Node {node.get('node_id')} requires profiling, but profiling is disabled"
            )
        return self.profiling.timing(node, category), self.profiling.find(node)

    def simulate(self, dag: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
        nodes = dag.get("nodes")
        edges = dag.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("DAG must contain nodes and edges arrays")
        self._validate_profile_coverage(nodes)
        original_node_count = len(nodes)
        original_edge_count = len(edges)
        weighted = copy.deepcopy(dag)
        timing_rows: list[dict[str, Any]] = []
        for node in weighted["nodes"]:
            timing, profile = self.timing_for_node(node)
            detail = timing.to_dict()
            profile_duration = profile.duration_s if profile is not None else None
            error = None
            if profile_duration not in (None, 0.0):
                error = (timing.duration_s - profile_duration) / profile_duration
            node["duration_s"] = timing.duration_s
            node["duration_source"] = timing.source
            node["value_sim_v2"] = detail
            row = {
                "node_id": node["node_id"],
                "label": node.get("label"),
                "task_kind": node.get("task_kind"),
                "op_name": node.get("op_name"),
                "category": timing.category,
                "duration_source": timing.source,
                "duration_s": timing.duration_s,
                "profile_duration_s": profile_duration,
                "relative_error": error,
                **detail,
            }
            timing_rows.append(row)
        if len(weighted["nodes"]) != original_node_count or len(weighted["edges"]) != original_edge_count:
            raise RuntimeError("simulator_v2 changed DAG topology")
        critical = longest_path(weighted)
        weighted["value_sim_v2"] = {
            "node_count": original_node_count,
            "edge_count": original_edge_count,
            "topology_unchanged": True,
            "longest_path_s": critical["duration_s"],
        }
        return weighted, timing_rows, critical


def _summary(
    timing_rows: list[dict[str, Any]],
    critical: dict[str, Any],
    topology: Topology,
    topology_config: dict[str, Any],
) -> dict[str, Any]:
    source_counts = Counter(str(row["duration_source"]) for row in timing_rows)
    category_counts = Counter(str(row["category"]) for row in timing_rows)
    source_duration: dict[str, float] = defaultdict(float)
    category_duration: dict[str, float] = defaultdict(float)
    errors: list[dict[str, Any]] = []
    for row in timing_rows:
        source_duration[str(row["duration_source"])] += float(row["duration_s"])
        category_duration[str(row["category"])] += float(row["duration_s"])
        if row["relative_error"] is not None:
            errors.append(
                {
                    "node_id": row["node_id"],
                    "category": row["category"],
                    "relative_error": row["relative_error"],
                }
            )
    override_ranks = sorted(int(rank) for rank in topology_config.get("device_compute_tflops", {}))
    return {
        "node_count": len(timing_rows),
        "source_counts": dict(source_counts),
        "category_counts": dict(category_counts),
        "source_duration_s": dict(source_duration),
        "category_duration_s": dict(category_duration),
        "profile_comparisons": errors,
        "compute_rate_overrides": [
            {
                "rank": rank,
                "compute_tflops": topology.device(rank).compute_tflops,
                "server_id": topology.device(rank).server_id,
                "affinity_group_id": topology.device(rank).affinity_group_id,
            }
            for rank in override_ranks
        ],
        "longest_path": critical,
    }


def _render_summary(summary: dict[str, Any], timing_rows: list[dict[str, Any]], run_name: str) -> str:
    lines = [
        f"# ValueSim v2 仿真报告：{run_name}",
        "",
        f"- 节点数：{summary['node_count']}",
        f"- 最长路径：{summary['longest_path']['duration_s']:.9f} s",
        "- 所有 profiling 节点均采用精确键匹配；数值节点未使用 profiling 校准系数。",
        "",
        "## 数据来源",
        "",
        "| 来源 | 节点数 | 耗时合计 (s) |",
        "| --- | ---: | ---: |",
    ]
    for source, count in sorted(summary["source_counts"].items()):
        lines.append(f"| `{source}` | {count} | {summary['source_duration_s'].get(source, 0.0):.9f} |")
    lines.extend(["", "## 单卡计算速率覆盖", ""])
    if summary["compute_rate_overrides"]:
        lines.extend(
            [
                "| Rank | Server | 亲合组 | 计算速率 (TFLOP/s) |",
                "| ---: | ---: | ---: | ---: |",
            ]
        )
        for device in summary["compute_rate_overrides"]:
            lines.append(
                f"| {device['rank']} | {device['server_id']} | {device['affinity_group_id']} | "
                f"{device['compute_tflops']:.3f} |"
            )
    else:
        lines.append("本轮未配置逐卡计算速率覆盖，所有设备使用 topology 默认算力。")
    lines.extend(
        [
            "",
            "## 逐节点结果",
            "",
            "| 节点 | 类别 | 来源 | 算法 | Payload (B) | 线上数据/rank (B) | 步数 | 耗时 (ms) | Profiling (ms) | 误差 |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in timing_rows:
        profile = "-" if row["profile_duration_s"] is None else f"{row['profile_duration_s'] * 1000:.3f}"
        error = "-" if row["relative_error"] is None else f"{row['relative_error']:+.2%}"
        lines.append(
            f"| `{row['node_id']}` | {row['category']} | `{row['duration_source']}` | `{row['algorithm']}` | "
            f"{row['logical_payload_bytes']:.0f} | {row['wire_bytes_per_rank']:.0f} | {row['logical_steps']} | "
            f"{row['duration_s'] * 1000:.3f} | {profile} | {error} |"
        )
    lines.extend(["", "## 最长路径节点", ""])
    for node in summary["longest_path"]["nodes"]:
        lines.append(
            f"- `{node['node_id']}`：{node['duration_s'] * 1000:.3f} ms（{node['duration_source']}）"
        )
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _python_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def run_simulation(
    dag_path: Path,
    config_path: Path,
    *,
    run_name: str | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    dag_path = dag_path.resolve()
    config_path = config_path.resolve()
    config = load_config(config_path)
    engine = SimulationEngine(config, config_path=config_path)
    weighted, timing_rows, critical = engine.simulate(load_json(dag_path))
    summary = _summary(timing_rows, critical, engine.topology, config["topology"])
    resolved_name = run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    root = output_root or Path(__file__).resolve().parent / "output"
    output_dir = root / resolved_name
    if output_dir.exists():
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    manifest = {
        "run_name": resolved_name,
        "created_at": datetime.now().astimezone().isoformat(),
        "dag_path": str(dag_path),
        "dag_sha256": _sha256(dag_path),
        "config_path": str(config_path),
        "config_sha256": _sha256(config_path),
        "profiling_path": str(engine.profiling.path) if engine.profiling is not None else None,
        "profiling_sha256": _sha256(engine.profiling.path) if engine.profiling is not None else None,
        "simulator_python_sha256": _python_tree_sha256(Path(__file__).resolve().parent),
        "files": [
            "weighted_dag.json",
            "node_timings.json",
            "topology.json",
            "resolved_config.json",
            "run_manifest.json",
            "summary.json",
            "summary.md",
        ],
    }
    write_json(output_dir / "weighted_dag.json", weighted)
    write_json(output_dir / "node_timings.json", timing_rows)
    write_json(output_dir / "topology.json", engine.topology.to_dict())
    write_json(output_dir / "resolved_config.json", config)
    write_json(output_dir / "run_manifest.json", manifest)
    write_json(output_dir / "summary.json", summary)
    (output_dir / "summary.md").write_text(
        _render_summary(summary, timing_rows, resolved_name), encoding="utf-8"
    )
    return {"output_dir": output_dir, "summary": summary, "manifest": manifest}
