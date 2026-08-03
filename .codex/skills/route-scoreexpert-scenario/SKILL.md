---
name: route-scoreexpert-scenario
description: Route a ScoreExpert GPU deployment scene through DeepWiki recall, authoritative local Wiki hard matching, direct PP/TP/DP/MBN inference, or DAGBuilder_Evolve simulation and owner-gated experience admission. Use when a user supplies a new topology, model, workload, slow-card distribution, optimization objective, or asks whether an existing experience can be reused before running simulation.
---

# Route ScoreExpert Scenario

Use this skill as the single entry point for “input one scene, query first, simulate only when needed, then replenish the experience library.”

Before acting, read both files completely:

- `references/scenario-contract.md` for required input and routing states.
- `references/workflow.md` for DeepWiki recall, local adjudication, simulation, and admission steps.

Also apply the current contracts rather than duplicating them:

- For local matching and Wiki writes, read `../maintain-scoreexpert-wiki/SKILL.md` and its `references/workflows.md`.
- For simulation, read `/Users/cookie/.codex/skills/scoreexpert-scenario-analysis/SKILL.md` and its `references/workflow.md`.

## Execute

1. Normalize the scene before querying. Do not reduce it to slow-card IDs.
2. Ask DeepWiki about `BUGg921/scoreexpert-wiki` for candidate mature rules and raw sources. Treat the answer as recall, not authority.
3. Reconcile every candidate against the local `SCHEMA.md`, `index.md`, objective summary, linked raw source, Git state, and direct-inference contract.
4. Before simulation, check whether an exact, structurally valid flat review draft already exists in `DAGBuilder_Evolve/outputs/`.
5. Emit exactly one routing state from the scenario contract.
6. Return immediately for `DIRECT_MATCH`, `DIRECT_MATCH_LOCAL_RECOVERY`, or `PENDING_REVIEW`.
7. For a complete `MISS`, `AMBIGUOUS_MATCH`, `OUT_OF_BOUND`, `CONFLICT`, or `STALE_RECALL` without an exact pending draft, run the bounded Evolve pipeline and create a self-contained review draft.
8. Stop after the draft. Import it only after the owner explicitly identifies the report as reviewed and approved.
9. After approval, snapshot the exact edited report into immutable raw, run candidate admission, update only the matching objective/category branch, update index/log, and lint.

## Non-negotiable boundaries

- DeepWiki cannot grant maturity, settle local Git state, or replace raw-source boundary checks.
- A DeepWiki miss does not force simulation when the local authoritative Wiki has a unique mature match.
- An existing exact pending report prevents duplicate simulation but does not count as a mature match.
- Missing decisive scene fields produce `INSUFFICIENT_INPUT`; do not invent them or start an invalid simulation.
- Score nomination, topology mapping, numerical simulation, and real Evaluation remain separate evidence layers.
- Partial search coverage yields only “当前已仿真候选最优”.
- Simulation completion is not admission. Never write an unreviewed draft into `raw/` or `concepts/`.
- Formal admission does not automatically update DeepWiki. Report whether commit, push, and DeepWiki re-index are still pending.

## Finish

Return the normalized scene, DeepWiki recall status, local match evidence, routing state, action taken, PP/TP/DP/MBN when available, source/report paths, evidence boundary, and next required gate.
