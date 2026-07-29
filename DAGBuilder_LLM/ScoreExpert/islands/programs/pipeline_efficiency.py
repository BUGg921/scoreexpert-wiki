"""
Island instruction: Prioritize PP and micro_batch_num interaction. Penalize pipeline bubble, tiny derived microbatch size, and unnecessary layer imbalance.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0002_pipeline_efficiency.md
Active evolution file. Seed record lives in ScoreExpert/islands/seeds/pipeline_efficiency.py.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
        'island_score': 1005.6,
        'evaluation': {'total_latency_s': 1.825072425, 'pp_size': 1, 'micro_batch_num': 4, 'tp_size': 16, 'dp_size': 2},
        'origin': 'seed',
        'observations': [{'round': 1, 'mode': 'full_database_ranking', 'status': 'pass', 'ranking_quality': 150.875009637, 'spearman_score_vs_negative_latency': 0.192080643, 'top_k_avg_latency_s': 5.470187905, 'top_k_best_latency_s': 2.000179116, 'database_best_score_rank': 14, 'total_latency_s': 5.470187905}],
        'source': """def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    \"\"\"Pipeline-efficiency seed scorer.\"\"\"
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))
    micro = float(model_cfg.get("global_batch_size", 1.0)) / max(1.0, float(dp * mbn))
    score = 1000.0
    # Penalize pipeline bubble directly.
    score -= 500.0 * bubble
    # Reject tiny derived microbatches; they under-utilize the pipeline.
    if micro < 1.0:
        score -= 100000.0
    elif micro < 2.0:
        score -= 300.0
    # Mildly prefer PP/TP when bubble and microbatch remain healthy.
    score += 0.8 * pp
    score += 0.3 * tp
    return float(score)
""",
    },
]

ISLAND_LEADERS = [
    {'island': 'pipeline_efficiency',
     'pp_size': 1,
     'micro_batch_num': 4,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1005.6,
     'score_rank': 10,
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
    {'island': 'pipeline_efficiency',
     'pp_size': 1,
     'micro_batch_num': 8,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1005.6,
     'score_rank': 11,
     'total_latency_s': 1.825072425,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn8_tp16_dp2',
     'metrics': {'estimated_total_gb': 9.328132096,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.583008256,
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
                 'derived_microbatch_size': 8.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'pipeline_efficiency',
     'pp_size': 1,
     'micro_batch_num': 32,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1005.6,
     'score_rank': 13,
     'total_latency_s': 1.825072425,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn32_tp16_dp2',
     'metrics': {'estimated_total_gb': 6.106906624,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.381681664,
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
                 'derived_microbatch_size': 2.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'pipeline_efficiency',
     'pp_size': 1,
     'micro_batch_num': 16,
     'tp_size': 16,
     'dp_size': 2,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1005.6,
     'score_rank': 12,
     'total_latency_s': 1.825072425,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn16_tp16_dp2',
     'metrics': {'estimated_total_gb': 7.180648448,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.448790528,
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
                 'derived_microbatch_size': 4.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
]


def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    """Pipeline-efficiency seed scorer."""
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    bubble = float(pp - 1) / max(1.0, float(mbn + pp - 1))
    micro = float(model_cfg.get("global_batch_size", 1.0)) / max(1.0, float(dp * mbn))
    score = 1000.0
    # Penalize pipeline bubble directly.
    score -= 500.0 * bubble
    # Reject tiny derived microbatches; they under-utilize the pipeline.
    if micro < 1.0:
        score -= 100000.0
    elif micro < 2.0:
        score -= 300.0
    # Mildly prefer PP/TP when bubble and microbatch remain healthy.
    score += 0.8 * pp
    score += 0.3 * tp
    return float(score)
