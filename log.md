# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete

## [2026-07-13] create | ScoreExpert 部署经验 Wiki initialized

- Domain: ScoreExpert GPU 部署经验、证据、边界与待验证假设。
- Created: `SCHEMA.md`, `index.md`, `log.md`, layer directories and lint workflow.

## [2026-07-13] ingest | ScoreExpert 正式经验与学习状态快照

- Raw sources: `raw/articles/scoreexpert-experience-store-2026-07-13.md`, `raw/articles/scoreexpert-source-registry-2026-07-13.md`, `raw/articles/scoreexpert-learning-status-2026-07-13.md`.
- Wiki pages: `entities/scoreexpert.md`, five concept pages, one comparison page and one filed query.
- Navigation: `index.md` updated to 8 pages.
- Source policy: two legacy report sources remain explicitly `unverified_legacy`; no Evaluation evidence was invented.

## [2026-07-13] lint | 1 review item found

- Structural errors: 0.
- Review item: `concepts/unverified-deployment-hypotheses.md` intentionally uses `confidence: low` because all listed hypotheses are unverified.
- Checks: orphan pages, broken wikilinks, index coverage, frontmatter, tag taxonomy, raw snapshot SHA-256, upstream source drift, page size and log rotation.

## [2026-07-13] update | Git maintenance baseline

- Added repository usage and maintenance guidance in `README.md`.
- Added `.gitignore` for macOS, Python, local environment and Obsidian per-device state.
- Added `.gitattributes` for stable LF line endings and Markdown/Python diffs.
- Prepared the complete Wiki as the initial `main` branch commit.

## [2026-07-13] create | Project-local Codex skill

- Added `.codex/skills/maintain-scoreexpert-wiki/SKILL.md` for project-specific ingest, query, lint, conflict, archive and Git workflows.
- Added `references/workflows.md` and `references/templates.md` for progressive disclosure.
- Reused the project-level `scripts/lint_wiki.py` instead of duplicating validation logic inside the skill.
- Added the skill invocation entry to `README.md`.
- Validation: skill name, YAML frontmatter, `agents/openai.yaml`, reference links and TODO scan passed with Ruby/YAML; Wiki lint reported 0 structural errors and the expected low-confidence review item.
- Environment note: the standard `quick_validate.py` could not import `yaml`, so no dependency was installed or vendored solely for validation.

## [2026-07-13] ingest | 32 卡基线 score strategy 分析

- Created immutable source snapshot: `raw/articles/32gpu-baseline-score-strategy-analysis-2026-07-13.md`.
- Original source SHA-256: `a445f9654b5cf16e30cb4a4d0b0b20bcc336bade358442630d57f593540bc88c`; raw body SHA-256: `eb5f2486a2181478da50d40837221d6a6f43068e955be7ad8529f86bd00bccf7`.
- Updated: `concepts/homogeneous-32gpu-baseline.md`, `comparisons/homogeneous-vs-single-slow-gpu.md`, and `index.md`.
- Classification: source-backed refinement of the existing active 32-GPU homogeneous baseline; no duplicate page created.
- Evidence: score derivation and topology explanation strengthened; direct Evaluation remains absent, so confidence stays `medium`.
- Governance: the Wiki now has an immutable snapshot; the previously imported source-registry snapshot labels this report `unverified_legacy`, while the current upstream KB has moved to schema v3 and no longer exposes the old `data/sources.json` path.
- Git: changes intentionally left uncommitted.

## [2026-07-13] lint | 2 review items after baseline ingest

- Structural errors: 0.
- Expected review: `concepts/unverified-deployment-hypotheses.md` keeps `confidence: low` because its hypotheses remain unverified.
- Source drift review: the immutable `scoreexpert-experience-store-2026-07-13.md` snapshot records upstream SHA-256 `5b2d812e...`, while the current upstream `data/experiences.json` is schema v3 with SHA-256 `5a7c3655...`.
- Scope decision: did not mix the changed upstream experience store into this single-source ingest; it requires a separate immutable snapshot and compatibility review.
