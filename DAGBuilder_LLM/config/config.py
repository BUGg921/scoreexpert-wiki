# ============================================================================
# Fixed model parameters. Search loops must not modify this section.
# ============================================================================

# LLaMA 7B transformer layers.
model_num_layers: int = 32

# LLaMA 7B hidden size.
model_hidden_size: int = 4096

# LLaMA 7B FFN hidden size.
model_ffn_hidden_size: int = 11008

# TP communication precision factor.
tp_precision_factor: int = 16

# DP communication precision factor.
dp_precision_factor: int = 32

# PP communication precision factor.
pp_precision_factor: int = 16

# EP communication precision factor.
ep_precision_factor: int = 16

# SP communication precision factor.
sp_precision_factor: int = 16


# ============================================================================
# Searchable parallelism parameters. Later optimization loops may tune this.
# ============================================================================

# Sequence length.
seq_len: int = 2048

# Global batch size across the whole DP domain.
global_batch_size: int = 128

# Data parallel size.
dp_size: int = 4

# Tensor parallel size.
tp_size: int = 4

# Pipeline parallel size.
pp_size: int = 2

# Virtual pipeline parallel size. vpp_size=1 means VPP is disabled.
vpp_size: int = 1

# Context parallel compute expert size, inner SP.
sp_ce_size: int = 1

# Context parallel memory expert size, outer SP.
sp_me_size: int = 1

# Number of microbatches.
microbatch_num: int = 4

# Local microbatch size derived from global_batch_size / dp_size / microbatch_num.
microbatch_size: float = global_batch_size / dp_size / microbatch_num

# PP scheduling strategy.
pp_strategy: str = "1f1b"

# DP communication strategy.
dp_strategy: str = "reduce_scatter_allgather_after_backward"

# DP allreduce granularity.
dp_allreduce_granularity: str = "stage"

dp_strategy_short: str = "rs_ag" if dp_strategy == "reduce_scatter_allgather_after_backward" else "naive_ar"


# ============================================================================
# Fixed hardware/network parameters. Search loops must not modify this section.
# ============================================================================

# Total GPU/NPU count.
num_gpus: int = 32

# In-node single-link static delay in seconds, provided by hardware.
npu_innode_static_delay_s: float = 60e-6

# RoCE link static delay in seconds.
roce_static_delay_s: float = 60e-6

# In-node communication bandwidth in Gbps. 7 * 4 * 56.24 = 1574.72 Gbps.
npu_innode_bandwidth_gbps: float = 7 * 4 * 56.24

# HCCS bandwidth in Gbps. 7 * 200 = 1400 Gbps.
hccs_bandwidth_gbps: float = 7 * 200

# Inter-node RoCE bandwidth in Gbps.
roce_bandwidth_gbps: float = 200

# In-node/RoCE bandwidth utilization ratio.
bandwidth_utilization_ratio: float = 0.8

# HCCS bandwidth utilization ratio.
hccs_bandwidth_utilization_ratio: float = 0.9

# Number of dies per node.
die_num_per_node: int = 16

# All-to-All concurrency.
alltoall_concurrency: int = 16

# HBM bandwidth in Gbps. 600 GB/s is represented as 600 * 8 Gbps.
hbm_bandwidth_gbps: float = 600 * 8

# NPU device memory capacity in GB.
npu_memory_gb: float = 16


# ============================================================================
# Fixed ValueSim parameters. Search loops may override only explicit knobs.
# ============================================================================

# Device peak throughput for one TP domain member, in FLOP/s.
device_peak_flops: float = 312e12

# Sustained compute efficiency used by the analytic model.
compute_efficiency: float = 0.45

# Default DP bucket cap. Stage-level DAG nodes may exceed this until DagGenerator
# emits bucket-level nodes.
dp_bucket_size_bytes: int = 256 * 1024 * 1024

# PP links default to RoCE because PP traffic is treated as outside affinity groups.
pp_link_type: str = "roce"

# DP collective algorithm selector for ValueSim.
dp_collective_algorithm: str = "abstract_layered"

# DP collective model precision. "hierarchical" keeps affinity-group layers in
# timing details without expanding communication steps into DAG nodes.
dp_collective_model: str = "hierarchical"

# Existing stage-level DP nodes stay monolithic unless DagGenerator emits split nodes.
allreduce_mode: str = "monolithic"

