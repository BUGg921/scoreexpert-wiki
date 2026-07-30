# Wiki Log

> Chronological record of all wiki actions. Append-only from this reset point.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete

## [2026-07-14] delete | Experience library reset

- Deleted all raw source snapshots, entity pages, concept pages, comparison pages, query pages and analysis outputs.
- Removed prior experience-specific index entries and historical experience log content.
- Preserved `README.md`, `SCHEMA.md`, project-local Codex skill, lint script and Git configuration.
- Recreated empty tracked directories with `.gitkeep` files for future experience input.

## [2026-07-14] ingest | Scoring strategy analysis

- Source: `/Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis.md`.
- Created immutable normalized snapshot: `raw/articles/scoring-strategy-analysis-2026-07-14.md`.
- Original SHA-256: `466feeb3687d200c4ef4c1e4e0125ca0754f9ab4da5bcf2bd83548287349f1f5`; immutable snapshot body SHA-256: `62dbc843380418bbaacbbc6762c1cecddf37308218f3471a2e60a2f743c8bef7`; embedded normalized source SHA-256: `92a30f5ebc82fcae67e4461ccb368bda23821e26458df8bdf5b8781b7c77366b`.
- Created: `entities/scoreexpert.md`, `concepts/homogeneous-32gpu-score-candidate.md`, `concepts/score-function-decision-chain.md`, `queries/validate-score-derived-candidate.md`.
- Classification: `unverified` deployment candidate; score derivation is available, but direct Evaluation, complete search space, model constraints and `micro` definition are missing.
- Navigation: `index.md` updated to 4 pages; no active formal experience added.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Scoring strategy analysis import

- Result: `Pages: 4 | Errors: 0 | Review items: 0`.
- Structural checks passed; wikilinks, frontmatter, source references and source-body hash are valid.
- Git: changes intentionally left uncommitted.

## [2026-07-14] update | Activate 32-GPU score-derived experience

- User decision: temporarily do not treat missing Evaluation, complete search space, model memory constraints or the `micro` definition as activation blockers; revisit them when evidence becomes available.
- Status changed: `unverified` → `active`; confidence remains `medium`.
- Default first candidate: `PP=1, TP=8, DP=4, MBN=1` for the recorded 32-GPU, 8-GPU-per-node and 16-GPU-per-affinity-group topology.
- Evidence boundary retained: the recommendation is supported by score derivation and explicit user review, not by direct Evaluation, and is not claimed as a hardware-global optimum.
- Updated: `concepts/homogeneous-32gpu-score-candidate.md`, `concepts/score-function-decision-chain.md`, `queries/validate-score-derived-candidate.md`, `entities/scoreexpert.md`, and `index.md`.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Active experience status update

- Result: `Pages: 4 | Errors: 0 | Review items: 0`.
- Structural checks passed after synchronizing the experience page, related pages, index and log.
- Git: changes intentionally left uncommitted.

## [2026-07-14] update | Make active experiences actionable

- Root cause: the previous skill template emphasized scenario, candidate, evidence and gaps, but did not require a reusable experience rule; the resulting page read like an evidence audit.
- Skill contract updated: every active experience must contain “触发条件 → 部署动作 → 作用机制 → 预期观测 → 失效边界”; parameter output or evidence review alone is insufficient.
- Updated reusable interfaces: `.codex/skills/maintain-scoreexpert-wiki/SKILL.md`, `references/workflows.md`, `references/templates.md`, and `SCHEMA.md`.
- Reworked `concepts/homogeneous-32gpu-score-candidate.md` with executable deployment steps, mechanisms, observable score effects, failure boundaries and a one-sentence reusable rule.
- Updated `index.md` to summarize the actual experience instead of only the parameter tuple.
- Status remains `active`; confidence remains `medium`; raw source snapshot is unchanged.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Actionable experience contract

- Wiki result: `Pages: 4 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Active-page semantic check passed: every current active experience contains an independent `部署经验总结` section.
- Skill frontmatter validation passed with an equivalent Ruby/YAML check; the bundled Python `quick_validate.py` could not start because this environment lacks the optional `PyYAML` module.
- Git: changes intentionally left uncommitted.

## [2026-07-14] update | Preserve explicit source experience

- Corrected the import behavior after user review: the source already contained an explicit four-part `经验总结`, which must be extracted before any Wiki synthesis.
- Restored the source conclusions in their original order: full-card priority; balanced TP/DP with the current `8:4` choice; `PP=1`; `MBN=1`.
- Reclassified “TP=8 aligns with an 8-GPU node” as `Wiki 补充推理` instead of presenting it as a source conclusion.
- Updated the skill, workflow, template and schema to require source-explicit conclusions to be preserved with their ordering, qualifiers and causal meaning.
- Updated `concepts/homogeneous-32gpu-score-candidate.md` and `index.md`; status remains `active`, confidence remains `medium`, and raw source is unchanged.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Explicit source experience preservation

- Wiki result: `Pages: 4 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Semantic check passed: all four source-explicit experience conclusions are present in source order, and the added topology interpretation is labeled `Wiki 补充推理`.
- Skill frontmatter passed the equivalent Ruby/YAML validation used in this environment.
- Git: changes intentionally left uncommitted.

## [2026-07-14] update | Make experience extraction source-adaptive

- Removed any implied fixed experience count; the four conclusions on the current page are source-specific, not a template requirement.
- Added three adaptive modes: explicit extraction for N source conclusions, distributed synthesis for decisions scattered through analysis/results, and `unverified` Wiki hypotheses when the source contains no deployment conclusion.
- Added mixed-mode handling and decision-based granularity rules so experiences are neither forced apart nor combined across different triggers/actions.
- Updated the skill, workflow, template and schema; existing experience content and status are unchanged.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Source-adaptive extraction modes

- Wiki result: `Pages: 4 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Skill frontmatter passed equivalent Ruby/YAML validation.
- Semantic review confirmed that the workflow does not prescribe a fixed experience count and distinguishes explicit extraction, distributed synthesis, Wiki hypothesis and mixed-source handling.
- Git: changes intentionally left uncommitted.

## [2026-07-14] update | Promote TP-to-DP ratio as an experience rule

- Corrected the extraction granularity: `TP:DP≈2:1` is now an explicit, recallable quantitative experience rather than a vague balance tendency or only the concrete `8:4` candidate.
- Separated the transferable rule `TP:DP≈2:1` from its current constrained instance `TP=8,DP=4`.
- Updated the experience page and index, and added reusable skill/workflow/template/schema rules requiring ratios, thresholds, bounds and inequalities to survive extraction.
- Status remains `active`; confidence remains `medium`; raw source is unchanged.
- Git: changes intentionally left uncommitted.

## [2026-07-14] lint | Quantitative experience preservation

- Wiki result: `Pages: 4 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Semantic check passed: `TP:DP≈2:1` appears as a core quantitative rule, `TP=8,DP=4` appears as its current instance, and the index exposes both.
- Skill frontmatter passed equivalent Ruby/YAML validation.
- Git: changes intentionally left uncommitted.

## [2026-07-15] update | Reframe 32-GPU result as a baseline-selection experience draft

- Reworked `concepts/homogeneous-32gpu-score-candidate.md` using a decision-experience structure: recall conditions, IF/THEN action, first baseline, minimum counterfactual set, quantitative scope, evidence, acceptance criteria, failure signals and fallbacks.
- Corrected the knowledge boundary: `TP=8,DP=4` is the winner among the recorded discrete candidates; `TP:DP=2:1` is not treated as a cross-scenario rule without additional evidence.
- Status changed from `active` to `unverified`; confidence changed from `medium` to `low` because the source has score evidence but no direct Evaluation, fixed effect threshold or executable rank/group mapping.
- Synchronized `index.md`, `entities/scoreexpert.md`, `concepts/score-function-decision-chain.md` and `queries/validate-score-derived-candidate.md`.
- The immutable raw source snapshot was not modified; Git changes remain uncommitted.

## [2026-07-15] lint | Baseline-selection experience draft

- Result: `Pages: 4 | Errors: 0 | Review items: 3`; structural checks and `git diff --check` passed.
- The three review items are intentional `confidence: low` markers on the experience draft, domain status page and validation plan.
- Low confidence is required because the source contains score evidence but no direct Evaluation, predefined effect threshold, cross-scenario validation or executable rank/group mapping.
- Source references, immutable raw hash, frontmatter, tags, wikilinks and index coverage are valid; Git changes remain uncommitted.

