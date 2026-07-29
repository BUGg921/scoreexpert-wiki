"""
Island instruction: Prioritize PP and micro_batch_num interaction. Penalize pipeline bubble, tiny derived microbatch size, and unnecessary layer imbalance.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0002_pipeline_efficiency.md
This file is an immutable record. Evolution must update ScoreExpert/islands/programs only.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
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
        'island_score': None,
        'evaluation': None,
        'origin': 'seed',
    },
]

ISLAND_LEADERS = []


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
