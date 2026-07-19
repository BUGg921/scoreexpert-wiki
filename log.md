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