## [2026-07-15] ingest | Single- and multi-slow-GPU analyses

- Imported immutable source snapshot `raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md` from `/Users/cookie/Documents/clc/DAG_build/Scoring strategy analysis_快慢卡.md`; original SHA-256 `9aca21dad5d3d0ade1b19e2d7f43623272a68cdca4f81db8a6bf5ff27f1d5c0e`, snapshot body SHA-256 `d1b1d5fd32beb4b104ed7fe9265515dc0b49228d026fb30f722f008781eee182`.
- Imported immutable source snapshot `raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md` from `/Users/cookie/Documents/clc/DAG_build/多张慢卡场景部署策略分析.md`; original SHA-256 `4dddd1033716ef8d7a76802eb8f75bbf91cce299c968bc785faa0ff10bb8ae67`, snapshot body SHA-256 `fff1b4381672c268d4dc3619cb49fd64240cae990592c814e0364420dcc53744`.
- Created `concepts/single-slow-gpu-isolation.md`, `concepts/two-slow-gpu-distributed-balance.md` and `concepts/four-slow-gpu-symmetric-replicas.md`; updated the standard 32-card page with cross-scenario routing.
- Synchronized `entities/scoreexpert.md` and `index.md`; the Wiki now exposes four separate decision experiences instead of one parameter-only conclusion.
- Status: standard 32-card and single-slow-GPU experiences are `unverified`; two- and four-slow-GPU experiences are `partially_supported` because the source reports Evaluation winners without raw metrics or perturbation tests.
- Git changes intentionally remain uncommitted.

## [2026-07-15] lint | Four 32-GPU scenario experiences

- Result: `Pages: 7 | Errors: 0 | Review items: 3`; structural checks and `git diff --check` passed.
- The low-confidence review items are intentional for the standard 32-card baseline, single-slow-GPU isolation draft and standard-candidate validation plan because direct Evaluation is absent.
- Semantic review preserved four distinct decisions: standard score baseline, localized single-slow-GPU isolation, two-slow-GPU cross-affinity balancing and four-slow-GPU symmetric replicas.
- Confirmed evidence boundaries: `MBN=64` is a search-boundary candidate; `TP:DP=2:1` is a constrained instance; the multi-slow-GPU score does not read slow-card count or placement.
- Git changes intentionally remain uncommitted.

## [2026-07-15] update | Experience-library evolution demonstration and review gate

- Created four same-template scenario source documents under `outputs/experience-evolution-demo/01-source-cards/` for homogeneous, single-slow-GPU, two-slow-GPU and four-slow-GPU scenarios; the two- and four-slow cards are separate views of the existing combined raw sources, not new raw snapshots.
- Saved three auditable library stages: initial homogeneous + single-slow library, addition of the two-slow scenario, and addition of the four-slow scenario.
- Every stage records pre-filter candidates, per-candidate gate decisions and reasons, post-filter experience/evidence/validation sets, and count changes.
- Added the reusable review gate to the project skill, workflow, templates and schema. Pure score explanations are retained as evidence; vague, duplicate, over-generalized and non-executable candidates are rejected; source-explicit conclusions remain preserved even when they do not enter the experience layer.
- Added navigation from `README.md` and `index.md`; no raw snapshot or existing concept status was changed.
- Git changes intentionally remain uncommitted.

## [2026-07-15] lint | Experience-library evolution demonstration

- Result: `Pages: 7 | Errors: 0 | Review items: 3`; structural checks and `git diff --check` passed.
- The three review items remain intentional low-confidence markers on the homogeneous baseline, single-slow-GPU isolation draft and validation plan.
- Skill frontmatter passed Ruby/YAML validation.
- Semantic review passed: four scene cards exist; the initial library does not use later scenes; both incremental stages preserve before/after decisions; `MBN=64` remains a search-boundary candidate; score-only claims do not enter the experience layer; identical `1/8/4/1` tuples remain separate when trigger, mechanism and acceptance metrics differ.
- Git changes intentionally remain uncommitted.

## [2026-07-15] update | Classify current experience knowledge into three categories

- Defined the only currently populated experience categories as `homogeneous-baseline`（同构基线）, `local-heterogeneity`（局部异构）and `distributed-heterogeneity`（分布式异构）.
- Classified the standard 32-card page as homogeneous baseline, the single-slow-GPU page as local heterogeneity, and the two-/four-slow-GPU pages as distributed heterogeneity.
- Added `experience_category` and matching registered tags to all four experience pages; added a visible “经验分类” section explaining each classification boundary.
- Reorganized `index.md` and `entities/scoreexpert.md` around the three experience categories. Score reasoning and validation remain supporting knowledge, not additional experience categories.
- Updated `README.md`, `SCHEMA.md`, the project skill and formal-experience template. Empty future categories such as communication, memory, batch, resource degradation and cross-scenario decisions are intentionally not created.
- Confidence and experience status did not change; raw sources were not modified; Git changes remain uncommitted.

## [2026-07-15] lint | Three-category experience classification

- Result: `Pages: 7 | Errors: 0 | Review items: 3`; structural checks and `git diff --check` passed.
- Added lint enforcement: every page tagged `experience` must use exactly one allowed `experience_category`, and that category must also appear as a registered tag.
- The three review items remain intentional low-confidence markers on the homogeneous baseline, local-heterogeneity draft and validation plan.
- Semantic review confirmed the current mapping is 1 homogeneous baseline experience, 1 local-heterogeneity experience and 2 distributed-heterogeneity experiences; support pages are not misclassified as deployment experience.
- Git changes intentionally remain uncommitted.

## [2026-07-15] update | Partition experience pages by category directories

- Moved the homogeneous baseline experience to `concepts/homogeneous-baseline/homogeneous-32gpu-score-candidate.md`.
- Moved the local-heterogeneity experience to `concepts/local-heterogeneity/single-slow-gpu-isolation.md`.
- Moved both distributed-heterogeneity experiences to `concepts/distributed-heterogeneity/`.
- Kept `concepts/score-function-decision-chain.md` at the concepts root because it is supporting evidence, not an experience category.
- Updated `README.md`, `SCHEMA.md`, the project skill, formal-experience template and evolution-demo path references. Page slugs, wikilinks, sources, status and confidence did not change.
- Git changes intentionally remain uncommitted.

## [2026-07-15] lint | Category directory partition

- Result: `Pages: 7 | Errors: 0 | Review items: 3`; structural checks and `git diff --check` passed after switching the linter from direct `glob` to recursive `rglob`.
- Added enforcement that every experience page must live directly under `concepts/<experience_category>/`; the category field, category tag and directory must agree.
- All existing wikilinks remain valid because page slugs were preserved.
- The three review items remain intentional low-confidence markers; no raw source was modified.
- Git changes intentionally remain uncommitted.

## [2026-07-16] create | Three category knowledge summaries

- Created `concepts/homogeneous-baseline/homogeneous-baseline-knowledge-summary.md` covering normal-card PP/TP/DP/MBN tendencies, full-card versus reduced-card choice, topology mapping, first baseline, counterfactual candidates and applicability boundaries.
- Created `concepts/local-heterogeneity/local-heterogeneity-knowledge-summary.md` covering the definition of local heterogeneity, TP/DP/PP pollution ranges, small-TP and deep-PP isolation, stage rebalance, MBN boundary behavior and isolation failure conditions.
- Created `concepts/distributed-heterogeneity/distributed-heterogeneity-knowledge-summary.md` covering why local isolation loses value, multiple slow stages, fast/slow replica waiting, isolation-to-balance switching, symmetric replica construction and the difference between balance and absolute performance.
- Added populated subtype tags only: `distribution-imbalanced` for the two-slow-GPU experience and `distribution-symmetric` for the four-slow-GPU experience. Speed- and position-imbalance tags were not created because current sources lack exact IDs, speed ratios and perturbation evidence.
- Added bidirectional links between each category summary and its concrete experience pages; synchronized `index.md`, `entities/scoreexpert.md`, `README.md` and `SCHEMA.md`.
- Knowledge status remains unchanged: homogeneous and local summaries are low confidence because Evaluation is absent; the distributed summary is medium confidence because sources report Evaluation winners without raw metrics.
- Raw sources were not modified; Git changes remain uncommitted.

