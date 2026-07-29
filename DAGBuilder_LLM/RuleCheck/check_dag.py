from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DAG = (
    ROOT.parent
    / "DagGenerator"
    / "outputs"
    / "pp4_gpipe_dp2_naive_ar"
    / "dag.json"
)
DEFAULT_RULES = ROOT / "rules" / "default_rules.json"


@dataclass
class Finding:
    id: str
    severity: str
    category: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    edge_refs: list[dict[str, str]] = field(default_factory=list)
    expected: str = ""
    actual: str = ""
    suggested_fix_for_generator: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "node_ids": self.node_ids,
            "edge_refs": self.edge_refs,
            "expected": self.expected,
            "actual": self.actual,
            "suggested_fix_for_generator": self.suggested_fix_for_generator,
        }


class RuleChecker:
    def __init__(self, dag: dict[str, Any], rules: dict[str, Any], source_dag: Path):
        self.dag = dag
        self.rules = rules
        self.source_dag = source_dag
        self.findings: list[Finding] = []
        self.diagnostics: list[Finding] = []
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, str]] = []
        self.node_by_id: dict[str, dict[str, Any]] = {}
        self.edge_set: set[tuple[str, str]] = set()
        self.edge_kind_set: set[tuple[str, str, str]] = set()
        self.outgoing: dict[str, list[str]] = defaultdict(list)
        self.incoming_edges: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.outgoing_edges: dict[str, list[dict[str, str]]] = defaultdict(list)

    def run(self) -> dict[str, Any]:
        self._check_schema()
        if not self._has_minimum_shape():
            return self._report()

        self.nodes = list(self.dag.get("nodes", []))
        self.edges = list(self.dag.get("edges", []))
        self._index_graph()

        self._check_unique_node_ids()
        self._check_parallel_domain_product()
        self._check_edge_endpoints()
        self._check_acyclic()
        self._check_start_reaches_end()
        self._check_forward_backward_pairing()
        self._check_intra_layer_dependencies()
        self._check_model_layer_dependencies()
        self._check_pp_cross_stage_dependencies()
        self._check_stream_placement()
        self._check_resource_serialization()
        self._check_naive_dp_allreduce()
        self._check_reduce_scatter_allgather()
        self._check_zero01_tail_order()
        self._check_dp_collective_duplication()
        self._check_readability()
        return self._report()

    def _enabled(self, name: str) -> bool:
        return bool(self.rules.get("enabled_checks", {}).get(name, True))

    def _severity(self, name: str, default: str = "error") -> str:
        return str(self.rules.get("severity", {}).get(name, default))

    def _add(
        self,
        *,
        rule: str,
        category: str,
        message: str,
        node_ids: list[str] | None = None,
        edge_refs: list[dict[str, str]] | None = None,
        expected: str = "",
        actual: str = "",
        suggested_fix_for_generator: str = "",
        diagnostic: bool = False,
    ) -> None:
        target = self.diagnostics if diagnostic else self.findings
        target.append(
            Finding(
                id=f"{rule}_{len(target) + 1:04d}",
                severity=self._severity(rule, "readability" if diagnostic else "error"),
                category=category,
                message=message,
                node_ids=node_ids or [],
                edge_refs=edge_refs or [],
                expected=expected,
                actual=actual,
                suggested_fix_for_generator=suggested_fix_for_generator,
            )
        )

    def _check_schema(self) -> None:
        if not self._enabled("schema"):
            return
        required = {"nodes", "edges", "layout", "domains", "selected_rules", "outputs"}
        missing = sorted(required - set(self.dag))
        if missing:
            self._add(
                rule="schema",
                category="schema",
                message="DAG JSON is missing required top-level fields.",
                expected=", ".join(sorted(required)),
                actual=", ".join(missing),
                suggested_fix_for_generator="Serialize the full DAG artifact contract before running RuleCheck.",
            )
        if not isinstance(self.dag.get("nodes", []), list) or not isinstance(self.dag.get("edges", []), list):
            self._add(
                rule="schema",
                category="schema",
                message="DAG nodes and edges must both be arrays.",
                expected="nodes: list, edges: list",
                actual=f"nodes: {type(self.dag.get('nodes')).__name__}, edges: {type(self.dag.get('edges')).__name__}",
                suggested_fix_for_generator="Write expanded nodes and edges as JSON arrays.",
            )

    def _has_minimum_shape(self) -> bool:
        return isinstance(self.dag.get("nodes"), list) and isinstance(self.dag.get("edges"), list)

    def _index_graph(self) -> None:
        self.node_by_id = {
            node.get("node_id"): node
            for node in self.nodes
            if isinstance(node, dict) and isinstance(node.get("node_id"), str)
        }
        for edge in self.edges:
            if not isinstance(edge, dict):
                continue
            src = edge.get("src")
            dst = edge.get("dst")
            kind = edge.get("edge_kind")
            if isinstance(src, str) and isinstance(dst, str):
                self.edge_set.add((src, dst))
                self.outgoing[src].append(dst)
                self.incoming_edges[dst].append(edge)
                self.outgoing_edges[src].append(edge)
                if isinstance(kind, str):
                    self.edge_kind_set.add((src, dst, kind))

    def _check_unique_node_ids(self) -> None:
        if not self._enabled("node_ids_unique"):
            return
        seen: set[str] = set()
        duplicates: list[str] = []
        for node in self.nodes:
            node_id = node.get("node_id") if isinstance(node, dict) else None
            if not isinstance(node_id, str):
                self._add(
                    rule="node_ids_unique",
                    category="schema",
                    message="A node is missing a string node_id.",
                    actual=str(node),
                    suggested_fix_for_generator="Assign a stable string node_id to every node.",
                )
                continue
            if node_id in seen:
                duplicates.append(node_id)
            seen.add(node_id)
        if duplicates:
            self._add(
                rule="node_ids_unique",
                category="schema",
                message="Duplicate node ids found.",
                node_ids=sorted(set(duplicates)),
                expected="Every node_id is unique.",
                actual=", ".join(sorted(set(duplicates))),
                suggested_fix_for_generator="Include enough metadata in node_id to distinguish DP rank, stage, layer, microbatch, and task kind.",
            )

    def _check_parallel_domain_product(self) -> None:
        if not self._enabled("parallel_domain_product"):
            return
        domains = self.dag.get("domains", {})
        if "num_gpus" not in domains:
            self._add(
                rule="parallel_domain_product",
                category="domain_semantics",
                message="DAG domains are missing num_gpus.",
                expected="domains.num_gpus exists and equals pp_size * tp_size * dp_size.",
                actual="num_gpus missing.",
                suggested_fix_for_generator="Serialize num_gpus into the generated DAG domains.",
            )
            return
        try:
            num_gpus = int(domains["num_gpus"])
            pp_size = int(domains["pp_size"])
            tp_size = int(domains["tp_size"])
            dp_size = int(domains["dp_size"])
        except (KeyError, TypeError, ValueError) as exc:
            self._add(
                rule="parallel_domain_product",
                category="domain_semantics",
                message="Parallel domain fields are not valid integers.",
                expected="num_gpus, pp_size, tp_size, and dp_size are positive integers.",
                actual=str(exc),
                suggested_fix_for_generator="Serialize all parallel domain sizes as integers.",
            )
            return
        product = pp_size * tp_size * dp_size
        if product != num_gpus:
            self._add(
                rule="parallel_domain_product",
                category="domain_semantics",
                message="Parallel domain product does not equal num_gpus.",
                expected="pp_size * tp_size * dp_size == num_gpus",
                actual=f"{pp_size} * {tp_size} * {dp_size} = {product}, num_gpus = {num_gpus}",
                suggested_fix_for_generator="Reject invalid configs or derive tp_size so PP * TP * DP equals num_gpus.",
            )

    def _check_edge_endpoints(self) -> None:
        if not self._enabled("edge_endpoints_exist"):
            return
        missing: list[dict[str, str]] = []
        for edge in self.edges:
            src = edge.get("src")
            dst = edge.get("dst")
            if src not in self.node_by_id or dst not in self.node_by_id:
                missing.append({"src": str(src), "dst": str(dst), "edge_kind": str(edge.get("edge_kind", ""))})
        if missing:
            self._add(
                rule="edge_endpoints_exist",
                category="schema",
                message="Some edges reference missing nodes.",
                edge_refs=missing[:20],
                expected="Every edge src/dst exists in nodes.",
                actual=f"{len(missing)} invalid edge(s)",
                suggested_fix_for_generator="Generate nodes before edges and validate edge endpoints before serialization.",
            )

    def _check_acyclic(self) -> None:
        if not self._enabled("acyclic"):
            return
        cycle = self._find_cycle()
        if cycle:
            self._add(
                rule="acyclic",
                category="graph_validity",
                message="DAG contains a cycle.",
                node_ids=cycle,
                expected="No directed cycle.",
                actual=" -> ".join(cycle),
                suggested_fix_for_generator="Remove or reverse the edge that turns a dependency chain back to an earlier task.",
            )

    def _find_cycle(self) -> list[str]:
        state: dict[str, int] = {}
        for node_id in sorted(self.node_by_id):
            if state.get(node_id, 0) != 0:
                continue
            state[node_id] = 1
            stack: list[tuple[str, int]] = [(node_id, 0)]
            path: list[str] = [node_id]
            path_index: dict[str, int] = {node_id: 0}
            while stack:
                current, child_index = stack[-1]
                children = [
                    child
                    for child in self.outgoing.get(current, [])
                    if child in self.node_by_id
                ]
                if child_index >= len(children):
                    stack.pop()
                    path.pop()
                    path_index.pop(current, None)
                    state[current] = 2
                    continue

                child = children[child_index]
                stack[-1] = (current, child_index + 1)
                child_state = state.get(child, 0)
                if child_state == 1:
                    return path[path_index[child]:] + [child]
                if child_state == 0:
                    state[child] = 1
                    path_index[child] = len(path)
                    path.append(child)
                    stack.append((child, 0))
        return []

    def _check_start_reaches_end(self) -> None:
        if not self._enabled("start_reaches_end"):
            return
        start = self.dag.get("layout", {}).get("start_node", "start")
        end = self.dag.get("layout", {}).get("end_node", "end")
        if start not in self.node_by_id or end not in self.node_by_id:
            self._add(
                rule="start_reaches_end",
                category="graph_validity",
                message="Start or End node is missing.",
                node_ids=[str(start), str(end)],
                expected="Both layout start_node and end_node exist.",
                actual="Missing start or end.",
                suggested_fix_for_generator="Emit explicit Start and End control nodes and record them in layout.",
            )
            return
        if not self._reachable(start, end):
            self._add(
                rule="start_reaches_end",
                category="graph_validity",
                message="End is not reachable from Start.",
                node_ids=[start, end],
                expected="A directed path exists from Start to End.",
                actual="No path found.",
                suggested_fix_for_generator="Connect only true completion dependencies, but preserve at least one full Start-to-End path.",
            )

    def _layer_nodes(self, task_kind: str) -> list[dict[str, Any]]:
        return [
            node for node in self.nodes
            if node.get("task_kind") == task_kind
            and node.get("global_layer_id") is not None
            and node.get("microbatch_id") is not None
            and node.get("dp_rank") is not None
        ]

    def _layer_key(self, node: dict[str, Any]) -> tuple[int, int, int]:
        return (int(node["dp_rank"]), int(node["global_layer_id"]), int(node["microbatch_id"]))

    def _check_forward_backward_pairing(self) -> None:
        if not self._enabled("forward_backward_pairing"):
            return
        forwards = {self._layer_key(node): node for node in self._layer_nodes("forward")}
        for backward in self._layer_nodes("backward"):
            key = self._layer_key(backward)
            if key not in forwards:
                self._add(
                    rule="forward_backward_pairing",
                    category="model_semantics",
                    message="Backward node has no matching forward node.",
                    node_ids=[backward["node_id"]],
                    expected=f"F(layer={key[1]}, microbatch={key[2]}, dp={key[0]}) exists.",
                    actual="Matching forward node missing.",
                    suggested_fix_for_generator="Generate paired F(x,y) and B(x,y) nodes for every DP rank, layer, and microbatch.",
                )

    def _check_intra_layer_dependencies(self) -> None:
        if not self._enabled("intra_layer_dependency"):
            return
        forwards = {self._layer_key(node): node for node in self._layer_nodes("forward")}
        backwards = {self._layer_key(node): node for node in self._layer_nodes("backward")}
        for key, forward in forwards.items():
            backward = backwards.get(key)
            if not backward:
                continue
            if (forward["node_id"], backward["node_id"]) not in self.edge_set:
                self._add(
                    rule="intra_layer_dependency",
                    category="model_semantics",
                    message="Missing layer-local F(x,y) -> B(x,y) dependency.",
                    node_ids=[forward["node_id"], backward["node_id"]],
                    expected=f"{forward['node_id']} -> {backward['node_id']}",
                    actual="Edge missing.",
                    suggested_fix_for_generator="Add an intra_layer_dependency data edge from every forward layer task to its matching backward task.",
                )

    def _check_model_layer_dependencies(self) -> None:
        if not self._enabled("model_layer_dependencies"):
            return
        pp_size = int(self.dag.get("domains", {}).get("pp_size", 0) or 0)
        num_layers = int(self.dag.get("domains", {}).get("num_layers", 0) or 0)
        num_microbatches = int(self.dag.get("domains", {}).get("num_microbatches", 0) or 0)
        dp_ranks = sorted({int(node["dp_rank"]) for node in self._layer_nodes("forward")})
        if num_layers <= 1:
            return
        stage_by_layer = self._stage_by_layer()
        for dp_rank in dp_ranks:
            for microbatch_id in range(num_microbatches):
                for layer_id in range(num_layers - 1):
                    f0 = self._find_layer_node("forward", dp_rank, layer_id, microbatch_id)
                    f1 = self._find_layer_node("forward", dp_rank, layer_id + 1, microbatch_id)
                    b0 = self._find_layer_node("backward", dp_rank, layer_id, microbatch_id)
                    b1 = self._find_layer_node("backward", dp_rank, layer_id + 1, microbatch_id)
                    if f0 and f1 and stage_by_layer.get(layer_id) == stage_by_layer.get(layer_id + 1):
                        self._require_edge(
                            rule="model_layer_dependencies",
                            category="model_semantics",
                            src=f0["node_id"],
                            dst=f1["node_id"],
                            expected_kind=self.rules["edge_kinds"]["forward_model"],
                            message="Missing same-stage forward layer dependency.",
                            fix="Add model_forward_dependency edges between adjacent forward layers in the same stage.",
                        )
                    if b0 and b1 and stage_by_layer.get(layer_id) == stage_by_layer.get(layer_id + 1):
                        self._require_edge(
                            rule="model_layer_dependencies",
                            category="model_semantics",
                            src=b1["node_id"],
                            dst=b0["node_id"],
                            expected_kind=self.rules["edge_kinds"]["backward_model"],
                            message="Missing same-stage backward layer dependency.",
                            fix="Add model_backward_dependency edges from higher layer backward to lower layer backward in the same stage.",
                        )
        if pp_size <= 0:
            return

    def _check_pp_cross_stage_dependencies(self) -> None:
        if not self._enabled("pp_cross_stage_dependencies"):
            return
        stage_layers = self._layers_by_stage()
        pp_size = int(self.dag.get("domains", {}).get("pp_size", len(stage_layers)) or len(stage_layers))
        num_microbatches = int(self.dag.get("domains", {}).get("num_microbatches", 0) or 0)
        dp_ranks = sorted({int(node["dp_rank"]) for node in self._layer_nodes("forward")})
        for dp_rank in dp_ranks:
            for microbatch_id in range(num_microbatches):
                for stage_id in range(pp_size - 1):
                    if stage_id not in stage_layers or stage_id + 1 not in stage_layers:
                        continue
                    src_layer = max(stage_layers[stage_id])
                    dst_layer = min(stage_layers[stage_id + 1])
                    src_f = self._find_layer_node("forward", dp_rank, src_layer, microbatch_id)
                    dst_f = self._find_layer_node("forward", dp_rank, dst_layer, microbatch_id)
                    ppf = self._find_pp_node("pp_forward_send", dp_rank, stage_id, microbatch_id)
                    if not (src_f and dst_f and ppf):
                        self._add(
                            rule="pp_cross_stage_dependencies",
                            category="pp_semantics",
                            message="Missing PP forward communication node or endpoint.",
                            node_ids=[node["node_id"] for node in (src_f, dst_f, ppf) if node],
                            expected=f"F stage {stage_id} -> P2P-F -> F stage {stage_id + 1}",
                            actual=f"dp={dp_rank}, microbatch={microbatch_id}",
                            suggested_fix_for_generator="Generate one P2P-F node per neighboring stage pair and microbatch.",
                        )
                    else:
                        self._require_edge("pp_cross_stage_dependencies", "pp_semantics", src_f["node_id"], ppf["node_id"], self.rules["edge_kinds"]["pp_forward_send"], "Missing PP forward send edge.", "Connect source stage forward output to P2P-F.")
                        self._require_edge("pp_cross_stage_dependencies", "pp_semantics", ppf["node_id"], dst_f["node_id"], self.rules["edge_kinds"]["pp_forward_recv"], "Missing PP forward receive edge.", "Connect P2P-F to destination stage forward input.")

                    src_b = self._find_layer_node("backward", dp_rank, dst_layer, microbatch_id)
                    dst_b = self._find_layer_node("backward", dp_rank, src_layer, microbatch_id)
                    ppb = self._find_pp_node("pp_backward_send", dp_rank, stage_id + 1, microbatch_id)
                    if not (src_b and dst_b and ppb):
                        self._add(
                            rule="pp_cross_stage_dependencies",
                            category="pp_semantics",
                            message="Missing PP backward communication node or endpoint.",
                            node_ids=[node["node_id"] for node in (src_b, dst_b, ppb) if node],
                            expected=f"B stage {stage_id + 1} -> P2P-B -> B stage {stage_id}",
                            actual=f"dp={dp_rank}, microbatch={microbatch_id}",
                            suggested_fix_for_generator="Generate one P2P-B node per neighboring stage pair and microbatch.",
                        )
                    else:
                        self._require_edge("pp_cross_stage_dependencies", "pp_semantics", src_b["node_id"], ppb["node_id"], self.rules["edge_kinds"]["pp_backward_send"], "Missing PP backward send edge.", "Connect downstream backward output to P2P-B.")
                        self._require_edge("pp_cross_stage_dependencies", "pp_semantics", ppb["node_id"], dst_b["node_id"], self.rules["edge_kinds"]["pp_backward_recv"], "Missing PP backward receive edge.", "Connect P2P-B to upstream backward input.")

    def _check_stream_placement(self) -> None:
        if not self._enabled("stream_placement"):
            return
        for node in self.nodes:
            task_kind = node.get("task_kind")
            stream = node.get("stream_type")
            if task_kind in {"forward", "backward", "optimizer"} and stream != "comp":
                self._add(
                    rule="stream_placement",
                    category="stream_semantics",
                    message="Computation task is not on a compute stream.",
                    node_ids=[node["node_id"]],
                    expected="stream_type=comp",
                    actual=f"stream_type={stream}",
                    suggested_fix_for_generator="Place F/B/OPT nodes on the stage compute row.",
                )
            if task_kind in {"pp_forward_send", "pp_backward_send"} and stream != "comm":
                self._add(
                    rule="stream_placement",
                    category="stream_semantics",
                    message="PP communication task is not on a communication stream.",
                    node_ids=[node["node_id"]],
                    expected="stream_type=comm",
                    actual=f"stream_type={stream}",
                    suggested_fix_for_generator="Place P2P-F/P2P-B nodes on the stage communication row.",
                )
            if task_kind == "dp_allreduce" and stream != "dp_comm":
                self._add(
                    rule="stream_placement",
                    category="stream_semantics",
                    message="DP allreduce task is not on the DP communication stream.",
                    node_ids=[node["node_id"]],
                    expected="stream_type=dp_comm",
                    actual=f"stream_type={stream}",
                    suggested_fix_for_generator="Place DP collective nodes on a DP communication row or declare a different DP collective layout.",
                )
            if task_kind in {"dp_reducescatter", "dp_allgather"} and stream != "dp_comm":
                self._add(
                    rule="stream_placement",
                    category="stream_semantics",
                    message="DP shard collective task is not on the DP communication stream.",
                    node_ids=[node["node_id"]],
                    expected="stream_type=dp_comm",
                    actual=f"stream_type={stream}",
                    suggested_fix_for_generator="Place DP ReduceScatter and AllGather nodes on the DP communication row.",
                )

    def _check_resource_serialization(self) -> None:
        if not self._enabled("resource_serialization"):
            return
        rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in self.nodes:
            if node.get("stream_type") in {"comp", "comm", "dp_comm"}:
                rows[str(node.get("row", ""))].append(node)
        for row, row_nodes in rows.items():
            ordered = sorted(row_nodes, key=lambda node: (float(node.get("column", 0)), str(node.get("node_id"))))
            for left, right in zip(ordered, ordered[1:]):
                if (left["node_id"], right["node_id"], self.rules["edge_kinds"]["resource"]) in self.edge_kind_set:
                    continue
                rule = {
                    "comp": "compute_resource_serialization",
                    "comm": "comm_resource_serialization",
                    "dp_comm": "dp_comm_resource_serialization",
                }.get(str(left.get("stream_type")), "resource_serialization")
                self._add(
                    rule=rule,
                    category="stream_semantics",
                    message="Adjacent tasks on the same stream are missing a resource-order edge.",
                    node_ids=[left["node_id"], right["node_id"]],
                    expected=f"{left['node_id']} -> {right['node_id']} with resource_dependency",
                    actual=f"row={row}",
                    suggested_fix_for_generator="Add green resource_dependency edges between consecutive tasks sharing the same stream.",
                )

    def _check_naive_dp_allreduce(self) -> None:
        if not self._enabled("naive_dp_allreduce"):
            return
        dp_strategy = self.dag.get("selected_rules", {}).get("dp_strategy")
        if dp_strategy != "naive_allreduce_after_backward":
            return
        stage_layers = self._layers_by_stage()
        num_microbatches = int(self.dag.get("domains", {}).get("num_microbatches", 0) or 0)
        dp_ranks = sorted({int(node["dp_rank"]) for node in self._layer_nodes("backward")})
        for ar_node in [node for node in self.nodes if node.get("task_kind") == "dp_allreduce"]:
            stage_id = ar_node.get("pp_stage_id")
            if stage_id is None or int(stage_id) not in stage_layers:
                continue
            required: list[str] = []
            for dp_rank in dp_ranks:
                for layer_id in stage_layers[int(stage_id)]:
                    for microbatch_id in range(num_microbatches):
                        backward = self._find_layer_node("backward", dp_rank, layer_id, microbatch_id)
                        if backward:
                            required.append(backward["node_id"])
            missing_reach = [node_id for node_id in required if not self._reachable(node_id, ar_node["node_id"])]
            if missing_reach:
                self._add(
                    rule="naive_dp_allreduce",
                    category="dp_semantics",
                    message="DP allreduce can start before all required backward nodes reach it.",
                    node_ids=[ar_node["node_id"], *missing_reach[:10]],
                    expected="All backward nodes for this stage and all DP ranks reach the DP allreduce.",
                    actual=f"{len(missing_reach)} missing predecessor path(s)",
                    suggested_fix_for_generator="Add trigger dependencies from each stage's completed backward frontier to its DP allreduce node.",
                )

    def _check_reduce_scatter_allgather(self) -> None:
        if not self._enabled("reduce_scatter_allgather"):
            return
        dp_strategy = self.dag.get("selected_rules", {}).get("dp_strategy")
        if dp_strategy != "reduce_scatter_allgather_after_backward":
            return
        stage_layers = self._layers_by_stage()
        num_microbatches = int(self.dag.get("domains", {}).get("num_microbatches", 0) or 0)
        dp_ranks = sorted({int(node["dp_rank"]) for node in self._layer_nodes("backward")})
        for rs_node in [node for node in self.nodes if node.get("task_kind") == "dp_reducescatter"]:
            stage_id = rs_node.get("pp_stage_id")
            if stage_id is None or int(stage_id) not in stage_layers:
                continue
            ag_nodes = [
                node for node in self.nodes
                if node.get("task_kind") == "dp_allgather" and node.get("pp_stage_id") == stage_id
            ]
            if not ag_nodes:
                self._add(
                    rule="reduce_scatter_allgather",
                    category="dp_semantics",
                    message="DP ReduceScatter has no matching AllGather for the same stage.",
                    node_ids=[rs_node["node_id"]],
                    expected="One dp_allgather with the same pp_stage_id.",
                    actual="Matching dp_allgather missing.",
                    suggested_fix_for_generator="Generate a DP AllGather node after each stage ReduceScatter.",
                )
                continue
            ag_node = ag_nodes[0]
            if not self._reachable(rs_node["node_id"], ag_node["node_id"]):
                self._add(
                    rule="reduce_scatter_allgather",
                    category="dp_semantics",
                    message="DP AllGather is not reachable from ReduceScatter.",
                    node_ids=[rs_node["node_id"], ag_node["node_id"]],
                    expected="ReduceScatter reaches AllGather.",
                    actual="No path found.",
                    suggested_fix_for_generator="Add a data dependency from ReduceScatter to AllGather.",
                )
            required: list[str] = []
            for dp_rank in dp_ranks:
                for layer_id in stage_layers[int(stage_id)]:
                    for microbatch_id in range(num_microbatches):
                        backward = self._find_layer_node("backward", dp_rank, layer_id, microbatch_id)
                        if backward:
                            required.append(backward["node_id"])
            missing_reach = [node_id for node_id in required if not self._reachable(node_id, rs_node["node_id"])]
            if missing_reach:
                self._add(
                    rule="reduce_scatter_allgather",
                    category="dp_semantics",
                    message="DP ReduceScatter can start before all required backward nodes reach it.",
                    node_ids=[rs_node["node_id"], *missing_reach[:10]],
                    expected="All backward nodes for this stage and all DP ranks reach ReduceScatter.",
                    actual=f"{len(missing_reach)} missing predecessor path(s)",
                    suggested_fix_for_generator="Add trigger dependencies from each stage's completed backward frontier to ReduceScatter.",
                )

    def _check_zero01_tail_order(self) -> None:
        if not self._enabled("zero01_tail_order"):
            return
        zero_nodes = self._zero_nodes()
        if not any(zero_nodes.values()) and self.dag.get("selected_rules", {}).get("dp_strategy") != "zero_01":
            return
        for gar in zero_nodes["gar"]:
            ready_ok = any(self._reachable(ready["node_id"], gar["node_id"]) for ready in zero_nodes["ready"])
            opt_nodes = [opt for opt in zero_nodes["opt"] if self._reachable(gar["node_id"], opt["node_id"])]
            pag_ok = any(self._reachable(opt["node_id"], pag["node_id"]) for opt in opt_nodes for pag in zero_nodes["pag"])
            if not (ready_ok and opt_nodes and pag_ok):
                self._add(
                    rule="zero01_tail_order",
                    category="dp_semantics",
                    message="ZeRO01 tail does not satisfy R -> G-AR -> OPT -> P-AG.",
                    node_ids=[gar["node_id"]],
                    expected="A ready marker reaches G-AR, G-AR reaches OPT, and OPT reaches P-AG.",
                    actual=f"ready_to_gar={ready_ok}, gar_to_opt={bool(opt_nodes)}, opt_to_pag={pag_ok}",
                    suggested_fix_for_generator="Generate explicit ZeRO01 semantic edges in the order R -> G-AR -> OPT -> P-AG.",
                )

    def _check_dp_collective_duplication(self) -> None:
        if not self._enabled("dp_collective_duplication"):
            return
        collective_nodes = [
            node for node in self.nodes
            if self._is_gar(node) or self._is_pag(node)
        ]
        by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in collective_nodes:
            by_label[str(node.get("label", node.get("node_id")))].append(node)
        for label, nodes in by_label.items():
            dp_ranks = {node.get("dp_rank") for node in nodes if node.get("dp_rank") is not None}
            if len(nodes) > 1 and len(dp_ranks) > 1:
                self._add(
                    rule="dp_collective_duplication",
                    category="dp_semantics",
                    message="DP group collective appears duplicated across DP ranks.",
                    node_ids=[node["node_id"] for node in nodes],
                    expected="One group collective node, or explicit metadata declaring replica-local participant view.",
                    actual=f"label={label}, copies={len(nodes)}",
                    suggested_fix_for_generator="Use a shared DP Group Comm row for group-level views, or annotate duplicated nodes as participant views.",
                )

    def _check_readability(self) -> None:
        if not self._enabled("readability"):
            return
        start = self.dag.get("layout", {}).get("start_node", "start")
        end = self.dag.get("layout", {}).get("end_node", "end")
        if end in self.node_by_id:
            end_col = float(self.node_by_id[end].get("column", 0))
            max_col = max(float(node.get("column", 0)) for node in self.nodes)
            if end_col < max_col:
                self._add(
                    rule="readability",
                    category="readability",
                    message="End node is not placed at the far right.",
                    node_ids=[end],
                    expected="End column is greater than or equal to all other columns.",
                    actual=f"end column={end_col}, max column={max_col}",
                    suggested_fix_for_generator="Place End to the right of the last real completion node.",
                    diagnostic=True,
                )
        reachable = self._reachable_set(start) if start in self.node_by_id else set()
        important_unreachable = [
            node["node_id"] for node in self.nodes
            if node.get("task_kind") not in {"control"} and node["node_id"] not in reachable
        ]
        if important_unreachable:
            self._add(
                rule="readability",
                category="readability",
                message="Some non-control nodes are not reachable from Start.",
                node_ids=important_unreachable[:20],
                expected="Main DAG nodes are reachable from Start.",
                actual=f"{len(important_unreachable)} unreachable non-control node(s)",
                suggested_fix_for_generator="Connect generated subgraphs into the main Start-to-End execution path.",
                diagnostic=True,
            )
        expected_roles = {
            "control": "control",
            "resource_dependency": "resource_dependency",
        }
        bad_roles = []
        for edge in self.edges:
            kind = edge.get("edge_kind")
            role = edge.get("color_role")
            if kind in expected_roles and role != expected_roles[kind]:
                bad_roles.append(edge)
        if bad_roles:
            self._add(
                rule="readability",
                category="readability",
                message="Some edges use a color role inconsistent with their edge kind.",
                edge_refs=[
                    {"src": e["src"], "dst": e["dst"], "edge_kind": str(e.get("edge_kind", ""))}
                    for e in bad_roles[:20]
                ],
                expected="control edges black/control role; resource edges green/resource role.",
                actual=f"{len(bad_roles)} inconsistent edge(s)",
                suggested_fix_for_generator="Keep control, data, and resource color roles aligned with edge semantics.",
                diagnostic=True,
            )
        minimum_gap = float(self.rules.get("layout", {}).get("minimum_same_row_column_gap", 0.7))
        tight_pairs: list[tuple[dict[str, Any], dict[str, Any], str, float]] = []
        rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in self.nodes:
            if node.get("stream_type") in {"comp", "comm", "dp_comm"}:
                rows[str(node.get("row", ""))].append(node)
        for row, nodes in rows.items():
            ordered = sorted(nodes, key=lambda item: (float(item.get("column", 0)), str(item.get("node_id"))))
            for left, right in zip(ordered, ordered[1:]):
                gap = float(right.get("column", 0)) - float(left.get("column", 0))
                if gap < minimum_gap:
                    tight_pairs.append((left, right, row, gap))
        if tight_pairs:
            left, right, row, gap = tight_pairs[0]
            self._add(
                rule="readability",
                category="readability",
                message="Some same-row nodes are too close and may visually overlap.",
                node_ids=[left["node_id"], right["node_id"]],
                expected=f"Adjacent same-row node column gap >= {minimum_gap}",
                actual=f"row={row}, first gap={gap:g}, total tight pairs={len(tight_pairs)}",
                suggested_fix_for_generator="Expand stage-internal model layers into separate columns instead of using tiny fractional offsets.",
                diagnostic=True,
            )

    def _require_edge(
        self,
        rule: str,
        category: str,
        src: str,
        dst: str,
        expected_kind: str,
        message: str,
        fix: str,
    ) -> None:
        if (src, dst, expected_kind) not in self.edge_kind_set:
            self._add(
                rule=rule,
                category=category,
                message=message,
                node_ids=[src, dst],
                expected=f"{src} -> {dst} [{expected_kind}]",
                actual="Required edge missing.",
                suggested_fix_for_generator=fix,
            )

    def _reachable(self, src: str, dst: str) -> bool:
        return dst in self._reachable_set(src)

    def _reachable_set(self, src: str) -> set[str]:
        seen = {src}
        queue = deque([src])
        while queue:
            current = queue.popleft()
            for child in self.outgoing.get(current, []):
                if child in self.node_by_id and child not in seen:
                    seen.add(child)
                    queue.append(child)
        return seen

    def _find_layer_node(self, task_kind: str, dp_rank: int, layer_id: int, microbatch_id: int) -> dict[str, Any] | None:
        for node in self.nodes:
            if (
                node.get("task_kind") == task_kind
                and node.get("dp_rank") == dp_rank
                and node.get("global_layer_id") == layer_id
                and node.get("microbatch_id") == microbatch_id
            ):
                return node
        return None

    def _find_pp_node(self, task_kind: str, dp_rank: int, stage_id: int, microbatch_id: int) -> dict[str, Any] | None:
        for node in self.nodes:
            if (
                node.get("task_kind") == task_kind
                and node.get("dp_rank") == dp_rank
                and node.get("pp_stage_id") == stage_id
                and node.get("microbatch_id") == microbatch_id
            ):
                return node
        return None

    def _layers_by_stage(self) -> dict[int, list[int]]:
        layers: dict[int, set[int]] = defaultdict(set)
        for node in self._layer_nodes("forward") + self._layer_nodes("backward"):
            if node.get("pp_stage_id") is not None:
                layers[int(node["pp_stage_id"])].add(int(node["global_layer_id"]))
        return {stage_id: sorted(values) for stage_id, values in layers.items()}

    def _stage_by_layer(self) -> dict[int, int]:
        result: dict[int, int] = {}
        for stage_id, layers in self._layers_by_stage().items():
            for layer_id in layers:
                result[layer_id] = stage_id
        return result

    def _zero_nodes(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "ready": [node for node in self.nodes if self._is_ready(node)],
            "gar": [node for node in self.nodes if self._is_gar(node)],
            "opt": [node for node in self.nodes if self._is_opt(node)],
            "pag": [node for node in self.nodes if self._is_pag(node)],
        }

    @staticmethod
    def _is_ready(node: dict[str, Any]) -> bool:
        label = str(node.get("label", "")).upper()
        node_id = str(node.get("node_id", "")).upper()
        return node.get("task_kind") in {"ready", "dp_ready"} or label == "R" or label.startswith("R(") or node_id.startswith("READY")

    @staticmethod
    def _is_gar(node: dict[str, Any]) -> bool:
        text = f"{node.get('task_kind', '')} {node.get('label', '')} {node.get('node_id', '')}".upper()
        return "G-AR" in text or "GAR" in text or "GRAD_ALLREDUCE" in text

    @staticmethod
    def _is_opt(node: dict[str, Any]) -> bool:
        text = f"{node.get('task_kind', '')} {node.get('label', '')} {node.get('node_id', '')}".upper()
        return "OPT" in text or "OPTIMIZER" in text

    @staticmethod
    def _is_pag(node: dict[str, Any]) -> bool:
        text = f"{node.get('task_kind', '')} {node.get('label', '')} {node.get('node_id', '')}".upper()
        return "P-AG" in text or "PAG" in text or "PARAM_ALLGATHER" in text or "ALL_GATHER" in text

    def _report(self) -> dict[str, Any]:
        all_findings = [finding.to_dict() for finding in self.findings]
        diagnostics = [finding.to_dict() for finding in self.diagnostics]
        errors = sum(1 for item in all_findings if item["severity"] == "error")
        warnings = sum(1 for item in all_findings if item["severity"] == "warning")
        readability = len(diagnostics) + sum(1 for item in all_findings if item["severity"] == "readability")
        return {
            "report_id": f"rulecheck_{self.dag.get('dag_id', self.source_dag.stem)}",
            "source_dag": str(self.source_dag.as_posix()),
            "status": "fail" if errors else "pass",
            "summary": {
                "total_findings": len(all_findings) + len(diagnostics),
                "errors": errors,
                "warnings": warnings,
                "readability": readability,
            },
            "selected_rules": {
                "dag_selected_rules": self.dag.get("selected_rules", {}),
                "rule_set_id": self.rules.get("rule_set_id", "default"),
                "enabled_checks": self.rules.get("enabled_checks", {}),
            },
            "findings": all_findings,
            "diagnostics": diagnostics,
            "outputs": {},
        }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# RuleCheck 报告: {report['status'].upper()}",
        "",
        f"- 源 DAG: `{report['source_dag']}`",
        f"- 错误: {summary['errors']}",
        f"- 警告: {summary['warnings']}",
        f"- 可读性提示: {summary['readability']}",
        "",
    ]
    if not report["findings"] and not report["diagnostics"]:
        lines.append("未发现问题。")
        lines.append("")
        return "\n".join(lines)

    for title, items in (("发现的问题", report["findings"]), ("诊断信息", report["diagnostics"])):
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for item in items:
            nodes = ", ".join(item["node_ids"]) if item["node_ids"] else "-"
            lines.extend(
                [
                    f"### {item['id']} [{item['severity']}] {item['category']}",
                    "",
                    item["message"],
                    "",
                    f"- 节点: `{nodes}`",
                    f"- 期望: {item['expected'] or '-'}",
                    f"- 实际: {item['actual'] or '-'}",
                    f"- 建议生成器修复: {item['suggested_fix_for_generator'] or '-'}",
                    "",
                ]
            )
    return "\n".join(lines)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def default_report_paths(dag_path: Path) -> tuple[Path, Path]:
    return dag_path.parent / "rule_check_report.json", dag_path.parent / "rule_check_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check DagGenerator DAG JSON semantics.")
    parser.add_argument("--dag", type=Path, default=DEFAULT_DAG, help="Path to generated dag.json.")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES, help="Path to RuleCheck rules JSON.")
    parser.add_argument("--report-json", type=Path, help="Output JSON report path.")
    parser.add_argument("--report-md", type=Path, help="Output Markdown report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dag = load_json(args.dag)
    rules = load_json(args.rules)
    checker = RuleChecker(dag, rules, args.dag)
    report = checker.run()
    default_json, default_md = default_report_paths(args.dag)
    report_json = args.report_json or default_json
    report_md = args.report_md or default_md
    report["outputs"] = {
        "json": str(report_json.as_posix()),
        "markdown": str(report_md.as_posix()),
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {report_json}")
    print(f"Wrote {report_md}")
    print(f"RuleCheck status: {report['status']} ({report['summary']['errors']} error(s), {report['summary']['warnings']} warning(s))")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
