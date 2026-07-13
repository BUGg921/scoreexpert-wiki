# ScoreExpert Wiki 模板

## Raw 来源快照

````markdown
---
source_url:
source_path: /original/path
ingested: YYYY-MM-DD
sha256: <Markdown 正文 SHA-256>
original_sha256: <原文件 SHA-256>
---

# 原始来源：标题

> 导入时间、原路径和用途说明。

```text
完整来源内容
```
````

## 知识页 frontmatter

```markdown
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [scoreexpert, deployment]
sources: [raw/articles/source.md]
confidence: high | medium | low
contested: false
contradictions: []
---
```

## 正式经验页面

```markdown
# 标题

## Scenario
- 总卡数、每节点卡数、亲和组
- 慢卡数量、ID、速度倍率、分布和 rank mapping
- 模型、batch、显存和搜索空间

## First candidate
`PP=?, TP=?, DP=?, MBN=?`

## Evidence
### Score evidence
### Topology evidence
### Evaluation evidence

## Boundaries
### Applies when
### Fails when

## Evidence gaps
```

## 查询结论页面

```markdown
# 问题

## Answer
## Decision flow
## Evidence and confidence
## Boundaries
## Related pages
```

## 日志条目

```markdown
## [YYYY-MM-DD] ingest | 来源标题

- Created: `raw/...`, `concepts/...`.
- Updated: `index.md`, related backlink pages.
- Confidence or conflict changes: ...
```