## [2026-07-16] lint | Three category knowledge summaries

- Result: `Pages: 10 | Errors: 0 | Review items: 5`; structural checks, `git diff --check` and skill frontmatter validation passed.
- Added maintenance enforcement: every enabled experience category must have one correctly typed `<category>-knowledge-summary.md`; summary pages cannot use the `experience` tag.
- The five review items are intentional low-confidence markers on the homogeneous experience and summary, local experience and summary, and the score-derived candidate validation plan.
- Semantic review kept Score evidence, topology reasoning and Evaluation evidence separate; `TP:DP=2:1` remains a constrained instance, `MBN=64` remains a search-boundary candidate, and reported Evaluation winners were not upgraded to active conclusions.
- Git changes intentionally remain uncommitted.
## [2026-07-18] update | Organize experience knowledge by optimization objective

- Added `concepts/deployment-objective-knowledge-framework.md` as the top-level knowledge entry: latency-first and stability-first, each split into homogeneous baseline, local heterogeneity and distributed heterogeneity.
- Fixed the required fields for each branch: scenario definition, card count/topology where applicable, `PP/TP/DP/MBN`, heterogeneity impact, isolation or balance/symmetry countermeasure, and scenario cases.
- Kept the existing three `experience_category` values as the scene/mechanism axis; optimization objective is a query, metric and acceptance axis, so existing experience cards were not duplicated or reclassified.
- Marked stability-first content as a validation gap because current sources lack repeatability, P99, OOM/failure, timeout and recovery Evaluation; no experience status or confidence was upgraded.
- Updated `SCHEMA.md`, the project skill and template, `README.md`, `entities/scoreexpert.md` and `index.md`. Raw sources and concrete experience cards were not modified; Git changes remain uncommitted.

## [2026-07-18] lint | Optimization-objective knowledge framework

- Result: `Pages: 11 | Errors: 0 | Review items: 5`; structural checks and `git diff --check` passed.
- The new framework is 199 lines and does not trigger the long-page review threshold.
- The five review items are intentional pre-existing `confidence: low` markers; this format change did not alter evidence, confidence or experience status.
- Semantic review confirmed two objective entries, three scene categories under each entry, one-copy experience-card reuse, and an explicit stability-Evaluation gap.
- Git changes remain uncommitted.

## [2026-07-18] create | Summarize all current experiences as latency-first

- Created `concepts/latency-first-experience-summary.md`, grouping all four current experience cards under the latency-first objective and the three existing scene categories.
- Summarized homogeneous full-card baseline, single-slow-card PP isolation, two-slow-card replica balancing and four-slow-card symmetric replica construction without merging or replacing their detailed pages.
- Added the cross-scene switch rule: homogeneous baseline -> local isolation while the anomaly is localizable -> distributed balance when slow cards cross regions -> symmetric replicas when all nodes are uniformly affected.
- Kept evidence states unchanged: homogeneous and single-slow remain `unverified`; two- and four-slow remain `partially_supported`; no page was promoted to `active`.
- Marked stability-first as currently empty rather than reusing latency cards as stability experience. Updated the objective framework, ScoreExpert entity and index; raw sources were not modified and Git changes remain uncommitted.

## [2026-07-18] lint | Latency-first experience summary

- Result: `Pages: 12 | Errors: 0 | Review items: 5`; structural checks and `git diff --check` passed.
- The new latency-first summary is 166 lines and contains valid source references, index coverage and outgoing wikilinks.
- The five review items are intentional pre-existing `confidence: low` markers; this summary did not alter evidence, confidence or experience status.
- Git changes remain uncommitted.

## [2026-07-19] delete | Remove superseded duplicate summaries and support pages

- Kept `concepts/deployment-objective-knowledge-framework.md`, `concepts/latency-first-experience-summary.md` and the complete `outputs/experience-evolution-demo/` directory as explicitly requested.
- Deleted the three redundant category summaries: `homogeneous-baseline-knowledge-summary.md`, `local-heterogeneity-knowledge-summary.md` and `distributed-heterogeneity-knowledge-summary.md`.
- Deleted `concepts/score-function-decision-chain.md` and `queries/validate-score-derived-candidate.md`; their necessary score reasoning, validation metrics and fallback rules remain in the latency-first summary and four concrete experience cards.
- Updated all inbound wikilinks, the schema, project skill, templates, README, linter, ScoreExpert entity and index to use the simpler two-layer structure: optimization-objective summary -> concrete experience cards.
- Raw sources, four concrete experience cards and evolution demonstration files were preserved; Git changes remain uncommitted.

## [2026-07-19] lint | Simplified two-layer experience library

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Confirmed the five selected obsolete pages are absent and all current Wiki links resolve.
- Confirmed `deployment-objective-knowledge-framework.md`, `latency-first-experience-summary.md` and every file under `outputs/experience-evolution-demo/` remain present.
- The two review items are intentional low-confidence markers on the homogeneous baseline and single-slow-card experience; deletion did not alter evidence status.
- Git changes remain uncommitted.

## [2026-07-19] update | Align project skill with simplified experience library

- Updated `.codex/skills/maintain-scoreexpert-wiki/SKILL.md` to make the authoritative knowledge path explicit: optimization-objective framework -> enabled objective summary -> concrete scenario card -> immutable raw source.
- Updated the workflow to route imports and queries through optimization objective first, update the matching objective summary with every concrete-card change, and avoid duplicate category summaries, standalone Score pages and generic validation pages by default.
- Added a safe cleanup contract: resolve exact keep/delete targets, preserve `raw/` and `outputs/experience-evolution-demo/` unless explicitly named, migrate unique knowledge before deletion, and remove stale link/schema/linter requirements in the same pass.
- Updated the formal experience template with optimization objective, primary metric, guardrails and objective-summary link; updated `agents/openai.yaml` to match the revised skill behavior.
- The bundled `quick_validate.py` could not start because `PyYAML` is unavailable; equivalent Ruby/YAML validation and repository lint are used instead. Git changes remain uncommitted.

## [2026-07-19] lint | Updated project-local skill

- Skill validation passed with Ruby/YAML: frontmatter contains only `name` and `description`, the folder name matches, all seven referenced resources exist, and `agents/openai.yaml` has valid interface fields and a skill-explicit default prompt.
- Wiki result: `Pages: 7 | Errors: 0 | Review items: 2`; `git diff --check` passed.
- The two review items remain intentional low-confidence markers on the homogeneous baseline and single-slow-card experience; the Skill update did not alter Wiki evidence status.
- Git changes remain uncommitted.

## [2026-07-19] update | Re-summarize four concrete latency experience cards

- Rewrote the four existing concrete files in place: homogeneous 32-GPU baseline, single-slow-card local isolation, two-slow-card distributed balance and four-slow-card symmetric replicas. No fifth experience file or duplicate category summary was created.
- Standardized each card around optimization objective and category, scenario definition, source-explicit experience, executable deployment summary, heterogeneity mechanism, first candidate and counterfactuals, score/topology/Evaluation boundaries, observability, failure conditions and fallback.
- Preserved source-specific conclusions and quantitative boundaries: `TP:DP=2:1` remains a constrained 32-card instance, `MBN=64` remains a search-boundary candidate, and the two-/four-slow-card score still cannot observe slow-card count or placement.
- Preserved evidence states: homogeneous and single-slow remain `unverified`/low confidence; two- and four-slow remain `partially_supported`/medium confidence. Raw sources and evolution snapshots were not modified.
- Updated the latency-first overview backlink to keep the ScoreExpert entity reachable. Git changes remain uncommitted.

## [2026-07-19] lint | Four re-summarized concrete experience cards

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Final card lengths are 102, 109, 108 and 108 lines, all below the 200-line review threshold.
- Semantic review confirmed all four cards contain optimization objective, scene category, source-explicit conclusions, deployment summary, observable metrics, counterfactual candidates, evidence separation and fallback boundaries.
- The two review items are intentional low-confidence markers on the score-only homogeneous and single-slow-card experiences; no evidence status was promoted.
- Git changes remain uncommitted.

## [2026-07-19] update | Rewrite parallel strategies as deployment experience

