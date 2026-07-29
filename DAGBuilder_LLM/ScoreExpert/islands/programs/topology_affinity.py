"""
Island instruction: Prioritize topology locality. Penalize TP cross-affinity most strongly, DP moderately, and PP lightly. Keep memory and micro-batch choices valid.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0001_topology_affinity.md
Active evolution file. Seed record lives in ScoreExpert/islands/seeds/topology_affinity.py.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
        'island_score': 1000.8,
        'evaluation': {'total_latency_s': 1.951141545, 'pp_size': 1, 'micro_batch_num': 4, 'tp_size': 8, 'dp_size': 4},
        'origin': 'seed',
        'observations': [{'round': 1, 'mode': 'full_database_ranking', 'status': 'pass', 'ranking_quality': -1080.561612709, 'spearman_score_vs_negative_latency': 0.114238949, 'top_k_avg_latency_s': 234.087741504, 'top_k_best_latency_s': 2.524590585, 'database_best_score_rank': 30, 'total_latency_s': 234.087741504}],
        'source': """def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    \"\"\"Topology-affinity seed scorer.\"\"\"
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    devices_per_node = int(topo_cfg.get("gpus_per_node", 1))
    score = 1000.0
    # Strongly penalize TP domains larger than one node.
    if tp > devices_per_node:
        score -= 1000.0
    # Penalize TP values that do not tile cleanly inside a node.
    if devices_per_node % max(1, tp) != 0:
        score -= 100.0
    # Keep a tiny DP reward so equal-topology candidates can separate.
    score += 0.2 * dp
    # Prefer smaller PP bubble when topology is otherwise equal.
    score -= 10.0 * float(pp - 1) / max(1.0, float(mbn))
    return float(score)
""",
    },
]

ISLAND_LEADERS = [
    {'island': 'topology_affinity',
     'pp_size': 1,
     'micro_batch_num': 4,
     'tp_size': 8,
     'dp_size': 4,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1000.8,
     'score_rank': 50,
     'total_latency_s': 1.951141545,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn4_tp8_dp4',
     'metrics': {'estimated_total_gb': 18.656264192,
                 'memory_overflow_gb': 2.656264192,
                 'memory_pressure': 1.166016512,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 8,
                 'dp_cross_affinity_groups': 8,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 32.0,
                 'derived_microbatch_size': 8.0},
     'rule_check': {'status': 'pass',
                    'violations': [],
                    'warnings': ['memory_soft_overflow'],
                    'risk_labels': ['memory_soft_overflow']}},
    {'island': 'topology_affinity',
     'pp_size': 1,
     'micro_batch_num': 8,
     'tp_size': 8,
     'dp_size': 4,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1000.8,
     'score_rank': 51,
     'total_latency_s': 1.951141545,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn8_tp8_dp4',
     'metrics': {'estimated_total_gb': 14.361296896,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.897581056,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 8,
                 'dp_cross_affinity_groups': 8,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 32.0,
                 'derived_microbatch_size': 4.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'topology_affinity',
     'pp_size': 1,
     'micro_batch_num': 32,
     'tp_size': 8,
     'dp_size': 4,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1000.8,
     'score_rank': 53,
     'total_latency_s': 1.951141545,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn32_tp8_dp4',
     'metrics': {'estimated_total_gb': 11.140071424,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.696254464,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 8,
                 'dp_cross_affinity_groups': 8,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 32.0,
                 'derived_microbatch_size': 1.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
    {'island': 'topology_affinity',
     'pp_size': 1,
     'micro_batch_num': 16,
     'tp_size': 8,
     'dp_size': 4,
     'active_gpus': 32,
     'idle_gpus': 0,
     'island_score': 1000.8,
     'score_rank': 52,
     'total_latency_s': 1.951141545,
     'evaluation_status': 'pass',
     'rulecheck_status': 'pass',
     'valuesim_status': 'pass',
     'failure_reason': '',
     'candidate_dir': 'outputs/scoreexpert_search_20260726_205315/initialization/evaluations/eval_pp1_mbn16_tp8_dp4',
     'metrics': {'estimated_total_gb': 12.213813248,
                 'memory_overflow_gb': 0.0,
                 'memory_pressure': 0.763363328,
                 'pipeline_bubble_ratio': 0.0,
                 'tp_cross_node_groups': 0,
                 'tp_cross_affinity_groups': 0,
                 'pp_cross_node_links': 0,
                 'pp_cross_affinity_links': 0,
                 'dp_cross_node_groups': 8,
                 'dp_cross_affinity_groups': 8,
                 'layer_imbalance': 0,
                 'global_batch_size': 128.0,
                 'local_minibatch_size': 32.0,
                 'derived_microbatch_size': 2.0},
     'rule_check': {'status': 'pass', 'violations': [], 'warnings': [], 'risk_labels': []}},
]


def score_strategy(strategy, model_cfg, topo_cfg, profile_cfg):
    """Topology-affinity seed scorer."""
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mbn = int(strategy["micro_batch_num"])
    devices_per_node = int(topo_cfg.get("gpus_per_node", 1))
    score = 1000.0
    # Strongly penalize TP domains larger than one node.
    if tp > devices_per_node:
        score -= 1000.0
    # Penalize TP values that do not tile cleanly inside a node.
    if devices_per_node % max(1, tp) != 0:
        score -= 100.0
    # Keep a tiny DP reward so equal-topology candidates can separate.
    score += 0.2 * dp
    # Prefer smaller PP bubble when topology is otherwise equal.
    score -= 10.0 * float(pp - 1) / max(1.0, float(mbn))
    return float(score)
