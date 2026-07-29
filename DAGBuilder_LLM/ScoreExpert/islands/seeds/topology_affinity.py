"""
Island instruction: Prioritize topology locality. Penalize TP cross-affinity most strongly, DP moderately, and PP lightly. Keep memory and micro-batch choices valid.
Seed source: D:/CodeProgram/codex/DAGBuilder/score_v2/prompts/runs/step0001_topology_affinity.md
This file is an immutable record. Evolution must update ScoreExpert/islands/programs only.
"""

ACTIVE_PROGRAM_ID = 'v0'

PROGRAM_BANK = [
    {
        'program_id': 'v0',
        'parent_ids': [],
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
        'island_score': None,
        'evaluation': None,
        'origin': 'seed',
    },
]

ISLAND_LEADERS = []


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