- Replaced parameter-list-style strategy summaries in all four latency-first cards with dimensioned deployment experience: `TP`, `TP/PP` or `TP/DP`, `DP`, and `PP/MBN` as supported by each scenario.
- Each dimension now states a reusable selection rule, interaction or switch condition before the concrete `PP/TP/DP/MBN` tuple; current tuples remain constrained scenario instances rather than the experience itself.
- Updated the latency-first overview and index to use the same rule-first format.
- Updated `SCHEMA.md`, the project-local Skill and its formal-card template so future “parallel strategy” sections cannot be satisfied by a parameter tuple alone.
- Evidence states were unchanged: homogeneous and single-slow remain low-confidence/unverified; two- and four-slow remain medium-confidence/partially-supported. Raw sources and evolution snapshots were not modified.

## [2026-07-19] lint | Dimensioned parallel-strategy experience

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Semantic check confirmed every concrete card contains a “parallel-strategy deployment experience” section, dimension-specific rules, and a separate current-scenario instance.
- The two review items are the intentional low-confidence states of the homogeneous and single-slow cards; no evidence status was promoted.
- Git changes remain uncommitted.

## [2026-07-19] update | Rewrite card count as resource-scale experience

- Replaced static card-count descriptions with resource-scale deployment experience in all four concrete cards: full-resource trigger, reduced-resource counterfactual, topology/parallelism reconstruction and current `active_gpu` instance.
- Added a heterogeneity-specific boundary: if reducing cards changes slow-card locality or replica symmetry, reclassify the scenario instead of attributing the result only to card count.
- Updated the latency-first overview, deployment-objective framework, index, `SCHEMA.md`, project-local Skill and template to enforce the rule-first resource format for future cards.
- Current 32-card values remain scenario instances; no source, evidence status or raw/evolution artifact was changed.

## [2026-07-19] lint | Resource-scale deployment experience

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Confirmed all four cards separate resource-scale rules from current 32-card instances and label added reduced-card/topology reasoning as Wiki validation rules where the source lacks direct Evaluation.
- The deployment-objective framework remains at the 200-line threshold without triggering a size review.
- The two remaining review items are the intentional low-confidence homogeneous and single-slow-card states; Git changes remain uncommitted.

## [2026-07-19] update | Separate overall experience from scenario instances

- Reworked `latency-first-experience-summary.md` so it begins with reusable latency-first overall experience instead of “current experience scope”.
- Removed concrete card counts, slow-card placements and PP/TP/DP/MBN tuples from general category rules; these now appear only under the matching “scenario case”, together with the linked single-scenario experience and evidence status.
- Recast `deployment-objective-knowledge-framework.md` as the permanent ScoreExpert deployment experience library, retaining the complete latency-first and stability-first branches even though stability-first currently has no deployment experience.
- Updated `SCHEMA.md`, README, index, project Skill, workflow, template and agent prompt to enforce the three-level structure: total library -> objective-level overall experience -> single-scenario experience card.
- No raw source, evolution snapshot, concrete experience card or evidence status was changed.

## [2026-07-19] lint | Three-level experience library

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Confirmed `latency-first-experience-summary.md` has no “current experience scope” section and all concrete card counts and parameter tuples occur only in scenario-case summaries.
- Confirmed the total library retains complete latency-first and stability-first branches; the framework remains at 200 lines without a size review.
- Skill frontmatter and agent YAML parsed successfully. The two remaining review items are intentional low-confidence evidence states; Git changes remain uncommitted.

## [2026-07-19] update | Name scenario cases directly

- Removed the redundant “single-scenario experience” labels from the latency-first overview.
- Renamed the four entries to direct business-facing cases: standard 32-card homogeneous baseline, single-slow-card local isolation, two-slow-card asymmetric balance and four-slow-card symmetric replicas.
- Updated the total library wording, schema, index, Skill workflow and templates so scenario cases use concrete case names such as “case” or “case one/case two”, while still linking the unique experience card.
- No deployment rule, parameter, source or evidence status changed.

## [2026-07-19] lint | Direct scenario-case names

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Confirmed the latency-first overview and total-library prose contain no “single-scenario experience” labels; all four entries use direct case names.
- The two remaining review items are unchanged low-confidence evidence states; Git changes remain uncommitted.

## [2026-07-20] update | Make direct inference the runtime objective

- Clarified the knowledge base objective as “offline admission, online inference”: a new scenario that matches one `active` experience and stays within its quantitative boundaries receives a deployment strategy without running a fresh real Evaluation.
- Added a direct-inference contract covering hard scenario fields, allowed parameter transformations, output strategy/mapping/confidence/fallback and stop conditions.
- Defined Evaluation, simulation and human review as admission, boundary-expansion and conflict-resolution tools rather than mandatory steps for every deployment.
- Updated README, entity page, index, total library, latency-first overview, schema, project Skill, workflow, formal-card template and agent prompt.
- Preserved the current evidence boundary: all four cards remain `unverified` or `partially_supported`, so the current library still enters knowledge-completion mode until an experience is reviewed and promoted to `active`.

## [2026-07-20] lint | Direct-inference knowledge contract

- Result: `Pages: 7 | Errors: 0 | Review items: 2`; structural checks and `git diff --check` passed.
- Skill frontmatter and agent YAML parsed successfully; the total library remains at 200 lines without a size review.
- Confirmed active matches use the direct-inference path, while missing, out-of-bound, conflicting or non-active matches use the knowledge-completion path.
- The two review items remain the intentional low-confidence homogeneous and single-slow-card states; Git changes remain uncommitted.

## [2026-07-20] update | Admit four mature latency experiences

- Treated the knowledge-base owner's explicit statement that all four current experiences are mature as the human-review admission decision.
- Promoted the homogeneous baseline, single-slow-card isolation, two-slow-card asymmetric balance and four-slow-card symmetric replica cards to `active` with `confidence: high`; removed their `hypothesis` tags.
- Added a direct-inference contract to every card with hard match fields, allowed transformations, direct PP/TP/DP/MBN output and stop/fallback conditions.
- Replaced mandatory “test first” and comparison-Evaluation wording with direct deployment plus runtime guardrails and fallback strategies.
- Preserved missing raw metrics as source-attachment completeness notes, while recording `ACCEPT_EXPERIENCE`, the 2026-07-20 owner review and active status separately.
- Updated the latency overview, total library, ScoreExpert entity, index, schema, Skill and workflow so experience maturity is not conflated with source attachment completeness.

## [2026-07-20] lint | Four active mature experiences

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed all four cards have `confidence: high`, `active` status, `ACCEPT_EXPERIENCE` owner-review admission and a complete direct-inference contract.
- Confirmed no current card retains `unverified`, `partially_supported`, `KEEP_FOR_VALIDATION`, “must upgrade” or mandatory comparison-Evaluation wording.
- Git changes remain uncommitted.

## [2026-07-20] update | Reduce scenario cards to two sections

- Rewrote all four concrete scenario cards so their only top-level body sections are “1. 场景描述” and “2. 具体的并行策略”.
- Moved maturity, topology, heterogeneity, hard-match and admission context into the scene description; kept the direct output, card-count rule, TP/PP/DP/MBN experience, actions, boundaries, fallback and admission record under the concrete parallel strategy.
- Updated README, index, total-library framework, schema, project Skill, workflow and formal-card template to enforce the same structure for future scenario cards.
- Preserved all four `active`, high-confidence admission decisions and direct-inference outputs; no raw source or evolution artifact was changed.

## [2026-07-20] lint | Two-section scenario cards

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed each of the four concrete cards contains exactly two second-level headings and remains below the 200-line review threshold.
- Confirmed Skill frontmatter and agent YAML parse successfully; Git changes remain uncommitted.

## [2026-07-20] update | Nest heterogeneity countermeasures under parallel strategy

- Reordered local and distributed heterogeneity knowledge as “scene definition → heterogeneity impact → parallel strategy”.
- Moved isolation, balance and symmetry countermeasures into parallel strategy instead of keeping them as peer sections; scenario cases now appear as strategy instances.
- Applied the same structure to the latency overview, the complete latency/stability framework, schema, README, index, project Skill, workflow and objective-summary template.
- Concrete scenario cards, active status, confidence and direct deployment outputs were unchanged.

