"""Reference configuration for the current 30B coarse DAG."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ValueSim.simulator_v2.topology.topology_128g import get_topology_128g


ROOT = Path(__file__).resolve().parents[3]


CONFIG = {
    "model": {
        "name": "30B",
        "num_layers": 44,
        "hidden_size": 2560,
        "ffn_hidden_size": 6912,
        "expert_ffn_hidden_size": 1024,
        "num_experts": 192,
        "top_k": 10,
        "microbatch_size": 2,
        "sequence_length": 4096,
        "dtype_bytes": {"bf16": 2, "fp32": 4, "int32": 4, "int64": 8},
    },
    "topology": get_topology_128g(),
    "network": {
        # Preserve the existing ValueSim v2 bandwidth-unit convention.
        "bandwidth_unit_bits": float(1024**3),
        "hccs_intra_server": {"bandwidth_gbps": 1400.0, "efficiency": 0.90, "latency_s": 60e-6},
        "hccs_inter_server": {"bandwidth_gbps": 1400.0, "efficiency": 0.90, "latency_s": 60e-6},
        "hccs_double_ring": {"bandwidth_gbps": 2 * 200.0, "efficiency": 0.90, "latency_s": 60e-6},
        "roce": {"bandwidth_gbps": 200.0, "efficiency": 0.80, "latency_s": 60e-6},
        "hbm": {"bandwidth_gbps": 600.0 * 8.0, "efficiency": 1.0, "latency_s": 0.0},
    },
    "parallel": {
        "tp_size": 4,
        "pp_size": 1,
        "dp_size": 32,
        "ep_size": 8,
        "cp_size": 1,
    },
    "simulation_flags": {
        "dp": 1,
        "pp": 1,
        "ep": 1,
        "tp": 0,
        "compute": 0,
        "optimizer": 0,
        "other": 0,
    },
    "simulation_overrides": {"node_id": {}, "op_name": {}},
    "algorithms": {
        "operations": {
            "dp_scalar_allreduce_loss_token_count": {
                "category": "dp",
                "collective": "all_reduce",
                "domain": "dp_cp",
                "algorithm": "ring",
                "link_kind": "hccs_inter_server",
                "payload_scope": "replicated",
                "payload_bytes": 4,
                "bucket_count": 1,
            },
            "zero3_grad_rs_dp_cp_attention": {
                "category": "dp",
                "collective": "reduce_scatter",
                "domain": "dp_cp",
                "algorithm": "hierarchical_ring_nhr",
                "payload_scope": "full_tensor",
                "payload_elements": 936_614_400,
                "dtype_bytes": 4,
                "bucket_count": 19,
                "intra_server_link": "hccs_double_ring",
                "inter_server_link": "hccs_inter_server",
                "cross_affinity_link": "roce",
                "include_executor_memory": True,
                "reduction_memory_accesses_per_byte": 4,
            },
            "zero3_grad_rs_dp_ep_moe": {
                "category": "dp",
                "collective": "reduce_scatter",
                "domain": "dp_ep",
                "algorithm": "nhr",
                "link_kind": "roce",
                "payload_scope": "full_tensor",
                "payload_elements": 1_014_497_280,
                "dtype_bytes": 4,
                "bucket_count": 22,
            },
            "dp_cp_expert_load_allreduce": {
                "category": "dp",
                "collective": "all_reduce",
                "domain": "dp_cp",
                "algorithm": "recursive_doubling",
                "link_kind": "hccs_inter_server",
                "payload_scope": "replicated",
                "payload_elements": 43 * 192,
                "dtype_bytes": 4,
                "bucket_count": 1,
            },
            "zero3_muon_grad_ag_dp_cp": {
                "category": "dp",
                "collective": "all_gather",
                "domain": "dp_cp",
                "algorithm": "hierarchical_nhr_ring",
                "payload_scope": "full_tensor",
                "payload_elements": 936_614_400,
                "dtype_bytes": 2,
                "bucket_count": 22,
                "include_local_staging": True,
                "local_staging_link": "hccs_inter_server",
            },
            "zero3_next_step_param_prefetch_dp_cp": {
                "category": "dp",
                "collective": "all_gather",
                "domain": "dp_cp",
                "algorithm": "hierarchical_nhr_ring",
                "payload_scope": "full_tensor",
                "payload_elements": 936_614_400,
                "dtype_bytes": 2,
                "bucket_count": 45,
                "include_local_staging": True,
                "local_staging_link": "hccs_inter_server",
            },
            "zero3_muon_grad_ag_dp_ep": {
                "category": "dp",
                "collective": "all_gather",
                "domain": "dp_ep",
                "algorithm": "nhr",
                "link_kind": "roce",
                "payload_scope": "full_tensor",
                "payload_elements": 1_014_497_280,
                "dtype_bytes": 2,
                "bucket_count": 22,
            },
            "zero3_next_step_param_prefetch_dp_ep": {
                "category": "dp",
                "collective": "all_gather",
                "domain": "dp_ep",
                "algorithm": "nhr",
                "link_kind": "roce",
                "payload_scope": "full_tensor",
                "payload_elements": 1_014_497_280,
                "dtype_bytes": 2,
                "bucket_count": 22,
            },
        },
        "task_kinds": {
            "pp_forward_send": {"category": "pp", "algorithm": "p2p", "payload_scope": "full_tensor"},
            "pp_backward_send": {"category": "pp", "algorithm": "p2p", "payload_scope": "full_tensor"},
            "pp_forward_recv": {"category": "pp", "algorithm": "p2p", "payload_scope": "full_tensor"},
            "pp_backward_recv": {"category": "pp", "algorithm": "p2p", "payload_scope": "full_tensor"},
            "ep_allreduce": {
                "category": "ep",
                "collective": "all_reduce",
                "domain": "ep",
                "algorithm": "nhr",
                "payload_scope": "replicated",
            },
            "ep_allgather": {
                "category": "ep",
                "collective": "all_gather",
                "domain": "ep",
                "algorithm": "nhr",
                "payload_scope": "full_tensor",
            },
            "ep_alltoall_dispatch": {
                "category": "ep",
                "collective": "all_to_all",
                "domain": "ep_tp",
                "algorithm": "hierarchical_pairwise",
                "payload_scope": "per_rank_send",
            },
            "ep_alltoall_combine": {
                "category": "ep",
                "collective": "all_to_all",
                "domain": "ep_tp",
                "algorithm": "hierarchical_pairwise",
                "payload_scope": "per_rank_send",
            },
            "ep_alltoall_metadata": {
                "category": "ep",
                "collective": "all_to_all_v",
                "domain": "ep_tp",
                "algorithm": "hierarchical_pairwise",
                "payload_scope": "per_rank_send",
            },
        },
        "compute": {
            "efficiency": 0.45,
            "flops_scope": "global",
            "backward_flop_multiplier": 2.0,
            "operation_flops": {},
        },
    },
    "profiling": {
        "path": str(ROOT / "ValueSim" / "profileSim" / "30B数值填充DAG.xlsx"),
        "sheet": "v2",
        "header_rows": 1,
        "columns": {"key": "A", "duration": "B", "payload": "C", "detail": "D"},
        "duration_unit": "us",
        "aliases": {},
    },
}


def get_config() -> dict:
    return deepcopy(CONFIG)
