"""
Island instruction: Balance time, memory risk, topology crossings, pipeline bubble, layer balance, and idle GPUs with simple interpretable terms.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0003_balanced_generalist.md
Active evolution file. Seed record lives in ScoreExpert/islands/seeds/balanced_generalist.py.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
        'island_score': 1011.504615385,
        'evaluation': {'total_latency_s': 1.789702814, 'pp_size': 2, 'micro_batch_num': 64, 'tp_size': 16, 'dp_size': 1},
        'origin': 'seed',
        'observations': [{'round': 1, 'mode': 'full_database_ranking', 'status': 'pass', 'ranking_quality': 199.864418027, 'spearman_score_vs_negative_latency': 0.366313429, 'top_k_avg_latency_s': 28.520927621, 'top_k_best_latency_s': 2.000179116, 'database_best_score_rank': 14, 'total_latency_s': 28.520927621}],
        'source': """def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    \"\"\"Balanced generalist seed scorer.\"\"\"
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    total = int(topo_cfg.get("num_gpus", topo_cfg.get("num_devices", 1)))
    active = pp * tp * dp
    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))
    micro = float(model_cfg.get("global_batch_size", 1.0)) / max(1.0, float(dp * mbn))
    score = 1000.0
    # Balance latency risk through pipeline bubble.
    score -= 300.0 * bubble
    # Penalize idle devices without making utilization the only objective.
    score -= 2.0 * max(0, total - active)
    # Keep memory pressure visible through the derived microbatch size.
    score -= 0.04 * micro
    # Mildly reward TP/DP when other costs remain acceptable.
    score += 1.0 * tp + 0.2 * dp
    return float(score)
""",
    },
]

ISLAND_LEADERS = [
    {'island': 'balanced_generalist',
     'pp_size': 2,
     'micro_batch_num': 64,
     'tp_size': 16,
     'dp_size': 1,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1011.504615385,
     'score_rank': 8,
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
    {'island': 'balanced_generalist',
     'pp_size': 2,
     'micro_batch_num': 32,
     'tp_size': 16,
     'dp_size': 1,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1006.949090909,
     'score_rank': 18,
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
    {'island': 'balanced_generalist',
     'pp_size': 1,
     'micro_batch_num': 64,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1016.36,
     'score_rank': 1,
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
    {'island': 'balanced_generalist',
     'pp_size': 1,
     'micro_batch_num': 4,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1015.76,
     'score_rank': 5,
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
    """Balanced generalist seed scorer."""
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    total = int(topo_cfg.get("num_gpus", topo_cfg.get("num_devices", 1)))
    active = pp * tp * dp
    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))
    micro = float(model_cfg.get("global_batch_size", 1.0)) / max(1.0, float(dp * mbn))
    score = 1000.0
    # Balance latency risk through pipeline bubble.
    score -= 300.0 * bubble
    # Penalize idle devices without making utilization the only objective.
    score -= 2.0 * max(0, total - active)
    # Keep memory pressure visible through the derived microbatch size.
    score -= 0.04 * micro
    # Mildly reward TP/DP when other costs remain acceptable.
    score += 1.0 * tp + 0.2 * dp
    return float(score)