## [2026-07-20] lint | Heterogeneity impact before strategy

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed local and distributed heterogeneity use exactly “scene definition → heterogeneity impact → parallel strategy” in the latency overview and both branches of the complete framework.
- Confirmed there are no peer “countermeasure” or “scenario case” headings under local/distributed heterogeneity; Skill frontmatter and agent YAML parse successfully.
- Git changes remain uncommitted.

## [2026-07-20] update | Generalize category definitions from active scenarios

- Rewrote homogeneous, local-heterogeneity and distributed-heterogeneity scene definitions by generalizing the four active experimental scenarios.
- Defined homogeneous by the absence of persistent device-speed differences, local heterogeneity by whether impact can be confined to one controllable local scope, and distributed heterogeneity by whether anomalies span multiple independent topology scopes.
- Kept 32 cards and one/two/four slow GPUs as scenario instances rather than category thresholds; preserved asymmetric and near-symmetric distributed subtypes.
- Updated the latency overview, complete framework, schema, README, index, project Skill and template; concrete cards and deployment strategies were unchanged.

## [2026-07-20] lint | Scenario-derived category definitions

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed all three definitions distinguish reusable category criteria from the current 32-card and one/two/four-slow-GPU instances.
- Confirmed the complete framework remains below 200 lines; Skill frontmatter and agent YAML parse successfully.
- Git changes remain uncommitted.

## [2026-07-20] update | State scene definitions directly

- Removed meta wording such as “derived from a case”, “current case” and “category threshold” from the three scene definitions.
- Restored concise scene descriptions: homogeneous has no persistent device-speed difference, local heterogeneity can be confined to one controllable scope, and distributed heterogeneity spans multiple independent topology scopes.
- Updated the latency overview, complete framework, schema, README, index, project Skill and template; cases and deployment strategies were unchanged.

## [2026-07-20] lint | Direct scene-definition wording

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the current scene definitions contain no “derived from case”, “current case size” or “category threshold” meta wording.
- Skill frontmatter and agent YAML parse successfully; Git changes remain uncommitted.

## [2026-07-20] update | Restore scenario cases as the fourth section

- Corrected local and distributed heterogeneity knowledge to “scene definition → heterogeneity impact → parallel strategy → scenario cases”.
- Kept isolation, balance and symmetry countermeasures inside parallel strategy, but moved concrete cases and admission status back into a separate fourth section.
- Updated the latency overview, complete latency/stability framework, schema, README, index, project Skill, workflow and objective-summary template.
- Concrete experience cards, active status, confidence and deployment outputs were unchanged.

## [2026-07-20] lint | Four-section heterogeneity knowledge

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed local and distributed heterogeneity both use four ordered sections in the latency overview and the latency/stability framework: scene definition, heterogeneity impact, parallel strategy and scenario cases.
- Confirmed countermeasures remain inside parallel strategy while concrete cases occupy a separate fourth section; Skill frontmatter and agent YAML parse successfully.
- Git changes remain uncommitted.

## [2026-07-20] update | Remove admission status from scenario cases

- Removed repeated admission status, owner-review dates and source-completeness notes from all latency-first scenario-case summaries and from the complete framework.
- Kept each case focused on scenario conditions, the concrete strategy instance and the link to its unique experience card.
- Updated schema, index, project Skill, workflow and objective-summary template so admission status remains only in concrete experience cards.
- No concrete experience status, confidence, strategy or source was changed.

## [2026-07-20] lint | Scenario cases without admission status

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the latency overview and complete framework contain no admission-status or owner-review lines inside scenario cases.
- Confirmed source markers remain attached to case descriptions and admission metadata remains available in the linked concrete cards; Skill frontmatter and agent YAML parse successfully.
- Git changes remain uncommitted.

## [2026-07-20] update | Remove strategy acceptance bullets

- Removed the “countermeasure acceptance” bullets from the local-heterogeneity and distributed-heterogeneity parallel strategies in the latency-first overview.
- Parallel strategy now contains only reusable deployment countermeasures and PP/TP/DP/MBN selection rules; no concrete experience card or deployment output changed.

## [2026-07-20] lint | Parallel strategies without acceptance items

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed no “strategy acceptance” or “countermeasure acceptance” item remains in the formal knowledge pages or project Skill.
- Git changes remain uncommitted.

## [2026-07-20] update | Merge overall countermeasures into parallel dimensions

- Removed standalone overall-countermeasure bullets from local and distributed heterogeneity strategies.
- Merged isolation into TP, TP/PP, DP and PP/MBN rules; merged balance and symmetry primarily into DP while retaining their TP, TP/PP and PP/MBN implications.
- Applied the same dimension-first wording to the latency overview, complete latency/stability framework, schema, README, index, project Skill, workflow and template.
- Scenario cases and concrete deployment cards were unchanged.

## [2026-07-20] lint | Dimension-integrated countermeasures

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed no standalone overall, isolation or balance/symmetry countermeasure bullet remains in the latency overview or complete framework.
- Skill frontmatter and agent YAML parse successfully; Git changes remain uncommitted.

## [2026-07-20] update | Move scenario-card governance into frontmatter

- Added `status`, `optimization_priority`, `admitted_by` and `admitted_at` to all four active concrete experience cards.
- Removed repeated status, optimization-goal, admission-basis, objective-summary and admission-record content from card bodies; the two body chapters now contain only scene conditions and deployable strategy.
- Updated schema, complete framework, README, index, project Skill, workflow and formal-card template to separate governance metadata from deployment knowledge.
- Extended the linter to require status and optimization priority on experience pages, require admission owner/date on active pages and reject governance labels in experience-card bodies.

## [2026-07-20] lint | Governance-free scenario-card bodies

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed all four cards contain the required governance frontmatter and exactly two top-level body chapters.
- Confirmed no status, optimization-goal, admission-basis, objective-summary or admission-record label remains in any concrete card body.
- Skill frontmatter and agent YAML parse successfully; Git changes remain uncommitted.

## [2026-07-20] update | Merge actions and separate applicability from fallback

- Moved each card's scenario applicability and cross-category switch conditions into “场景描述 → 不适用条件”.
- Merged PP/TP/DP/MBN, mapping and executable setup steps into “直接输出”, removing the separate “部署动作” section.
- Replaced “适用边界与回退” with “失效条件与回退”, which now contains only runtime failures such as OOM, replica skew or a dominant slow stage and their fallback strategies.
- Updated all four cards, schema, complete framework, README, index, project Skill, workflow and formal-card template; extended lint to enforce the new subheadings and require an in-body non-applicability condition.

## [2026-07-20] lint | Executable output and runtime-only fallback

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed every concrete card contains “不适用条件” in scene description and exactly the required strategy subheadings: direct output, deployment experience and failure/fallback.
- Confirmed no concrete card retains the obsolete deployment-action or applicability/fallback subheading; Skill frontmatter and agent YAML parse successfully.
- Git changes remain uncommitted.

## [2026-07-20] update | Rename direct output to deployment strategy

- Renamed the concrete-card subheading “直接输出” to “部署策略” in all four active scenario cards.
- Updated the schema, complete framework, README, index, project Skill, workflow, template and linter; the parameter, mapping and execution content under the heading was unchanged.

## [2026-07-20] lint | Deployment-strategy heading

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed all four concrete cards use “部署策略、部署经验、失效条件与回退” and no longer use the old “直接输出” heading.
- Skill frontmatter and agent YAML parse successfully; Git changes remain uncommitted.

## [2026-07-20] update | Remove governance workflow from latency overview

- Removed “6. 经验准入、直接推理与回退” from the latency-first experience summary because it described knowledge governance and query workflow rather than additional latency deployment experience.
- Kept the reusable rule in the overview's overall experience: validation cost is paid at admission, matched active experience is reused directly, and only misses, boundary violations or conflicts trigger new validation.
- Kept the complete admission and direct-inference contract in `SCHEMA.md` and the project Skill, with the core rule retained in the total-library framework; scenario-specific failure and fallback rules remain in the four concrete experience cards.

## [2026-07-20] lint | Latency overview without governance section

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the latency-first summary now ends with cross-scenario decision rules, while retaining links to the complete framework and ScoreExpert domain entry.
- Git changes remain uncommitted.

## [2026-07-20] delete | Remove redundant latency-wide summary section

- Removed “1. 延迟优先总体经验” and its six summary bullets because their deployment content is already expanded in the three scenario-knowledge sections.
- Retained one sentence below the page title defining latency-first and its throughput, memory, OOM and runtime-variation constraints.
- Renumbered the remaining sections from 1 through 4 and updated the README and index descriptions; no scenario rule, scenario case or concrete experience card was removed.

