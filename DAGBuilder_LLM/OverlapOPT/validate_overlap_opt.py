from __future__ import annotations

from rules import apply_overlap_rules, longest_path_latency


def make_pp_forward_sample() -> dict:
    return {
        "dag_id": "pp_forward_overlap_sample",
        "nodes": [
            {"node_id": "start", "task_kind": "control", "duration_s": 0.0},
            {"node_id": "F_s0_mb0", "task_kind": "forward", "dp_rank": 0, "pp_stage_id": 0, "microbatch_id": 0, "duration_s": 3.0, "column": 1},
            {"node_id": "F_s0_mb1", "task_kind": "forward", "dp_rank": 0, "pp_stage_id": 0, "microbatch_id": 1, "duration_s": 3.0, "column": 2},
            {"node_id": "PPF_s0_to_s1_mb1", "task_kind": "pp_forward_send", "dp_rank": 0, "pp_stage_id": 0, "microbatch_id": 1, "duration_s": 1.0, "column": 3},
            {"node_id": "end", "task_kind": "control", "duration_s": 0.0},
        ],
        "edges": [
            {"src": "start", "dst": "F_s0_mb0"},
            {"src": "F_s0_mb0", "dst": "F_s0_mb1"},
            {"src": "F_s0_mb1", "dst": "PPF_s0_to_s1_mb1"},
            {"src": "PPF_s0_to_s1_mb1", "dst": "end"},
        ],
        "layout": {"start_node": "start", "end_node": "end"},
    }


def make_pp_backward_sample() -> dict:
    return {
        "dag_id": "pp_backward_no_overlap_sample",
        "nodes": [
            {"node_id": "start", "task_kind": "control", "duration_s": 0.0},
            {"node_id": "B_s0_mb0", "task_kind": "backward", "dp_rank": 0, "pp_stage_id": 0, "microbatch_id": 0, "duration_s": 3.0},
            {"node_id": "PPB_s1_to_s0_mb1", "task_kind": "pp_backward_send", "dp_rank": 0, "pp_stage_id": 1, "microbatch_id": 1, "duration_s": 1.0},
            {"node_id": "end", "task_kind": "control", "duration_s": 0.0},
        ],
        "edges": [
            {"src": "start", "dst": "B_s0_mb0"},
            {"src": "B_s0_mb0", "dst": "PPB_s1_to_s0_mb1"},
            {"src": "PPB_s1_to_s0_mb1", "dst": "end"},
        ],
        "layout": {"start_node": "start", "end_node": "end"},
    }


def make_dp_allreduce_sample() -> dict:
    return {
        "dag_id": "dp_allreduce_no_overlap_sample",
        "nodes": [
            {"node_id": "start", "task_kind": "control", "duration_s": 0.0},
            {"node_id": "B_s0_mb0", "task_kind": "backward", "pp_stage_id": 0, "duration_s": 4.0},
            {"node_id": "DP_AR_s0", "task_kind": "dp_allreduce", "pp_stage_id": 0, "duration_s": 2.0},
            {"node_id": "end", "task_kind": "control", "duration_s": 0.0},
        ],
        "edges": [
            {"src": "start", "dst": "B_s0_mb0"},
            {"src": "B_s0_mb0", "dst": "DP_AR_s0"},
            {"src": "DP_AR_s0", "dst": "end"},
        ],
        "layout": {"start_node": "start", "end_node": "end"},
    }


def make_dp_rs_ag_sample() -> dict:
    return {
        "dag_id": "dp_rs_ag_overlap_sample",
        "nodes": [
            {"node_id": "start", "task_kind": "control", "duration_s": 0.0},
            {"node_id": "B_s0_mb0", "task_kind": "backward", "pp_stage_id": 0, "duration_s": 4.0},
            {"node_id": "DP_RS_s0", "task_kind": "dp_reducescatter", "pp_stage_id": 0, "duration_s": 2.0},
            {"node_id": "DP_AG_s0", "task_kind": "dp_allgather", "pp_stage_id": 0, "duration_s": 2.0},
            {"node_id": "end", "task_kind": "control", "duration_s": 0.0},
        ],
        "edges": [
            {"src": "start", "dst": "B_s0_mb0"},
            {"src": "B_s0_mb0", "dst": "DP_RS_s0"},
            {"src": "DP_RS_s0", "dst": "DP_AG_s0"},
            {"src": "DP_AG_s0", "dst": "end"},
        ],
        "layout": {"start_node": "start", "end_node": "end"},
    }


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def node_by_id(dag: dict, node_id: str) -> dict:
    return {node["node_id"]: node for node in dag["nodes"]}[node_id]


def main() -> int:
    pp_sample = make_pp_forward_sample()
    overlapped, report = apply_overlap_rules(pp_sample)
    pp_node = node_by_id(overlapped, "PPF_s0_to_s1_mb1")
    assert_true(pp_node["duration_s"] == 0.0, "PP forward send should be fully hidden by previous forward compute.")
    assert_true(
        pp_node["overlap_opt_detail"]["aligned_start_with"] == ["F_s0_mb0"],
        "PP forward send should align with previous microbatch forward compute.",
    )
    assert_true(report["overlap_saved_s"] > 0.0, "PP forward sample should save latency.")

    backward_sample = make_pp_backward_sample()
    overlapped, report = apply_overlap_rules(backward_sample)
    assert_true(
        node_by_id(overlapped, "PPB_s1_to_s0_mb1")["duration_s"] == 1.0,
        "PP backward send should not be changed by forward-only PP rule.",
    )
    assert_true(report["overlap_saved_s"] == 0.0, "PP backward sample should save zero latency.")

    ar_sample = make_dp_allreduce_sample()
    overlapped, report = apply_overlap_rules(ar_sample)
    assert_true(node_by_id(overlapped, "DP_AR_s0")["duration_s"] == 2.0, "DP allreduce should not overlap in static rs+ag rules.")
    assert_true(report["overlap_saved_s"] == 0.0, "DP allreduce sample should save zero latency.")

    rs_ag_sample = make_dp_rs_ag_sample()
    overlapped, report = apply_overlap_rules(rs_ag_sample)
    assert_true(node_by_id(overlapped, "DP_RS_s0")["duration_s"] == 1.0, "ReduceScatter should hide 50%.")
    assert_true(node_by_id(overlapped, "DP_AG_s0")["duration_s"] == 1.5, "AllGather should hide 25%.")
    assert_true(longest_path_latency(overlapped) < longest_path_latency(rs_ag_sample), "RS+AG sample should reduce latency.")
    assert_true(report["safety"]["derived_dag_acyclic"], "Derived DAG should be acyclic.")

    print("OverlapOPT validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
