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