## [2026-07-20] lint | Latency overview without summary section

- Result: `Pages: 7 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed “延迟优先总体经验” and “总体经验可以概括为” no longer appear in the latency-first overview; the remaining knowledge sections are numbered consecutively from 1 through 4.
- Git changes remain uncommitted.

## [2026-07-21] update | Separate numeric strategies, reasons and scenario cases

- Changed local and distributed heterogeneity knowledge to the five-part structure “scene definition → heterogeneity impact → parallel strategy → reason → scenario cases”.
- Moved admitted numeric results into “parallel strategy”: single slow GPU uses `PP=16,TP=2,DP=1,MBN=64`; the two distributed cases use `PP=1,TP=8,DP=4,MBN=1`, with `TP:DP=2:1` recorded explicitly.
- Moved TP synchronization, PP-stage, DP-replica and pipeline-bubble explanations into the separate “reason” section, while retaining scenario summaries and links in “scenario cases”.
- Updated the latency overview, complete latency/stability framework, schema, README, index, project Skill, workflow and template. Concrete experience-card parameters and status were not changed by this update.

## [2026-07-21] lint | Five-part heterogeneous knowledge structure

- Confirmed local and distributed heterogeneity use “scene definition → heterogeneity impact → numeric parallel strategy → reason → scenario cases” in the latency overview and complete framework.
- Confirmed Skill frontmatter and agent YAML parse successfully, and no obsolete four-part structure remains in the maintained schema, README, index, workflow or template.
- Wiki lint still reports four existing concrete-card errors because all four cards lack the currently required “失效条件与回退” subheading; this structure update did not restore or redefine those card sections.

## [2026-07-21] update | Apply five-part structure to homogeneous knowledge

- Changed homogeneous baseline knowledge to “scene definition → homogeneous impact → numeric parallel strategy → reason → scenario cases”, matching the local and distributed branches.
- Replaced the standalone resource-scale section with communication, synchronization and pipeline impacts; resource changes are now treated as new scene-matching inputs rather than unconditional transformations inside the original scene.
- Recorded the admitted homogeneous strategy as `PP=1,TP=8,DP=4,MBN=1` with `TP:DP=2:1`, and separated the reasons for PP, TP, DP and MBN.
- Updated the latency overview, complete latency/stability framework, schema, README, index, project Skill, workflow and template; the concrete homogeneous experience card was not changed by this structure update.

## [2026-07-21] lint | Unified five-part three-category structure

- Confirmed homogeneous, local-heterogeneity and distributed-heterogeneity branches all use five ordered sections in the latency overview and in both objective branches of the complete framework.
- Confirmed numeric strategy, reason and scenario-case responsibilities are separated; Skill frontmatter, agent YAML and `git diff --check` pass.
- Wiki lint continues to report the same four concrete-card errors for the missing required “失效条件与回退” subheading; this overview-structure update did not redefine those card bodies.

## [2026-07-21] delete | Remove homogeneous impact section

- Removed “同构基线的影响” from both latency-first and stability-first homogeneous knowledge.
- Homogeneous knowledge now uses “scene definition → numeric parallel strategy → reason → scenario cases”; local and distributed heterogeneity retain their separate heterogeneity-impact section.
- Updated the latency overview, complete framework, schema, README, index, project Skill, workflow and template; numeric strategies and reasons were unchanged.

## [2026-07-21] lint | Homogeneous knowledge without impact section

- Confirmed homogeneous knowledge now has four ordered sections and retains numeric strategy, reasons and scenario cases; local and distributed knowledge retain their five ordered sections.
- Skill frontmatter, agent YAML and `git diff --check` pass; no maintained schema or template still requires “同构基线的影响”.
- Wiki lint reports 16 broken-link errors because all four concrete experience-card files are currently deleted in the working tree; this structure update did not restore or clean up those separate deletions.

## [2026-07-21] delete | Remove heterogeneous impact sections

- Removed “局部异构的影响” and “分布式异构的影响” from latency-first and stability-first objective knowledge.
- All three categories now use “scene definition → numeric parallel strategy → reason → scenario cases”.
- Updated overview, complete framework, schema, README, index, Skill, workflow and template; numeric strategies, reasons and scenario cases were retained.

## [2026-07-21] lint | Unified four-part knowledge structure

- Confirmed all three categories use four ordered sections in the latency overview and in both objective branches of the complete framework; no maintained schema, workflow or template still requires a heterogeneous-impact section.
- Skill frontmatter, agent YAML and `git diff --check` pass.
- Wiki lint reports 16 broken-link errors because all four concrete experience-card files remain deleted in the working tree; this structure update preserved those separate deletions.

## [2026-07-22] update | Rewrite source reports as four scenario files

- Re-summarized the three root source reports into four independent scenario files: homogeneous 32 GPU, single slow GPU, two slow GPUs across affinity groups, and four slow GPUs distributed one per node.
- Preserved the report body format of task, experiment scene, optimum, scoring code and experience summary.
- Separated executable numeric parallel strategies from the reasons for PP, TP, DP, MBN and topology mapping; split the former multi-slow-GPU report into independent two-GPU and four-GPU files.
- At this stage the rewritten reports remained in the project root; the four deleted formal experience cards were unchanged.

## [2026-07-22] lint | Four rewritten scenario source files

- Confirmed all four source files retain the five-part report body and contain separate “parallel strategy”, “reason” and “conclusion boundary” subsections.
- Confirmed each file records explicit `PP/TP/DP/MBN` values and the applicable `TP:DP` ratio; `git diff --check` passes.
- Wiki lint remains at `Pages: 3 | Errors: 16 | Review items: 0` because the four formal experience cards are still deleted and their existing incoming wikilinks are broken; this source rewrite did not restore them.

## [2026-07-22] ingest | Move four scenario reports into raw

- Moved the four rewritten root reports into dated immutable snapshots under `raw/articles/`: homogeneous 32 GPU, single slow GPU, two slow GPUs, and four slow GPUs.
- Added `source_path`, `ingested`, body `sha256`, and `original_sha256` frontmatter to each snapshot without changing its report body.
- Did not restore or overwrite the three earlier raw snapshots, which were already deleted in the working tree.
- Updated `index.md` to describe the four current organized scenario sources.
- Updated `entities/scoreexpert.md` and `concepts/latency-first-experience-summary.md` so their source metadata and inline citations point to the four new raw snapshots rather than the deleted historical files.

## [2026-07-22] lint | Four raw scenario snapshots

- Confirmed all four new raw snapshots pass body SHA-256 validation and no rewritten scenario report remains in the project root.
- Confirmed maintained knowledge pages no longer reference the three deleted historical raw files; `git diff --check` passes.
- Wiki lint remains at `Pages: 3 | Errors: 16 | Review items: 0`; all remaining errors are broken wikilinks caused by the four formal experience cards that remain deleted in the working tree.

## [2026-07-22] update | Align links and architecture with current files

- Removed all references to the four deleted concrete experience cards from the ScoreExpert entry, total framework, latency overview and index.
- Linked scenario cases to the four existing raw sources with ordinary Markdown links; raw files remain source-layer documents rather than wikilink targets.
- Aligned README, schema, project Skill, workflow and templates with the current “total library → objective summary → raw scenario source” structure; old formal-card templates are retained only for migration compatibility.
- Updated the index page count from 7 to the actual 3 formal knowledge pages.

## [2026-07-22] lint | Current-file architecture without broken links

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; all 16 obsolete concrete-card wikilinks have been removed.
- Confirmed every local Markdown link to the four raw scenario sources resolves, raw hashes remain valid, and `git diff --check` passes.
- Confirmed Skill frontmatter and agent YAML parse successfully; the deleted-card and deleted-historical-source states remain unchanged.

## [2026-07-22] update | Add trigger conditions to parallel strategies

- Rewrote the latency-first parallel strategies as “trigger condition → numeric PP/TP/DP/MBN strategy → topology mapping”.
- Added the homogeneous full-card condition `idle loss > communication-optimization benefit`, the local-isolation condition, and separate two-slow-card and four-slow-card conditions.
- Kept parameter-selection mechanisms in the independent “reason” sections and synchronized the complete framework, README, schema, Skill, workflow and templates.

## [2026-07-22] lint | Conditional parallel strategies

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; all latency-first branches retain the ordered “scene definition → parallel strategy → reason → scenario cases” structure.
- Confirmed each mature parallel strategy now contains a trigger condition, concrete `PP/TP/DP/MBN` values and topology mapping, while reasons remain separate.
- Skill frontmatter, agent YAML and `git diff --check` pass; raw source snapshots were not modified.

## [2026-07-22] update | Refine heterogeneous strategy conditions

- Refined the local-heterogeneity strategy to compare the compute benefit of retaining and isolating one slow GPU against deep-PP pipeline and scheduling costs.
- Refined the two-slow-card strategy to require both reduced PP-isolation value and a full-card compute benefit larger than replica-wait and communication costs.
- Refined the four-slow-card strategy to require symmetric-replica benefit and full-card compute benefit to dominate multi-stage isolation and node-local TP communication costs.
- Synchronized the latency overview, complete framework and project Skill; numeric strategies, reasons, scenario links and raw sources were unchanged.

## [2026-07-22] lint | Refined local and distributed conditions

- Result: `Pages: 3 | Errors: 0 | Review items: 0`.
- Confirmed local and distributed parallel strategies now include explicit benefit/cost conditions, full numeric parameters and topology mappings in both the latency overview and complete framework.
- Skill frontmatter and `git diff --check` pass; raw source snapshots remain unchanged.

## [2026-07-22] update | Separate reusable strategies from scenario names

- Removed “single-slow-card isolation”, “two-slow-card asymmetric balance” and “four-slow-card symmetric replicas” labels from parallel-strategy sections.
- Generalized local strategy by whether impact can be localized, and distributed strategies by whether DP replicas are asymmetric or can be mapped symmetrically.
- Kept concrete slow-card counts and scenario names only in “scenario cases”; synchronized the total framework, schema, Skill and workflow.

## [2026-07-22] lint | Reusable strategy wording

- Result: `Pages: 3 | Errors: 0 | Review items: 0`.
- Confirmed no parallel-strategy section contains the three concrete scenario labels; those labels remain only in scenario cases.
- Skill frontmatter and `git diff --check` pass; raw source snapshots remain unchanged.

## [2026-07-22] update | Add DeepWiki README entry

- Added the `Ask DeepWiki` badge directly below the README title.
- The badge links to `https://deepwiki.com/BUGg921/scoreexpert-wiki` as a visible AI question-and-answer entry for the repository.

