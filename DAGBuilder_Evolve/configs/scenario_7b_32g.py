from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
LLM_REPO = PROJECT.parent / "DAGBuilder_LLM"

CONFIG = {
    "name": "7b_32g",
    "repository_root": str(LLM_REPO),
    "output_root": str(PROJECT / "outputs"),
    "model": {
        "name": "LLaMA-7B",
        "num_layers": 32,
        "hidden_size": 4096,
        "ffn_hidden_size": 11008,
        "parameter_count": 7_000_000_000,
        "dtype_bytes": 2,
        "gradient_dtype_bytes": 4,
    },
    "workload": {
        "global_batch_size": 128,
        "sequence_length": 2048,
        "compute_efficiency": 0.45,
        "backward_flop_multiplier": 2.0,
        "activation_multiplier": 8.0,
        "optimizer_state_multiplier": 2.0,
    },
    "memory": {"device_capacity_gb": 16.0},
    "topology": {
        "total_devices": 32,
        "default_compute_tflops": 312.0,
        "affinity_groups": [
            {"affinity_group_id": 0, "servers": [{"server_id": 0, "ranks": list(range(0, 16))}]},
            {"affinity_group_id": 1, "servers": [{"server_id": 1, "ranks": list(range(16, 32))}]},
        ],
        "device_overrides": {},
        "link_overrides": [],
    },
    "network": {
        "bandwidth_unit_bits": float(1024**3),
        "hccs_intra_server": {"bandwidth_gbps": 1574.72, "efficiency": 0.8, "latency_s": 60e-6},
        "hccs_inter_server": {"bandwidth_gbps": 1400.0, "efficiency": 0.9, "latency_s": 60e-6},
        "roce": {"bandwidth_gbps": 200.0, "efficiency": 0.8, "latency_s": 60e-6},
        "hbm": {"bandwidth_gbps": 4800.0, "efficiency": 1.0, "latency_s": 0.0},
    },
    "search": {
        "active_gpu_counts": [4, 8, 16, 32],
        "pp_values": [1, 2, 4, 8, 16, 32],
        "tp_values": [1, 2, 4, 8, 16],
        "dp_values": [1, 2, 4, 8, 16, 32],
        "micro_batch_num_values": [1, 2, 4, 8, 16, 32, 64],
        "schedules": ["gpipe", "1f1b"],
        "dp_communications": ["allreduce", "rs_ag"],
        "nominations_per_program": 8,
    },
    "evolution": {
        "rounds": 10,
        "random_seed": 20260724,
        "island_capacity": 20,
        "global_archive_size": 8,
        "migration_rounds": [5, 10],
        "program_timeout_s": 5.0,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
        "api_key_env": "DEEPSEEK_API_KEY",
        "timeout_s": 120,
        "temperature": 0.7,
    },
}