# Hardware grouping inputs used by layered collective models.
affinity_group_size: int = 16
ranks_per_node: int = die_num_per_node
num_affinity_groups: int = max(1, num_gpus // max(1, affinity_group_size))
rank_to_affinity_group: list[int] = [rank // max(1, affinity_group_size) for rank in range(num_gpus)]

# Ascend TP domains are modeled as supernodes and constrained to affinity-local
# sizes for this ValueSim stage.
tp_size_limit: int = 16
validate_pp_affinity_symmetry: bool = True

# Backward compute is approximated as a multiple of forward compute.
backward_flop_multiplier: float = 2.0

# TP supernode timing model. Compute is divided by TP size, then intra-TP
# collective communication is added without changing the DAG topology.
tp_compute_sharding_enabled: bool = True
tp_comm_enabled: bool = True
tp_comm_model: str = "ring"
tp_forward_collectives_per_layer: int = 2
tp_backward_collectives_per_layer: int = 2
tp_comm_payload: str = "activation"
tp_intra_affinity_link_type: str = "hccs"
tp_cross_affinity_link_type: str = "roce"
tp_comm_overlap_ratio: float = 0.0


MODEL_PARA = {
    "num_layers": model_num_layers,
    "hidden_size": model_hidden_size,
    "ffn_hidden_size": model_ffn_hidden_size,
    "precision_factors": {
        "tp": tp_precision_factor,
        "dp": dp_precision_factor,
        "pp": pp_precision_factor,
        "ep": ep_precision_factor,
        "sp": sp_precision_factor,
    },
}


PARALLELISM_CONFIG = {
    "global_batch_size": global_batch_size,
    "seq_len": seq_len,
    "dp_size": dp_size,
    "tp_size": tp_size,
    "pp_size": pp_size,
    "vpp_size": vpp_size,
    "sp_ce_size": sp_ce_size,
    "sp_me_size": sp_me_size,
    "microbatch_num": microbatch_num,
    "microbatch_size": microbatch_size,
    "pp_strategy": pp_strategy,
    "dp_strategy": dp_strategy,
    "dp_allreduce_granularity": dp_allreduce_granularity,
}


NETWORK_CONFIG = {
    "npu_innode_static_delay_s": npu_innode_static_delay_s,
    "roce_static_delay_s": roce_static_delay_s,
    "npu_innode_bandwidth_gbps": npu_innode_bandwidth_gbps,
    "hccs_bandwidth_gbps": hccs_bandwidth_gbps,
    "roce_bandwidth_gbps": roce_bandwidth_gbps,
    "bandwidth_utilization_ratio": bandwidth_utilization_ratio,
    "hccs_bandwidth_utilization_ratio": hccs_bandwidth_utilization_ratio,
    "die_num_per_node": die_num_per_node,
    "alltoall_concurrency": alltoall_concurrency,
    "hbm_bandwidth_gbps": hbm_bandwidth_gbps,
    "npu_memory_gb": npu_memory_gb,
}


VALUE_SIM_CONFIG = {
    "device_peak_flops": device_peak_flops,
    "compute_efficiency": compute_efficiency,
    "dp_bucket_size_bytes": dp_bucket_size_bytes,
    "pp_link_type": pp_link_type,
    "dp_collective_algorithm": dp_collective_algorithm,
    "dp_collective_model": dp_collective_model,
    "allreduce_mode": allreduce_mode,
    "affinity_group_size": affinity_group_size,
    "ranks_per_node": ranks_per_node,
    "num_affinity_groups": num_affinity_groups,
    "rank_to_affinity_group": rank_to_affinity_group,
    "tp_size_limit": tp_size_limit,
    "validate_pp_affinity_symmetry": validate_pp_affinity_symmetry,
    "backward_flop_multiplier": backward_flop_multiplier,
    "tp_compute_sharding_enabled": tp_compute_sharding_enabled,
    "tp_comm_enabled": tp_comm_enabled,
    "tp_comm_model": tp_comm_model,
    "tp_forward_collectives_per_layer": tp_forward_collectives_per_layer,
    "tp_backward_collectives_per_layer": tp_backward_collectives_per_layer,
    "tp_comm_payload": tp_comm_payload,
    "tp_intra_affinity_link_type": tp_intra_affinity_link_type,
    "tp_cross_affinity_link_type": tp_cross_affinity_link_type,
    "tp_comm_overlap_ratio": tp_comm_overlap_ratio,
}


SEARCH_CONFIG = {
    "top_k": 3,
    "evaluation_budget": 8,
    "candidate_pool_per_island": 64,
    "initial_nomination_top_n": 64,
    "program_nomination_top_n": 32,
    "protected_candidate_ttl": 3,
    "score_db_search": {
        "max_rounds": 100,
        "patience_rounds": 10,
        "min_relative_improvement": 0.001,
        "target_gap_to_database_best": 0.01,
        "stop_on_target_gap": False,
        "stop_on_patience": False,
        "island_workers": 4,
        "ranking_top_k": 16,
        "experience_retrieval_top_k": 3,
        "migration_interval": 10,
    },
    "allow_idle_gpus": True,
    "allowed_active_gpu_counts": [4, 8, 16, 32],
    "allowed_tp_sizes": [1, 2, 4, 8, 16],
    "micro_batch_candidates": [1, 2, 4, 8, 16, 32, 64],
    "placement_matrix_value": "binary",
    "enable_pp_schedule_search": False,
    "allowed_pp_strategies": [pp_strategy],
    # StrategyScorer is a formula expert. Stage-one scores are decoupled from
    # Evaluation latency; Evaluation only feeds back longest-path latency.
    "scoring_mode": "formula_expert",
    "base_score": 1000.0,
    "invalid_strategy_score": -1.0e18,
    "bubble_weight": 100.0,
    "memory_risk_weight": 1000.0,
    "topology_penalty_weight": 10.0,
    "comm_weight": 1.0,
    "memory_safe_threshold_ratio": 0.9,
    "memory_safe_soft_weight": 1.0,
    "memory_safe_risk_weight": 100.0,
    "memory_safe_risk_exponent": 2,
    "topology_tp_cross_affinity_weight": 100.0,
    "topology_dp_cross_affinity_weight": 10.0,
    "topology_pp_cross_affinity_weight": 1.0,
    # Islands use separate scoring formulas and keep separate mutation bias.
    "islands": ["memory_safe", "topology_affinity"],
    "island_mutation_bias": {
        "memory_safe": {"tp": 2.0, "pp": 2.0, "dp": 0.5},
        "topology_affinity": {"tp": 1.0, "pp": 1.0, "dp": 1.0},
    },
    # Migration schedule for island evolution:
    # first 30% no migration, middle 50% low-frequency migration, final 20%
    # exploitation with more frequent migration.
    "evolution": {
        "total_iterations": 30,
        "enabled": True,
        "max_rounds": 5,
        "programs_per_prompt": 2,
        "migration_interval": 3,
        "replace_fraction": 0.5,
        "metric": "baseline_latency_s",
        "phase_ratios": {"explore": 0.3, "low_migration": 0.5, "exploit": 0.2},
        "low_migration_interval": 5,
        "exploit_migration_interval": 1,
        "migrants_per_event": 1,
        "structure_difference_keys": ["pp_size", "tp_size", "dp_size", "micro_batch_num", "signature"],
    },
    "sandbox": {
        "timeout_seconds": 2,
        "max_program_chars": 6000,
    },
    "cluster_scenarios": [
        {
            "name": "target_32g_2affinity_2nodes",
            "num_gpus": 32,
            "affinity_groups": 2,
            "nodes_per_affinity_group": 1,
            "gpus_per_node": 16,
            "weight": 1.0,
        }
    ],
    "funsearch": {
        "enabled": True,
        "llm_client": "local_command",
        "max_steps": 5,
        "samples_per_prompt": 1,
        "k_programs_per_prompt": 2,
        "full_eval_programs_per_step": 1,
        "full_eval_strategies_per_program": 1,
        "island_population_size": 4,
        "agent_timeout_seconds": 120,
        "local_agent_command": "",
        "fallback_to_mock": True,
        "program_bank_top_k_per_island": 12,
        "prompt_examples_per_island": 2,
        "sampler_model": "gpt-5.5",
        "reset_interval": 100,
        "reset_patience": 3,
        "keep_local_top_m": 3,
        "copy_remote_top_k": 2,
    },
    "deepseek": {
        "enabled": True,
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
        "api_key_env": "DEEPSEEK_API_KEY",
        "timeout_seconds": 120,
        "temperature": 0.7,
        "pricing_per_1m_tokens": {"input": 0.435, "output": 0.87},
    },
    "overlapopt": {
        "enabled": True,
        "top_k": 3,
        "max_iterations": 5,
        "keep_metric": "overlap_saved_ratio",
        "pp_strategies": ["gpipe", "1f1b"],
        "dp_strategies": ["naive_allreduce_after_backward", "reduce_scatter_allgather_after_backward"],
    },
    "full_loop": {
        "outer_rounds": 5,
        "score_rounds": 5,
        "overlap_iterations": 5,
    },
}


IMMUTABLE_CONFIG_SECTIONS = (
    "model_para",
    "network_config",
)


CONFIG = {
    "dag_id": f"{pp_strategy}_pp{pp_size}_dp{dp_size}_tp{tp_size}_mb{microbatch_num}_{dp_strategy_short}",
    "immutable_config_sections": IMMUTABLE_CONFIG_SECTIONS,
    "model_para": MODEL_PARA,
    "parallelism_config": PARALLELISM_CONFIG,
    "network_config": NETWORK_CONFIG,
    "value_sim_config": VALUE_SIM_CONFIG,
    "search_config": SEARCH_CONFIG,
    "domains": {
        "num_gpus": num_gpus,
        "dp_size": dp_size,
        "tp_size": tp_size,
        "pp_size": pp_size,
        "num_layers": model_num_layers,
        "num_microbatches": microbatch_num,
    },
    "strategies": {
        "pp_strategy": pp_strategy,
        "dp_strategy": dp_strategy,
        "dp_allreduce_granularity": dp_allreduce_granularity,
    },
    "color_theme": {
        "forward_node_color": "#D7E7F5",
        "backward_node_color": "#FCE4CC",
        "pp_comm_node_color": "#ECE4FF",
        "dp_comm_node_color": "#DDF3DD",
        "control_node_color": "#F2F2F2",
        "data_dependency_edge_color": "#2F6FB3",
        "resource_dependency_edge_color": "#2E8B57",
        "control_edge_color": "#333333",
    },
    "outputs": {
        "base_dir": "outputs",
        "name_template": "pp{pp_size}_{pp_strategy}_dp{dp_size}_{dp_strategy_short}",
        "html_filename": "dag.html",
        "json_filename": "dag.json",
    },
}