## [2026-07-22] lint | DeepWiki README entry

- Result: `Pages: 3 | Errors: 0 | Review items: 0`.
- Confirmed the README badge Markdown is valid and `git diff --check` passes.
- Existing deletions under `outputs/experience-evolution-demo/` were left unchanged.

## [2026-07-27] update | Generalize minimum-PP and TP-to-DP ratio strategies

- Replaced fixed 32-GPU tuples in the homogeneous and distributed parallel-strategy sections with a reusable solver: use all available GPUs when compute benefit dominates communication cost, choose the minimum feasible `PP`, solve integer `TP` and `DP` under `PP × TP × DP = active_gpu` and `TP:DP=2:1`, and choose the minimum feasible `MBN`.
- Kept the 32-GPU tuples only in scenario cases and immutable raw sources; the single-slow-GPU local-isolation strategy remains fixed because deep PP is its isolation mechanism rather than an avoidable pipeline cost.
- Updated the direct-inference contract so a different card count may be answered without Evaluation only when the admitted scaling rule produces complete integer groups within model and communication boundaries.
- Synchronized the total framework, latency overview, ScoreExpert entry, schema, project Skill, workflow and template. Existing unrelated README, IDE metadata and DAGBuilder working-tree changes were left untouched.

## [2026-07-27] lint | Resource-scalable parallel strategies

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the admitted solver maps 8 GPUs to `PP=1,TP=4,DP=2,MBN=1` and preserves the 32-GPU example as `PP=1,TP=8,DP=4,MBN=1`.
- Confirmed fixed 32-GPU tuples remain only in scenario cases and the separate local-isolation strategy; raw source snapshots were not modified.
- Existing staged IDE metadata, untracked DAGBuilder directories and the unrelated README demo removal remain untouched.

## [2026-07-27] update | Generalize local-heterogeneity isolation strategy

- Replaced the fixed 32-GPU local-heterogeneity tuple with a reusable solver: minimize `DP` to avoid replica skew, preserve `TP:DP=2:1`, derive integer `PP` from `PP × TP × DP = active_gpu`, and use the resulting maximum feasible PP depth for local stage isolation.
- Changed `MBN=64` from a reusable fixed value to the 32-GPU scenario's search-boundary example; the reusable rule selects the largest feasible MBN under memory, latency and scheduling constraints.
- Kept `PP=16,TP=2,DP=1,MBN=64` in the scenario case and immutable raw source only. No raw source was modified.
- Synchronized the local-heterogeneity solver into the project Skill and query workflow so future maintenance keeps it distinct from the minimum-PP homogeneous/distributed rule.

## [2026-07-27] lint | Resource-scalable local isolation

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the solver maps 8 GPUs to `PP=4,TP=2,DP=1` and 32 GPUs to `PP=16,TP=2,DP=1`; `MBN` remains a boundary-driven value rather than a fixed cross-resource constant.
- Confirmed fixed `PP=16,TP=2,DP=1,MBN=64` text remains only in the 32-GPU scenario case and immutable raw source.

## [2026-07-27] update | Merge distributed-heterogeneity parameter strategies

- Merged the asymmetric-replica and symmetric-replica entries into one distributed-heterogeneity parallel strategy because both use the same minimum-PP, `TP:DP=2:1` parameter solver.
- Kept two explicit mapping branches inside the shared strategy: predicted-execution-time balancing for asymmetric replicas, and identical anomaly structure for replicas that can be mapped symmetrically.
- Kept the two-slow-GPU and four-slow-GPU scenario cases and raw sources separate; only the reusable strategy was merged.
- Updated the project Skill so future equivalent parameter rules are merged while mapping branches and scenario sources remain explicit.

## [2026-07-27] lint | Merged distributed-heterogeneity strategy

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed both the latency summary and total framework contain exactly one numbered distributed-heterogeneity strategy.
- Confirmed the merged strategy retains explicit asymmetric-replica balancing and symmetric-replica mapping branches, while both scenario cases and raw sources remain separate.

## [2026-07-27] update | Number reasons to match parallel strategies

- Replaced the distributed-heterogeneity reason bullets with one numbered reason corresponding to the single merged parallel strategy.
- Kept common parameter reasoning, asymmetric-replica balancing and symmetric-replica mapping as explicit subpoints inside reason 1.
- Updated the schema, README, project Skill and template so reasons must match parallel strategies by number; mapping branches merged into one strategy must be explained inside the corresponding reason item.
- Applied the same one-to-one numbering to the mature homogeneous and local-heterogeneity branches; stability-first knowledge gaps remain unnumbered because they do not contain mature strategies.

## [2026-07-27] lint | One-to-one strategy and reason numbering

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed homogeneous, local-heterogeneity and distributed-heterogeneity branches each contain one numbered strategy and one corresponding numbered reason in both the latency summary and total framework.
- Confirmed the distributed reason retains common parameter reasoning plus explicit asymmetric and symmetric mapping explanations inside reason 1.

## [2026-07-27] update | Remove redundant reason correspondence labels

- Removed the visible “对应并行策略 1” label from all mature reason items.
- Kept the shared `1.` numbering and placed the reason content directly after it; one-to-one correspondence remains implicit in the matching strategy and reason numbers.
- Updated the template wording to describe shared numbering without generating the redundant label.

## [2026-07-27] lint | Direct reason numbering

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed no maintained concept, schema, README, Skill, workflow or template contains the visible “对应并行策略” label.
- Confirmed all mature reason sections retain direct numbered content beginning with `1.`.

## [2026-07-27] update | Expand local-heterogeneity scene definition

- Expanded the local-heterogeneity definition to cover stable anomaly identification, known rank/speed/location, concentration or remapping into one local execution unit, unaffected structure outside that unit, and model support for local rank/stage/layer/load adjustment.
- Clarified that local heterogeneity is determined by whether the impact can be contained, not by slow-GPU count: multiple anomalies can remain local if one unit contains them, while even one slow GPU is not locally isolatable when its impact cannot be remapped or rebalanced.
- Added explicit boundaries to homogeneous and distributed heterogeneity and synchronized the latency summary, both objective branches of the total framework, schema and project Skill.

