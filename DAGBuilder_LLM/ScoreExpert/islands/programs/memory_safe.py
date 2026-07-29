"""
Island instruction: Prioritize memory headroom. Strongly penalize OOM risk and nonlinear risk above 85%-90% memory pressure while keeping pipeline bubble reasonable.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0000_memory_safe.md
Active evolution file. Seed record lives in ScoreExpert/islands/seeds/memory_safe.py.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
        'island_score': 1048.84,
        'evaluation': {'total_latency_s': 1.789702814, 'pp_size': 2, 'micro_batch_num': 64, 'tp_size': 16, 'dp_size': 1},
        'origin': 'seed',
        'observations': [{'round': 1, 'mode': 'full_database_ranking', 'status': 'pass', 'ranking_quality': 544.574683812, 'spearman_score_vs_negative_latency': 0.60443622, 'top_k_avg_latency_s': 7.03447557, 'top_k_best_latency_s': 2.33016721, 'database_best_score_rank': 52, 'total_latency_s': 7.03447557}],
        'source': """def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    \"\"\"Memory-safe seed scorer.\"\"\"
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    batch = float(model_cfg.get("global_batch_size", 1.0))
    micro = batch / max(1.0, float(dp * mbn))
    score = 1000.0
    # Penalize larger per-step microbatch pressure.
    score -= 0.08 * micro
    # Prefer TP because it usually reduces per-device parameter pressure.
    score += 3.0 * tp
    # Keep a mild PP preference without dominating memory safety.
    score += 0.5 * pp
    return float(score)
""",
    },
]

ISLAND_LEADERS = [
    {'island': 'memory_safe',
     'pp_size': 2,
     'micro_batch_num': 64,
     'tp_size': 16,
     'dp_size': 1,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1048.84,
     'score_rank': 1,
     'total_latency_s': 1.789702814,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp2_mbn64_tp16_dp1',
     'metrics': {'estimated_total_gb': 3.053453312,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.190840832,
                 'pipeline_bubble_ratio': 0.015384615,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 1,
                 'pp_cross_affinity_links': 1,
                 'dp_cross_node_groups': 0,
                 'dp_cross_affinity_groups': 0,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 128.0,
                 'derived_microbatch_size': 2.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'memory_safe',
     'pp_size': 2,
     'micro_batch_num': 32,
     'tp_size': 16,
     'dp_size': 1,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1048.68,
     'score_rank': 2,
     'total_latency_s': 1.817247763,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp2_mbn32_tp16_dp1',
     'metrics': {'estimated_total_gb': 3.590324224,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.224395264,
                 'pipeline_bubble_ratio': 0.03030303,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 1,
                 'pp_cross_affinity_links': 1,
                 'dp_cross_node_groups': 0,
                 'dp_cross_affinity_groups': 0,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 128.0,
                 'derived_microbatch_size': 4.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'memory_safe',
     'pp_size': 1,
     'micro_batch_num': 64,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1048.42,
     'score_rank': 3,
     'total_latency_s': 1.825072425,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn64_tp16_dp2',
     'metrics': {'estimated_total_gb': 5.570035712,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.348127232,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 16,
                 'dp_cross_affinity_groups': 16,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 64.0,
                 'derived_microbatch_size': 1.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'memory_safe',
     'pp_size': 1,
     'micro_batch_num': 4,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1047.22,
     'score_rank': 13,
     'total_latency_s': 1.825072425,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn4_tp16_dp2',
     'metrics': {'estimated_total_gb': 13.623099392,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.851443712,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 16,
                 'dp_cross_affinity_groups': 16,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 64.0,
                 'derived_microbatch_size': 16.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
]


def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    """Memory-safe seed scorer."""
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    batch = float(model_cfg.get("global_batch_size", 1.0))
    micro = batch / max(1.0, float(dp * mbn))
    score = 1000.0
    # Penalize larger per-step microbatch pressure.
    score -= 0.08 * micro
    # Prefer TP because it usually reduces per-device parameter pressure.
    score += 3.0 * tp
    # Keep a mild PP preference without dominating memory safety.
    score += 0.5 * pp
    return float(score)
