"""
Island instruction: Balance time, memory risk, topology crossings, pipeline bubble, layer balance, and idle GPUs with simple interpretable terms.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0003_balanced_generalist.md
This file is an immutable record. Evolution must update ScoreExpert/islands/programs only.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
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
        'island_score': None,
        'evaluation': None,
        'origin': 'seed',
    },
]

ISLAND_LEADERS = []


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