## [2026-07-27] lint | Detailed local-heterogeneity definition

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the local definition records stable anomaly detection, rank/speed/location, local topology scope, remapping capability, unaffected external structure, and boundaries to homogeneous and distributed heterogeneity.
- Confirmed the immutable single-slow-GPU raw source was not modified.

## [2026-07-30] ingest | S7 five-slow 2/1/1/1 Evolve evidence

- Created immutable source snapshot: `raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md`.
- Created candidate review: `outputs/s7-five-slow-2-1-1-1-candidate-review-2026-07-30.md`.
- Updated: `entities/scoreexpert.md`, `concepts/deployment-objective-knowledge-framework.md`, `concepts/latency-first-experience-summary.md`, and `index.md`.
- Admission result: `KEEP_FOR_VALIDATION`; the run evaluated `65/873` candidates and has no real-training Evaluation, so mature deployment rules were not changed.

## [2026-07-30] governance | Restore Wiki as the formal experience authority

- Confirmed the formal authority chain is `entities/scoreexpert.md` → `concepts/deployment-objective-knowledge-framework.md` → `concepts/latency-first-experience-summary.md` → `raw/articles/*.md`.
- Updated the global `scoreexpert-scenario-analysis` Skill so the default Evolve pipeline no longer writes `/Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/experiences.json`.
- Reclassified the JSON project as a historical structured MVP/compatibility store and retired its mistakenly active S7 record.

## [2026-07-30] lint | S7 Wiki authority correction

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; Wiki structural checks and `git diff --check` passed.
- Confirmed the S7 raw body hash matches the immutable snapshot and its upstream `original_sha256`.
- Confirmed the revised Skill pipeline exposes no JSON-KB write option; Python compilation, Skill frontmatter validation, and all 12 legacy JSON compatibility tests passed.

## [2026-07-30] governance | Add manual review gate before raw and concepts

- Changed the Evolve workflow to stop after producing `scenario_analysis.md` in the run directory; simulation completion no longer imports raw or updates concepts.
- Added an explicit owner gate: the user edits and reviews the draft, then separately authorizes raw import and concepts update.
- Required raw to snapshot the exact user-reviewed file and required all subsequent concepts changes to derive from that raw source rather than unreviewed simulation artifacts.
- Updated `SCHEMA.md`, the Wiki maintenance Skill/workflow, and the global `scoreexpert-scenario-analysis` Skill, workflow, pipeline output, and UI metadata.

## [2026-07-30] lint | Manual review gate

- Result: `Pages: 3 | Errors: 0 | Review items: 0`; structural checks and `git diff --check` passed.
- Confirmed the pipeline reports `awaiting_manual_user_review` and `wiki_written: false` after simulation.
- Confirmed Skill and UI YAML through the system Ruby/YAML parser; the bundled Python validator could not start because this environment lacks `PyYAML`.

## [2026-07-30] update | Add simulation gaps and next-run recommendations

- Extended generated `scenario_analysis.md` drafts with two required sections after the five-part body: `未仿真的场景` and `下一步仿真建议`.
- Added explicit completed-scenario context to the 32-GPU four-node scenario factory; coverage is based on registered completed runs plus the current run, never config-file existence.
- Added prioritized controls for dual-slow-GPU placement and slow-card counts 3, 4, 6, 7 and 8 while keeping slow-card speed and other workload dimensions fixed.
- Updated Evolve tests, README, and the global scenario-analysis Skill/workflow. No raw snapshot or concepts experience was changed.

## [2026-07-30] lint | Simulation gap report sections

- Result: all 5 Evolve tests passed in 34.284 seconds.
- Result: `Pages: 3 | Errors: 0 | Review items: 0`; Wiki structural checks and `git diff --check` passed.
- Confirmed the 32-GPU scenario config preserves the user-confirmed coverage context through config load/serialization, and Skill frontmatter remains valid.

## [2026-07-30] fix | Derive simulation coverage from the experience library

- Removed the user-confirmed hard-coded coverage list from the 32-GPU scenario factory.
- Made report generation read `concepts/latency-first-experience-summary.md`, follow its raw scenario links, and distinguish mature experience from `KEEP_FOR_VALIDATION`.
- Changed count and dual-slow topology recommendations to subtract experience-library coverage plus the current run; user-spoken lists and config-file existence are no longer coverage authorities.
- Added a parser test for summary-to-raw coverage extraction. No raw snapshot or concepts experience content was changed.

## [2026-07-30] lint | Experience-library-derived coverage

- Result: all 6 Evolve tests passed in 34.044 seconds.
- Confirmed the current Wiki resolves four mature scenarios (normal, single slow, cross-affinity dual slow, symmetric four slow) and one `KEEP_FOR_VALIDATION` five-slow scenario.
- Confirmed the generated gap now recommends dual-slow same-node/same-affinity variants and slow-card counts 3, 6, 7 and 8; it no longer recommends the already summarized cross-affinity dual-slow or four-slow cases.

## [2026-07-30] review | Approve S7 five-slow source and concepts

- The knowledge-base owner confirmed that `DAGBuilder_Evolve/outputs/s7-five-slow-2-1-1-1_20260730_144533/scenario_analysis.md` passed manual review and authorized raw/concepts admission.
- The reviewed file SHA-256 is `3896fd84269edf7701961cf5968700af02f25cc9c072024f6615556fc95e6c48`, exactly matching `original_sha256` in the existing immutable snapshot `raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md`; no duplicate raw snapshot was created.
- Revalidated the two concepts against that raw source. Their existing S7 case and source link already match the reviewed report, so no semantic rewrite was needed.
- Admission remains `KEEP_FOR_VALIDATION`: manual source review authorizes Wiki inclusion but does not replace the missing real-training Evaluation or the unassessed `808/873` candidates, and no mature-experience promotion was authorized.

## [2026-07-30] admission | Promote approved S7 to formal experience

- Clarified the owner policy: “审核通过并授权入库” means formal mature admission, not merely source-content review.
- Changed S7 from `KEEP_FOR_VALIDATION` to `ACCEPT_EXPERIENCE` and added its distinct distributed-heterogeneity rule to both objective concepts: use `TP=1,DP=2`, derive integer PP from `PP=active_gpu/(TP×DP)`, and choose MBN within deep-pipeline memory, bubble and scheduling boundaries.
- Kept direct reuse restricted to the reviewed raw source's 32-card topology, model, workload, five-slow 2/1/1/1 placement and fixed Rank mapping. The `65/873` search coverage, four equivalent optima and missing real-training Evaluation remain explicit evidence limitations.
- Updated the ScoreExpert entity, index, candidate review and both maintenance Skills so future owner-approved reports default to `ACCEPT_EXPERIENCE`; no immutable raw source was modified.

## [2026-07-30] retract | Withdraw S7 formal experience admission

- The knowledge-base owner explicitly withdrew the prior S7 approval after identifying an audit mistake.
- Removed the S7 `TP=1,DP=2` deep-PP rule and its corresponding reason from both objective concepts, so it is no longer available for direct deployment inference.
- Restored S7 to `KEEP_FOR_VALIDATION` in the candidate review, entity and index. The existing raw snapshot remains immutable as historical simulation evidence; no source file was deleted or rewritten.
- Kept the general owner policy unchanged: a future “审核通过并授权入库” still means `ACCEPT_EXPERIENCE`, unless that approval is later explicitly withdrawn as in this case.

## [2026-07-30] workflow | Flatten Evolve review-draft outputs

- Changed the scenario-analysis pipeline to use a temporary run directory only while simulation and evidence validation are active.
- After successful validation, the pipeline now moves the sole review draft to `DAGBuilder_Evolve/outputs/<scenario-id>_<timestamp>_scenario_analysis.md` and removes the temporary directory and supporting artifacts.
- Flattened the existing S3, S4, S7 and S12 review drafts into the `outputs/` root; no scenario subdirectories remain.
- Updated the Evolve README, Wiki schema, maintenance workflow and global scenario-analysis Skill. Existing immutable raw `source_path` fields remain historical and were not rewritten.
