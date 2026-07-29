"""
Island instruction: Prioritize memory headroom. Strongly penalize OOM risk and nonlinear risk above 85%-90% memory pressure while keeping pipeline bubble reasonable.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0000_memory_safe.md
This file is an immutable record. Evolution must update ScoreExpert/islands/programs only.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
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
        'island_score': None,
        'evaluation': None,
        'origin': 'seed',
    },
]

ISLAND_LEADERS = []


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
